import sys
from PySide6.QtWidgets import QApplication

from config.paths import ensure_dirs
from gui.main_window import MainWindow
from utils.logger import setup_logger
from utils.i18n import load_language
from utils.theme import apply_theme


def main():
    ensure_dirs()
    setup_logger()
    load_language("zh_cn")

    app = QApplication(sys.argv)
    app.setApplicationName("HangupTool")
    app.setOrganizationName("HangupTool")

    apply_theme(app)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()