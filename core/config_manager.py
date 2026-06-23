"""
Configuration manager: read/write IP presets to %APPDATA%\IPSwitcher\configs.json
"""
import json
import os
from typing import List, Dict, Any


DEFAULT_CONFIGS: List[Dict[str, Any]] = [
    {
        "name": "联合网络",
        "ip": "211.162.46.92",
        "mask": "255.255.255.248",
        "gateway": "211.162.46.89",
        "dns1": "211.162.47.1",
        "dns2": "211.162.47.2",
    },
    {
        "name": "用户加速环境",
        "ip": "192.168.251.4",
        "mask": "255.255.255.0",
        "gateway": "192.168.251.1",
        "dns1": "211.138.151.161",
        "dns2": "211.138.156.166",
    },
    {
        "name": "电信家宽",
        "ip": "192.168.252.4",
        "mask": "255.255.255.0",
        "gateway": "192.168.252.1",
        "dns1": "218.85.152.99",
        "dns2": "114.114.114.114",
    },
    {
        "name": "普通移动家宽",
        "ip": "192.168.253.4",
        "mask": "255.255.255.0",
        "gateway": "192.168.253.1",
        "dns1": "211.138.151.161",
        "dns2": "",
    },
    {
        "name": "纯移动环境",
        "ip": "113.18.158.133",
        "mask": "255.255.255.0",
        "gateway": "113.18.158.1",
        "dns1": "211.138.151.161",
        "dns2": "",
    },
    {
        "name": "无规则联通",
        "ip": "113.18.158.104",
        "mask": "255.255.255.0",
        "gateway": "113.18.158.1",
        "dns1": "211.138.151.161",
        "dns2": "",
    },
    {
        "name": "无规则电信",
        "ip": "113.18.158.108",
        "mask": "255.255.255.0",
        "gateway": "113.18.158.1",
        "dns1": "211.138.151.161",
        "dns2": "",
    },
    {
        "name": "测试用移动套联通",
        "ip": "113.18.158.112",
        "mask": "255.255.255.0",
        "gateway": "113.18.158.1",
        "dns1": "211.138.151.161",
        "dns2": "",
    },
    {
        "name": "测试用移动套电信",
        "ip": "113.18.158.116",
        "mask": "255.255.255.0",
        "gateway": "113.18.158.1",
        "dns1": "211.138.151.161",
        "dns2": "",
    },
    {
        "name": "正式用移动套联通",
        "ip": "113.18.158.120",
        "mask": "255.255.255.0",
        "gateway": "113.18.158.1",
        "dns1": "211.138.151.161",
        "dns2": "",
    },
    {
        "name": "正式用移动套电信",
        "ip": "113.18.158.124",
        "mask": "255.255.255.0",
        "gateway": "113.18.158.1",
        "dns1": "211.138.151.161",
        "dns2": "",
    },
    {
        "name": "福州节点日韩出口",
        "ip": "192.168.10.4",
        "mask": "255.255.255.0",
        "gateway": "192.168.10.1",
        "dns1": "8.8.8.8",
        "dns2": "",
    },
    {
        "name": "福州节点法兰克福出口",
        "ip": "192.168.10.14",
        "mask": "255.255.255.0",
        "gateway": "192.168.10.1",
        "dns1": "8.8.8.8",
        "dns2": "",
    },
    {
        "name": "福州节点香港出口",
        "ip": "192.168.10.24",
        "mask": "255.255.255.0",
        "gateway": "192.168.10.1",
        "dns1": "8.8.8.8",
        "dns2": "",
    },
]


def _get_config_path() -> str:
    """Return the path to configs.json under %APPDATA%\\IPSwitcher\\."""
    appdata = os.environ.get("APPDATA", os.path.expanduser("~"))
    config_dir = os.path.join(appdata, "IPSwitcher")
    os.makedirs(config_dir, exist_ok=True)
    return os.path.join(config_dir, "configs.json")


class ConfigManager:
    """Manages loading and saving of IP configuration presets."""

    def __init__(self) -> None:
        self._path = _get_config_path()
        self._configs: List[Dict[str, Any]] = []
        self.load()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load(self) -> None:
        """Load configs from disk; write defaults on first run."""
        if os.path.exists(self._path):
            try:
                with open(self._path, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
                if isinstance(data, list):
                    self._configs = data
                    return
            except (json.JSONDecodeError, OSError):
                pass
        # First run or corrupted file → use defaults
        self._configs = [dict(c) for c in DEFAULT_CONFIGS]
        self.save()

    def save(self) -> None:
        """Persist current configs to disk."""
        with open(self._path, "w", encoding="utf-8") as fh:
            json.dump(self._configs, fh, ensure_ascii=False, indent=2)

    def get_all(self) -> List[Dict[str, Any]]:
        return list(self._configs)

    def get(self, index: int) -> Dict[str, Any]:
        return dict(self._configs[index])

    def add(self, config: Dict[str, Any]) -> None:
        self._configs.append(dict(config))
        self.save()

    def update(self, index: int, config: Dict[str, Any]) -> None:
        self._configs[index] = dict(config)
        self.save()

    def delete(self, index: int) -> None:
        del self._configs[index]
        self.save()

    def count(self) -> int:
        return len(self._configs)
