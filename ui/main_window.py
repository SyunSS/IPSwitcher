"""
Main application window for IP Switcher.
"""
import os
import subprocess
import sys
from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QTextEdit,
    QFrame,
    QSplitter,
    QMessageBox,
    QProgressBar,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QObject, QTimer
from PyQt6.QtGui import QColor

from core.config_manager import ConfigManager
from core.network import (
    get_adapters_with_status, apply_static_ip, apply_dhcp,
    get_public_ip, set_adapter_state,
)
from ui.config_dialog import ConfigDialog
from ui.styles import get_style


# ──────────────────────────────────────────────────────────────────────
# Background worker so the UI stays responsive during netsh execution
# ──────────────────────────────────────────────────────────────────────

class _WorkerSignals(QObject):
    log = pyqtSignal(str, bool)   # (message, is_error)
    finished = pyqtSignal(bool)   # overall_success


class _ApplyWorker(QThread):
    def __init__(self, adapter: str, config: dict | None, dhcp: bool = False) -> None:
        super().__init__()
        self.signals = _WorkerSignals()
        self._adapter = adapter
        self._config = config
        self._dhcp = dhcp

    def run(self) -> None:
        if self._dhcp:
            results = apply_dhcp(self._adapter)
        else:
            results = apply_static_ip(self._adapter, self._config)

        overall_ok = True
        for ok, cmd, output in results:
            self.signals.log.emit(f"$ {cmd}", False)
            if output:
                self.signals.log.emit(output, not ok)
            if not ok:
                overall_ok = False

        self.signals.finished.emit(overall_ok)


class _IpFetchWorker(QThread):
    """Background thread to fetch public IP without blocking the UI."""
    done = pyqtSignal(str)   # IP info string (success or error message)

    def run(self) -> None:
        self.done.emit(get_public_ip())


class _AdapterStateWorker(QThread):
    """Background thread to enable/disable a network adapter."""
    done = pyqtSignal(bool, str)  # (success, message)

    def __init__(self, adapter: str, enable: bool) -> None:
        super().__init__()
        self._adapter = adapter
        self._enable = enable

    def run(self) -> None:
        ok, msg = set_adapter_state(self._adapter, self._enable)
        self.done.emit(ok, msg)


def _get_config_dir() -> str:
    """Return the config directory path used by ConfigManager."""
    appdata = os.environ.get("APPDATA", os.path.expanduser("~"))
    return os.path.join(appdata, "IPSwitcher")


# ──────────────────────────────────────────────────────────────────────
# Main Window
# ──────────────────────────────────────────────────────────────────────

