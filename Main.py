
#test to check Orcalab Datafangst API
from PySide6.QtWidgets import QApplication
import sys
from gui import MainWindow
import api_requests as api

app = QApplication(sys.argv)
w = MainWindow()
w.show()
app.exec()
sys.exit()
