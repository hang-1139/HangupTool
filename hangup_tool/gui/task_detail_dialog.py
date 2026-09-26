from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLabel, QDialogButtonBox,
    QPlainTextEdit, QTabWidget, QWidget,
)

from core.task_file import TaskFile
from utils.i18n import tr


class TaskDetailDialog(QDialog):
    """显示 .hpt 文件的所有信息。后续可扩展为可编辑。"""

    def __init__(self, task: TaskFile, parent=None):
        super().__init__(parent)
        self.task = task
        self.setWindowTitle(tr("task_detail.title"))
        self.resize(620, 520)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        tabs = QTabWidget()

        # --- 基本信息 ---
        info_widget = QWidget()
        form = QFormLayout(info_widget)
        m = self.task.meta
        form.addRow(tr("task_detail.name"), QLabel(m.name or "-"))
        form.addRow(tr("task_detail.task_version"), QLabel(m.task_version or "-"))
        form.addRow(tr("task_detail.supported_app"), QLabel(m.supported_app_version or "-"))
        form.addRow(
            tr("task_detail.supports_logic_exit"),
            QLabel(tr("yes") if m.supports_logic_exit else tr("no")),
        )
        form.addRow(tr("task_detail.author"), QLabel(m.author or "-"))
        form.addRow(tr("task_detail.created_at"), QLabel(m.created_at or "-"))
        form.addRow(tr("task_detail.updated_at"), QLabel(m.updated_at or "-"))
        form.addRow(
            tr("task_detail.format_version"),
            QLabel(str(self.task.format_version)),
        )
        tabs.addTab(info_widget, tr("task_detail.tab.info"))

        # --- 描述 ---
        desc_widget = QWidget()
        desc_layout = QVBoxLayout(desc_widget)
        desc_text = QPlainTextEdit(m.description or tr("task_detail.no_desc"))
        desc_text.setReadOnly(True)
        desc_layout.addWidget(desc_text)
        tabs.addTab(desc_widget, tr("task_detail.tab.desc"))

        # --- 流程 ---
        flow_widget = QWidget()
        flow_layout = QVBoxLayout(flow_widget)
        flow_text = QPlainTextEdit(self._format_flow())
        flow_text.setReadOnly(True)
        flow_text.setStyleSheet("font-family: Consolas, monospace;")
        flow_layout.addWidget(flow_text)
        tabs.addTab(flow_widget, tr("task_detail.tab.flow"))

        layout.addWidget(tabs)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok)
        buttons.button(QDialogButtonBox.Ok).setText(tr("task_detail.close"))
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)

    def _format_flow(self) -> str:
        steps = self.task.flow.get("steps", [])
        if not steps:
            return tr("task_detail.no_steps")
        lines = []
        for i, step in enumerate(steps, 1):
            stype = step.get("type", "?")
            params = step.get("params", {})
            lines.append(f"{i:>3}. [{stype}]  {params}")
        return "\n".join(lines)