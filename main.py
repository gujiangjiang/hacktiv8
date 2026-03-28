import sys
from PyQt5.QtWidgets import QApplication

from modules.gui import MainWindow

if __name__ == '__main__':
    app = QApplication(sys.argv)
    # The main window now manages the server connection logic
    window = MainWindow()
    window.show()
    sys.exit(app.exec())