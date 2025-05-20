import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget
from celulares import MobileTab
from notebooks import NotebookTab
from chips import SimTab

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gerenciador de Aparelhos Corporativos")
        self.setGeometry(100, 100, 1000, 600)

        tabs = QTabWidget()
        tabs.addTab(MobileTab(), "Celulares")
        tabs.addTab(NotebookTab(), "Notebooks")
        tabs.addTab(SimTab(), "Chips SIM")
        self.setCentralWidget(tabs)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())
