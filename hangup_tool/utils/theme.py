from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtWidgets import QApplication

# ============ 字体 ============
# 中文黑体候选，按优先级排列；命中第一个可用的就用它
FONT_CANDIDATES = [
    "SimHei",                 # Windows 黑体
    "Microsoft YaHei UI",     # Windows 微软雅黑 UI
    "Microsoft YaHei",        # Windows 微软雅黑
    "PingFang SC",            # macOS 苹方
    "Heiti SC",               # macOS 黑体-简
    "Source Han Sans SC",     # 思源黑体
    "Noto Sans CJK SC",       # Linux 常见
    "WenQuanYi Micro Hei",    # Linux 文泉驿微米黑
]

# 等宽字体候选（日志区用）
MONO_CANDIDATES = [
    "Consolas",
    "JetBrains Mono",
    "Cascadia Mono",
    "Menlo",
    "Monaco",
    "DejaVu Sans Mono",
    "Courier New",
]

FONT_SIZE = 10   # pt

# ============ 颜色 ============
C = {
    "bg":         "#f5f6f7",   # 主背景
    "panel":      "#ffffff",   # 面板/输入框背景
    "border":     "#dcdfe4",   # 边框
    "border_hi":  "#3498db",   # 聚焦边框
    "text":       "#2c3e50",   # 主文字
    "text_muted": "#888888",   # 次要文字
    "hover":      "#eef3f8",   # 悬停背景
    "pressed":    "#dde8f3",   # 按下背景
    "disabled":   "#f0f0f0",   # 禁用背景
    "primary":    "#3498db",   # 主题色
    "success":    "#27ae60",   # 运行中
    "warning":    "#e67e22",   # 暂停
    "danger":     "#e74c3c",   # 错误
    "log_bg":     "#fafafa",   # 日志区背景
}


def _pick(candidates: list[str], fallback: str = "sans-serif") -> str:
    """从候选里挑第一个当前系统装了的字体"""
    families = set(QFontDatabase.families())
    for name in candidates:
        if name in families:
            return name
    return fallback


def apply_theme(app: QApplication):
    """程序启动时调用一次，把风格、字体、QSS 全部锁定"""
    # 1) 强制 Fusion 风格 —— 跨平台外观一致的根本
    app.setStyle("Fusion")

    # 2) 全局字体
    family = _pick(FONT_CANDIDATES)
    font = QFont(family, FONT_SIZE)
    font.setStyleStrategy(QFont.PreferAntialias)
    app.setFont(font)

    # 3) 全局 QSS
    mono = _pick(MONO_CANDIDATES, "monospace")
    app.setStyleSheet(_build_qss(family, mono))


