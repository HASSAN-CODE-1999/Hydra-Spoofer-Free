import subprocess
import os
import re
import psutil
import random
import string
import socket
import json

import Details

class MOFManager:
    def run_hidden(self, cmd):
        """Run a command in the background without opening a visible CMD window."""
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        return subprocess.run(cmd, 
            shell=True,
            startupinfo=startupinfo,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )

    def run_powershell(self, script):
        """Execute PowerShell script and return parsed JSON result."""
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            result = subprocess.run(
                ["powershell", "-Command", script],
                startupinfo=startupinfo,
                capture_output=True,
                text=True,
                check=True,
                shell=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            return json.loads(result.stdout) if result.stdout.strip() else {}
        except (subprocess.CalledProcessError, json.JSONDecodeError):
            return {}

    def get_hardware_info(self, category):
        """Get hardware information using PowerShell for various categories."""
        ps_scripts = {
            "computer_system": "Get-CimInstance Win32_ComputerSystemProduct | Select-Object Name, Vendor, Version, UUID, IdentifyingNumber | ConvertTo-Json",
            "bios": "Get-CimInstance Win32_BIOS | Select-Object SMBIOSBIOSVersion, Manufacturer, Name, SerialNumber | ConvertTo-Json",
            "processor": "Get-CimInstance Win32_Processor | Select-Object DeviceID, Name, ProcessorId, PartNumber, SerialNumber | ConvertTo-Json",
            "baseboard": "Get-CimInstance Win32_BaseBoard | Select-Object Manufacturer, Product, SerialNumber, Name | ConvertTo-Json",
            "system_enclosure": "Get-CimInstance Win32_SystemEnclosure | Select-Object Manufacturer, LockPresent, SerialNumber, SMBIOSAssetTag, SecurityStatus | ConvertTo-Json",
            "disk_drive": "Get-CimInstance Win32_DiskDrive | Select-Object DeviceID, SerialNumber, Model, Caption | ConvertTo-Json",
            "physical_memory": "Get-CimInstance Win32_PhysicalMemory | Select-Object Tag, SerialNumber | ConvertTo-Json",
            "video_controller": "Get-CimInstance Win32_VideoController | Select-Object Name, Description, PNPDeviceID | ConvertTo-Json"
        }
        
        if category in ps_scripts:
            return self.run_powershell(ps_scripts[category])
        return {}

    def get_network_info(self):
        """Get network interface MAC addresses."""
        addrs = psutil.net_if_addrs()
        macs = {}
        for iface, addr_list in addrs.items():
            for addr in addr_list:
                if addr.family == psutil.AF_LINK and iface in ['Ethernet', 'Ethernet0', 'Wi-Fi', 'WiFi', 'Bluetooth']:
                    macs[iface] = addr.address
        return macs

    def get_partition_serials(self):
        """Get partition serial numbers using PowerShell."""
        script = "Get-CimInstance Win32_LogicalDisk | Select-Object DeviceID, VolumeSerialNumber | ConvertTo-Json"
        return self.run_powershell(script)

    def get_hostname(self):
        """Get current device hostname."""
        return socket.gethostname()

    def generate_serial(self, original, is_uuid=False, is_upper=False):
        """Generate a random serial number based on original format."""
        if is_uuid:
            chars = "0123456789ABCDEF"
            new = f"{''.join(random.choices(chars, k=8))}-{''.join(random.choices(chars, k=4))}-{''.join(random.choices(chars, k=4))}-{''.join(random.choices(chars, k=4))}-{''.join(random.choices(chars, k=12))}"
        else:
            if is_upper:
                chars = string.ascii_uppercase + string.digits
            else:
                chars = string.ascii_letters + string.digits
            new = ''.join(random.choices(chars, k=len(original))) if original else ''.join(random.choices(chars, k=10))
        return new

    def generate_disk_serial(self):
        """Generate a disk serial number in specific format."""
        def random_hex_segment(length=4):
            return ''.join(random.choices(string.hexdigits.upper(), k=length))
        
        segments = [
            random_hex_segment(4), random_hex_segment(4),
            random_hex_segment(4), random_hex_segment(4),
            random_hex_segment(4), random_hex_segment(4),
            random_hex_segment(4), random_hex_segment(4)
        ]
        return '_'.join(segments)

    def generate_gpu_serial(self, original_serial):
        """Generate spoofed GPU serial number maintaining vendor format."""
        vendor_ids = {"8086": "INTEL", "10DE": "NVIDIA", "1002": "AMD"}
        vendor_id_map = {"INTEL": "8086", "NVIDIA": "10DE", "AMD": "1002"}
        
        pattern = r"^PCI\\\\VEN_([0-9A-F]{4})&DEV_[0-9A-F]{4}&SUBSYS_[0-9A-F]{8}&REV_[0-9A-F]{2}\\\\[0-9]&[0-9A-F]{8}&[0-9]&[0-9]{2}([0-9]{2})?$"
        match = re.match(pattern, original_serial)
        
        if not match:
            raise ValueError("Invalid GPU serial format.")
        
        extracted_vendor_id = match.group(1).upper()
        detected_vendor = vendor_ids.get(extracted_vendor_id, "UNKNOWN")
        vendor_id = vendor_id_map.get(detected_vendor, "8086")

        device_id = ''.join(random.choices(string.hexdigits, k=4)).upper()
        subsystem_id = ''.join(random.choices(string.hexdigits, k=8)).upper()
        revision_id = ''.join(random.choices(string.hexdigits, k=2)).upper()

        hardware_id_part1 = random.randint(0, 9)
        hardware_id_part2 = ''.join(random.choices(string.hexdigits, k=8)).upper()
        hardware_id_part3 = random.randint(0, 9)
        hardware_id_part4_length = random.choice([2, 4])
        hardware_id_part4 = ''.join(random.choices(string.digits, k=hardware_id_part4_length))

        return f"PCI\\\\VEN_{vendor_id}&DEV_{device_id}&SUBSYS_{subsystem_id}&REV_{revision_id}\\\\{hardware_id_part1}&{hardware_id_part2}&{hardware_id_part3}&{hardware_id_part4}"

    def create_mof_file(self, content):
        """Create and compile MOF file with minimal disk exposure"""
        mof_path = None
        try:
            # Create temp file with random name
            import tempfile
            fd, mof_path = tempfile.mkstemp(suffix='.mof', text=True)
            
            # Write content and close file descriptor
            os.write(fd, content.encode('utf-8'))
            os.close(fd)
            
            # Compile immediately
            subprocess.run(
                ["mofcomp", mof_path],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            return True
        except Exception:
            return False
        finally:
            # Delete immediately after use
            if mof_path and os.path.exists(mof_path):
                try:
                    os.remove(mof_path)
                except:
                    pass

    def spoof_smbios_serials(self, cpu_info=None, cs_info=None, baseboard_info=None, enclosure_info=None, bios_info=None):
        """Spoof SMBIOS serial numbers (CPU, BIOS, Baseboard, System Enclosure)."""
        if cpu_info is not None:
            cpu_info = cpu_info
            processor_id = cpu_info.get('ProcessorId', '')
            processor_serial_number = cpu_info.get('SerialNumber', '')
            processor_part_number = cpu_info.get('PartNumber', '')
        else:
            cpu_info = self.get_hardware_info("processor")
            processor_id = self.generate_serial(cpu_info.get('ProcessorId', ''), is_upper=True)
            processor_serial_number = self.generate_serial(cpu_info.get('SerialNumber', ''))
            processor_part_number = self.generate_serial(cpu_info.get('PartNumber', ''))
        
        if cs_info is not None:
            cs_info = cs_info
            cs_idn = cs_info.get('IdentifyingNumber', '')
            cs_uuid = cs_info.get('UUID', '')
        else:
            cs_info = self.get_hardware_info("computer_system")
            cs_idn = self.generate_serial(cs_info.get('IdentifyingNumber', ''))
            cs_uuid = self.generate_serial(cs_info.get('UUID', ''), is_uuid=True)

        if baseboard_info is not None:
            baseboard_info = baseboard_info
            bb_product = baseboard_info.get('Product', '')
            bb_serial = baseboard_info.get('SerialNumber', '')
        else:
            baseboard_info = self.get_hardware_info("baseboard")
            bb_product = self.generate_serial(baseboard_info.get('Product', ''))
            bb_serial = self.generate_serial(baseboard_info.get('SerialNumber', ''))

        if enclosure_info is not None:
            enclosure_info = enclosure_info
            enclosure_serial = enclosure_info.get('SerialNumber', '')
        else:
            enclosure_info = self.get_hardware_info("system_enclosure")
            enclosure_serial = self.generate_serial(enclosure_info.get('SerialNumber', ''))

        if bios_info is not None:
            bios_info = bios_info
            bios_serial = bios_info.get('SerialNumber', '')
            bios_version = bios_info.get('SMBIOSBIOSVersion', '')
        else:
            bios_info = self.get_hardware_info("bios")
            bios_serial = self.generate_serial(bios_info.get('SerialNumber', '')).upper()
            bios_version = self.generate_serial(self.get_hardware_info("bios").get('SMBIOSBIOSVersion', ''), is_upper=True)

        mof_content = f'''#pragma namespace("\\\\\\\\.\\\\root\\\\CIMv2")

    [DYNPROPS]
    class Win32_Processor
    {{
        [key] string DeviceID;
        string Name;
        string ProcessorId;
        string SerialNumber;
        string PartNumber;
    }};

    instance of Win32_Processor
    {{
        DeviceID = "{self.get_hardware_info("processor").get('DeviceID', 'CPU0')}";
        Name = "{cpu_info.get('Name', '')}";
        ProcessorId = "{processor_id}";
        SerialNumber = "{processor_serial_number}";
        PartNumber = "{processor_part_number}";
    }};

    [DYNPROPS]
    class Win32_ComputerSystemProduct
    {{
        [key] string Name;
        string Vendor;
        string Version;
        string IdentifyingNumber;
        string UUID;
    }};

    instance of Win32_ComputerSystemProduct
    {{
        Name = "{self.get_hardware_info("computer_system").get('Name', '')}";
        Vendor = "{cs_info.get('Vendor', '')}";
        Version = "{cs_info.get('Version', '')}";
        IdentifyingNumber = "{cs_idn}";
        UUID = "{cs_uuid}";
    }};

    [DYNPROPS]
    class Win32_BaseBoard
    {{
        [key] string Manufacturer;
        string Name;
        string Product;
        string SerialNumber;
    }};

    instance of Win32_BaseBoard
    {{
        Manufacturer = "{self.get_hardware_info("baseboard").get('Manufacturer', '')}";
        Name = "{baseboard_info.get('Name', '')}";
        Product = "{bb_product}";
        SerialNumber = "{bb_serial}";
    }};

    [DYNPROPS]
    class Win32_SystemEnclosure
    {{
        [key] string Manufacturer;
        string LockPresent;
        string SMBIOSAssetTag;
        string SecurityStatus;
        string SerialNumber;
    }};

    instance of Win32_SystemEnclosure
    {{
        Manufacturer = "{self.get_hardware_info("system_enclosure").get('Manufacturer', '')}";
        LockPresent = "{enclosure_info.get('LockPresent', '')}";
        SMBIOSAssetTag = "{enclosure_info.get('SMBIOSAssetTag', '')}";
        SecurityStatus = "{enclosure_info.get('SecurityStatus', '')}";
        SerialNumber = "{enclosure_serial}";
    }};

    [DYNPROPS]
    class Win32_BIOS
    {{
        [key] string Name;
        string Manufacturer;
        string SMBIOSBIOSVersion;
        string SerialNumber;
    }};

    instance of Win32_BIOS
    {{
        Name = "{self.get_hardware_info("bios").get('Name', '')}";
        Manufacturer = "{bios_info.get('Manufacturer', '')}";
        SMBIOSBIOSVersion = "{bios_version}";
        SerialNumber = "{bios_serial}";
    }};
    '''
        return self.create_mof_file(mof_content)

    def spoof_hard_disks(self, disks=None):
        try:
            script = '''#pragma namespace("\\\\\\\\.\\\\root\\\\CIMv2")

[DYNPROPS]
class Win32_DiskDrive
{
    [key] string DeviceID;
    string SerialNumber;
    string Model;
    string Caption;
};
'''
            if disks is not None:
                backup = True
            else:
                disks = self.get_hardware_info("disk_drive")
                backup = False

            if isinstance(disks, dict):
                if any(key.startswith('Disk_') for key in disks.keys()):
                    disk_list = list(disks.values())
                else:
                    disk_list = [disks]
            elif isinstance(disks, list):
                disk_list = disks

            current_disks = self.get_hardware_info("disk_drive")
            current_disks_map = []
            if isinstance(current_disks, dict):
                if any(key.startswith('Disk_') for key in current_disks.keys()):
                    current_disk_list = list(current_disks.values())
                else:
                    current_disk_list = [current_disks]
            elif isinstance(current_disks, list):
                current_disk_list = current_disks
            else:
                current_disk_list = []
            
            for current_disk in current_disk_list:
                device_id = current_disk.get('DeviceID', '')
                current_disks_map.append(device_id)
            
            for disk in disk_list:
                if backup:
                    serial = disk.get('SerialNumber', '')
                    device_id = current_disks_map[disk_list.index(disk)]
                else:
                    serial = self.generate_disk_serial()
                    device_id = current_disks_map[disk_list.index(disk)]
                script += f'''
instance of Win32_DiskDrive
{{
    DeviceID = "\\\\\\\\.\\\\{device_id[4:]}";
    SerialNumber = "{serial}";
    Model = "{disk.get('Model', '')}";
    Caption = "{disk.get('Caption', '')}";
}};
        '''
            return self.create_mof_file(script)
        except Exception:
            return False

    def spoof_memory(self, memory_modules=None):
        """Spoof memory serial numbers."""
        try:
            if memory_modules is not None:
                backup = True
            else:
                memory_modules = self.get_hardware_info("physical_memory")
                backup = False

            # Handle both data structures
            if isinstance(memory_modules, dict):
                if any(key.startswith('Memory_') for key in memory_modules.keys()):
                    memory_list = list(memory_modules.values())
                else:
                    memory_list = [memory_modules]
            elif isinstance(memory_modules, list):
                memory_list = memory_modules

            # Get current memory info for Tags
            current_memory = self.get_hardware_info("physical_memory")
            current_memory_map = []
            if isinstance(current_memory, dict):
                if any(key.startswith('Memory_') for key in current_memory.keys()):
                    current_memory_list = list(current_memory.values())
                else:
                    current_memory_list = [current_memory]
            elif isinstance(current_memory, list):
                current_memory_list = current_memory
            else:
                current_memory_list = []

            for current_mem in current_memory_list:
                tag = current_mem.get('Tag', '')
                current_memory_map.append(tag)

            script = '''#pragma namespace("\\\\\\\\.\\\\root\\\\CIMv2")

            [DYNPROPS]
            class Win32_PhysicalMemory
            {
                [key] string Tag;
                string SerialNumber;
            };
            '''
                        
            for mem in memory_list:
                if backup:
                    serial = mem.get('SerialNumber', '')
                    tag = current_memory_map[memory_list.index(mem)]
                else:
                    serial = self.generate_serial(mem.get('SerialNumber', ''))
                    tag = current_memory_map[memory_list.index(mem)]
                
                script += f'''instance of Win32_PhysicalMemory
            {{
                Tag = "{tag}";
                SerialNumber = "{serial}";
            }};
            '''
                        
            return self.create_mof_file(script)
        except Exception:
            return False

    def spoof_gpus(self):
        """Spoof GPU serial numbers."""
        try:
            gpus = self.get_hardware_info("video_controller")
            script = '''#pragma namespace("\\\\\\\\.\\\\root\\\\CIMv2")

    [DYNPROPS]
    class Win32_VideoController
    {
        [key] string Name;
        string Description;
        string PNPDeviceID;
    };
    '''
            for gpu in gpus:
                original_id = gpu.get('PNPDeviceID', '')
                try:
                    spoofed_id = self.generate_gpu_serial(original_id)
                except ValueError:
                    spoofed_id = self.generate_serial(original_id)
                
                script += f'''
    instance of Win32_VideoController
    {{
        Name = "{gpu.get('Name', '')}";
        Description = "{gpu.get('Description', '')}";
        PNPDeviceID = "{spoofed_id}";
    }};
    '''
            return self.create_mof_file(script)
        except Exception:
            return False
    
    def restore_originals(self):
        self.run_hidden(r"mofcomp C:\Windows\System32\wbem\cimwin32.mof")
    
    def get_all_serials(self):
        """
        Collect all hardware serials organized by module name.
        
        Returns:
            dict: Dictionary with module names as keys and serials as values
        """
        serials_data = {}
        
        try:
            # BIOS Serials - using your working WMI function
            bios_info = self.get_hardware_info("bios")
            serials_data["BIOS"] = {
                "SMBIOSBIOSVersion": bios_info["SMBIOSBIOSVersion"],
                "Manufacturer": bios_info["Manufacturer"],
                "Name": bios_info["Name"],
                "SerialNumber": bios_info["SerialNumber"]
            }
            
            # BaseBoard Serials - using your working WMI function
            baseboard_info = self.get_hardware_info("baseboard")
            serials_data["BaseBoard"] = {
                "Manufacturer": baseboard_info["Manufacturer"],
                "Product": baseboard_info["Product"],
                "SerialNumber": baseboard_info["SerialNumber"],
                "Name": baseboard_info["Name"]
            }
            
            # Processor Serials - using your working WMI function
            processor_info = self.get_hardware_info("processor")
            serials_data["Processor"] = {
                "DeviceID": processor_info["DeviceID"],
                "Name": processor_info["Name"],
                "ProcessorId": processor_info["ProcessorId"],
                "SerialNumber": processor_info["SerialNumber"],
                "PartNumber": processor_info["PartNumber"]
            }
            
            # Computer System Product Serials - using your working WMI function
            computer_system_info = self.get_hardware_info("computer_system")
            serials_data["ComputerSystem"] = {
                "Name": computer_system_info["Name"],
                "Vendor": computer_system_info["Vendor"],
                "Version": computer_system_info["Version"],
                "UUID": computer_system_info["UUID"],
                "IdentifyingNumber": computer_system_info["IdentifyingNumber"]
            }
            
            # System Enclosure Serials - using your working WMI function
            systemenclosure_info = self.get_hardware_info("system_enclosure")
            serials_data["SystemEnclosure"] = {
                "Manufacturer": systemenclosure_info["Manufacturer"],
                "LockPresent": systemenclosure_info["LockPresent"],
                "SerialNumber": systemenclosure_info["SerialNumber"],
                "SMBIOSAssetTag": systemenclosure_info["SMBIOSAssetTag"],
                "SecurityStatus": systemenclosure_info["SecurityStatus"]
            }
            
            # Disk Drive Serials
            disk_info = self.get_hardware_info("disk_drive")
            if disk_info and isinstance(disk_info, list):
                disks = {}
                for i, disk in enumerate(disk_info):
                    disks[f"Disk_{i}"] = {
                        "DeviceID": disk.get('DeviceID', 'N/A'),
                        "SerialNumber": disk.get('SerialNumber', 'N/A'),
                        "Model": disk.get('Model', 'N/A'),
                        "Caption": disk.get('Caption', 'N/A')
                    }
                serials_data["DiskDrives"] = disks
            else:
                serials_data["DiskDrives"] = {
                    "DeviceID": disk_info["DeviceID"],
                    "SerialNumber": disk_info["SerialNumber"],
                    "Model": disk_info["Model"],
                    "Caption": disk_info["Caption"],
                }
            
            # Memory Serials
            memory_info = self.get_hardware_info("physical_memory")
            if memory_info and isinstance(memory_info, list):
                memory_modules = {}
                for i, mem in enumerate(memory_info):
                    memory_modules[f"Memory_{i}"] = {
                        "Tag": mem.get('Tag', 'N/A'),
                        "SerialNumber": mem.get('SerialNumber', 'N/A')
                    }
                serials_data["Memory"] = memory_modules
            else:
                serials_data["Memory"] = {
                    "Tag": memory_info["Tag"],
                    "SerialNumber": memory_info["SerialNumber"],
                }
            
            # # GPU Serials
            # gpu_info = self.get_hardware_info("video_controller")
            # if gpu_info and isinstance(gpu_info, list):
            #     gpus = {}
            #     for i, gpu in enumerate(gpu_info):
            #         gpus[f"GPU_{i}"] = {
            #             "Name": gpu.get('Name', 'N/A'),
            #             "Description": gpu.get('Description', 'N/A'),
            #             "PNPDeviceID": gpu.get('PNPDeviceID', 'N/A')
            #         }
            #     serials_data["GPUs"] = gpus
            # else:
            #     serials_data["GPUs"] = {
            #         "Name": gpu_info["Name"],
            #         "Description": gpu_info["Description"],
            #         "PNPDeviceID": gpu_info["PNPDeviceID"],
            #     }

            
            # # Network MAC Addresses
            # network_info = self.get_network_info()
            # if network_info:
            #     serials_data["Network"] = network_info
            
            # # Partition Serials
            # partition_info = self.get_partition_serials()
            # if partition_info and isinstance(partition_info, list):
            #     partitions = {}
            #     for partition in partition_info:
            #         if isinstance(partition, dict):
            #             partitions[partition.get('DeviceID', 'N/A')] = partition.get('VolumeSerialNumber', 'N/A')
            #     serials_data["Partitions"] = partitions
            # else:
            #     serials_data["Partitions"] = {
            #         "DeviceID": partition_info["DeviceID"],
            #     }
            
            # # Hostname
            # serials_data["Hostname"] = self.get_hostname()
            
        except Exception as e:
            Details.debug_print(f"Error in get_all_serials: {e}")
            import traceback
            traceback.print_exc()
        
        return serials_data

    def print_serials(self, serials_data=None):
        """
        Print all serials in a readable format.
        
        Args:
            serials_data: Optional pre-collected serials data
            simple: Whether to use simplified format
        """
        if serials_data is None:
            serials_data = self.get_all_serials()
        
        for module, data in serials_data.items():
            Details.debug_print(f"\n{module}:")
            if isinstance(data, dict):
                for key, value in data.items():
                    if isinstance(value, dict):
                        Details.debug_print(f"  {key}:")
                        for sub_key, sub_value in value.items():
                            Details.debug_print(f"    {sub_key}: {sub_value}")
                    else:
                        Details.debug_print(f"  {key}: {value}")
            else:
                Details.debug_print(f"  {data}")


if __name__ == "__main__":
    mof = MOFManager()
    # Details.debug_print(mof.get_hardware_info("processor"))
    # Details.debug_print(mof.get_hardware_info("computer_system"))
    # Details.debug_print(mof.get_hardware_info("baseboard"))
    # Details.debug_print(mof.get_hardware_info("system_enclosure"))
    # Details.debug_print(mof.get_hardware_info("bios"))
    # Details.debug_print(mof.get_hardware_info("disk_drive"))
    
    # Get all serials in detailed format
    all_serials = mof.get_all_serials()
    # Details.debug_print(all_serials)
    # Details.debug_print("Detailed serials structure:")
    mof.print_serials(all_serials)
    