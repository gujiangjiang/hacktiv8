from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel, QMessageBox
)
from PyQt5.QtCore import QTimer

from pymobiledevice3.lockdown import create_using_usbmux

from modules.config import SUPPORTED
from modules.activator import ActivationThread

class MainWindow(QMainWindow):
    def __init__(self, backend_url):
        super().__init__()
        # Store the dynamic backend_url
        self.backend_url = backend_url

        self.setWindowTitle('hacktiv8 v2.0.0')
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

        # Pass the backend_url to the worker thread
        self.worker = ActivationThread(self.backend_url)
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