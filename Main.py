
#test to check Orcalab Datafangst API
from PySide6.QtWidgets import QApplication
import sys
from gui import MainWindow


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    w.inputChanged()
    sys.exit(app.exec())
