from core.task_file import TaskFile
from core.worker import Worker
from core.tasks import DemoTask


def build_worker(task_file: TaskFile) -> Worker:
    """
    把 TaskFile 编译成可执行的 Worker。

    ⚠️ 当前为占位实现：无论任务内容如何，都返回 DemoTask。
    等 .hpt 的 flow.steps 语义定下来后，这里会改为：
      1. 遍历 steps
      2. 为每个 step 生成对应的动作对象
      3. 用一个通用 Worker 顺序执行
    """
    return DemoTask()