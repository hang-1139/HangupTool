from pathlib import Path

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon, QPixmap

from config.paths import TEXTURES_DIR

# 缓存已缩放的图标，避免重复解码 128×128 的 png
_cache: dict[tuple[str, int], QIcon] = {}


def _icon_path(name: str) -> Path:
    return TEXTURES_DIR / "icons" / f"{name}.png"


def get_icon(name: str, size: int = 24) -> QIcon:
    """
    按名字加载图标并缩放到指定大小。
    - 文件缺失 / 解码失败 → 返回空 QIcon（按钮显示纯文字，不会崩）
    - 同名不同尺寸会被缓存
    """
    key = (name, size)
    if key in _cache:
        return _cache[key]

    path = _icon_path(name)
    if not path.exists():
        return QIcon()

    src = QPixmap(str(path))
    if src.isNull():
        return QIcon()

    scaled = src.scaled(
        QSize(size, size),
        Qt.KeepAspectRatio,
        Qt.SmoothTransformation,
    )
    icon = QIcon(scaled)
    _cache[key] = icon
    return icon


def get_app_icon() -> QIcon:
    """程序窗口图标，使用 textures/app_icon.png（若存在）"""
    path = TEXTURES_DIR / "app_icon.png"
    if not path.exists():
        return QIcon()
    return QIcon(str(path))