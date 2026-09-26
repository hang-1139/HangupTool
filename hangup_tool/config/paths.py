from pathlib import Path

# 项目根目录（config/paths.py 的上两层）
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# 所有用户数据统一放在这里
DATA_DIR = PROJECT_ROOT / "data"

# 应用设置文件
SETTINGS_FILE = DATA_DIR / "settings.json"

# 任务保存文件目录（每个任务一个文件，格式后续确定）
TASKS_DIR = DATA_DIR / "tasks"

# 日志目录（预留，将来可把日志也落盘）
LOGS_DIR = DATA_DIR / "logs"

# 语言文件目录
LANG_DIR = DATA_DIR / "lang"


def ensure_dirs():
    """启动时调用，确保所有需要的目录都存在"""
    for d in (DATA_DIR, TASKS_DIR, LOGS_DIR):
        d.mkdir(parents=True, exist_ok=True)