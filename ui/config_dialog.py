"""
Dialog for adding or editing an IP configuration preset.
"""
import re
from typing import Dict, Any, Optional

from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QComboBox,
    QFormLayout,
    QDialogButtonBox,
    QMessageBox,
    QFrame,
)
from PyQt6.QtCore import Qt


# Common subnet masks offered in the dropdown
COMMON_MASKS = [
    "255.255.255.0",
    "255.255.255.128",
    "255.255.255.192",
    "255.255.255.224",
    "255.255.255.240",
    "255.255.255.248",
    "255.255.255.252",
    "255.255.0.0",
    "255.0.0.0",
]

_IP_REGEX = re.compile(
    r"^((25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(25[0-5]|2[0-4]\d|[01]?\d\d?)$"
)


def _is_valid_ip(value: str) -> bool:
    return bool(_IP_REGEX.match(value.strip()))


class ConfigDialog(QDialog):
    """Modal dialog for creating or editing an IP configuration preset."""

    def __init__(self, parent=None, config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(parent)
        self._editing = config is not None
        self._result_config: Dict[str, Any] = {}
        self.setWindowTitle("编辑配置" if self._editing else "新增配置")
        self.setMinimumWidth(420)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)

        self._build_ui(config or {})

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self, cfg: Dict[str, Any]) -> None:
        root = QVBoxLayout(self)
        root.setSpacing(16)
        root.setContentsMargins(20, 20, 20, 20)

        # --- Title ---
        title = QLabel("编辑配置" if self._editing else "新增配置")
        title.setObjectName("title")
        root.addWidget(title)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        root.addWidget(sep)

        # --- Form ---
        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self._name_edit = QLineEdit(cfg.get("name", ""))
        self._name_edit.setPlaceholderText("例：联合网络")
        form.addRow("配置名称 *", self._name_edit)

        self._ip_edit = QLineEdit(cfg.get("ip", ""))
        self._ip_edit.setPlaceholderText("例：192.168.1.100")
        form.addRow("IP 地址 *", self._ip_edit)

        # Mask combo + custom input
        mask_row = QHBoxLayout()
        mask_row.setSpacing(6)
        self._mask_combo = QComboBox()
        self._mask_combo.setEditable(True)
        self._mask_combo.addItems(COMMON_MASKS)
        current_mask = cfg.get("mask", "255.255.255.0")
        if current_mask in COMMON_MASKS:
            self._mask_combo.setCurrentText(current_mask)
        else:
            self._mask_combo.setCurrentText(current_mask)
        mask_row.addWidget(self._mask_combo)
        form.addRow("子网掩码 *", mask_row)

        self._gw_edit = QLineEdit(cfg.get("gateway", ""))
        self._gw_edit.setPlaceholderText("例：192.168.1.1（纯内网可留空）")
        form.addRow("默认网关", self._gw_edit)

        self._dns1_edit = QLineEdit(cfg.get("dns1", ""))
        self._dns1_edit.setPlaceholderText("例：8.8.8.8（纯内网可留空）")
        form.addRow("首选 DNS", self._dns1_edit)

        self._dns2_edit = QLineEdit(cfg.get("dns2", ""))
        self._dns2_edit.setPlaceholderText("（可选）")
        form.addRow("备用 DNS", self._dns2_edit)

        root.addLayout(form)

        # --- Hint ---
        hint = QLabel("* 为必填项；网关/DNS 可留空（适用于纯内网直连）")
        hint.setObjectName("detail_label")
        hint.setWordWrap(True)
        root.addWidget(hint)

        # --- Buttons ---
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("确定")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("取消")
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

    # ------------------------------------------------------------------
    # Validation & result
    # ------------------------------------------------------------------

    def _on_accept(self) -> None:
        errors = []

        name = self._name_edit.text().strip()
        if not name:
            errors.append("配置名称不能为空")

        ip = self._ip_edit.text().strip()
        if not ip or not _is_valid_ip(ip):
            errors.append(f"IP 地址格式无效：'{ip}'")

        mask = self._mask_combo.currentText().strip()
        if not mask or not _is_valid_ip(mask):
            errors.append(f"子网掩码格式无效：'{mask}'")

        gw = self._gw_edit.text().strip()
        if gw and not _is_valid_ip(gw):
            errors.append(f"默认网关格式无效：'{gw}'")

        dns1 = self._dns1_edit.text().strip()
        if dns1 and not _is_valid_ip(dns1):
            errors.append(f"首选 DNS 格式无效：'{dns1}'")

        dns2 = self._dns2_edit.text().strip()
        if dns2 and not _is_valid_ip(dns2):
            errors.append(f"备用 DNS 格式无效：'{dns2}'")

        if errors:
            QMessageBox.warning(self, "输入错误", "\n".join(errors))
            return

        self._result_config = {
            "name": name,
            "ip": ip,
            "mask": mask,
            "gateway": gw,
            "dns1": dns1,
            "dns2": dns2,
        }
        self.accept()

    def get_config(self) -> Dict[str, Any]:
        """Call after exec() returns Accepted."""
        return dict(self._result_config)
