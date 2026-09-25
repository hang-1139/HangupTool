import logging
import sys
from PySide6.QtCore import QObject, Signal


class LogEmitter(QObject):
    """把日志通过 Qt 信号发给 GUI 线程，保证线程安全"""
    message = Signal(str, str)  # (level, formatted_message)


log_emitter = LogEmitter()


class QtLogHandler(logging.Handler):
    def __init__(self, emitter: LogEmitter):
        super().__init__()
        self.emitter = emitter

    def emit(self, record: logging.LogRecord):
        try:
            msg = self.format(record)
            self.emitter.message.emit(record.levelname, msg)
        except Exception:
            self.handleError(record)


def setup_logger() -> logging.Logger:
    logger = logging.getLogger("HangupTool")
    if logger.handlers:  # 避免重复初始化
        return logger

    logger.setLevel(logging.DEBUG)
    fmt = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s", "%H:%M:%S")

    # 控制台输出
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(fmt)
    logger.addHandler(console)

    # GUI 输出
    qt_handler = QtLogHandler(log_emitter)
    qt_handler.setFormatter(fmt)
    logger.addHandler(qt_handler)

    return logger