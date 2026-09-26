import sys
from PySide6.QtWidgets import QApplication

from config.paths import ensure_dirs
from gui.main_window import MainWindow
from utils.logger import setup_logger
from utils.i18n import load_language


def main():
    ensure_dirs()
    setup_logger()

    # 加载语言（暂时硬编码 zh_cn，将来从设置里读）
    load_language("zh_cn")

    app = QApplication(sys.argv)
    app.setApplicationName("HangupTool")
    app.setOrganizationName("HangupTool")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()