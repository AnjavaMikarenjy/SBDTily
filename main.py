import sys
import os
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebChannel import QWebChannel
from PyQt6.QtCore import QUrl 

from backend.api import Backend

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BD TILY DIANA")
        self.showMaximized()

        self.web = QWebEngineView(self)
        self.setCentralWidget(self.web)

        self.channel = QWebChannel()

        # ✅ on passe le webview ici
        self.backend = Backend(self.web)

        self.channel.registerObject("backend", self.backend)
        self.web.page().setWebChannel(self.channel)

        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        FRONTEND_PATH = os.path.join(BASE_DIR, "frontend", "index.html")

        self.web.load(QUrl.fromLocalFile(FRONTEND_PATH))



if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