def _build_qss(family: str, mono: str) -> str:
    c = C
    return f"""
    * {{
        font-family: "{family}";
        font-size: {FONT_SIZE}pt;
        outline: none;
    }}

    QWidget {{
        color: {c['text']};
        background-color: {c['bg']};
    }}

    QMainWindow, QDialog {{
        background-color: {c['bg']};
    }}

    /* ---------- 分组框 ---------- */
    QGroupBox {{
        background-color: {c['panel']};
        border: 1px solid {c['border']};
        border-radius: 6px;
        margin-top: 14px;
        padding: 12px 10px 10px 10px;
        font-weight: bold;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        left: 12px;
        padding: 0 4px;
        color: {c['text']};
        background-color: {c['panel']};
    }}

    /* ---------- 普通按钮 ---------- */
    QPushButton {{
        background-color: {c['panel']};
        border: 1px solid {c['border']};
        border-radius: 6px;
        padding: 6px 14px;
        min-height: 22px;
    }}
    QPushButton:hover {{
        background-color: {c['hover']};
        border-color: {c['primary']};
    }}
    QPushButton:pressed {{
        background-color: {c['pressed']};
    }}
    QPushButton:disabled {{
        color: {c['text_muted']};
        background-color: {c['disabled']};
        border-color: #e0e0e0;
    }}

    /* ---------- 小图标按钮 ---------- */
    QToolButton {{
        background-color: transparent;
        border: 1px solid transparent;
        border-radius: 4px;
        padding: 3px;
    }}
    QToolButton:hover {{
        background-color: {c['hover']};
        border-color: {c['border']};
    }}
    QToolButton:pressed {{
        background-color: {c['pressed']};
    }}
    QToolButton:disabled {{
        background-color: transparent;
    }}

    /* ---------- 文本输入 ---------- */
    QLineEdit, QPlainTextEdit, QTextEdit {{
        background-color: {c['panel']};
        border: 1px solid {c['border']};
        border-radius: 4px;
        padding: 4px 6px;
        selection-background-color: {c['primary']};
        selection-color: white;
    }}
    QLineEdit:focus, QPlainTextEdit:focus, QTextEdit:focus {{
        border-color: {c['border_hi']};
    }}
    QLineEdit:disabled, QPlainTextEdit:disabled, QTextEdit:disabled {{
        background-color: {c['disabled']};
        color: {c['text_muted']};
    }}

    /* ---------- 数字输入 ---------- */
    QSpinBox, QDoubleSpinBox {{
        background-color: {c['panel']};
        border: 1px solid {c['border']};
        border-radius: 4px;
        padding: 4px 6px;
    }}
    QSpinBox:focus, QDoubleSpinBox:focus {{
        border-color: {c['border_hi']};
    }}
    QSpinBox::up-button, QDoubleSpinBox::up-button,
    QSpinBox::down-button, QDoubleSpinBox::down-button {{
        width: 16px;
        border: none;
        background: transparent;
    }}
    QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {{
        image: none;
        border-left: 4px solid transparent;
        border-right: 4px solid transparent;
        border-bottom: 5px solid {c['text']};
        width: 0; height: 0;
    }}
    QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {{
        image: none;
        border-left: 4px solid transparent;
        border-right: 4px solid transparent;
        border-top: 5px solid {c['text']};
        width: 0; height: 0;
    }}

    /* ---------- 单选 ---------- */
    QRadioButton {{
        spacing: 6px;
    }}
    QRadioButton::indicator {{
        width: 14px;
        height: 14px;
        border-radius: 8px;
        border: 1px solid {c['border']};
        background-color: {c['panel']};
    }}
    QRadioButton::indicator:hover {{
        border-color: {c['primary']};
    }}
    QRadioButton::indicator:checked {{
        border: 4px solid {c['primary']};
        background-color: {c['panel']};
    }}
    QRadioButton:disabled {{
        color: {c['text_muted']};
    }}

    /* ---------- 复选 ---------- */
    QCheckBox {{
        spacing: 6px;
    }}
    QCheckBox::indicator {{
        width: 14px;
        height: 14px;
        border-radius: 3px;
        border: 1px solid {c['border']};
        background-color: {c['panel']};
    }}
    QCheckBox::indicator:checked {{
        background-color: {c['primary']};
        border-color: {c['primary']};
    }}
    QCheckBox:disabled {{
        color: {c['text_muted']};
    }}

    /* ---------- 日志区 ---------- */
    QTextEdit#logView {{
        font-family: "{mono}";
        background-color: {c['log_bg']};
    }}

    /* ---------- 状态标签（通过 dynamic property 切色） ---------- */
    QLabel#stateLabel {{
        font-weight: bold;
    }}
    QLabel#stateLabel[state="idle"]     {{ color: {c['text_muted']}; }}
    QLabel#stateLabel[state="running"]  {{ color: {c['success']}; }}
    QLabel#stateLabel[state="paused"]   {{ color: {c['warning']}; }}

    /* ---------- 菜单栏 ---------- */
    QMenuBar {{
        background-color: {c['panel']};
        border-bottom: 1px solid {c['border']};
    }}
    QMenuBar::item {{
        padding: 4px 10px;
        background: transparent;
    }}
    QMenuBar::item:selected {{
        background-color: {c['hover']};
    }}
    QMenu {{
        background-color: {c['panel']};
        border: 1px solid {c['border']};
        padding: 4px;
    }}
    QMenu::item {{
        padding: 5px 24px 5px 20px;
        border-radius: 4px;
    }}
    QMenu::item:selected {{
        background-color: {c['hover']};
    }}
    QMenu::separator {{
        height: 1px;
        background-color: {c['border']};
        margin: 4px 8px;
    }}

    /* ---------- 工具栏 ---------- */
    QToolBar {{
        background-color: {c['panel']};
        border-bottom: 1px solid {c['border']};
        spacing: 4px;
        padding: 4px;
    }}
    QToolBar QToolButton {{
        padding: 4px 10px;
    }}

    /* ---------- 状态栏 ---------- */
    QStatusBar {{
        background-color: {c['panel']};
        border-top: 1px solid {c['border']};
        color: {c['text_muted']};
    }}
    QStatusBar::item {{
        border: none;
    }}

    /* ---------- 选项卡 ---------- */
    QTabWidget::pane {{
        background-color: {c['panel']};
        border: 1px solid {c['border']};
        border-radius: 4px;
        top: -1px;
    }}
    QTabBar::tab {{
        background-color: {c['bg']};
        border: 1px solid {c['border']};
        border-bottom: none;
        border-top-left-radius: 4px;
        border-top-right-radius: 4px;
        padding: 5px 12px;
        margin-right: 2px;
    }}
    QTabBar::tab:selected {{
        background-color: {c['panel']};
        border-bottom: 1px solid {c['panel']};
    }}
    QTabBar::tab:hover:!selected {{
        background-color: {c['hover']};
    }}

    /* ---------- 分隔条 ---------- */
    QSplitter::handle {{
        background-color: {c['border']};
    }}
    QSplitter::handle:horizontal {{ width: 2px; }}
    QSplitter::handle:vertical   {{ height: 2px; }}

    /* ---------- 滚动条 ---------- */
    QScrollBar:vertical {{
        background: transparent;
        width: 10px;
        margin: 0;
    }}
    QScrollBar::handle:vertical {{
        background: #c8ccd1;
        border-radius: 5px;
        min-height: 24px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: #aab0b6;
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0; background: none;
    }}
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
        background: none;
    }}
    QScrollBar:horizontal {{
        background: transparent;
        height: 10px;
        margin: 0;
    }}
    QScrollBar::handle:horizontal {{
        background: #c8ccd1;
        border-radius: 5px;
        min-width: 24px;
    }}
    QScrollBar::handle:horizontal:hover {{
        background: #aab0b6;
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0; background: none;
    }}
    QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
        background: none;
    }}

    /* ---------- 对话框按钮 ---------- */
    QDialogButtonBox QPushButton {{
        min-width: 72px;
    }}
    """