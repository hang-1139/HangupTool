import threading
from enum import Enum

from PySide6.QtCore import QThread, Signal


class ExitMode(Enum):
    COUNT = "count"       # 执行 N 次后退出
    SIGNAL = "signal"     # 等待任务内部触发退出信号
    FOREVER = "forever"   # 永远执行，直到用户停止


class Worker(QThread):
    """
    所有自动化任务的基类。

    子类只需实现 execute_once(iteration)，描述"一次完整任务"是什么。
    循环、暂停、退出模式、间隔都由基类处理。
    """

    # ---- 生命周期信号 ----
    started_signal = Signal()
    finished_signal = Signal(str)   # 携带结束原因
    paused_signal = Signal()
    resumed_signal = Signal()

    # ---- 任务事件信号 ----
    error = Signal(str)
    log = Signal(str)
    iteration_done = Signal(int)    # 累计完成的迭代次数（从 1 开始）

    # ---- 结束原因常量 ----
    REASON_USER = "user"
    REASON_COMPLETED = "completed"
    REASON_LOGIC = "logic"
    REASON_ERROR = "error"

    def __init__(self, name: str = "Worker", parent=None):
        super().__init__(parent)
        self.name = name

        # 运行状态
        self._is_running = False
        self._is_paused = False
        self._pause_event = threading.Event()
        self._pause_event.set()          # set = 未暂停

        # 运行配置（由外部注入）
        self.exit_mode = ExitMode.FOREVER
        self.max_iterations = 0          # 仅 COUNT 模式使用
        self.interval = 1.0              # 0 表示无间隔

        # 运行进度
        self._current_iteration = 0
        self._stop_reason = self.REASON_COMPLETED

    # ================= 子类实现 =================
    def execute_once(self, iteration: int):
        """
        执行一次完整任务。
        iteration 从 0 开始计数。
        实现中应周期性调用 self.interruptible_sleep() 以响应暂停/停止。
        """
        raise NotImplementedError("子类必须实现 execute_once()")

    # ================= 线程入口 =================
    def run(self):
        self._is_running = True
        self._is_paused = False
        self._pause_event.set()
        self._current_iteration = 0
        self._stop_reason = self.REASON_COMPLETED

        self.started_signal.emit()
        try:
            self._main_loop()
        except Exception as e:
            self._stop_reason = self.REASON_ERROR
            self.error.emit(f"{type(e).__name__}: {e}")
        finally:
            self._is_running = False
            self._is_paused = False
            self._pause_event.set()
            self.finished_signal.emit(self._stop_reason)

    def _main_loop(self):
        while self._is_running:
            # ① 暂停栅栏
            if not self._wait_if_paused():
                self._stop_reason = self.REASON_USER
                break

            # ② 次数限制检查
            if self.exit_mode == ExitMode.COUNT and self.max_iterations > 0:
                if self._current_iteration >= self.max_iterations:
                    self._stop_reason = self.REASON_COMPLETED
                    break

            # ③ 执行一次
            self.execute_once(self._current_iteration)
            self._current_iteration += 1
            self.iteration_done.emit(self._current_iteration)

            # ④ 间隔（如果 > 0）
            if self.interval > 0 and self._is_running:
                if not self.interruptible_sleep(self.interval):
                    self._stop_reason = self.REASON_USER
                    break

    # ================= 外部控制 =================
    def stop(self):
        self._is_running = False
        self._pause_event.set()          # 唤醒暂停中的线程以便退出

    def pause(self):
        if self._is_running and not self._is_paused:
            self._is_paused = True
            self._pause_event.clear()
            self.paused_signal.emit()

    def resume(self):
        if self._is_running and self._is_paused:
            self._is_paused = False
            self._pause_event.set()
            self.resumed_signal.emit()

    def request_logic_exit(self):
        """任务内部调用：触发逻辑退出"""
        self._stop_reason = self.REASON_LOGIC
        self._is_running = False

    # ================= 状态查询 =================
    def is_running(self) -> bool:
        return self._is_running and self.isRunning()

    def is_paused(self) -> bool:
        return self._is_paused

    def current_iteration(self) -> int:
        return self._current_iteration

    # ================= 工具方法（供子类调用） =================
    def interruptible_sleep(self, duration: float) -> bool:
        """
        分段睡眠，响应 stop 和 pause。
        返回 False 表示已被请求停止（应尽快退出）。
        暂停期间睡眠进度冻结，恢复后继续剩余时间。
        """
        if duration <= 0:
            return self._is_running

        steps = max(1, int(duration * 20))   # 每段 ~50ms
        step = duration / steps
        for _ in range(steps):
            if not self._is_running:
                return False
            if not self._wait_if_paused():
                return False
            self.msleep(max(1, int(step * 1000)))
        return True

    def _wait_if_paused(self) -> bool:
        """
        暂停时阻塞，恢复或停止时返回。
        返回 False 表示已停止（应退出）。
        """
        while self._is_running:
            if self._pause_event.wait(timeout=0.1):
                return True
        return False