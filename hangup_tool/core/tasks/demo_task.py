from core.worker import Worker
from utils.i18n import tr


class DemoTask(Worker):
    """示例任务：每次迭代打印一行日志。"""

    def __init__(self, interval: float = 1.0):
        super().__init__(name="DemoTask")
        self.interval = interval

    def execute_once(self, iteration: int):
        self.log.emit(tr("log.task_iteration", n=iteration + 1))