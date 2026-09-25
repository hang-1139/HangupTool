from PySide6.QtCore import QThread, Signal


class Worker(QThread):
    """
    所有自动化任务的基类。
    子类只需重写 execute()，循环中检查 self._is_running 即可优雅退出。
    """
    started_signal = Signal()          # 任务开始
    finished_signal = Signal()         # 任务结束
    error = Signal(str)                # 任务出错
    log = Signal(str)                  # 任务日志
    progress = Signal(int)             # 进度 0-100

    def __init__(self, name: str = "Worker", parent=None):
        super().__init__(parent)
        self.name = name
        self._is_running = False

    # ---------- 子类重写 ----------
    def execute(self):
        raise NotImplementedError("子类必须实现 execute()")

    # -----------------------------
    def run(self):
        self._is_running = True
        self.started_signal.emit()
        try:
            self.execute()
        except Exception as e:
            self.error.emit(f"{type(e).__name__}: {e}")
        finally:
            self._is_running = False
            self.finished_signal.emit()

    def stop(self):
        """请求停止（不阻塞，等待 run() 自然退出）"""
        self._is_running = False

    def is_running(self) -> bool:
        return self._is_running and self.isRunning()

    # ---------- 工具方法 ----------
    def interruptible_sleep(self, duration: float) -> bool:
        """可被 stop() 中断的睡眠，返回 False 表示已被请求停止"""
        steps = max(1, int(duration * 10))
        step = duration / steps
        for _ in range(steps):
            if not self._is_running:
                return False
            self.msleep(int(step * 1000))
        return True