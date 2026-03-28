import time
import os
from PyQt5.QtCore import QThread, pyqtSignal

from pymobiledevice3.lockdown import create_using_usbmux
from pymobiledevice3.services.afc import AfcService
from pymobiledevice3.services.diagnostics import DiagnosticsService

from modules.utils import resource_path
from modules.payload import build_db_from_sql

class ActivationThread(QThread):
    status = pyqtSignal(str)
    success = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, backend_url):
        super().__init__()
        # Store backend_url passed from MainWindow
        self.backend_url = backend_url

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

            # Path updated to use the new 'assets' directory
            sql_path = resource_path(os.path.join('assets', 'payload.sql'))
            
            # Use self.backend_url instead of global BACKEND_URL
            if tuple(int(x) for x in values.get('ProductVersion').split('.')) >= (10, 3):
                payload_db = build_db_from_sql(sql_path, self.backend_url, '/private/var/containers/Shared/SystemGroup/systemgroup.com.apple.mobilegestaltcache/Library/Caches/com.apple.MobileGestalt.plist')
            else:
                payload_db = build_db_from_sql(sql_path, self.backend_url, '/private/var/mobile/Library/Caches/com.apple.MobileGestalt.plist')

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