import os, sys
import signal
import subprocess
from tkinter import messagebox
import hashlib

import DataStoring as DS


def resource_path(relative_path=None):
    """ Get absolute path to bundled resource, works for dev and PyInstaller/Nuitka onefile mode. """
    if hasattr(sys, '_MEIPASS'):
        base_dir = sys._MEIPASS
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    if relative_path:
        return os.path.join(base_dir, relative_path)
    else:
        return os.path.join(base_dir)
           
applicationName = "HYDRA SPOOFER"
__version__ = "1.5.5"
imgsPath = resource_path("imgs\\")
hold_connection_flag = False
kill_switch = False
reg_key_path = rf"SOFTWARE\{applicationName}"
save_user_data = "key"


def get_hwid(real=False):
    key_path = rf"SOFTWARE\HWID"
    key_name = "HWID"

    stored_hwid = ""

    if not stored_hwid:
        try:
            ps_cmd = (
                "$c = (Get-CimInstance Win32_Processor).ProcessorId;"
                "$u = (Get-CimInstance Win32_ComputerSystemProduct).UUID;"
                "$raw = [string]$u + '|' + [string]$c;"
                "Write-Output $raw.Replace(' ', '').ToUpper()"
            )

            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_cmd],
                capture_output=True,
                text=True,
                check=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )

            raw_data = result.stdout.strip()
            
            if raw_data and len(raw_data.replace('|', '')) > 10:
                DS.write_to_registry(key_path, key_name, raw_data)
                stored_hwid = raw_data
            else:
                raise ValueError("Incomplete hardware profile")

        except Exception as e:
            messagebox.showerror("Runtime error!", "Error while checking device credentials.\nSystem powershell may have an issue.")
            kill()

    if not stored_hwid:
        kill()

    if real:
        return str(stored_hwid)
    else:
        return hashlib.sha224(stored_hwid.encode()).hexdigest().upper()

def kill():
    os.kill(os.getpid(), signal.SIGTERM)