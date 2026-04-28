import json
import os
import re
from datetime import datetime
from MOFManager import MOFManager
import Details

class BackupManager:
    def __init__(self):
        self.mof = MOFManager()
        # ريجيكس لمنع رموز حقن الأوامر (Command Injection) لضمان الأمان
        self.injection_pattern = re.compile(r'[;&`]')

    def _sanitize_data(self, data):
        # فحص البيانات المدخلة للتأكد من خلوها من أي رموز حقن أوامر خبيثة
        if isinstance(data, dict):
            return {str(k): self._sanitize_data(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._sanitize_data(i) for i in data]
        elif isinstance(data, str):
            if self.injection_pattern.search(data):
                Details.debug_print(f"[!] Security Alert: Blocked potential injection: {data}")
                return "INVALID_DATA_SECURED"
            return data
        return data

    def write_backup(self, data, filename=None, backup_dir="backups"):
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"backup_{timestamp}.json"
        elif not filename.endswith(".json"):
            filename = f"{filename}.json"
        
        backup_path = os.path.join(backup_dir, filename)
        
        try:
            # استخدام صيغة JSON بدلاً من pickle لمنع ثغرات تنفيذ الأكواد (RCE)
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            Details.debug_print(f"Backup created: {backup_path}")
            return backup_path
        except Exception as e:
            Details.debug_print(f"Write Error: {e}")
            return None

    def read_backup(self, filename, backup_dir="backups"):
        backup_path = os.path.join(backup_dir, filename)
        if not os.path.exists(backup_path):
            return None
        
        try:
            with open(backup_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            # تطبيق الفحص الأمني (Sanitization) على البيانات المستعادة
            return self._sanitize_data(data)
        except Exception as e:
            Details.debug_print(f"Read Error: {e}")
            return None

    def list_backups(self, backup_dir="backups"):
        if not os.path.exists(backup_dir): return []
        backups = [f for f in os.listdir(backup_dir) if f.endswith('.json')]
        backups.sort(key=lambda x: os.path.getmtime(os.path.join(backup_dir, x)), reverse=True)
        return backups

    def backup_hardware_info(self, filename=None, backup_dir="backups"):
        return self.write_backup(self.mof.get_all_serials(), filename, backup_dir)

    def restore_hardware_info(self, filename, backup_dir="backups"):
        restore = self.read_backup(filename, backup_dir)
        if not restore:
            return False, "Failed to read backup"

        try:
            # تمرير البيانات المطهّرة (Sanitized) لضمان عدم تنفيذ أوامر غير مصرح بها
            self.mof.spoof_smbios_serials(
                restore.get("Processor", {}),
                restore.get("ComputerSystem", {}),
                restore.get("BaseBoard", {}),
                restore.get("SystemEnclosure", {}),
                restore.get("BIOS", {})
            )
            self.mof.spoof_hard_disks(restore.get("DiskDrives", {}))
            self.mof.spoof_memory(restore.get("Memory", {}))
            return True, "Success"
        except Exception as e:
            Details.debug_print(f"Restore Error: {e}")
            return False, str(e)

