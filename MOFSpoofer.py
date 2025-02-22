import os
import subprocess
import ctypes
from tkinter import messagebox
import random
import string
import winreg
import binascii
import uuid
import time

import Details
from BackupManager import BackupManager
from MOFManager import MOFManager

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_hidden(cmd):
    """Run a command in the background without opening a visible CMD window."""
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW  # Hides the window
    return subprocess.run(cmd, shell=True, startupinfo=startupinfo, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

class SpooferServiceManager:
    MOFM = MOFManager()
    BUM = BackupManager()
    original_file = "backups\\Origin.json"
    
    def get_partition_serials(self):
        try:
            ps_command = "powershell -Command Get-CimInstance Win32_LogicalDisk | Select-Object DeviceID, VolumeSerialNumber | ConvertTo-Json"
            result = run_hidden(ps_command)
            
            if not result.stdout.strip():
                return {}
            
            import json
            data = json.loads(result.stdout)
            
            # Handle single disk (dict) or multiple disks (list)
            if isinstance(data, dict):
                data = [data]
            
            serials = {}
            for disk in data:
                device_id = disk.get('DeviceID', '')
                serial = disk.get('VolumeSerialNumber', '')
                if device_id and serial:
                    serials[device_id] = serial
            
            return serials
        except Exception:
            return {}
    
    def spoof_partition_serials(self):
        new_serials = {}
        
        try:
            for drive in self.get_partition_serials().keys():
                part1 = ''.join(random.choices("ABCDEF0123456789", k=4))  # ABCD
                part2 = ''.join(random.choices("0123456789", k=4))  # 1234
                new_serial = f"{part1}-{part2}"  # Example: A1B2-3456
                new_serials[drive] = new_serial

                cmd = f'"{Details.resource_path("Volumeid.exe")}" /accepteula {drive} {part1}-{part2}'
                run_hidden(cmd)
        except:
            return False
            
        return True
    
    def generate_realistic_device_name(self):
        prefixes = ["DESKTOP-", "WIN-", "PC-", "WORK-"]
        return random.choice(prefixes) + ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(7))

    def set_reg_value(self, root_key, sub_key, value_name, value_type, value):
        try:
            key = winreg.CreateKey(root_key, sub_key)
            if value_type == "REG_SZ":
                winreg.SetValueEx(key, value_name, 0, winreg.REG_SZ, value)
            elif value_type == "REG_DWORD":
                winreg.SetValueEx(key, value_name, 0, winreg.REG_DWORD, value)
            elif value_type == "REG_BINARY":
                winreg.SetValueEx(key, value_name, 0, winreg.REG_BINARY, value)
            winreg.CloseKey(key)
            return True
        except:
            return False

    def spoof_windows_identifiers(self):
        try:
            identifiers = {
                "ComputerName": self.generate_realistic_device_name(),
                "MachineGuid": str(uuid.uuid4()),  # Use proper UUID format
                "ProductId": f"{random.randint(10000,99999)}-{random.randint(10000,99999)}-{random.randint(10000,99999)}-{random.randint(10000,99999)}",
                "BuildGUID": str(uuid.uuid4()),  # Use proper UUID format
                "InstallDate": random.randint(0x5C000000, 0x65000000),  # 2019-2023 timestamp range
                "DigitalProductId": binascii.hexlify(os.urandom(164)).decode(),
                "DeviceId": str(uuid.uuid4()).upper(),  # For Settings > About
                "ProfileGuid": str(uuid.uuid4()),  # User profile GUID
                "SqmId": str(uuid.uuid4()),  # Windows Customer Experience Improvement Program
                "UserId": str(uuid.uuid4()),  # User identifier
            }
            self.set_reg_value(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\ComputerName\ComputerName", "ComputerName", "REG_SZ", identifiers['ComputerName'])
            self.set_reg_value(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\ComputerName\ActiveComputerName", "ComputerName", "REG_SZ", identifiers['ComputerName'])
            self.set_reg_value(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters", "NV Hostname", "REG_SZ", identifiers['ComputerName'])
            self.set_reg_value(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters", "Hostname", "REG_SZ", identifiers['ComputerName'])
            self.set_reg_value(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Cryptography", "MachineGuid", "REG_SZ", identifiers['MachineGuid'])
            self.set_reg_value(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion", "ProductId", "REG_SZ", identifiers['ProductId'])
            self.set_reg_value(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion", "BuildGUID", "REG_SZ", identifiers['BuildGUID'])
            self.set_reg_value(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion", "InstallDate", "REG_DWORD", identifiers['InstallDate'])
            self.set_reg_value(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion", "DigitalProductId", "REG_BINARY", binascii.unhexlify(identifiers['DigitalProductId']))
            self.set_reg_value(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\SQMClient", "MachineId", "REG_SZ", identifiers['DeviceId'])
            self.set_reg_value(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\SQMClient", "UserId", "REG_SZ", identifiers['UserId'])
            self.set_reg_value(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion", "ProfileGuid", "REG_SZ", identifiers['ProfileGuid'])
        except:
            return False
        return True

    def spoof_mac_address(self, mac_addresses=None):
        """
        Spoof MAC addresses for network adapters.
        
        Args:
            mac_addresses (dict, optional): Custom MAC addresses
                Keys: 'ethernet', 'wifi', 'bluetooth'
                Values: MAC address strings in format 'XX:XX:XX:XX:XX:XX'
        """
        # Extract custom MACs or use None
        custom_eth_mac = mac_addresses.get('ethernet', '') if mac_addresses else ''
        custom_wifi_mac = mac_addresses.get('wifi', '') if mac_addresses else ''
        custom_bt_mac = mac_addresses.get('bluetooth', '') if mac_addresses else ''
        
        # Convert colons to no separator for registry (XXXXXXXXXXXX format)
        def format_mac_for_registry(mac):
            if mac:
                return mac.replace(':', '').replace('-', '').upper()
            return ''
        
        eth_mac_reg = format_mac_for_registry(custom_eth_mac)
        wifi_mac_reg = format_mac_for_registry(custom_wifi_mac)
        bt_mac_reg = format_mac_for_registry(custom_bt_mac)
        
        script = rf"""@ECHO OFF
echo Changing all network adapter and Bluetooth MAC addresses...
echo.

:: Check for admin rights
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo Error: Administrator privileges required!
    echo Please run this script as administrator.
    pause
    exit /b 1
)

SETLOCAL ENABLEDELAYEDEXPANSION
SETLOCAL ENABLEEXTENSIONS

echo Current MAC addresses:
echo -------------------
getmac /v
echo -------------------
echo.
echo Changing MAC addresses...
echo.

:: Custom MAC addresses (empty if not provided)
SET "CUSTOM_ETH_MAC={eth_mac_reg}"
SET "CUSTOM_WIFI_MAC={wifi_mac_reg}"
SET "CUSTOM_BT_MAC={bt_mac_reg}"

::Generate and implement a random MAC address for network adapters
SET "ADAPTER_COUNT=0"
FOR /F "tokens=1" %%a IN ('powershell -Command "Get-CimInstance Win32_NetworkAdapter -Filter 'PhysicalAdapter=True' | Select-Object -ExpandProperty DeviceID"') DO (
    :: Determine if this is Ethernet or WiFi
    SET "USE_CUSTOM_MAC="
    
    :: Check adapter type via PowerShell
    FOR /F "tokens=*" %%t IN ('powershell -Command "Get-CimInstance Win32_NetworkAdapter -Filter \"DeviceID=%%a\" | Select-Object -ExpandProperty Name"') DO (
        SET "ADAPTER_NAME=%%t"
    )
    
    :: If adapter name contains WiFi/Wireless and custom WiFi MAC provided, use it
    echo !ADAPTER_NAME! | findstr /I /C:"Wi-Fi" /C:"Wireless" /C:"WLAN" >nul
    IF !ERRORLEVEL! EQU 0 (
        IF NOT "!CUSTOM_WIFI_MAC!"=="" (
            SET "MAC=!CUSTOM_WIFI_MAC!"
            SET "USE_CUSTOM_MAC=1"
        )
    ) ELSE (
        :: Otherwise it's Ethernet, use custom Ethernet MAC if provided
        IF NOT "!CUSTOM_ETH_MAC!"=="" (
            IF !ADAPTER_COUNT! EQU 0 (
                SET "MAC=!CUSTOM_ETH_MAC!"
                SET "USE_CUSTOM_MAC=1"
                SET /A ADAPTER_COUNT+=1
            )
        )
    )
    
    :: If no custom MAC, generate random
    IF NOT DEFINED USE_CUSTOM_MAC (
        CALL :MAC
    )
    
    echo Adapter ID: %%a, New MAC: !MAC!
    FOR %%b IN (0 00 000) DO (
        REG QUERY HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\Class\{{4D36E972-E325-11CE-BFC1-08002bE10318}}\%%b%%a >NUL 2>NUL && (
            REG ADD HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\Class\{{4D36E972-E325-11CE-BFC1-08002bE10318}}\%%b%%a /v NetworkAddress /t REG_SZ /d !MAC! /f >NUL 2>NUL
            FOR /F "tokens=*" %%c IN ('REG QUERY HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\Class\{{4D36E972-E325-11CE-BFC1-08002bE10318}}\%%b%%a /v DriverDesc ^| findstr /i "DriverDesc"') DO (
                set "line=%%c"
                set "line=!line:*REG_SZ    =!"
                echo Changed MAC for: !line!
            )
        )
    )
)

::Generate and implement a random MAC address for Bluetooth adapters
FOR /F "tokens=*" %%a IN ('powershell -Command "Get-CimInstance Win32_PnPEntity -Filter \"PNPClass='Bluetooth'\" | Where-Object {{$_.DeviceID -like 'BTH*'}} | Select-Object -ExpandProperty DeviceID"') DO (
    :: Use custom Bluetooth MAC if provided
    IF NOT "!CUSTOM_BT_MAC!"=="" (
        SET "MAC=!CUSTOM_BT_MAC!"
    ) ELSE (
        CALL :MAC
    )
    echo Bluetooth Device: %%a, New MAC: !MAC!
    FOR /F "tokens=*" %%b IN ('REG QUERY "HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Services\BTHPORT\Parameters\Devices" /s ^| findstr /i "HKEY_"') DO (
        REG ADD "%%b" /v "LocalAddress" /t REG_SZ /d !MAC! /f >NUL 2>NUL
        echo Changed Bluetooth MAC address in registry: %%b
    )
)

::Disable power saving mode for network adapters
FOR /F "tokens=1" %%a IN ('powershell -Command "Get-CimInstance Win32_NetworkAdapter -Filter 'PhysicalAdapter=True' | Select-Object -ExpandProperty DeviceID"') DO (
    FOR %%b IN (0 00 000) DO (
        REG QUERY HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\Class\{{4D36E972-E325-11CE-BFC1-08002bE10318}}\%%b%%a >NUL 2>NUL && (
            REG ADD HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\Class\{{4D36E972-E325-11CE-BFC1-08002bE10318}}\%%b%%a /v PnPCapabilities /t REG_DWORD /d 24 /f >NUL 2>NUL
            echo Disabled power saving for adapter %%b%%a
        )
    )
)

::Reset NIC adapters so the new MAC address is implemented and the power saving mode is disabled.
echo.
echo Resetting network adapters...
FOR /F "tokens=*" %%a IN ('powershell -Command "Get-NetAdapter | Where-Object {{$_.Status -ne 'Disabled'}} | Select-Object -ExpandProperty Name"') DO (
    echo Resetting adapter: %%a
    netsh interface set interface name="%%a" disable >NUL 2>NUL
    timeout /t 1 /nobreak >NUL
    netsh interface set interface name="%%a" enable >NUL 2>NUL
)

echo.
echo Restarting Bluetooth services...
net stop "Bluetooth Support Service" /y >NUL 2>NUL
timeout /t 2 /nobreak >NUL
net start "Bluetooth Support Service" >NUL 2>NUL
echo Bluetooth services restarted.

echo.
echo New MAC addresses:
echo -------------------
timeout /t 3 /nobreak >NUL
getmac /v
echo -------------------
echo.
echo Bluetooth MAC addresses:
echo -------------------
REG QUERY "HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Services\BTHPORT\Parameters\Devices" /s | findstr /i "LocalAddress"
echo -------------------
echo.
echo All MAC addresses (network and Bluetooth) spoofing completed!
echo.
timeout /t 3 /nobreak >nul
GOTO :EOF
:MAC
::Generates semi-random value of a length according to the "if !COUNT!" line, minus one, and from the characters in the GEN variable
SET COUNT=0
SET GEN=ABCDEF0123456789
SET GEN2=26AE
SET MAC=
:MACLOOP
SET /a COUNT+=1
SET RND=%random%
::%%n, where the value of n is the number of characters in the GEN variable minus one. So if you have 15 characters in GEN, set the number as 14
SET /A RND=RND%%16
SET RNDGEN=!GEN:~%RND%,1!
SET /A RND2=RND%%4
SET RNDGEN2=!GEN2:~%RND2%,1!
IF "!COUNT!" EQU "2" (SET MAC=!MAC!!RNDGEN2!) ELSE (SET MAC=!MAC!!RNDGEN!)
IF !COUNT! LEQ 11 GOTO MACLOOP
exit /b 0
        """

        try:
            Details.hold_connection_flag = True
            NEW_MAC_BAT = Details.resource_path("MAC_CHANGER.bat")
            with open(NEW_MAC_BAT, 'w') as f:
                f.write(script)
                f.close()
            run_hidden(Details.resource_path(NEW_MAC_BAT))
            os.remove(NEW_MAC_BAT)
            
            # Wait for connection restore logic
            tries = 0
            while 1:
                if Details.get_public_ip() is not None:
                    break
                if tries > 20: # 20 tries * 5 seconds = 100 seconds timeout
                    messagebox.showerror("Connection Error", "Failed to spoof MAC address\nCheck internet connection")
                    return False
                time.sleep(5)
                tries += 1
                
            Details.hold_connection_flag = False

            return True
        except Exception as e:
            Details.debug_print(f"Failed to spoof MAC address: {str(e)}")
            return False
    
    def restore_original_mac_addresses(self):
        Details.hold_connection_flag = True
        """Remove MAC address overrides from registry and reset adapters."""
        removed = False
        NETWORK_CLASS_KEY = r"SYSTEM\CurrentControlSet\Control\Class\{4d36e972-e325-11ce-bfc1-08002be10318}"
        
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, NETWORK_CLASS_KEY) as base:
                for i in range(0, winreg.QueryInfoKey(base)[0]):
                    try:
                        subkey_name = winreg.EnumKey(base, i)
                        with winreg.OpenKey(base, subkey_name, 0, winreg.KEY_ALL_ACCESS) as subkey:
                            try:
                                winreg.DeleteValue(subkey, "NetworkAddress")
                                Details.debug_print(f"[+] Removed MAC override from adapter {subkey_name}")
                                removed = True
                            except FileNotFoundError:
                                pass
                    except Exception:
                        pass
        except Exception as e:
            Details.debug_print(f"[!] Registry access failed: {e}")
        
        # Reset network adapters if MAC overrides were removed
        if removed:
            Details.debug_print("[*] Resetting network adapters...")
            try:
                # Disable adapters
                subprocess.run(
                    ["powershell", "-Command", "Get-NetAdapter | Where-Object {$_.Status -ne 'Disabled'} | Disable-NetAdapter -Confirm:$false"],
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    timeout=10
                )
                time.sleep(3)
                # Enable adapters
                subprocess.run(
                    ["powershell", "-Command", "Get-NetAdapter | Enable-NetAdapter -Confirm:$false"],
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    timeout=10
                )
                Details.debug_print("[✔] MAC addresses restored to hardware defaults")
            except Exception as e:
                Details.debug_print(f"[!] Adapter reset failed: {e}")
        else:
            Details.debug_print("[ℹ] No MAC override found (already original)")

        # Wait for connection restore logic
        tries = 0
        while 1:
            if Details.get_public_ip() is not None:
                break
            if tries > 20: # 20 tries * 5 seconds = 100 seconds timeout
                messagebox.showerror("Connection Error", "Failed to restore original MAC address\nCheck internet connection")
                return False
            time.sleep(5)
            tries += 1
            
        Details.hold_connection_flag = False
        
        return removed
    
    def restart_system(self, force=False):
        if force:
                os.system("shutdown /r /t 5")
        else:
            if messagebox.askyesno("Restart", "System needs to restart to complete. Restart now?"):
                try:
                    os.system("shutdown /r /t 5")
                except Exception as e:
                    Details.debug_print(f"Failed to initiate restart: {str(e)}")
    
    def check_spoofer_installed(self):
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\HydraSpoofer", 0, winreg.KEY_READ)
            value, _ = winreg.QueryValueEx(key, "SpoofStatus")
            winreg.CloseKey(key)
            return value == 1
        except FileNotFoundError:
            return False
        except Exception:
            return False
    
    def set_spoof_status(self, active=True):
        """Set or remove the registry spoof status flag"""
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\HydraSpoofer", 0, winreg.KEY_SET_VALUE)
        except FileNotFoundError:
             key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\HydraSpoofer")
        
        try:
            if active:
                winreg.SetValueEx(key, "SpoofStatus", 0, winreg.REG_DWORD, 1)
            else:
                try:
                    winreg.DeleteValue(key, "SpoofStatus")
                except FileNotFoundError:
                    pass
            winreg.CloseKey(key)
            return True
        except Exception:
            return False

    def install_service(self, config=None):
        if not is_admin():
            messagebox.showerror("Error", "Administrator privileges required")
            return False, "Administrator privileges required"
        
        if not os.path.exists(self.original_file):
            self.BUM.backup_hardware_info("Origin")
        
        # Set registry flag to indicate spoofing occurred
        self.set_spoof_status(True)

        error_message = []
        success_message = []
        
        # Default behavior: Spoof everything randomly if no config
        should_spoof_mac = True
        should_spoof_win = True
        should_spoof_parts = True
        should_spoof_smbios = True
        should_spoof_disk = True
        should_spoof_mem = True
        # should_spoof_gpu = True
        
        # SMBIOS specific data
        cpu_data = None
        baseboard_data = None
        bios_data = None
        system_data = None
        enclosure_data = None
        
        # Other data
        disk_data = None
        mem_data = None

        if config:
            # Parse config
            should_spoof_mac = config.get("spoof_mac", False)
            should_spoof_win = config.get("spoof_win", False)
            should_spoof_parts = config.get("spoof_parts", False)
            should_spoof_smbios = config.get("spoof_smbios", False)
            should_spoof_disk = config.get("spoof_disk", False)
            should_spoof_mem = config.get("spoof_mem", False)
            # should_spoof_gpu = config.get("spoof_gpu", False)

            # Helper to prepare data for MOFManager
            def prepare_data(category, serial_key, custom_val):
                if custom_val and custom_val.strip():
                    info = self.MOFM.get_hardware_info(category)
                    info[serial_key] = custom_val
                    return info
                return None # None means random in MOFManager

            if should_spoof_smbios:
                cpu_data = prepare_data("processor", "ProcessorId", config.get("cpu_serial"))
                baseboard_data = prepare_data("baseboard", "SerialNumber", config.get("baseboard_serial"))
                bios_data = prepare_data("bios", "SerialNumber", config.get("bios_serial"))
                system_data = prepare_data("computer_system", "UUID", config.get("uuid_serial"))
                enclosure_data = prepare_data("system_enclosure", "SerialNumber", config.get("enclosure_serial"))
            
            if should_spoof_disk:
                disks = self.MOFM.get_hardware_info("disk_drive")
                if isinstance(disks, dict): disks = [disks]
                elif not disks: disks = []
                
                new_disks = []
                for i, d in enumerate(disks):
                    custom_val = config.get(f"disk_{i}_serial")
                    if custom_val and custom_val.strip():
                        d['SerialNumber'] = custom_val
                    else:
                        d['SerialNumber'] = self.MOFM.generate_disk_serial()
                    new_disks.append(d)
                disk_data = new_disks
            
            # Memory similar to disk
            if should_spoof_mem:
                mems = self.MOFM.get_hardware_info("physical_memory")
                if isinstance(mems, dict): mems = [mems]
                elif not mems: mems = []

                new_mems = []
                for i, m in enumerate(mems):
                    custom_val = config.get(f"mem_{i}_serial")
                    if custom_val and custom_val.strip():
                        m['SerialNumber'] = custom_val
                    else:
                        m['SerialNumber'] = self.MOFM.generate_serial(m.get('SerialNumber', ''))
                    new_mems.append(m)
                mem_data = new_mems

        
        if should_spoof_mac:
            # Parse custom MAC addresses if provided
            mac_addresses = {}
            if config:
                if config.get("mac_ethernet"):
                    mac_addresses['ethernet'] = config.get("mac_ethernet")
                if config.get("mac_wifi"):
                    mac_addresses['wifi'] = config.get("mac_wifi")
                if config.get("mac_bluetooth"):
                    mac_addresses['bluetooth'] = config.get("mac_bluetooth")
            
            if not self.spoof_mac_address(mac_addresses=mac_addresses if mac_addresses else None):
                error_message.append("• Failed to spoof (MAC Address)")
            else:
                success_message.append("• Spoofed (MAC Address)")
        
        if should_spoof_win:
            if not self.spoof_windows_identifiers():
                error_message.append("• Failed to spoof (Windows Internals)")
            else:
                success_message.append("• Spoofed (Windows Internals)")
            
        if should_spoof_parts:
            if not self.spoof_partition_serials():
                error_message.append("• Failed to spoof (Disks Partitions)")
            else:
                success_message.append("• Spoofed (Disks Partitions)")
        
        if should_spoof_smbios:
            if not self.MOFM.spoof_smbios_serials(cpu_info=cpu_data, cs_info=system_data, baseboard_info=baseboard_data, bios_info=bios_data, enclosure_info=enclosure_data):
                error_message.append("• Failed to spoof (BaseBoard/BIOS/CPU)")
            else:
                success_message.append("• Spoofed (BaseBoard/BIOS/CPU)")
        
        if should_spoof_disk:
            if not self.MOFM.spoof_hard_disks(disks=disk_data):
                error_message.append("• Failed to spoof (Disks)")
            else:
                success_message.append("• Spoofed (Disks)")
        
        if should_spoof_mem:
            if not self.MOFM.spoof_memory(memory_modules=mem_data):
                error_message.append("• Failed to spoof (Memory)")
            else:
                success_message.append("• Spoofed (Memory)")
        
        # if should_spoof_gpu:
        #     if not self.MOFM.spoof_gpus():
        #         message += "• Failed to spoof (GPUs)" if message is None else "\n• Failed to spoof (GPUs)"
        
        if error_message:
            return False, error_message
        return True, success_message
    
    
    def uninstall_service(self, service=False):
        if not is_admin():
            messagebox.showerror("Error", "Administrator privileges required")
            return False
        
        # Restore original MAC addresses
        self.restore_original_mac_addresses()
        
        # Restore SMBIOS and other hardware info
        self.MOFM.restore_originals()
        
        # Remove backup file
        if os.path.exists(self.original_file):
            os.remove(self.original_file)
        
        # Clear spoof status flag
        self.set_spoof_status(False)

        if service:
            self.restart_system(force=True)
        return True