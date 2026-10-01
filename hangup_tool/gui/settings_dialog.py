from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QStackedWidget, QWidget, QFormLayout, QKeySequenceEdit,
    QPushButton, QGroupBox, QMessageBox, QLabel, QSizePolicy,
)

from utils import shortcuts as sc
from utils.i18n import tr
from utils.textures import get_app_icon


class SettingsDialog(QDialog):
    """应用设置窗口：左侧导航 + 右侧页面 + 底部按钮"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("settings.title"))
        self.setWindowIcon(get_app_icon())
        self.resize(680, 480)

        # 动作名 -> QKeySequenceEdit
        self._shortcut_edits: dict[str, QKeySequenceEdit] = {}

        self._init_ui()
        self._load_current_values()

    # ==================== UI ====================
    def _init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(10)

        body = QHBoxLayout()
        body.setSpacing(10)

        # ---- 左侧导航 ----
        self.nav = QListWidget()
        self.nav.setFixedWidth(160)
        self.nav.addItem(QListWidgetItem(tr("settings.nav.shortcuts")))
        self.nav.currentRowChanged.connect(self._on_nav_changed)
        body.addWidget(self.nav)

        # ---- 右侧页面 ----
        self.stack = QStackedWidget()
        self.stack.addWidget(self._build_shortcuts_page())
        body.addWidget(self.stack, 1)

        root.addLayout(body, 1)

        # ---- 底部按钮 ----
        bottom = QHBoxLayout()

        self.reset_btn = QPushButton(tr("settings.btn.reset"))
        self.reset_btn.clicked.connect(self._on_reset)
        bottom.addWidget(self.reset_btn)

        bottom.addStretch()

        self.cancel_btn = QPushButton(tr("settings.btn.cancel"))
        self.cancel_btn.clicked.connect(self.reject)
        bottom.addWidget(self.cancel_btn)

        self.save_btn = QPushButton(tr("settings.btn.save"))
        self.save_btn.setDefault(True)
        self.save_btn.clicked.connect(self._on_save)
        bottom.addWidget(self.save_btn)

        root.addLayout(bottom)

        self.nav.setCurrentRow(0)

    def _build_shortcuts_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)

        hint = QLabel(tr("settings.shortcuts.hint"))
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #888;")  # 会被全局 QSS 覆盖或忽略，无害
        layout.addWidget(hint)

        box = QGroupBox(tr("settings.shortcuts.group"))
        form = QFormLayout(box)
        form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)

        for name in sc.DEFAULTS:
            edit = QKeySequenceEdit()
            edit.setClearButtonEnabled(True)
            self._shortcut_edits[name] = edit
            form.addRow(tr(f"shortcut.{name}"), edit)

        layout.addWidget(box)
        layout.addStretch()
        return page

    # ==================== 事件 ====================
    def _on_nav_changed(self, row: int):
        if 0 <= row < self.stack.count():
            self.stack.setCurrentIndex(row)

    def _load_current_values(self):
        """从 settings 加载当前快捷键到编辑框"""
        for name, edit in self._shortcut_edits.items():
            edit.setKeySequence(QKeySequence(sc.get_shortcut(name)))

    def _on_reset(self):
        """只重置 UI，不立即保存"""
        for name, edit in self._shortcut_edits.items():
            edit.setKeySequence(QKeySequence(sc.DEFAULTS.get(name, "")))

    def _on_save(self):
        # ① 收集
        new_shortcuts: dict[str, str] = {}
        for name, edit in self._shortcut_edits.items():
            new_shortcuts[name] = edit.keySequence().toString()

        # ② 冲突检查（空快捷键跳过）
        seen: dict[str, str] = {}
        for name, seq in new_shortcuts.items():
            if not seq:
                continue
            if seq in seen:
                QMessageBox.warning(
                    self,
                    tr("settings.conflict.title"),
                    tr("settings.conflict.body",
                       seq=seq, name=tr(f"shortcut.{seen[seq]}")),
                )
                return
            seen[seq] = name

        # ③ 写入 settings
        for name, seq in new_shortcuts.items():
            sc.set_shortcut(name, seq)
        sc.save()

        self.accept()