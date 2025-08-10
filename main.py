# main.py
import sys
from PySide6.QtWidgets import QApplication
from gui import A2LSearchWindow


def main():
    app = QApplication(sys.argv)
    window = A2LSearchWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()