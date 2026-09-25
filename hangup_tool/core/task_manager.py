from PySide6.QtCore import QObject, Signal
from core.worker import Worker


class TaskManager(QObject):
    """
    统一管理所有 Worker 的生命周期，并对外抛出统一的信号。
    后续想加新任务，只要 new 一个 Worker，register 一下即可。
    """
    task_started = Signal(str)         # (task_name)
    task_finished = Signal(str)        # (task_name)
    task_error = Signal(str, str)      # (task_name, error_msg)
    task_log = Signal(str, str)        # (task_name, log_msg)
    task_progress = Signal(str, int)   # (task_name, value)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._workers: dict[str, Worker] = {}

    def register(self, name: str, worker: Worker):
        if name in self._workers:
            raise ValueError(f"任务 '{name}' 已存在")
        self._workers[name] = worker

        worker.started_signal.connect(lambda: self.task_started.emit(name))
        worker.finished_signal.connect(lambda: self.task_finished.emit(name))
        worker.error.connect(lambda msg: self.task_error.emit(name, msg))
        worker.log.connect(lambda msg: self.task_log.emit(name, msg))
        worker.progress.connect(lambda v: self.task_progress.emit(name, v))

    def start(self, name: str):
        w = self._workers.get(name)
        if w and not w.isRunning():
            w.start()

    def stop(self, name: str, wait_ms: int = 3000):
        w = self._workers.get(name)
        if w and w.isRunning():
            w.stop()
            w.wait(wait_ms)

    def stop_all(self, wait_ms: int = 3000):
        for name in list(self._workers.keys()):
            self.stop(name, wait_ms)

    def is_running(self, name: str) -> bool:
        w = self._workers.get(name)
        return bool(w and w.isRunning())