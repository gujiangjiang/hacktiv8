import sys
import os
import time
import sqlite3
import tempfile
import http.server
import threading
import re
import socket

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QVBoxLayout, QPushButton, QLabel, QMessageBox
)
from PyQt5.QtCore import QThread, pyqtSignal, QTimer

from pymobiledevice3.lockdown import create_using_usbmux
from pymobiledevice3.services.afc import AfcService
from pymobiledevice3.services.diagnostics import DiagnosticsService


SUPPORTED = {
    'iPhone4,1': {'9.3.5', '9.3.6'},

    'iPad2,1': {'8.4.1', '9.3.5'},
    'iPad2,2': {'9.3.5', '9.3.6'},
    'iPad2,3': {'9.3.5', '9.3.6'},
    'iPad2,4': {'8.4.1', '9.3.5'},

    'iPad2,5': {'8.4.1', '9.3.5'},
    'iPad2,6': {'9.3.5', '9.3.6'},
    'iPad2,7': {'9.3.5', '9.3.6'},

    'iPad3,1': {'8.4.1', '9.3.5'},
    'iPad3,2': {'9.3.5', '9.3.6'},
    'iPad3,3': {'9.3.5', '9.3.6'},

    'iPod5,1': {'8.4.1', '9.3.5'},

    'iPhone5,1': {'10.3.3', '10.3.4'},
    'iPhone5,2': {'10.3.3', '10.3.4'},

    'iPhone5,3': {'10.3.3', '10.3.4'},
    'iPhone5,4': {'10.3.3', '10.3.4'},

    'iPad3,4': {'10.3.3', '10.3.4'},
    'iPad3,5': {'10.3.3', '10.3.4'},
    'iPad3,6': {'10.3.3', '10.3.4'}
}

# pyinstaller resource path fix
def resource_path(name):
    base = getattr(sys, '_MEIPASS', os.path.abspath('.'))
    return os.path.join(base, name)

# --- Local Backend Server Implementation ---
class LocalBackendHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        # Extract User-Agent from headers
        user_agent = self.headers.get('User-Agent', '')
        
        # Parse model and build from User-Agent using regex
        model_match = re.search(r'model/([a-zA-Z0-9,]+)', user_agent)
        build_match = re.search(r'build/([a-zA-Z0-9]+)', user_agent)

        if model_match and build_match:
            model = model_match.group(1)
            build = build_match.group(1)

            # Prevent directory traversal attacks
            if '..' in model or '..' in build:
                self.send_response(403)
                self.end_headers()
                return

            # Construct the local file path for patched.plist
            base_dir = resource_path(os.path.join('backend', 'plists'))
            file_path = os.path.join(base_dir, model, build, 'patched.plist')

            # Serve the file if it exists
            if os.path.exists(file_path):
                self.send_response(200)
                self.send_header('Content-Type', 'application/xml')
                self.send_header('Content-Disposition', 'attachment; filename="patched.plist"')
                self.send_header('Content-Length', str(os.path.getsize(file_path)))
                self.end_headers()
                
                with open(file_path, 'rb') as f:
                    self.wfile.write(f.read())
                return

        # Return 403 Forbidden if parsing fails or file doesn't exist
        self.send_response(403)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'Forbidden')

    def log_message(self, format, *args):
        # Suppress logging to keep the console output clean
        pass

# Function to automatically get the current machine's local IP address
def get_local_ip():
    try:
        # Create a dummy socket to determine the preferred routing IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception:
        # Fallback to localhost if network is unreachable
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

def start_local_server():
    local_ip = get_local_ip()
    # Bind to 0.0.0.0 to allow access from the iOS device over Wi-Fi
    httpd = http.server.HTTPServer(("0.0.0.0", 0), LocalBackendHandler)
    port = httpd.server_address[1]
    
    # Run the server in a daemon thread so it closes when the main app exits
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    
    # Return the dynamically generated URL with the real local IP
    return f"http://{local_ip}:{port}"

# Initialize the local server and dynamically set the BACKEND_URL
BACKEND_URL = start_local_server()
# -------------------------------------------

def build_db_from_sql(sql_path, backend_url, target_path):
    with open(sql_path, 'r', encoding='utf-8') as f:
        sql = f.read()

    sql = sql.replace('BACKEND_URL', backend_url).replace('TARGET_PATH', target_path)

    tmp = tempfile.NamedTemporaryFile(delete=False)
    tmp.close()

    try:
        con = sqlite3.connect(tmp.name)
        con.executescript(sql)
        con.commit()
        con.close()

        with open(tmp.name, 'rb') as f:
            return f.read()
    finally:
        os.unlink(tmp.name)

