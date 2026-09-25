from core.worker import Worker


class DemoTask(Worker):
    """
    示例任务：循环输出日志和进度。
    后续你可以把它替换成真实的自动化逻辑，例如：
      - 使用 pyautogui 点击 / 截图找图
      - 使用 pynput 监听按键
      - 使用 Selenium 操作网页
    """

    def __init__(self, interval: float = 1.0):
        super().__init__(name="DemoTask")
        self.interval = interval
        self._counter = 0

    def execute(self):
        self.log.emit(f"任务启动，间隔 = {self.interval}s")
        while self._is_running:
            self._counter += 1
            self.log.emit(f"第 {self._counter} 次执行")

            # 模拟执行耗时操作
            if not self.interruptible_sleep(self.interval):
                break

            self.progress.emit(self._counter % 100)

        self.log.emit("任务已退出")