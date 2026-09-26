import json
import logging
from config.paths import LANG_DIR

log = logging.getLogger("HangupTool")

DEFAULT_LANG = "zh_cn"

_current_lang = DEFAULT_LANG
_translations: dict[str, str] = {}          # 当前语言
_fallback_translations: dict[str, str] = {} # 中文 fallback


def _read_lang_file(code: str) -> dict:
    path = LANG_DIR / f"{code}.json"
    if not path.exists():
        log.warning(f"语言文件不存在: {path}")
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        log.error(f"加载语言文件失败 {path}: {e}")
        return {}


def load_language(code: str) -> bool:
    global _current_lang, _translations, _fallback_translations

    # 无论加载哪种语言，都先把中文作为 fallback 准备好
    if not _fallback_translations:
        fallback_data = _read_lang_file(DEFAULT_LANG)
        _fallback_translations = fallback_data.get("strings", {})
        if not _fallback_translations:
            log.warning(f"默认语言 {DEFAULT_LANG} 加载失败，将无法回退")

    # 若请求的就是中文，直接复用 fallback
    if code == DEFAULT_LANG:
        if not _fallback_translations:
            return False
        _current_lang = DEFAULT_LANG
        _translations = _fallback_translations
        log.info(f"已加载语言: {code} ({len(_translations)} 条)")
        return True

    data = _read_lang_file(code)
    if not data:
        # 目标语言读取失败 → 保持当前状态，或退回到中文
        log.warning(f"语言 {code} 加载失败，回退到 {DEFAULT_LANG}")
        _current_lang = DEFAULT_LANG
        _translations = _fallback_translations
        return False

    _current_lang = code
    _translations = data.get("strings", {})
    log.info(
        f"已加载语言: {code} "
        f"({len(_translations)} 条, fallback {len(_fallback_translations)} 条)"
    )
    return True


def tr(key: str, **kwargs) -> str:
    """
    翻译 key。查找顺序：
      1. 当前语言
      2. 中文 fallback
      3. key 本身（理论上不会走到这里，除非中文文件也没这个 key）
    """
    text = _translations.get(key)
    if text is None:
        text = _fallback_translations.get(key)
    if text is None:
        text = key

    if kwargs:
        try:
            text = text.format(**kwargs)
        except (KeyError, IndexError):
            pass
    return text


def current_language() -> str:
    return _current_lang


def available_languages() -> dict[str, str]:
    """扫描 LANG_DIR，返回 {code: 显示名}"""
    result: dict[str, str] = {}
    if not LANG_DIR.exists():
        return result
    for path in sorted(LANG_DIR.glob("*.json")):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            meta = data.get("_meta", {})
            result[meta.get("code", path.stem)] = meta.get("name", path.stem)
        except Exception as e:
            log.warning(f"读取语言元信息失败 {path}: {e}")
    return result