import html
import logging
from datetime import datetime

from PySide6.QtCore import Qt, QByteArray, QSize
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QFormLayout, QHBoxLayout,
    QPushButton, QLabel, QTextEdit, QGroupBox, QSplitter,
    QStatusBar, QToolBar, QDoubleSpinBox, QSpinBox, QMessageBox,
    QLineEdit, QFileDialog, QRadioButton, QButtonGroup,
    QToolButton,
)

from config.paths import TASKS_DIR, LOGS_DIR
from config.settings import settings
from config.version import APP_VERSION
from core.task_builder import build_worker
from core.task_file import TaskFile, HPTError, HPTVersionError, HPT_EXTENSION
from core.task_manager import TaskManager
from gui.task_detail_dialog import TaskDetailDialog
from utils.logger import log_emitter
from utils.i18n import tr
from utils.textures import get_icon, get_app_icon

log = logging.getLogger("HangupTool")

TASK_KEY = "current"
ICON_SIZE = 24

# 快捷键集中定义，方便后续统一调整
SHORTCUT_START = "F5"
SHORTCUT_PAUSE = "F8"
SHORTCUT_STOP = "F9"
SHORTCUT_EXPORT_LOG = "Ctrl+Shift+S"


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{tr('app.title')} v{APP_VERSION}")

        # 窗口图标（缺失 app_icon.png 时自动跳过）
        app_icon = get_app_icon()
        if not app_icon.isNull():
            self.setWindowIcon(app_icon)

        self.resize(1050, 720)

        # 核心对象
        self.task_manager = TaskManager(self)
        self.current_task: TaskFile | None = None
        self.current_worker = None

        # 导出日志用的纯文本缓冲（与日志区所见内容一致）
        self._log_lines: list[str] = []

        # UI 构建顺序：先建控件，再挂菜单/工具栏/状态栏，最后加载配置
        self._init_ui()
        self._init_menu()
        self._init_toolbar()
        self._init_statusbar()
        self._init_log()
        self._load_settings()

        log.info(tr("log.window_ready"))

    # ==================== UI 构建 ====================
    def _init_ui(self):
        control = self._build_control_panel()
        logp = self._build_log_panel()
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(control)
        splitter.addWidget(logp)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 3)
        splitter.setSizes([420, 630])
        self.setCentralWidget(splitter)

    def _build_control_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)

        # ---------- 任务参数 ----------
        params = QGroupBox(tr("group.params"))
        pf = QFormLayout(params)

        # 任务文件行
        file_row = QHBoxLayout()
        self.task_file_edit = QLineEdit()
        self.task_file_edit.setPlaceholderText(tr("placeholder.task_file"))
        self.task_file_edit.editingFinished.connect(self._on_task_path_edited)

        self.browse_btn = QToolButton()
        self.browse_btn.setIcon(get_icon("browse", ICON_SIZE))
        self.browse_btn.setIconSize(QSize(ICON_SIZE, ICON_SIZE))
        self.browse_btn.setText("📁")
        self.browse_btn.setToolTip(tr("tooltip.browse"))
        self.browse_btn.clicked.connect(self._on_browse)

        self.detail_btn = QToolButton()
        self.detail_btn.setIcon(get_icon("info", ICON_SIZE))
        self.detail_btn.setIconSize(QSize(ICON_SIZE, ICON_SIZE))
        self.detail_btn.setText("ℹ")
        self.detail_btn.setToolTip(tr("tooltip.detail"))
        self.detail_btn.clicked.connect(self._on_show_detail)
        self.detail_btn.setEnabled(False)

        file_row.addWidget(self.task_file_edit, 1)
        file_row.addWidget(self.browse_btn)
        file_row.addWidget(self.detail_btn)
        pf.addRow(tr("label.task_file"), file_row)

        # 间隔
        self.interval_spin = QDoubleSpinBox()
        self.interval_spin.setRange(0.0, 3600.0)
        self.interval_spin.setDecimals(1)
        self.interval_spin.setSingleStep(0.1)
        self.interval_spin.setValue(1.0)
        self.interval_spin.setSuffix(tr("label.interval_suffix"))
        self.interval_spin.setToolTip(tr("tooltip.interval_zero"))
        pf.addRow(tr("label.interval"), self.interval_spin)

        # 退出模式
        pf.addRow(QLabel(tr("label.exit_mode")))

        self.exit_group = QButtonGroup(self)

        row_count = QHBoxLayout()
        self.radio_count = QRadioButton(tr("radio.exit_count"))
        self.max_iter_spin = QSpinBox()
        self.max_iter_spin.setRange(1, 999999)
        self.max_iter_spin.setValue(1)
        self.max_iter_spin.setEnabled(False)
        row_count.addWidget(self.radio_count)
        row_count.addWidget(self.max_iter_spin)
        row_count.addStretch()
        pf.addRow("", row_count)
        self.exit_group.addButton(self.radio_count, 0)

        self.radio_signal = QRadioButton(tr("radio.exit_signal"))
        self.radio_signal.setEnabled(False)
        pf.addRow("", self.radio_signal)
        self.exit_group.addButton(self.radio_signal, 1)

        self.radio_forever = QRadioButton(tr("radio.exit_forever"))
        self.radio_forever.setChecked(True)
        pf.addRow("", self.radio_forever)
        self.exit_group.addButton(self.radio_forever, 2)

        self.exit_group.buttonClicked.connect(self._on_exit_mode_changed)
        self._on_exit_mode_changed()

        layout.addWidget(params)

        # ---------- 任务控制 ----------
        ctrl = QGroupBox(tr("group.control"))
        cl = QVBoxLayout(ctrl)

        self.start_btn = QPushButton(tr("btn.start"))
        self.start_btn.setIcon(get_icon("start", ICON_SIZE))
        self.start_btn.setIconSize(QSize(ICON_SIZE, ICON_SIZE))

        self.pause_btn = QPushButton(tr("btn.pause"))
        self.pause_btn.setIcon(get_icon("pause", ICON_SIZE))
        self.pause_btn.setIconSize(QSize(ICON_SIZE, ICON_SIZE))
        self.pause_btn.setEnabled(False)

        self.stop_btn = QPushButton(tr("btn.stop"))
        self.stop_btn.setIcon(get_icon("stop", ICON_SIZE))
        self.stop_btn.setIconSize(QSize(ICON_SIZE, ICON_SIZE))
        self.stop_btn.setEnabled(False)

        cl.addWidget(self.start_btn)
        cl.addWidget(self.pause_btn)
        cl.addWidget(self.stop_btn)
        layout.addWidget(ctrl)

        # ---------- 状态 ----------
        st = QGroupBox(tr("group.status"))
        sl = QVBoxLayout(st)

        self.state_label = QLabel(tr("status.idle"))
        self.state_label.setObjectName("stateLabel")
        self.state_label.setProperty("state", "idle")

        self.count_label = QLabel(tr("status.run_count", n=0))
        self.progress_label = QLabel(tr("status.progress", n=0, total="-"))

        sl.addWidget(self.state_label)
        sl.addWidget(self.count_label)
        sl.addWidget(self.progress_label)
        layout.addWidget(st)

        layout.addStretch()

        self.start_btn.clicked.connect(self._on_start)
        self.pause_btn.clicked.connect(self._on_pause_resume)
        self.stop_btn.clicked.connect(self._on_stop)
        return panel

    def _build_log_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(8, 8, 8, 8)

        title = QLabel(tr("log.title"))
        title.setObjectName("panelTitle")
        layout.addWidget(title)

        self.log_view = QTextEdit()
        self.log_view.setObjectName("logView")
        self.log_view.setReadOnly(True)
        layout.addWidget(self.log_view)
        return panel

    def _init_menu(self):
        mb = self.menuBar()

        # ---------- 文件 ----------
        fm = mb.addMenu(tr("menu.file"))

        export_a = QAction(tr("menu.file.export_log"), self)
        export_a.setShortcut(QKeySequence(SHORTCUT_EXPORT_LOG))
        export_a.triggered.connect(self._on_export_log)
        fm.addAction(export_a)

        save_a = QAction(tr("menu.file.save"), self)
        save_a.setShortcut(QKeySequence.Save)
        save_a.triggered.connect(self._save_settings)
        fm.addAction(save_a)

        fm.addSeparator()

        quit_a = QAction(tr("menu.file.quit"), self)
        quit_a.setShortcut(QKeySequence.Quit)
        quit_a.triggered.connect(self.close)
        fm.addAction(quit_a)

        # ---------- 帮助 ----------
        hm = mb.addMenu(tr("menu.help"))
        about_a = QAction(tr("menu.help.about"), self)
        about_a.triggered.connect(self._show_about)
        hm.addAction(about_a)

    def _init_toolbar(self):
        tb = QToolBar("main", self)
        tb.setMovable(False)
        tb.setIconSize(QSize(ICON_SIZE, ICON_SIZE))
        self.addToolBar(tb)

        # 开始
        self.start_action = QAction(
            get_icon("start", ICON_SIZE), tr("toolbar.start"), self
        )
        self.start_action.setShortcut(SHORTCUT_START)
        self.start_action.triggered.connect(self._on_start)
        tb.addAction(self.start_action)

        # 暂停（运行中才可用）
        self.pause_action = QAction(
            get_icon("pause", ICON_SIZE), tr("toolbar.pause"), self
        )
        self.pause_action.setShortcut(SHORTCUT_PAUSE)
        self.pause_action.setEnabled(False)
        self.pause_action.triggered.connect(self._on_pause_resume)
        tb.addAction(self.pause_action)

        # 停止
        self.stop_action = QAction(
            get_icon("stop", ICON_SIZE), tr("toolbar.stop"), self
        )
        self.stop_action.setShortcut(SHORTCUT_STOP)
        self.stop_action.triggered.connect(self._on_stop)
        tb.addAction(self.stop_action)

    def _init_statusbar(self):
        sb = QStatusBar()
        self.setStatusBar(sb)
        self.status_label = QLabel(tr("status.ready"))
        sb.addWidget(self.status_label)
        self.counter_label = QLabel(tr("status.run_count", n=0))
        sb.addPermanentWidget(self.counter_label)

    def _init_log(self):
        log_emitter.message.connect(self._append_log)

    def _append_log(self, level: str, message: str):
        # ① 纯文本缓冲（导出用）
        self._log_lines.append(message)

        # ② 彩色显示
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

    def _set_state(self, state: str, text: str):
        """切换状态标签的颜色和文本（颜色由 QSS 根据 dynamic property 决定）"""
        self.state_label.setText(text)
        self.state_label.setProperty("state", state)
        self.state_label.style().unpolish(self.state_label)
        self.state_label.style().polish(self.state_label)

    # ==================== 日志导出 ====================
    def _on_export_log(self):
        now = datetime.now()
        # 文件名：log-YYYY-MM-DD-HH-MM-SS.txt
        # ⚠️ 冒号在 Windows 文件名中非法，用 - 代替
        default_name = (
            f"log-{now.strftime('%Y-%m-%d')}-{now.strftime('%H-%M-%S')}.txt"
        )
        default_path = str(LOGS_DIR / default_name)

        path, _ = QFileDialog.getSaveFileName(
            self,
            tr("file_dialog.export_log"),
            default_path,
            tr("file_dialog.log_filter"),
        )
        if not path:
            return

        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write("\n".join(self._log_lines))
        except OSError as e:
            QMessageBox.critical(
                self, tr("dialog.export_fail.title"),
                tr("dialog.export_fail.body", msg=str(e)),
            )
            log.error(f"导出日志失败: {e}")
            return

        QMessageBox.information(
            self, tr("dialog.export_ok.title"),
            tr("dialog.export_ok.body", path=path),
        )
        log.info(tr("log.log_exported", path=path))

    # ==================== 任务文件 ====================
    def _on_browse(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            tr("file_dialog.select_task"),
            str(TASKS_DIR),
            tr("file_dialog.task_filter"),
        )
        if path:
            self.task_file_edit.setText(path)
            self._load_task_file(path)

    def _on_task_path_edited(self):
        path = self.task_file_edit.text().strip()
        if path:
            self._load_task_file(path)

    def _load_task_file(self, path: str):
        try:
            tf = TaskFile.load(path)
        except HPTVersionError as e:
            self._clear_task()
            QMessageBox.warning(self, tr("dialog.warn.title"), str(e))
            log.warning(f"版本不兼容: {e}")
            return
        except HPTError as e:
            self._clear_task()
            QMessageBox.critical(self, tr("dialog.error.title"), str(e))
            log.error(f"加载任务失败: {e}")
            return

        self.current_task = tf
        self.detail_btn.setEnabled(True)
        self.radio_signal.setEnabled(tf.meta.supports_logic_exit)
        log.info(tr("log.task_loaded", name=tf.meta.name, version=tf.meta.task_version))
        self.status_label.setText(tr("status.task_loaded", name=tf.meta.name))

    def _clear_task(self):
        self.current_task = None
        self.detail_btn.setEnabled(False)
        self.radio_signal.setEnabled(False)
        if self.radio_signal.isChecked():
            self.radio_forever.setChecked(True)
        self._on_exit_mode_changed()

    def _on_show_detail(self):
        if not self.current_task:
            return
        dlg = TaskDetailDialog(self.current_task, self)
        dlg.exec()

    # ==================== 退出模式联动 ====================
    def _on_exit_mode_changed(self):
        self.max_iter_spin.setEnabled(self.radio_count.isChecked())

    def _build_exit_mode(self):
        from core.worker import ExitMode
        if self.radio_count.isChecked():
            return ExitMode.COUNT, self.max_iter_spin.value()
        if self.radio_signal.isChecked():
            return ExitMode.SIGNAL, 0
        return ExitMode.FOREVER, 0

    # ==================== 任务控制 ====================
    def _on_start(self):
        if not self.current_task:
            QMessageBox.warning(
                self, tr("dialog.warn.title"), tr("dialog.warn.no_task")
            )
            return

        exit_mode, max_iter = self._build_exit_mode()

        # 若旧 worker 存在，先丢掉
        if self.current_worker is not None:
            self.task_manager._workers.pop(TASK_KEY, None)
            self.current_worker = None

        worker = build_worker(self.current_task)
        worker.interval = self.interval_spin.value()
        worker.exit_mode = exit_mode
        worker.max_iterations = max_iter

        self.current_worker = worker
        self.task_manager.register(TASK_KEY, worker)

        # 连接信号（每次 new worker 都要连）
        self.task_manager.task_started.connect(self._on_task_started, Qt.UniqueConnection)
        self.task_manager.task_finished.connect(self._on_task_finished, Qt.UniqueConnection)
        self.task_manager.task_error.connect(self._on_task_error, Qt.UniqueConnection)
        self.task_manager.task_log.connect(self._on_task_log, Qt.UniqueConnection)
        self.task_manager.task_paused.connect(self._on_task_paused, Qt.UniqueConnection)
        self.task_manager.task_resumed.connect(self._on_task_resumed, Qt.UniqueConnection)
        self.task_manager.task_progress.connect(self._on_task_progress, Qt.UniqueConnection)

        log.info(tr("log.start_clicked",
                    interval=self.interval_spin.value(),
                    mode=exit_mode.value,
                    max_iter=max_iter))
        self.task_manager.start(TASK_KEY)

    def _on_pause_resume(self):
        if not self.current_worker:
            return
        if self.current_worker.is_paused():
            log.info(tr("log.resume_clicked"))
            self.task_manager.resume(TASK_KEY)
        else:
            log.info(tr("log.pause_clicked"))
            self.task_manager.pause(TASK_KEY)

    def _on_stop(self):
        if not self.current_worker:
            return
        log.info(tr("log.stop_clicked"))
        self.task_manager.stop(TASK_KEY)

    # ==================== 任务信号响应 ====================
    def _on_task_started(self, name: str):
        self._set_state("running", tr("status.running"))
        self.status_label.setText(tr("status.running"))
        # 侧栏按钮
        self.start_btn.setEnabled(False)
        self.pause_btn.setEnabled(True)
        self.pause_btn.setText(tr("btn.pause"))
        self.pause_btn.setIcon(get_icon("pause", ICON_SIZE))
        self.stop_btn.setEnabled(True)
        # 工具栏
        self.start_action.setEnabled(False)
        self.pause_action.setEnabled(True)
        self.pause_action.setText(tr("toolbar.pause"))
        self.pause_action.setIcon(get_icon("pause", ICON_SIZE))

    def _on_task_paused(self, name: str):
        self._set_state("paused", tr("status.paused"))
        # 侧栏
        self.pause_btn.setText(tr("btn.resume"))
        self.pause_btn.setIcon(get_icon("resume", ICON_SIZE))
        # 工具栏
        self.pause_action.setText(tr("toolbar.resume"))
        self.pause_action.setIcon(get_icon("resume", ICON_SIZE))

    def _on_task_resumed(self, name: str):
        self._set_state("running", tr("status.running"))
        # 侧栏
        self.pause_btn.setText(tr("btn.pause"))
        self.pause_btn.setIcon(get_icon("pause", ICON_SIZE))
        # 工具栏
        self.pause_action.setText(tr("toolbar.pause"))
        self.pause_action.setIcon(get_icon("pause", ICON_SIZE))

    def _on_task_finished(self, name: str, reason: str):
        self._set_state("idle", tr("status.idle"))
        self.status_label.setText(tr("status.stopped"))
        # 侧栏
        self.start_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.pause_btn.setText(tr("btn.pause"))
        self.pause_btn.setIcon(get_icon("pause", ICON_SIZE))
        self.stop_btn.setEnabled(False)
        # 工具栏
        self.start_action.setEnabled(True)
        self.pause_action.setEnabled(False)
        self.pause_action.setText(tr("toolbar.pause"))
        self.pause_action.setIcon(get_icon("pause", ICON_SIZE))
        log.info(tr("log.task_finished", reason=reason))

    def _on_task_error(self, name: str, msg: str):
        log.error(tr("log.task_error", name=name, msg=msg))
        QMessageBox.critical(
            self, tr("dialog.error.title"),
            tr("dialog.error.body", name=name, msg=msg),
        )

    def _on_task_log(self, name: str, msg: str):
        log.info(f"[{name}] {msg}")

    def _on_task_progress(self, name: str, value: int):
        self.count_label.setText(tr("status.run_count", n=value))
        self.counter_label.setText(tr("status.run_count", n=value))
        if self.radio_count.isChecked():
            total = self.max_iter_spin.value()
            self.progress_label.setText(
                tr("status.progress", n=value, total=total)
            )
        else:
            self.progress_label.setText(tr("status.progress", n=value, total="∞"))

    # ==================== 配置 ====================
    def _load_settings(self):
        geo_b64 = settings.get("window/geometry")
        if geo_b64:
            try:
                self.restoreGeometry(QByteArray.fromBase64(geo_b64.encode("ascii")))
            except Exception as e:
                log.warning(f"restore geometry failed: {e}")
        self.interval_spin.setValue(settings.get_float("task/interval", 1.0))
        self.task_file_edit.setText(settings.get("task/last_file", ""))
        p = self.task_file_edit.text().strip()
        if p:
            self._load_task_file(p)

    def _save_settings(self):
        geo_b64 = bytes(self.saveGeometry().toBase64()).decode("ascii")
        settings.set("window/geometry", geo_b64)
        settings.set("task/interval", self.interval_spin.value())
        settings.set("task/last_file", self.task_file_edit.text().strip())
        settings.sync()
        log.info(tr("log.settings_saved"))

    # ==================== 其他 ====================
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