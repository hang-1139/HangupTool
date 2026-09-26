import html
import logging

from PySide6.QtCore import Qt, QByteArray
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QFormLayout,
    QPushButton, QLabel, QTextEdit, QGroupBox, QSplitter,
    QStatusBar, QToolBar, QDoubleSpinBox, QMessageBox,
)

from config.settings import settings
from config.version import APP_VERSION
from core.task_manager import TaskManager
from core.tasks import DemoTask
from utils.logger import log_emitter
from utils.i18n import tr

log = logging.getLogger("HangupTool")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{tr('app.title')} v{APP_VERSION}")
        self.resize(1000, 700)

        self.task_manager = TaskManager(self)

        self._init_ui()
        self._init_menu()
        self._init_toolbar()
        self._init_statusbar()
        self._init_tasks()
        self._init_log()
        self._load_settings()

        log.info(tr("log.window_ready"))

    # ================= UI 构建 =================
    def _init_ui(self):
        control_panel = self._build_control_panel()
        log_panel = self._build_log_panel()

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(control_panel)
        splitter.addWidget(log_panel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)
        splitter.setSizes([300, 700])
        self.setCentralWidget(splitter)

    def _build_control_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)

        # ---- 参数配置 ----
        param_group = QGroupBox(tr("group.params"))
        form = QFormLayout(param_group)
        self.interval_spin = QDoubleSpinBox()
        self.interval_spin.setRange(0.1, 3600.0)
        self.interval_spin.setDecimals(1)
        self.interval_spin.setSingleStep(0.1)
        self.interval_spin.setValue(1.0)
        self.interval_spin.setSuffix(tr("label.interval_suffix"))
        form.addRow(tr("label.interval"), self.interval_spin)
        layout.addWidget(param_group)

        # ---- 任务控制 ----
        btn_group = QGroupBox(tr("group.control"))
        btn_layout = QVBoxLayout(btn_group)
        self.start_btn = QPushButton(tr("btn.start"))
        self.stop_btn = QPushButton(tr("btn.stop"))
        self.stop_btn.setEnabled(False)
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.stop_btn)
        layout.addWidget(btn_group)

        # ---- 状态显示 ----
        status_group = QGroupBox(tr("group.status"))
        status_layout = QVBoxLayout(status_group)
        self.run_state_label = QLabel(tr("status.idle"))
        self.run_state_label.setStyleSheet("color: #888; font-weight: bold;")
        self.run_count_label = QLabel(tr("status.run_count", n=0))
        status_layout.addWidget(self.run_state_label)
        status_layout.addWidget(self.run_count_label)
        layout.addWidget(status_group)

        layout.addStretch()

        self.start_btn.clicked.connect(self._on_start)
        self.stop_btn.clicked.connect(self._on_stop)
        return panel

    def _build_log_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(8, 8, 8, 8)

        title = QLabel(tr("log.title"))
        title.setStyleSheet("font-weight: bold; font-size: 13px;")
        layout.addWidget(title)

        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setStyleSheet(
            "font-family: Consolas, 'Courier New', monospace;"
            "font-size: 12px; background: #fafafa;"
        )
        layout.addWidget(self.log_view)
        return panel

    def _init_menu(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu(tr("menu.file"))
        save_action = QAction(tr("menu.file.save"), self)
        save_action.setShortcut(QKeySequence.Save)
        save_action.triggered.connect(self._save_settings)
        file_menu.addAction(save_action)
        file_menu.addSeparator()
        quit_action = QAction(tr("menu.file.quit"), self)
        quit_action.setShortcut(QKeySequence.Quit)
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        help_menu = menubar.addMenu(tr("menu.help"))
        about_action = QAction(tr("menu.help.about"), self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _init_toolbar(self):
        toolbar = QToolBar("main", self)
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        start_action = QAction(tr("toolbar.start"), self)
        start_action.setShortcut("F8")
        start_action.triggered.connect(self._on_start)
        toolbar.addAction(start_action)

        stop_action = QAction(tr("toolbar.stop"), self)
        stop_action.setShortcut("F9")
        stop_action.triggered.connect(self._on_stop)
        toolbar.addAction(stop_action)

    def _init_statusbar(self):
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status_label = QLabel(tr("status.ready"))
        self.status.addWidget(self.status_label)
        self.counter_label = QLabel(tr("status.run_count", n=0))
        self.status.addPermanentWidget(self.counter_label)

    # ================= 任务与日志 =================
    def _init_tasks(self):
        self.demo_task = DemoTask(interval=1.0)
        self.task_manager.register("demo", self.demo_task)

        self.task_manager.task_started.connect(self._on_task_started)
        self.task_manager.task_finished.connect(self._on_task_finished)
        self.task_manager.task_error.connect(self._on_task_error)
        self.task_manager.task_log.connect(self._on_task_log)
        self.task_manager.task_progress.connect(self._on_task_progress)

    def _init_log(self):
        log_emitter.message.connect(self._append_log)

    def _append_log(self, level: str, message: str):
        color = {
            "DEBUG": "#888888", "INFO": "#2c3e50",
            "WARNING": "#e67e22", "ERROR": "#e74c3c",
            "CRITICAL": "#c0392b",
        }.get(level, "#000000")
        self.log_view.append(
            f'<span style="color:{color};">{html.escape(message)}</span>'
        )
        self.log_view.verticalScrollBar().setValue(
            self.log_view.verticalScrollBar().maximum()
        )

    # ================= 事件响应 =================
    def _on_start(self):
        self.demo_task.interval = self.interval_spin.value()
        log.info(tr("log.start_clicked", interval=self.interval_spin.value()))
        self.task_manager.start("demo")

    def _on_stop(self):
        log.info(tr("log.stop_clicked"))
        self.task_manager.stop("demo")

    def _on_task_started(self, name: str):
        self.status_label.setText(f"{tr('status.running')} {name}")
        self.run_state_label.setText(tr("status.running"))
        self.run_state_label.setStyleSheet("color: #27ae60; font-weight: bold;")
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)

    def _on_task_finished(self, name: str):
        self.status_label.setText(tr("status.stopped"))
        self.run_state_label.setText(tr("status.idle"))
        self.run_state_label.setStyleSheet("color: #888; font-weight: bold;")
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)

    def _on_task_error(self, name: str, msg: str):
        log.error(tr("log.task_error", name=name, msg=msg))
        QMessageBox.critical(
            self, tr("dialog.error.title"),
            tr("dialog.error.body", name=name, msg=msg),
        )

    def _on_task_log(self, name: str, msg: str):
        log.info(f"[{name}] {msg}")

    def _on_task_progress(self, name: str, value: int):
        self.counter_label.setText(tr("status.run_count", n=value))

    # ================= 配置 =================
    def _load_settings(self):
        geo_b64 = settings.get("window/geometry")
        if geo_b64:
            try:
                geo = QByteArray.fromBase64(geo_b64.encode("ascii"))
                self.restoreGeometry(geo)
            except Exception as e:
                log.warning(f"restore geometry failed: {e}")
        self.interval_spin.setValue(settings.get_float("task/interval", 1.0))

    def _save_settings(self):
        geo_b64 = bytes(self.saveGeometry().toBase64()).decode("ascii")
        settings.set("window/geometry", geo_b64)
        settings.set("task/interval", self.interval_spin.value())
        settings.sync()
        log.info(tr("log.settings_saved"))

    # ================= 其他 =================
    def _show_about(self):
        QMessageBox.about(
            self, tr("dialog.about.title"),
            tr("dialog.about.body", version=APP_VERSION),
        )

    def closeEvent(self, event):
        log.info(tr("log.exiting"))
        self.task_manager.stop_all()
        self._save_settings()
        event.accept()