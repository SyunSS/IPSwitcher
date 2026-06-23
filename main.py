"""
Entry point for IP Switcher.

On Windows:
  - Checks if the process is running with administrator privileges.
  - If not, re-launches itself via ShellExecuteW with 'runas' verb (UAC prompt).
  - If already admin (or on non-Windows for dev testing), launches the Qt GUI.
"""
import sys
import os


def _is_admin() -> bool:
    """Return True if the current process has administrator privileges."""
    if sys.platform != "win32":
        # On non-Windows (dev/CI), pretend we have admin so the UI starts.
        return True
    try:
        import ctypes
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def _relaunch_as_admin() -> None:
    """Re-launch this executable/script with UAC elevation and exit."""
    import ctypes

    if getattr(sys, "frozen", False):
        # PyInstaller single-file exe
        exe = sys.executable
        params = " ".join(f'"{a}"' for a in sys.argv[1:])
    else:
        exe = sys.executable
        script = os.path.abspath(sys.argv[0])
        params = f'"{script}"' + (" " + " ".join(f'"{a}"' for a in sys.argv[1:]) if len(sys.argv) > 1 else "")

    # SW_SHOWNORMAL = 1
    ret = ctypes.windll.shell32.ShellExecuteW(None, "runas", exe, params, None, 1)
    if ret <= 32:
        # ShellExecuteW failed (e.g. user cancelled UAC)
        import ctypes.wintypes
        from PyQt6.QtWidgets import QApplication, QMessageBox
        _app = QApplication(sys.argv)
        QMessageBox.critical(
            None,
            "权限错误",
            "无法获取管理员权限。\n\n"
            "请右键点击程序图标，选择「以管理员身份运行」。",
        )
    sys.exit(0)


def main() -> None:
    is_admin = _is_admin()

    if sys.platform == "win32" and not is_admin:
        _relaunch_as_admin()
        return  # Unreachable, but keeps static analysis happy

    # ── Launch Qt application ──────────────────────────────────────
    from PyQt6.QtWidgets import QApplication
    from ui.main_window import MainWindow

    app = QApplication(sys.argv)
    app.setApplicationName("IP 切换管理器")
    app.setOrganizationName("IPSwitcher")

    # High-DPI is enabled by default in Qt6

    window = MainWindow(is_admin=is_admin)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
