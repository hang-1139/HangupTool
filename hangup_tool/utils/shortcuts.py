from config.settings import settings

# 动作名 -> 默认快捷键（空字符串表示无快捷键）
DEFAULTS: dict[str, str] = {
    "start": "F5",
    "pause": "F8",
    "stop": "F9",
    "export_log": "Ctrl+Shift+S",
}


def get_shortcut(name: str) -> str:
    """读取快捷键，未设置时返回默认值"""
    return settings.get(f"shortcuts/{name}", DEFAULTS.get(name, ""))


def set_shortcut(name: str, value: str):
    settings.set(f"shortcuts/{name}", value)


def all_shortcuts() -> dict[str, str]:
    return {k: get_shortcut(k) for k in DEFAULTS}


def reset_all():
    """把所有快捷键恢复为默认值（仅写入内存，需要 save() 才落盘）"""
    for k, v in DEFAULTS.items():
        settings.set(f"shortcuts/{k}", v)


def save():
    settings.sync()