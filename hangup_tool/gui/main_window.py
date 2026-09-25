import html
import logging

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtCore import QByteArray
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QFormLayout, QHBoxLayout,
    QPushButton, QLabel, QTextEdit, QGroupBox, QSplitter,
    QStatusBar, QToolBar, QDoubleSpinBox, QMessageBox,
)

from config.settings import settings
from core.task_manager import TaskManager
from core.tasks import DemoTask
from utils.logger import log_emitter

log = logging.getLogger("HangupTool")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("挂机工具 v0.1")
        self.resize(1000, 700)

        # 任务管理器
        self.task_manager = TaskManager(self)

        # 构建界面
        self._init_ui()
        self._init_menu()
        self._init_toolbar()
        self._init_statusbar()
        self._init_tasks()
        self._init_log()
        self._load_settings()

        log.info("主窗口初始化完成")

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
        param_group = QGroupBox("任务参数")
        form = QFormLayout(param_group)
        self.interval_spin = QDoubleSpinBox()
        self.interval_spin.setRange(0.1, 3600.0)
        self.interval_spin.setDecimals(1)  # 保留 1 位小数
        self.interval_spin.setSingleStep(0.1)
        self.interval_spin.setValue(1.0)
        self.interval_spin.setSuffix(" 秒")
        form.addRow("执行间隔：", self.interval_spin)
        layout.addWidget(param_group)

        # ---- 任务控制 ----
        btn_group = QGroupBox("任务控制")
        btn_layout = QVBoxLayout(btn_group)
        self.start_btn = QPushButton("▶  开始挂机 (F8)")
        self.stop_btn = QPushButton("■  停止 (F9)")
        self.stop_btn.setEnabled(False)
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.stop_btn)
        layout.addWidget(btn_group)

        # ---- 状态显示 ----
        status_group = QGroupBox("运行状态")
        status_layout = QVBoxLayout(status_group)
        self.run_state_label = QLabel("● 空闲")
        self.run_state_label.setStyleSheet("color: #888; font-weight: bold;")
        self.run_count_label = QLabel("执行次数：0")
        status_layout.addWidget(self.run_state_label)
        status_layout.addWidget(self.run_count_label)
        layout.addWidget(status_group)

        layout.addStretch()

        # 信号
        self.start_btn.clicked.connect(self._on_start)
        self.stop_btn.clicked.connect(self._on_stop)

        return panel

    def _build_log_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(8, 8, 8, 8)

        title = QLabel("运行日志")
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

        # 文件菜单
        file_menu = menubar.addMenu("文件(&F)")
        save_action = QAction("保存配置(&S)", self)
        save_action.setShortcut(QKeySequence.Save)
        save_action.triggered.connect(self._save_settings)
        file_menu.addAction(save_action)
        file_menu.addSeparator()
        quit_action = QAction("退出(&Q)", self)
        quit_action.setShortcut(QKeySequence.Quit)
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        # 帮助菜单
        help_menu = menubar.addMenu("帮助(&H)")
        about_action = QAction("关于(&A)", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _init_toolbar(self):
        toolbar = QToolBar("主工具栏", self)
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        start_action = QAction("开始", self)
        start_action.setShortcut("F8")
        start_action.triggered.connect(self._on_start)
        toolbar.addAction(start_action)

        stop_action = QAction("停止", self)
        stop_action.setShortcut("F9")
        stop_action.triggered.connect(self._on_stop)
        toolbar.addAction(stop_action)

    def _init_statusbar(self):
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status_label = QLabel("就绪")
        self.status.addWidget(self.status_label)
        self.counter_label = QLabel("运行次数：0")
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
            "DEBUG": "#888888",
            "INFO": "#2c3e50",
            "WARNING": "#e67e22",
            "ERROR": "#e74c3c",
            "CRITICAL": "#c0392b",
        }.get(level, "#000000")
        self.log_view.append(
            f'<span style="color:{color};">{html.escape(message)}</span>'
        )
        # 自动滚到底部
        self.log_view.verticalScrollBar().setValue(
            self.log_view.verticalScrollBar().maximum()
        )

    # ================= 事件响应 =================
    def _on_start(self):
        self.demo_task.interval = self.interval_spin.value()
        log.info(f"用户点击开始，间隔 = {self.interval_spin.value()} 秒")
        self.task_manager.start("demo")

    def _on_stop(self):
        log.info("用户点击停止")
        self.task_manager.stop("demo")

    def _on_task_started(self, name: str):
        self.status_label.setText(f"运行中：{name}")
        self.run_state_label.setText("● 运行中")
        self.run_state_label.setStyleSheet("color: #27ae60; font-weight: bold;")
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)

    def _on_task_finished(self, name: str):
        self.status_label.setText("已停止")
        self.run_state_label.setText("● 空闲")
        self.run_state_label.setStyleSheet("color: #888; font-weight: bold;")
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)

    def _on_task_error(self, name: str, msg: str):
        log.error(f"任务 [{name}] 出错：{msg}")
        QMessageBox.critical(self, "任务错误", f"任务 [{name}] 出错：\n\n{msg}")

    def _on_task_log(self, name: str, msg: str):
        log.info(f"[{name}] {msg}")

    def _on_task_progress(self, name: str, value: int):
        self.counter_label.setText(f"运行次数：{value}")

    # ================= 配置 =================
    def _load_settings(self):
        # 窗口几何信息（base64 → QByteArray）
        geo_b64 = settings.get("window/geometry")
        if geo_b64:
            try:
                geo = QByteArray.fromBase64(geo_b64.encode("ascii"))
                self.restoreGeometry(geo)
            except Exception as e:
                log.warning(f"恢复窗口位置失败：{e}")

        self.interval_spin.setValue(settings.get_float("task/interval", 1.0))

    def _save_settings(self):
        # QByteArray → base64 字符串，才能塞进 JSON
        geo_b64 = bytes(self.saveGeometry().toBase64()).decode("ascii")
        settings.set("window/geometry", geo_b64)
        settings.set("task/interval", self.interval_spin.value())
        settings.sync()
        log.info("配置已保存")

    # ================= 其他 =================
    def _show_about(self):
        QMessageBox.about(
            self,
            "关于挂机工具",
            "<h3>挂机工具 v0.1</h3>"
            "<p>基于 PySide6 + Python 3.14 开发</p>"
            "<p>框架已就绪，等待接入自动化任务。</p>"
        )

    def closeEvent(self, event):
        log.info("程序退出中，正在停止所有任务...")
        self.task_manager.stop_all()
        self._save_settings()
        event.accept()