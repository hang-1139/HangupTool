import json
import logging
from typing import Any

from config.paths import SETTINGS_FILE, ensure_dirs

log = logging.getLogger("HangupTool")


class AppSettings:
    """
    基于 JSON 文件的配置管理。
    所有设置都保存在 data/settings.json。
    """

    def __init__(self):
        self._data: dict = {}
        self._load()

    def _load(self):
        ensure_dirs()
        if SETTINGS_FILE.exists():
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
            except (json.JSONDecodeError, OSError) as e:
                log.warning(f"读取设置文件失败，使用默认值：{e}")
                self._data = {}
        else:
            self._data = {}

    def save(self):
        ensure_dirs()
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2)
        except OSError as e:
            log.error(f"保存设置文件失败：{e}")

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def get_int(self, key: str, default: int = 0) -> int:
        try:
            return int(self._data.get(key, default))
        except (TypeError, ValueError):
            return default

    def get_bool(self, key: str, default: bool = False) -> bool:
        val = self._data.get(key, default)
        if isinstance(val, bool):
            return val
        return str(val).lower() in ("true", "1", "yes")

    def get_float(self, key: str, default: float = 0.0) -> float:
        try:
            return float(self._data.get(key, default))
        except (TypeError, ValueError):
            return default

    def set(self, key: str, value: Any):
        self._data[key] = value

    def sync(self):
        self.save()


settings = AppSettings()