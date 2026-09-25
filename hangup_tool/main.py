import sys
from PySide6.QtWidgets import QApplication

from config.paths import ensure_dirs
from gui.main_window import MainWindow
from utils.logger import setup_logger


def main():
    # 1) 先确保数据目录存在（settings 加载、日志文件都需要它）
    ensure_dirs()

    # 2) 初始化日志
    setup_logger()

    app = QApplication(sys.argv)
    app.setApplicationName("HangupTool")
    app.setOrganizationName("HangupTool")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()