import sys
from unittest.mock import patch
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel

# Global variable to hold the simulated device state
SIMULATED_STATE = "DISCONNECTED"

# Mock class to simulate the lockdown client returned by create_using_usbmux
class MockLockdownClient:
    def get_value(self):
        global SIMULATED_STATE
        if SIMULATED_STATE == "SUPPORTED":
            # Simulate a supported older device (e.g., iPhone 5)
            # Make sure this device exists in your config.py SUPPORTED dictionary
            return {'ProductType': 'iPhone5,2', 'ProductVersion': '10.3.3', 'ActivationState': 'Unactivated'}
        elif SIMULATED_STATE == "UNSUPPORTED":
            # Simulate a newer, unsupported device
            return {'ProductType': 'iPhone14,2', 'ProductVersion': '16.0', 'ActivationState': 'Unactivated'}
        else:
            # Simulate 'No device connected' by raising an exception
            raise Exception("No device found")

# Mock function to replace the real create_using_usbmux during UI testing
def mock_create_using_usbmux(*args, **kwargs):
    global SIMULATED_STATE
    if SIMULATED_STATE == "DISCONNECTED":
        raise Exception("No device found")
    return MockLockdownClient()

# A simple control panel UI to change the simulated state on the fly
class SimulatorController(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("UI Simulator Control")
        self.setFixedSize(300, 150)
        
        layout = QVBoxLayout()
        
        self.btn_disc = QPushButton("Simulate: Disconnected")
        self.btn_disc.clicked.connect(lambda: self.set_state("DISCONNECTED"))
        
        self.btn_supp = QPushButton("Simulate: Supported Device (iPhone5,2)")
        self.btn_supp.clicked.connect(lambda: self.set_state("SUPPORTED"))
        
        self.btn_unsupp = QPushButton("Simulate: Unsupported Device (iPhone14,2)")
        self.btn_unsupp.clicked.connect(lambda: self.set_state("UNSUPPORTED"))
        
        layout.addWidget(QLabel("Change Device State in Real-Time:"))
        layout.addWidget(self.btn_disc)
        layout.addWidget(self.btn_supp)
        layout.addWidget(self.btn_unsupp)
        self.setLayout(layout)

    def set_state(self, state):
        global SIMULATED_STATE
        SIMULATED_STATE = state

if __name__ == '__main__':
    # 1. Patch the create_using_usbmux function ONLY in the gui module.
    # This tricks gui.py into using our mock function instead of real USB polling.
    patcher = patch('modules.gui.create_using_usbmux', side_effect=mock_create_using_usbmux)
    patcher.start()

    # 2. Import your original modules AFTER the patch is applied
    from modules.server import start_local_server
    from modules.gui import MainWindow

    # 3. Initialize the app normally
    backend_url = start_local_server()
    app = QApplication(sys.argv)
    
    # Show your Main UI
    window = MainWindow(backend_url)
    window.show()
    
    # Show the Simulator Control Panel
    controller = SimulatorController()
    controller.show()
    
    # Run the application loop
    sys.exit(app.exec())