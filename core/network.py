"""
Network utilities: enumerate adapters, apply IP configuration via netsh,
and fetch public IP info.
"""
import subprocess
import sys
from typing import List, Tuple, Dict, Any


def get_public_ip(timeout: int = 8) -> str:
    """
    Fetch the public IP info from myip.ipip.net.
    Uses urllib (built-in) for reliability on Windows without curl.
    Returns a human-readable string on success, or an error message on failure.
    """
    try:
        import urllib.request
        import socket

        socket.setdefaulttimeout(timeout)
        req = urllib.request.Request(
            "http://myip.ipip.net",
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read()
            encoding = resp.info().get_content_charset("utf-8")
            text = data.decode(encoding).strip()
            return text if text else "获取失败（空响应）"
    except Exception as exc:
        return f"获取失败：{exc}"


def get_adapters_with_status() -> List[Tuple[str, str, bool]]:
    """
    Return a list of (adapter_name, interface_description, is_enabled) tuples.

    - adapter_name: the NetConnectionID / friendly name shown in "Network Connections" (e.g. "以太网 2")
    - interface_description: the hardware/driver description (e.g. "Realtek PCIe GbE Family Controller")
    - is_enabled: True = enabled/administratively Up, False = Disabled

    is_enabled = True means the adapter is Up or Disconnected (hardware enabled).
    is_enabled = False means the adapter is administratively Disabled.
    """
    try:
        ps_cmd = (
            "Get-NetAdapter | "
            "Select-Object Name, InterfaceDescription, Status | "
            "ForEach-Object { $_.Name + '|' + $_.InterfaceDescription + '|' + $_.Status }"
        )
        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", ps_cmd],
            capture_output=True,
            text=True,
            timeout=10,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )
        stdout = result.stdout or ""
        if result.returncode == 0 and stdout.strip():
            adapters = []
            for line in stdout.strip().splitlines():
                line = line.strip()
                if "|" in line:
                    parts = line.split("|")
                    if len(parts) >= 3:
                        name = parts[0].strip()
                        description = parts[1].strip()
                        status = parts[2].strip().lower()
                        is_enabled = status != "disabled"
                        if name:
                            # Store (name, description, is_enabled) — caller splits if needed
                            adapters.append((name, description, is_enabled))
            if adapters:
                return adapters
    except Exception:
        pass

    # Fallback: wmic (no status/description, assume all enabled)
    try:
        result = subprocess.run(
            ["wmic", "nic", "get", "NetConnectionID,NetEnabled"],
            capture_output=True,
            text=True,
            timeout=10,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )
        stdout = result.stdout or ""
        if result.returncode == 0:
            lines = stdout.strip().splitlines()[1:]  # skip header
            adapters = []
            for line in lines:
                parts = line.split()
                if len(parts) >= 2:
                    name = " ".join(parts[:-1]).strip()
                    enabled_str = parts[-1].strip().upper()
                    is_enabled = enabled_str == "TRUE"
                    if name:
                        adapters.append((name, "", is_enabled))
            if adapters:
                return adapters
    except Exception:
        pass

    return [("以太网", "", True)]


def get_adapters() -> List[str]:
    """Return just the adapter names (backwards-compat wrapper)."""
    return [name for name, _, _ in get_adapters_with_status()]


def set_adapter_state(adapter: str, enable: bool) -> Tuple[bool, str]:
    """
    Enable or disable a network adapter via PowerShell.
    Returns (success, output_message).
    """
    action = "Enable-NetAdapter" if enable else "Disable-NetAdapter"
    ps_cmd = f'{action} -Name "{adapter}" -Confirm:$false'
    try:
        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", ps_cmd],
            capture_output=True,
            text=True,
            timeout=15,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )
        stdout = result.stdout or ""
        stderr = result.stderr or ""
        combined = (stdout + stderr).strip()
        ok = result.returncode == 0 and "error" not in combined.lower()
        if ok:
            action_cn = "启用" if enable else "禁用"
            return True, f"网卡「{adapter}」已{action_cn}"
        return False, combined or "操作失败"
    except subprocess.TimeoutExpired:
        return False, "操作超时"
    except Exception as exc:
        return False, str(exc)


def _run_netsh(args: List[str]) -> Tuple[bool, str]:
    """Run a netsh command; return (success, combined_output)."""
    cmd = ["netsh"] + args
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )
        stdout = result.stdout or ""
        stderr = result.stderr or ""
        combined = (stdout + stderr).strip()
        # netsh succeeds with returncode 0; some versions return 0 even on failure
        # so also check for Chinese/English error keywords
        ok = result.returncode == 0 and "错误" not in combined and "error" not in combined.lower()
        return ok, combined
    except subprocess.TimeoutExpired:
        return False, "命令执行超时"
    except FileNotFoundError:
        return False, "找不到 netsh 命令（仅支持 Windows）"
    except Exception as exc:
        return False, str(exc)


def apply_static_ip(adapter: str, config: Dict[str, Any]) -> List[Tuple[bool, str, str]]:
    """
    Apply a static IP configuration to *adapter*.

    Gateway and DNS fields are optional — leave empty for pure intranet (no-gateway) setups.
    Returns a list of (success, command_description, output) tuples,
    one per netsh call executed.
    """
    results: List[Tuple[bool, str, str]] = []

    gw = config.get("gateway", "").strip()

    # --- Set IP address + mask (+ optional gateway) ---
    ip_args = [
        "interface", "ip", "set", "address",
        f"name={adapter}",
        "source=static",
        f"addr={config['ip']}",
        f"mask={config['mask']}",
        f"gateway={'none' if not gw else gw}",
    ]
    if gw:
        ip_args.append("gwmetric=0")
    cmd_desc = f"netsh {' '.join(ip_args)}"
    ok, out = _run_netsh(ip_args)
    results.append((ok, cmd_desc, out))

    if not ok:
        return results  # No point setting DNS if IP failed

    # --- Set primary DNS (optional) ---
    dns1 = config.get("dns1", "").strip()
    if dns1:
        dns_args = [
            "interface", "ip", "set", "dns",
            f"name={adapter}",
            "source=static",
            f"addr={dns1}",
            "register=primary",
        ]
        cmd_desc = f"netsh {' '.join(dns_args)}"
        ok2, out2 = _run_netsh(dns_args)
        results.append((ok2, cmd_desc, out2))

    # --- Set secondary DNS (optional) ---
    dns2 = config.get("dns2", "").strip()
    if dns2:
        dns2_args = [
            "interface", "ip", "add", "dns",
            f"name={adapter}",
            f"addr={dns2}",
            "index=2",
        ]
        cmd_desc = f"netsh {' '.join(dns2_args)}"
        ok3, out3 = _run_netsh(dns2_args)
        results.append((ok3, cmd_desc, out3))

    return results


def apply_dhcp(adapter: str) -> List[Tuple[bool, str, str]]:
    """
    Switch *adapter* to DHCP (automatic IP + automatic DNS).

    Returns a list of (success, command_description, output) tuples.
    """
    results: List[Tuple[bool, str, str]] = []

    ip_args = [
        "interface", "ip", "set", "address",
        f"name={adapter}",
        "source=dhcp",
    ]
    cmd_desc = f"netsh {' '.join(ip_args)}"
    ok, out = _run_netsh(ip_args)
    results.append((ok, cmd_desc, out))

    dns_args = [
        "interface", "ip", "set", "dns",
        f"name={adapter}",
        "source=dhcp",
    ]
    cmd_desc = f"netsh {' '.join(dns_args)}"
    ok2, out2 = _run_netsh(dns_args)
    results.append((ok2, cmd_desc, out2))

    return results
