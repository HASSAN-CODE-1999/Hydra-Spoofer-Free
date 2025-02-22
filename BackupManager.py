import json
import pickle
import os
from datetime import datetime

from MOFManager import MOFManager
import Details

class BackupManager:
    def __init__(self):
        self.mof = MOFManager()

    def write_backup(self, data, filename=None, backup_dir="backups", format="json"):
        """
        Write data to a backup file.
        
        Args:
            data: The data to backup (should be serializable)
            filename: Optional filename (will auto-generate if None)
            backup_dir: Directory to store backups
            format: "json" or "pickle"
        
        Returns:
            str: Path to the created backup file
        """
        # Create backup directory if it doesn't exist
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        
        # Generate filename if not provided
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"backup_{timestamp}.{format}"
        else:
            # Ensure file has proper extension
            if not filename.endswith(f".{format}"):
                filename = f"{filename}.{format}"
        
        backup_path = os.path.join(backup_dir, filename)
        
        try:
            if format.lower() == "json":
                with open(backup_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
            elif format.lower() == "pickle":
                with open(backup_path, 'wb') as f:
                    pickle.dump(data, f)
            else:
                raise ValueError("Format must be 'json' or 'pickle'")
            
            Details.debug_print(f"Backup successfully created: {backup_path}")
            return backup_path
            
        except Exception as e:
            Details.debug_print(f"Error creating backup: {e}")
            return None

    def read_backup(self, filename, backup_dir="backups", format="auto"):
        """
        Read data from a backup file.
        
        Args:
            filename: Name of the backup file
            backup_dir: Directory where backups are stored
            format: "json", "pickle", or "auto" to detect from extension
        
        Returns:
            The restored data, or None if error
        """
        backup_path = os.path.join(backup_dir, filename)
        
        if not os.path.exists(backup_path):
            Details.debug_print(f"Backup file not found: {backup_path}")
            return None
        
        # Auto-detect format from file extension
        if format == "auto":
            if filename.endswith('.json'):
                format = "json"
            elif filename.endswith('.pickle') or filename.endswith('.pkl'):
                format = "pickle"
            else:
                raise ValueError("Could not auto-detect format from file extension")
        
        try:
            if format.lower() == "json":
                with open(backup_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            elif format.lower() == "pickle":
                with open(backup_path, 'rb') as f:
                    data = pickle.load(f)
            else:
                raise ValueError("Format must be 'json' or 'pickle'")
            
            Details.debug_print(f"Backup successfully restored from: {backup_path}")
            return data
            
        except Exception as e:
            Details.debug_print(f"Error reading backup: {e}")
            return None

    def list_backups(self, backup_dir="backups"):
        """
        List all available backup files.
        
        Args:
            backup_dir: Directory where backups are stored
        
        Returns:
            list: Sorted list of backup filenames (newest first)
        """
        if not os.path.exists(backup_dir):
            return []
        
        backups = []
        for file in os.listdir(backup_dir):
            if file.endswith(('.json', '.pickle', '.pkl')):
                file_path = os.path.join(backup_dir, file)
                mod_time = os.path.getmtime(file_path)
                backups.append((file, mod_time))
        
        # Sort by modification time (newest first)
        backups.sort(key=lambda x: x[1], reverse=True)
        return [backup[0] for backup in backups]

    def backup_hardware_info(self, filename=None, backup_dir="backups"):
        """
        Backup all hardware information to a file.
        
        Args:
            backup_dir: Directory to store the backup
        
        Returns:
            str: Path to the created backup file
        """
        if filename is None:
            filename = f"hardware_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        return self.write_backup(self.mof.get_all_serials(), filename, backup_dir, "json")

    def restore_hardware_info(self, filename, backup_dir="backups"):
        """
        Restore hardware information from backup.
        
        Args:
            filename: Name of the backup file
            backup_dir: Directory where backups are stored
        
        Returns:
            dict: The restored hardware data
        """
        restore = self.read_backup(filename, backup_dir, "json")

        module_dicts = {}

        for module, data in restore.items():
            module_dicts[module] = data.copy() if isinstance(data, dict) else {module: data}

        if not self.mof.spoof_smbios_serials(module_dicts["Processor"],
                                      module_dicts["ComputerSystem"],
                                      module_dicts["BaseBoard"],
                                      module_dicts["SystemEnclosure"],
                                      module_dicts["BIOS"]):
            return False, "Failed to restore (BaseBoard)"
        
        if not self.mof.spoof_hard_disks(module_dicts["DiskDrives"]):
            return False, "Failed to restore (Disks)"

        if not self.mof.spoof_memory(module_dicts["Memory"]):
            return False, "Failed to restore (Memorys)"
        
        return True, ""


# Example usage:
if __name__ == "__main__":
    bu = BackupManager()
    # # Backup all hardware info
    # backup_path = bu.backup_hardware_info()
    
    # Restore from specific backup
    restored_data = bu.restore_hardware_info("Spoof1.json")