class ActivationThread(QThread):
    status = pyqtSignal(str)
    success = pyqtSignal(str)
    error = pyqtSignal(str)

    def wait_for_device(self, timeout=160):
        deadline = time.monotonic() + timeout

        while time.monotonic() < deadline:
            try:
                lockdown = create_using_usbmux()
                DiagnosticsService(lockdown=lockdown).mobilegestalt(
                    keys=['ProductType']
                )
                return lockdown
            except Exception:
                time.sleep(2)

        raise TimeoutError()

    def push_payload(self, lockdown, payload_db):
        with AfcService(lockdown=lockdown) as afc:
            for filename in afc.listdir('Downloads'):
                afc.rm('Downloads/' + filename)
            time.sleep(3)

            afc.set_file_contents(
                'Downloads/downloads.28.sqlitedb',
                payload_db
            )
        DiagnosticsService(lockdown=lockdown).restart()
        return self.wait_for_device()

    def should_hactivate(self, lockdown):
        diag = DiagnosticsService(lockdown=lockdown)
        return diag.mobilegestalt(
            keys=['ShouldHactivate']
        ).get('ShouldHactivate')

    def run(self):
        try:
            lockdown = create_using_usbmux()
            values = lockdown.get_value()

            if values.get('ActivationState') == 'Activated':
                self.success.emit('Device is already activated')
                return

            sql_path = resource_path('payload.sql')
            if tuple(int(x) for x in values.get('ProductVersion').split('.')) >= (10, 3):
                payload_db = build_db_from_sql(sql_path, BACKEND_URL, '/private/var/containers/Shared/SystemGroup/systemgroup.com.apple.mobilegestaltcache/Library/Caches/com.apple.MobileGestalt.plist')
            else:
                payload_db = build_db_from_sql(sql_path, BACKEND_URL, '/private/var/mobile/Library/Caches/com.apple.MobileGestalt.plist')

            self.status.emit('Activating device...')

            for attempt in range(5):
                lockdown = self.push_payload(lockdown, payload_db)

                delay = 15 + attempt * 5
                time.sleep(delay)

                if self.should_hactivate(lockdown):
                    DiagnosticsService(lockdown=lockdown).restart()
                    self.success.emit('Done!')
                    return

                self.status.emit(f'Retrying activation\nAttempt {attempt + 1}/5')
                time.sleep(5)

            self.error.emit(
                'Activation failed after multiple attempts. Make sure the device is connected to the Wi-Fi.'
            )

        except TimeoutError:
            self.error.emit(
                'Device did not reconnect in time. Please ensure it is connected and try again.'
            )
        except Exception as e:
            self.error.emit(repr(e))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('hacktiv8 v1.1.0')
        self.setFixedSize(500, 200)

        self.status = QLabel('No device connected')
        self.activate = QPushButton('Activate Device')
        self.activate.setEnabled(False)

        layout = QVBoxLayout()
        layout.addWidget(self.status)
        layout.addWidget(self.activate)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.activate.clicked.connect(self.start_activation)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.poll_device)
        self.timer.start(1000)

    def poll_device(self):
        try:
            lockdown = create_using_usbmux()
            values = lockdown.get_value()

            product = values.get('ProductType')
            version = values.get('ProductVersion')

            is_supported = SUPPORTED.get(product)

            if not is_supported:
                self._set_state(f'Unsupported Device: {product}', False)
                return

            if version not in is_supported:
                self._set_state(f'Unsupported {product} iOS version: {version}', False)
                return

            self._set_state(f'Connected: {product} ({version})', True)

        except Exception:
            self._set_state('No device connected', False)

    def _set_state(self, text, enabled):
        self.status.setText(text)
        self.activate.setEnabled(enabled)

    def start_activation(self):
        QMessageBox.information(
            self,
            'Info',
            'Your device will now be activated. Please ensure it is connected to Wi-Fi.'
        )

        self.timer.stop()
        self.activate.setEnabled(False)

        self.worker = ActivationThread()
        self.worker.status.connect(self.status.setText)
        self.worker.success.connect(self.on_success)
        self.worker.error.connect(self.on_error)
        self.worker.start()

    def on_success(self, msg):
        self.status.setText(msg)
        QMessageBox.information(self, 'Success', msg)
        self.activate.setEnabled(True)
        self.timer.start(1000)

    def on_error(self, msg):
        QMessageBox.critical(self, 'Error', msg)
        self.status.setText('Error occurred')
        self.timer.start(1000)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())