class MainWindow(QMainWindow):
    def __init__(self, is_admin: bool) -> None:
        super().__init__()
        self._is_admin = is_admin
        self._cfg_mgr = ConfigManager()
        self._worker: _ApplyWorker | None = None
        self._adapter_worker: _AdapterStateWorker | None = None
        self._dark_mode: bool = False
        self._adapter_desc_map: dict = {}   # name -> interface description

        self.setWindowTitle("IP 切换管理器")
        self.setMinimumSize(860, 580)
        self.resize(1020, 660)

        # Apply light theme by default; could be toggled later
        self.setStyleSheet(get_style(dark=False))

        self._build_ui()
        self._refresh_adapters()
        self._refresh_list()
        self._refresh_ip()   # 启动时获取一次公网 IP

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        # ── Header ──────────────────────────────────────────────────
        header = QHBoxLayout()
        title_lbl = QLabel("IP 切换管理器")
        title_lbl.setObjectName("title")
        header.addWidget(title_lbl)
        header.addSpacing(12)

        badge_text = "● 管理员" if self._is_admin else "● 非管理员"
        badge_obj = "badge_admin" if self._is_admin else "badge_noadmin"
        self._badge = QLabel(badge_text)
        self._badge.setObjectName(badge_obj)
        header.addWidget(self._badge)
        header.addSpacing(16)

        # Public IP info panel
        self._ip_info_lbl = QLabel("公网 IP：获取中…")
        self._ip_info_lbl.setObjectName("ip_info")
        header.addWidget(self._ip_info_lbl)

        self._ip_refresh_btn = QPushButton("刷新 IP")
        self._ip_refresh_btn.setObjectName("btn_secondary")
        self._ip_refresh_btn.setMinimumWidth(70)
        self._ip_refresh_btn.setToolTip("刷新公网 IP")
        self._ip_refresh_btn.clicked.connect(self._refresh_ip)
        header.addWidget(self._ip_refresh_btn)

        header.addStretch()

        # Theme toggle
        self._theme_btn = QPushButton("深色模式")
        self._theme_btn.setObjectName("btn_secondary")
        self._theme_btn.setMinimumWidth(90)
        self._theme_btn.clicked.connect(self._toggle_theme)
        header.addWidget(self._theme_btn)

        root.addLayout(header)

        # ── Adapter row ─────────────────────────────────────────────
        adapter_row = QHBoxLayout()
        adapter_row.addWidget(QLabel("目标网卡："))
        self._adapter_combo = QComboBox()
        self._adapter_combo.setMinimumWidth(220)
        self._adapter_combo.currentIndexChanged.connect(self._on_adapter_changed)
        adapter_row.addWidget(self._adapter_combo)

        # Status badge
        self._adapter_status_lbl = QLabel("—")
        self._adapter_status_lbl.setObjectName("adapter_status_unknown")
        self._adapter_status_lbl.setFixedWidth(68)
        adapter_row.addWidget(self._adapter_status_lbl)

        # Detailed adapter description
        self._adapter_desc_lbl = QLabel("（无详细信息）")
        self._adapter_desc_lbl.setObjectName("adapter_desc")
        self._adapter_desc_lbl.setMinimumWidth(160)
        self._adapter_desc_lbl.setStyleSheet(
            "color: #888; font-size: 11px; padding-left: 4px;"
        )
        adapter_row.addWidget(self._adapter_desc_lbl)

        # Enable / Disable buttons
        self._enable_btn = QPushButton("启用网卡")
        self._enable_btn.setObjectName("btn_enable")
        self._enable_btn.setMinimumWidth(80)
        self._enable_btn.clicked.connect(lambda: self._on_set_adapter_state(True))
        adapter_row.addWidget(self._enable_btn)

        self._disable_btn = QPushButton("禁用网卡")
        self._disable_btn.setObjectName("btn_danger")
        self._disable_btn.setMinimumWidth(80)
        self._disable_btn.clicked.connect(lambda: self._on_set_adapter_state(False))
        adapter_row.addWidget(self._disable_btn)

        refresh_btn = QPushButton("刷新")
        refresh_btn.setObjectName("btn_secondary")
        refresh_btn.setMinimumWidth(60)
        refresh_btn.clicked.connect(self._refresh_adapters)
        adapter_row.addWidget(refresh_btn)
        adapter_row.addStretch()
        root.addLayout(adapter_row)

        # ── Splitter: left list | right detail ──────────────────────
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)

        # Left panel
        left_card = QFrame()
        left_card.setObjectName("card")
        left_layout = QVBoxLayout(left_card)
        left_layout.setContentsMargins(10, 10, 10, 10)
        left_layout.setSpacing(8)

        presets_lbl = QLabel("IP 配置预设")
        presets_lbl.setObjectName("section_title")
        left_layout.addWidget(presets_lbl)

        self._list = QListWidget()
        self._list.currentRowChanged.connect(self._on_selection_changed)
        left_layout.addWidget(self._list)
        splitter.addWidget(left_card)

        # Right panel
        right_card = QFrame()
        right_card.setObjectName("card")
        right_layout = QVBoxLayout(right_card)
        right_layout.setContentsMargins(14, 14, 14, 14)
        right_layout.setSpacing(10)

        detail_lbl = QLabel("配置详情")
        detail_lbl.setObjectName("section_title")
        right_layout.addWidget(detail_lbl)

        # Detail grid
        detail_grid = QHBoxLayout()
        left_labels = QVBoxLayout()
        right_values = QVBoxLayout()

        for field in ("配置名称", "IP 地址", "子网掩码", "默认网关", "首选 DNS", "备用 DNS"):
            lbl = QLabel(field + "：")
            lbl.setObjectName("detail_label")
            lbl.setFixedWidth(80)
            left_labels.addWidget(lbl)

        detail_grid.addLayout(left_labels)

        self._det_name = QLabel("—")
        self._det_ip = QLabel("—")
        self._det_mask = QLabel("—")
        self._det_gw = QLabel("—")
        self._det_dns1 = QLabel("—")
        self._det_dns2 = QLabel("—")

        for val_lbl in (
            self._det_name, self._det_ip, self._det_mask,
            self._det_gw, self._det_dns1, self._det_dns2
        ):
            val_lbl.setObjectName("detail_value")
            val_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            right_values.addWidget(val_lbl)

        detail_grid.addLayout(right_values)
        detail_grid.addStretch()
        right_layout.addLayout(detail_grid)
        right_layout.addStretch()

        # Log area
        log_lbl = QLabel("执行日志")
        log_lbl.setObjectName("section_title")
        right_layout.addWidget(log_lbl)

        self._log = QTextEdit()
        self._log.setReadOnly(True)
        self._log.setMinimumHeight(140)
        right_layout.addWidget(self._log)

        splitter.addWidget(right_card)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        root.addWidget(splitter, stretch=1)

        # ── Button bar ──────────────────────────────────────────────
        btn_bar = QHBoxLayout()
        btn_bar.setSpacing(8)

        self._apply_btn = QPushButton("▶  应用配置")
        self._apply_btn.clicked.connect(self._on_apply)

        self._edit_btn = QPushButton("编辑")
        self._edit_btn.setObjectName("btn_secondary")
        self._edit_btn.clicked.connect(self._on_edit)

        self._add_btn = QPushButton("新增")
        self._add_btn.setObjectName("btn_secondary")
        self._add_btn.clicked.connect(self._on_add)

        self._del_btn = QPushButton("删除")
        self._del_btn.setObjectName("btn_danger")
        self._del_btn.clicked.connect(self._on_delete)

        self._dhcp_btn = QPushButton("设为 DHCP")
        self._dhcp_btn.setObjectName("btn_secondary")
        self._dhcp_btn.clicked.connect(self._on_dhcp)

        for btn in (self._apply_btn, self._edit_btn, self._add_btn, self._del_btn, self._dhcp_btn):
            btn_bar.addWidget(btn)

        btn_bar.addStretch()

        self._open_folder_btn = QPushButton("📂 打开配置文件夹")
        self._open_folder_btn.setObjectName("btn_secondary")
        self._open_folder_btn.setMinimumWidth(140)
        self._open_folder_btn.clicked.connect(self._on_open_folder)
        btn_bar.addWidget(self._open_folder_btn)

        root.addLayout(btn_bar)

        # Selection-dependent buttons start disabled; add/dhcp are always available
        self._set_buttons_enabled(False)

    # ------------------------------------------------------------------
    # Data helpers
    # ------------------------------------------------------------------

    def _refresh_adapters(self) -> None:
        prev = self._adapter_combo.currentText()
        self._adapter_combo.blockSignals(True)
        self._adapter_combo.clear()
        self._adapter_status_map: dict = {}
        self._adapter_desc_map: dict = {}
        for name, desc, enabled in get_adapters_with_status():
            self._adapter_combo.addItem(name)
            self._adapter_status_map[name] = enabled
            self._adapter_desc_map[name] = desc
        self._adapter_combo.blockSignals(False)
        # Restore previous or default to 以太网
        idx = self._adapter_combo.findText(prev)
        if idx < 0:
            idx = self._adapter_combo.findText("以太网")
        if idx >= 0:
            self._adapter_combo.setCurrentIndex(idx)
        self._update_adapter_status_label()

    def _update_adapter_status_label(self) -> None:
        name = self._adapter_combo.currentText().strip()
        enabled = self._adapter_status_map.get(name, None) if hasattr(self, "_adapter_status_map") else None
        if enabled is True:
            self._adapter_status_lbl.setText("● 已启用")
            self._adapter_status_lbl.setObjectName("adapter_status_enabled")
        elif enabled is False:
            self._adapter_status_lbl.setText("● 已禁用")
            self._adapter_status_lbl.setObjectName("adapter_status_disabled")
        else:
            self._adapter_status_lbl.setText("● 未知")
            self._adapter_status_lbl.setObjectName("adapter_status_unknown")
        # Re-apply style (objectName change needs stylesheet refresh)
        self._adapter_status_lbl.setStyleSheet(self._adapter_status_lbl.styleSheet())
        self.setStyleSheet(self.styleSheet())
        # Update description label
        desc = self._adapter_desc_map.get(name, "") if hasattr(self, "_adapter_desc_map") else ""
        if desc:
            self._adapter_desc_lbl.setText(desc)
            self._adapter_desc_lbl.setToolTip(desc)
        else:
            self._adapter_desc_lbl.setText("（无详细信息）")
            self._adapter_desc_lbl.setToolTip("")
        # Update combo tooltip for easy identification
        if desc:
            self._adapter_combo.setToolTip(f"{name}\n{desc}")
        else:
            self._adapter_combo.setToolTip(name)

    def _on_adapter_changed(self, _index: int) -> None:
        self._update_adapter_status_label()

    def _refresh_list(self) -> None:
        current_row = self._list.currentRow()
        self._list.clear()
        for cfg in self._cfg_mgr.get_all():
            item = QListWidgetItem(f"  {cfg['name']}  •  {cfg['ip']}")
            self._list.addItem(item)
        # Restore selection
        if 0 <= current_row < self._list.count():
            self._list.setCurrentRow(current_row)
        elif self._list.count() > 0:
            self._list.setCurrentRow(0)

    def _current_index(self) -> int:
        return self._list.currentRow()

    def _set_buttons_enabled(self, enabled: bool) -> None:
        for btn in (self._apply_btn, self._edit_btn, self._del_btn):
            btn.setEnabled(enabled)

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_selection_changed(self, row: int) -> None:
        if row < 0 or row >= self._cfg_mgr.count():
            self._clear_detail()
            self._set_buttons_enabled(False)
            return

        cfg = self._cfg_mgr.get(row)
        self._det_name.setText(cfg.get("name", "—"))
        self._det_ip.setText(cfg.get("ip", "—"))
        self._det_mask.setText(cfg.get("mask", "—"))
        self._det_gw.setText(cfg.get("gateway", "—"))
        self._det_dns1.setText(cfg.get("dns1", "—") or "—")
        self._det_dns2.setText(cfg.get("dns2", "—") or "（无）")
        self._set_buttons_enabled(True)

    def _clear_detail(self) -> None:
        for lbl in (self._det_name, self._det_ip, self._det_mask,
                    self._det_gw, self._det_dns1, self._det_dns2):
            lbl.setText("—")

    def _on_apply(self) -> None:
        row = self._current_index()
        if row < 0:
            return
        adapter = self._adapter_combo.currentText().strip()
        if not adapter:
            QMessageBox.warning(self, "提示", "请先选择目标网卡")
            return
        cfg = self._cfg_mgr.get(row)
        self._log_info(f"=== 正在应用「{cfg['name']}」→ [{adapter}] ===")
        self._start_worker(adapter, cfg, dhcp=False)

    def _on_dhcp(self) -> None:
        adapter = self._adapter_combo.currentText().strip()
        if not adapter:
            QMessageBox.warning(self, "提示", "请先选择目标网卡")
            return
        reply = QMessageBox.question(
            self, "确认", f"将网卡「{adapter}」切换为 DHCP 自动获取 IP？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        self._log_info(f"=== 正在设置「{adapter}」为 DHCP 模式 ===")
        self._start_worker(adapter, None, dhcp=True)

    def _on_set_adapter_state(self, enable: bool) -> None:
        adapter = self._adapter_combo.currentText().strip()
        if not adapter:
            QMessageBox.warning(self, "提示", "请先选择目标网卡")
            return
        action = "启用" if enable else "禁用"
        reply = QMessageBox.question(
            self, "确认",
            f"确定要{action}网卡「{adapter}」吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        if self._adapter_worker and self._adapter_worker.isRunning():
            QMessageBox.information(self, "提示", "正在操作网卡，请稍候…")
            return
        self._enable_btn.setEnabled(False)
        self._disable_btn.setEnabled(False)
        self._log_info(f"=== 正在{action}网卡「{adapter}」 ===")
        self._adapter_worker = _AdapterStateWorker(adapter, enable)
        self._adapter_worker.done.connect(self._on_adapter_state_done)
        self._adapter_worker.start()

    def _on_adapter_state_done(self, success: bool, msg: str) -> None:
        if success:
            self._log_info(f"=== {msg} ===")
        else:
            self._log_error(f"=== 操作失败：{msg} ===")
        # Refresh adapter list to update status
        self._refresh_adapters()
        self._enable_btn.setEnabled(True)
        self._disable_btn.setEnabled(True)

    def _on_add(self) -> None:
        dlg = ConfigDialog(self)
        if dlg.exec() == ConfigDialog.DialogCode.Accepted:
            self._cfg_mgr.add(dlg.get_config())
            self._refresh_list()
            self._list.setCurrentRow(self._cfg_mgr.count() - 1)

    def _on_edit(self) -> None:
        row = self._current_index()
        if row < 0:
            return
        dlg = ConfigDialog(self, config=self._cfg_mgr.get(row))
        if dlg.exec() == ConfigDialog.DialogCode.Accepted:
            self._cfg_mgr.update(row, dlg.get_config())
            self._refresh_list()
            self._list.setCurrentRow(row)

    def _on_delete(self) -> None:
        row = self._current_index()
        if row < 0:
            return
        cfg = self._cfg_mgr.get(row)
        reply = QMessageBox.question(
            self, "确认删除", f"确定删除配置「{cfg['name']}」吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        self._cfg_mgr.delete(row)
        self._refresh_list()

    # ------------------------------------------------------------------
    # Worker management
    # ------------------------------------------------------------------

    def _start_worker(self, adapter: str, config: dict | None, dhcp: bool) -> None:
        if self._worker and self._worker.isRunning():
            QMessageBox.information(self, "提示", "正在执行操作，请稍候…")
            return
        self._set_all_buttons_enabled(False)
        self._worker = _ApplyWorker(adapter, config, dhcp)
        self._worker.signals.log.connect(self._on_worker_log)
        self._worker.signals.finished.connect(self._on_worker_finished)
        self._worker.start()

    def _set_all_buttons_enabled(self, enabled: bool) -> None:
        for btn in (self._apply_btn, self._edit_btn, self._add_btn,
                    self._del_btn, self._dhcp_btn):
            btn.setEnabled(enabled)

    def _on_worker_log(self, msg: str, is_error: bool) -> None:
        if is_error:
            self._log_error(msg)
        else:
            self._log_info(msg)

    def _on_worker_finished(self, success: bool) -> None:
        if success:
            self._log_info("=== 操作成功完成 ===")
            QMessageBox.information(self, "成功", "IP 配置已成功应用！")
            # Wait 3 seconds for network to settle before fetching public IP
            self._ip_info_lbl.setText("公网 IP：获取中（等待网络生效）…")
            self._ip_refresh_btn.setEnabled(False)
            QTimer.singleShot(3000, self._refresh_ip)
        else:
            self._log_error("=== 操作失败，请检查日志 ===")
            QMessageBox.critical(self, "失败", "IP 配置应用失败，请查看执行日志了解详情。")

        # Re-enable buttons based on current selection
        has_sel = self._current_index() >= 0
        self._add_btn.setEnabled(True)
        self._dhcp_btn.setEnabled(True)
        self._set_buttons_enabled(has_sel)

    # ------------------------------------------------------------------
    # Public IP fetching
    # ------------------------------------------------------------------

    def _refresh_ip(self) -> None:
        """Fetch public IP in a background thread and update the header label."""
        if hasattr(self, "_ip_worker") and self._ip_worker and self._ip_worker.isRunning():
            return   # already running
        self._ip_info_lbl.setText("公网 IP：获取中…")
        self._ip_refresh_btn.setEnabled(False)
        self._ip_worker = _IpFetchWorker()
        self._ip_worker.done.connect(self._on_ip_fetched)
        self._ip_worker.start()

    def _on_ip_fetched(self, info: str) -> None:
        self._ip_info_lbl.setText(f"公网 IP：{info}")
        if hasattr(self, "_ip_refresh_btn"):
            self._ip_refresh_btn.setEnabled(True)

    # ------------------------------------------------------------------
    # Config folder
    # ------------------------------------------------------------------

    def _on_open_folder(self) -> None:
        folder = _get_config_dir()
        if sys.platform == "win32":
            os.startfile(folder) if hasattr(os, "startfile") else subprocess.Popen(
                ["explorer", folder], creationflags=subprocess.CREATE_NO_WINDOW
            )
        else:
            subprocess.Popen(["open", folder] if sys.platform == "darwin" else ["xdg-open", folder])


    # ------------------------------------------------------------------
    # Log helpers
    # ------------------------------------------------------------------

    def _log_info(self, msg: str) -> None:
        self._log.setTextColor(QColor("#4ec9b0"))
        self._log.append(msg)
        self._log.setTextColor(QColor("#d4d4d4"))

    def _log_error(self, msg: str) -> None:
        self._log.setTextColor(QColor("#f44747"))
        self._log.append(msg)
        self._log.setTextColor(QColor("#d4d4d4"))

    # ------------------------------------------------------------------
    # Theme toggle
    # ------------------------------------------------------------------

    def _toggle_theme(self) -> None:
        self._dark_mode = not self._dark_mode
        self.setStyleSheet(get_style(dark=self._dark_mode))
        self._theme_btn.setText("浅色模式" if self._dark_mode else "深色模式")
