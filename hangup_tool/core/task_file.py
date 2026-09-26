import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any

from config.version import APP_VERSION, HPT_FORMAT_VERSION

log = logging.getLogger("HangupTool")

HPT_EXTENSION = ".hpt"


# ============ 异常 ============
class HPTError(Exception):
    """任务文件读写错误"""


class HPTVersionError(HPTError):
    """版本不兼容"""


# ============ 版本工具 ============
def _parse_version(v: str) -> tuple[int, ...]:
    parts = []
    for seg in v.split("."):
        seg = seg.strip()
        if not seg:
            break
        try:
            parts.append(int(seg))
        except ValueError:
            break
    return tuple(parts) or (0,)


def _cmp(a: tuple, b: tuple, op: str) -> bool:
    n = max(len(a), len(b))
    a = a + (0,) * (n - len(a))
    b = b + (0,) * (n - len(b))
    return {
        ">=": a >= b, "<=": a <= b,
        ">": a > b,  "<": a < b,
        "==": a == b, "!=": a != b,
    }[op]


def check_version_compatible(app_version: str, spec: str) -> bool:
    """支持 '>=0.1.0'、'>0.1,<2.0'、'==1.0.0'、'any'"""
    spec = (spec or "").strip()
    if not spec or spec.lower() == "any":
        return True

    app_v = _parse_version(app_version)
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        matched = False
        for op in (">=", "<=", "==", "!=", ">", "<"):
            if part.startswith(op):
                if not _cmp(app_v, _parse_version(part[len(op):]), op):
                    return False
                matched = True
                break
        if not matched:  # 无运算符，视为 ==
            if app_v != _parse_version(part):
                return False
    return True


# ============ 数据结构 ============
@dataclass
class TaskMeta:
    name: str = ""
    description: str = ""
    task_version: str = "1.0.0"
    supported_app_version: str = "any"
    supports_logic_exit: bool = False
    author: str = ""
    created_at: str = ""
    updated_at: str = ""


@dataclass
class TaskFile:
    format_version: int = HPT_FORMAT_VERSION
    meta: TaskMeta = field(default_factory=TaskMeta)
    flow: dict = field(default_factory=lambda: {"steps": []})

    # ---- 转换 ----
    def to_dict(self) -> dict:
        return {
            "format_version": self.format_version,
            "meta": asdict(self.meta),
            "flow": self.flow,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TaskFile":
        m = data.get("meta", {})
        return cls(
            format_version=data.get("format_version", HPT_FORMAT_VERSION),
            meta=TaskMeta(
                name=m.get("name", ""),
                description=m.get("description", ""),
                task_version=m.get("task_version", "1.0.0"),
                supported_app_version=m.get("supported_app_version", "any"),
                supports_logic_exit=m.get("supports_logic_exit", False),
                author=m.get("author", ""),
                created_at=m.get("created_at", ""),
                updated_at=m.get("updated_at", ""),
            ),
            flow=data.get("flow", {"steps": []}),
        )

    # ---- 保存 ----
    def save(self, path: Path):
        path = Path(path)
        if path.suffix != HPT_EXTENSION:
            path = path.with_suffix(HPT_EXTENSION)

        now = datetime.now().isoformat(timespec="seconds")
        if not self.meta.created_at:
            self.meta.created_at = now
        self.meta.updated_at = now

        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
        log.info(f"任务已保存: {path}")

    # ---- 加载 ----
    @classmethod
    def load(cls, path: Path) -> "TaskFile":
        path = Path(path)
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise HPTError(f"JSON 解析失败: {e}") from e
        except OSError as e:
            raise HPTError(f"读取文件失败: {e}") from e

        tf = cls.from_dict(data)

        # 格式版本校验
        if tf.format_version > HPT_FORMAT_VERSION:
            raise HPTVersionError(
                f"任务文件格式版本 {tf.format_version} 高于程序支持的 {HPT_FORMAT_VERSION}"
            )

        # 应用版本校验
        spec = tf.meta.supported_app_version
        if not check_version_compatible(APP_VERSION, spec):
            raise HPTVersionError(
                f"任务要求程序版本 {spec}，当前为 {APP_VERSION}"
            )

        log.info(f"任务已加载: {path}")
        return tf