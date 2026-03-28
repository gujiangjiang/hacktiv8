from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QMessageBox,
    QGroupBox, QLineEdit, QFormLayout, QGridLayout
)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QFont

from pymobiledevice3.lockdown import create_using_usbmux

from modules.config import SUPPORTED
from modules.activator import ActivationThread
# Import start_local_server to trigger it only when the button is clicked
from modules.server import start_local_server

class MainWindow(QMainWindow):
    def __init__(self, dummy_url=None): # dummy_url kept to prevent breaking test_ui.py
        super().__init__()
        
        # --- Server State Setup ---
        # Changed 'Externel' to 'Remote' as requested
        self.remote_url = "http://overcast302.dev/hacktiv8/server.php"
        self.local_url = None
        self.use_local = False
        # Set default backend to remote server
        self.backend_url = self.remote_url

        self.setWindowTitle('hacktiv8 v2.0.0')
        # Increase window size significantly to make text fully visible and layout clean
        self.setFixedSize(750, 450)

        # --- Font Styling ---
        # Create a basic bold and larger font for key elements
        self.bold_font = QFont()
        self.bold_font.setBold(True)
        self.bold_font.setPointSize(12)

        # --- Server Configuration Group ---
        server_group = QGroupBox("Server Configuration")
        server_group_layout = QVBoxLayout()
        # Ensure elements are not too cramped within the group
        server_group_layout.setContentsMargins(15, 15, 15, 15)
        
        # Form layout for detailed server information
        server_form = QFormLayout()
        
        # Display the server type (Remote/Local) in a non-editable QLineEdit for easy selection
        self.server_type_display = QLineEdit("Remote")
        self.server_type_display.setReadOnly(True)
        # Apply a simple stylesheet to make it look less like an input field, but still selectable
        self.server_type_display.setStyleSheet("""
            QLineEdit {
                background-color: transparent; 
                border: none;
                font-size: 11pt;
            }
        """)

        # Display the full server URL in a wider, non-editable QLineEdit to prevent text cutoff
        self.server_url_display = QLineEdit(self.backend_url)
        self.server_url_display.setReadOnly(True)
        self.server_url_display.setMinimumWidth(500) # Ensure long URLs fit
        # Style it to make it look like a clean, readonly value box
        self.server_url_display.setStyleSheet("""
            QLineEdit {
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                padding: 5px;
                border-radius: 4px;
                font-size: 11pt;
            }
        """)

        # Add rows to the form layout
        server_form.addRow("Server Type:", self.server_type_display)
        server_form.addRow("Server URL:", self.server_url_display)
        server_group_layout.addLayout(server_form)

        # HBoxLayout for server actions like switching and (future) starting local
        server_actions_layout = QHBoxLayout()
        # Toggle button to switch between Remote and Local servers
        self.server_toggle_btn = QPushButton('Switch to Local Server')
        self.server_toggle_btn.clicked.connect(self.toggle_server)
        
        # Push the button to the right for better visual flow
        server_actions_layout.addStretch() 
        server_actions_layout.addWidget(self.server_toggle_btn)
        server_group_layout.addLayout(server_actions_layout)

        # Set the main layout for the group box
        server_group.setLayout(server_group_layout)

        # --- Device Status Group ---
        device_group = QGroupBox("Device Status")
        device_group_layout = QVBoxLayout()
        # Ensure good spacing and margins within the group
        device_group_layout.setContentsMargins(15, 15, 15, 15)
        device_group_layout.setSpacing(10) # Set spacing between child widgets

        # Title label for overall status
        self.status_title = QLabel('Overall Connection Status:')
        self.status_title.setFont(self.bold_font)
        # Original status label for dynamic updates
        self.status = QLabel('No device connected')
        self.status.setWordWrap(True) # In case of very long errors
        self.status.setFont(QFont("Arial", 11))
        
        # Grid layout for detailed, easy-to-read device details
        device_details_layout = QGridLayout()
        device_details_layout.setSpacing(5) # Spacing between labels and values

        # Product Type detailed label and value
        product_label = QLabel("Product Type:")
        self.device_product_label = QLabel("-")
        self.device_product_label.setFont(self.bold_font)
        device_details_layout.addWidget(product_label, 0, 0)
        device_details_layout.addWidget(self.device_product_label, 0, 1)

        # iOS Version detailed label and value
        version_label = QLabel("iOS Version:")
        self.device_version_label = QLabel("-")
        self.device_version_label.setFont(self.bold_font)
        device_details_layout.addWidget(version_label, 1, 0)
        device_details_layout.addWidget(self.device_version_label, 1, 1)

        # Activation State detailed label and value
        activation_label = QLabel("Activation State:")
        self.device_activation_label = QLabel("-")
        self.device_activation_label.setFont(self.bold_font)
        device_details_layout.addWidget(activation_label, 2, 0)
        device_details_layout.addWidget(self.device_activation_label, 2, 1)

        # Assemble the detailed device group layout
        device_group_layout.addWidget(self.status_title)
        device_group_layout.addWidget(self.status)
        device_group_layout.addLayout(device_details_layout)
        
        # Set the main layout for the device group box
        device_group.setLayout(device_group_layout)

        # --- Main Action Button ---
        # Primary action button with prominent size and styling
        self.activate = QPushButton('Activate Device')
        self.activate.setFont(self.bold_font)
        self.activate.setMinimumHeight(45) # Make it look more like a button
        # Apply modern styling for normal, disabled, and hover states
        self.activate.setStyleSheet("""
            QPushButton {
                background-color: #007bff; /* Blue */
                color: white;
                border-radius: 6px;
                border: none;
                font-size: 13pt;
            }
            QPushButton:disabled {
                background-color: #cccccc; /* Greyed out */
                color: #666666;
            }
            QPushButton:hover {
                background-color: #0056b3; /* Darker blue on hover */
            }
        """)
        self.activate.setEnabled(False) # Start disabled until device connects
        self.activate.clicked.connect(self.start_activation)

        # --- Main Layout ---
        # Overall vertical layout for the central widget
        main_layout = QVBoxLayout()
        # Add generous content margins to the overall window
        main_layout.setContentsMargins(20, 20, 20, 20) 
        # Spacing between groups and the button
        main_layout.setSpacing(15) 

        # Add structured groups to the main layout
        main_layout.addWidget(server_group)
        main_layout.addWidget(device_group)
        
        # Add a stretchable spacer to push the main button to the bottom
        main_layout.addStretch() 
        
        # Center the main activation button horizontally
        main_button_layout = QHBoxLayout()
        main_button_layout.addStretch()
        main_button_layout.addWidget(self.activate)
        main_button_layout.addStretch()
        main_layout.addLayout(main_button_layout)

        # Set the main layout to a central container widget
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        # --- Device Polling Timer ---
        # Polling every 1 second, as original
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.poll_device)
        self.timer.start(1000)

    def toggle_server(self):
        """Toggle between remote and local backend servers."""
        if self.use_local:
            # Switch back to external/remote server
            self.use_local = False
            self.backend_url = self.remote_url
            # Correcting text to Remote as requested
            self.server_type_display.setText("Remote")
            self.server_url_display.setText(self.backend_url)
            self.server_toggle_btn.setText('Switch to Local Server')
        else:
            # Switch to local server
            if not self.local_url:
                # Start the local server ONLY on the first time it is requested
                self.local_url = start_local_server()
            
            self.use_local = True
            self.backend_url = self.local_url
            # Correcting text to Local
            self.server_type_display.setText("Local")
            self.server_url_display.setText(self.backend_url)
            self.server_toggle_btn.setText('Switch to Remote Server')

    def poll_device(self):
        try:
            lockdown = create_using_usbmux()
            values = lockdown.get_value()

            # Safely get values, defaulting to '-' if missing
            product = values.get('ProductType', '-')
            version = values.get('ProductVersion', '-')
            activation_state = values.get('ActivationState', '-')

            is_supported = SUPPORTED.get(product)

            # Updated status text to be cleaner with the detailed grid
            if not is_supported:
                self._set_state(f'Unsupported Device', False, product, version, activation_state)
                return

            if version not in is_supported:
                self._set_state(f'Unsupported {product} iOS version', False, product, version, activation_state)
                return

            # Success state with clear status title
            self._set_state(f'Connected and Supported', True, product, version, activation_state)

        except Exception:
            self._set_state('No device connected', False)

    def _set_state(self, status_text, enabled, product='-', version='-', activation_state='-'):
        # Clear detailed device information if no device is connected
        if status_text == 'No device connected':
            product = '-'
            version = '-'
            activation_state = '-'

        # Update both the general status label and detailed labels
        self.status.setText(status_text)
        self.device_product_label.setText(product)
        self.device_version_label.setText(version)
        self.device_activation_label.setText(activation_state)
        # Enable or disable the main action button
        self.activate.setEnabled(enabled)

    def start_activation(self):
        QMessageBox.information(
            self,
            'Info',
            'Your device will now be activated. Please ensure it is connected to Wi-Fi.'
        )

        # Stop the poll timer to prevent UI updates during processing
        self.timer.stop()
        self.activate.setEnabled(False)

        # Pass the current backend_url to the worker thread
        self.worker = ActivationThread(self.backend_url)
        self.worker.status.connect(self.status.setText)
        self.worker.success.connect(self.on_success)
        self.worker.error.connect(self.on_error)
        self.worker.start()

    def on_success(self, msg):
        self.status.setText(msg)
        QMessageBox.information(self, 'Success', msg)
        self.activate.setEnabled(True)
        # Restart the timer for continuous device polling
        self.timer.start(1000)

    def on_error(self, msg):
        QMessageBox.critical(self, 'Error', msg)
        self.status.setText('Error occurred')
        # Restart the timer for continuous device polling
        self.timer.start(1000)