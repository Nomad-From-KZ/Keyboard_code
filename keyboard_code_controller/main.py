import sys
import ctypes
from PyQt6.QtWidgets import QApplication
from gui import CodeControllerGUI


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False


def main():
    # Warning check if running without Administrator privileges
    if not is_admin():
        print("[WARNING] Program is running without Administrator rights.")
        print("[WARNING] Windows may prevent hooking if the browser runs as Admin or UIPI is active.")

    app = QApplication(sys.argv)
    window = CodeControllerGUI()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()