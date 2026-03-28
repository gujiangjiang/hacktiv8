import sys
from PyQt5.QtWidgets import QApplication

from modules.server import start_local_server
from modules.gui import MainWindow

if __name__ == '__main__':
    # Initialize the local server and get the dynamic URL first
    backend_url = start_local_server()
    
    app = QApplication(sys.argv)
    # Pass the backend URL into the main window
    window = MainWindow(backend_url)
    window.show()
    sys.exit(app.exec())