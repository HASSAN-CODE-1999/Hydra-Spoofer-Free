import customtkinter as ctk
import psutil
import threading
import time
from tkinter import messagebox, filedialog
import datetime
import sys
from PIL import Image
import os
import subprocess
import webbrowser

import Details
from MOFSpoofer import SpooferServiceManager
from BackupManager import BackupManager
import DataStoring as DS

def run_powershell(cmd):
    """Run a PowerShell command and return its stdout (trimmed)."""
    try:
        result = subprocess.run(
            ["powershell", "-Command", cmd],
            capture_output=True,
            text=True,
            check=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        output = result.stdout.strip()
        return output if output else "Unknown"
    except Exception:
        return "Unknown"

class HydraSpoofer(ctk.CTk):
    NORMAL_STATUS = "NO CHANGES"
    MANIPULATED_STATUS = "SPOOFED"

    def __init__(self):
        super().__init__()

        self.spoofer = SpooferServiceManager()
        self.bum = BackupManager()

        # Window configuration - wider and slight transparency
        self.title("{} v{}".format(Details.applicationName, Details.__version__))
        self.geometry("700x560")
        self.resizable(False, False)
        try:
            self.iconbitmap(Details.imgsPath + "favicon.ico")
        except Exception:
            pass

        # subtle transparency (platform dependent)
        try:
            self.attributes('-alpha', 0.95)
        except Exception:
            pass
        
        # Center the window on screen
        self.center_window()
        
        # Modern UI Theme (dark blue range)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Color scheme - dark blue focused theme with transparent-feel
        self.colors = {
            # ===== Core accents (brighter on dark) =====
            'primary': "#00e5ff",        # Neon cyan
            'secondary': "#3ab7ff",      # Electric blue
            'accent': "#1fa2ff",         # Sharp blue

            # ===== Status =====
            'warning': "#ff4c4c",        # Strong red (alerts pop hard)
            'success': "#00e676",        # Neon green

            # ===== Backgrounds (much darker) =====
            'bg_dark': "#030812",        # Near-black navy
            'bg_card': "#071426",        # Card background
            'bg_input': "#020a16",       # Almost black input fields

            # ===== Text =====
            'text_primary': "#eaf6ff",   # Crisp white-blue
            'text_secondary': "#7fa6c7", # Muted but readable

            # ===== UI Details =====
            'border': "#0c2a44",         # Subtle but visible borders

            # ===== Highlights =====
            'gold': "#ffc861",           # Premium highlight
            'green': "#00ff9c"           # Cyber green
        }
        
        # Load images safely
        self.images = {
            'system': self.load_icon('computer.png'),
            'network': self.load_icon('network.png'),
            'mobo': self.load_icon('motherboard.png'),
            'id': self.load_icon('id.png'),
            'ssd': self.load_icon('ssd.png'),
            'clean': self.load_icon('clean.png'),
            'save': self.load_icon('save.png'),
            'start': self.load_icon('start.png'),
            'regenerate': self.load_icon('regenerate.png'),
            'restore': self.load_icon('restore.png'),
            'logout': self.load_icon('logout.png'),
            'ram': self.load_icon('ram.png'),
            'bios': self.load_icon('chip.png'),
            'pid': self.load_icon('pid.png'),
            'github': self.load_icon("github.png"),
            'discord': self.load_icon("discord.png"),
            'instagram': self.load_icon("instagram.png"),
        }
        
        self.cards = {}
        
        # Variables
        self.spoofing_in_progress = False
        self.status_text = ctk.StringVar(value="🔥 SYSTEM READY FOR SPOOFING")
        self.animation_running = False
        self.custom_config = {} # Stores advanced spoofing configuration
        
        self.pc_info = self.get_pc_info()
        self.card_labels = {} 
        self.create_widgets()
    
    def update_system_changes(self):
        def _update_card_label(key, new_value):
            """Helper to update label text safely"""
            lbl = self.card_labels.get(key)
            if lbl:
                # Only update if changed to avoid flicker
                if lbl.cget("text") != new_value:
                    lbl.configure(text=new_value)

        def _update_status_indicator(text, color):
            """Helper to update the top status indicator"""
            if hasattr(self, 'system_status'):
                current_text = self.system_status.cget("text")
                target_text = f"● {text}"
                if current_text != target_text:
                    self.system_status.configure(text=target_text, text_color=color)
        
        try:
            # Fetch new info
            new_info = self.get_pc_info()
            
            # Check for changes and update UI cards
            for key, value in new_info.items():
                current_ui_val = self.card_labels.get(key)
                if current_ui_val:
                    # Schedule UI update on main thread
                    self.after(0, _update_card_label, key, value)
            
            # Check spoof status for header label
            is_spoofed = self.spoofer.check_spoofer_installed()
            new_status_text = self.MANIPULATED_STATUS if is_spoofed else self.NORMAL_STATUS
            new_color = self.colors['success'] if is_spoofed else self.colors['warning']
            
            self.after(0, _update_status_indicator, new_status_text, new_color)

        except Exception:
            pass
                
    def load_icon(self, path, size=(20, 20)):
        try:
            img = Image.open(Details.imgsPath + path)
            return ctk.CTkImage(light_image=img, dark_image=img, size=size)
        except Exception:
            return None
    
    def center_window(self):
        """Center the window on the screen"""
        self.update_idletasks()
        width = 700
        height = 560
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
    
    def get_pc_info(self):
        """Collect essential system information using PowerShell instead of WMI."""
        info = {
            "MAC": "",
            "MOTHERBOARD": "Unknown",
            "UUID": "Unknown",
            "DISKS": "Unknown",
            "BIOS": "Unknown",
            "SMBIOS": "Unknown",
            "MEMORY": "Unknown",
            "CPU_ID": "Unknown",
            "ENCLOSURE": "Unknown"
        }

        try:
            # ================= MAC ADDRESSES =================
            macs = {"WiFi": "Unknown", "Ethernet": "Unknown"}
            wifi_keywords = ['wlan', 'wi-fi', 'wifi']
            eth_keywords = ['eth', 'en', 'ethernet']

            for if_name, if_addrs in psutil.net_if_addrs().items():
                mac_address = None
                for addr in if_addrs:
                    if getattr(addr, 'family', None) == psutil.AF_LINK and getattr(addr, 'address', None):
                        mac_address = addr.address.replace('-', ':')
                        break

                if mac_address:
                    lower_name = if_name.lower()
                    if any(k in lower_name for k in wifi_keywords) and macs["WiFi"] == "Unknown":
                        macs["WiFi"] = mac_address
                    elif any(k in lower_name for k in eth_keywords) and macs["Ethernet"] == "Unknown":
                        macs["Ethernet"] = mac_address

                if macs["WiFi"] != "Unknown" and macs["Ethernet"] != "Unknown":
                    break

            if macs["WiFi"] != "Unknown":
                info["MAC"] += "WiFi " + macs["WiFi"] + '\n'
            if macs["Ethernet"] != "Unknown":
                info["MAC"] += "Ethernet " + macs["Ethernet"]

            # ================= HARDWARE INFO VIA POWERSHELL =================
            info["MOTHERBOARD"] = run_powershell("(Get-CimInstance Win32_BaseBoard).SerialNumber")
            info["UUID"] = run_powershell("(Get-CimInstance Win32_ComputerSystemProduct).UUID")

            disks = run_powershell("(Get-CimInstance Win32_DiskDrive | Select-Object -ExpandProperty SerialNumber) -join ','")
            info["DISKS"] = disks.replace(",", ",\n") if disks != "Unknown" else "Unknown"

            info["BIOS"] = run_powershell("(Get-CimInstance Win32_BIOS).SerialNumber")
            info["SMBIOS"] = run_powershell("(Get-CimInstance Win32_BIOS).SMBIOSBIOSVersion")

            memory = run_powershell("(Get-CimInstance Win32_PhysicalMemory | Select-Object -ExpandProperty SerialNumber) -join ','")
            info["MEMORY"] = memory.replace(",", ",\n") if memory != "Unknown" else "Unknown"
            
            # ================= CPU ID & ENCLOSURE =================
            cpu_id = run_powershell("(Get-CimInstance Win32_Processor).ProcessorId")
            info["CPU_ID"] = cpu_id if cpu_id and cpu_id != "Unknown" else "Unknown"
            
            enclosure = run_powershell("(Get-CimInstance Win32_SystemEnclosure).SerialNumber")
            info["ENCLOSURE"] = enclosure if enclosure and enclosure != "Unknown" else "Unknown"

        except Exception as e:
            messagebox.showerror("Error", "Error getting system info")
            Details.debug_print(f"Error getting system info: {str(e)}")

        return info
    
    def create_widgets(self):
        """Create all GUI elements with modern styling"""
        # Configure main window background
        self.configure(fg_color=self.colors['bg_dark'])
        
        # Header with glow effect
        self.create_header()
        
        # Main container - use horizontal split with larger left info area
        self.main_frame = ctk.CTkFrame(
            self, 
            fg_color="transparent",
            corner_radius=0
        )
        self.main_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.info_frame = ctk.CTkFrame(
            self.main_frame,
            corner_radius=15,
            fg_color=self.colors['bg_card'],
            border_width=1,
            border_color=self.colors['border']
        )
        self.info_frame.pack(fill="both", expand=True, pady=6)
        self.info_frame.pack_propagate(False)
        
        self.actions_frame = ctk.CTkFrame(
            self.main_frame,
            corner_radius=15,
            fg_color=self.colors['bg_card'],
            border_width=1,
            border_color=self.colors['accent']
        )
        self.actions_frame.pack(fill="x", pady=6)
        
        # Create sections
        self.create_info_section()
        self.create_actions_section()
        self.create_status_bar()
    
    def create_header(self):
        """Create animated header with cyberpunk styling"""
        header_frame = ctk.CTkFrame(
            self,
            height=50,
            corner_radius=0,
            fg_color=self.colors['bg_dark'],
            border_width=0
        )
        header_frame.pack(fill="x", padx=0, pady=0)
        header_frame.pack_propagate(False)
        
        # Title area
        self.title_label = ctk.CTkLabel(
            header_frame,
            text=f"{Details.applicationName}",
            font=("Orbitron", 26, "bold"),
            text_color=self.colors['primary'],
            anchor="center"
        )
        self.title_label.pack(side='left', padx=20)
        
        # Right side buttons
        right_controls = ctk.CTkFrame(header_frame, fg_color="transparent")
        right_controls.pack(side='right', padx=18)
    
    def create_info_section(self):
        # Section header with icon
        header_frame = ctk.CTkFrame(self.info_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=18, pady=5)
        
        ctk.CTkLabel(
            header_frame,
            text="SYSTEM FINGERPRINT",
            compound='left',
            image=self.images.get('system'),
            font=("Orbitron", 16, "bold"),
            text_color=self.colors['primary'],
            anchor="w"
        ).pack(side="left")
        
        if self.spoofer.check_spoofer_installed():
            status = self.MANIPULATED_STATUS
            color = self.colors['success']
        else:
            status = self.NORMAL_STATUS
            color = self.colors['warning']
        
        self.system_status = ctk.CTkLabel(
            header_frame,
            text=f"● {status}",
            font=("Consolas", 11, "bold"),
            text_color=color,
            anchor="e"
        )
        self.system_status.pack(side="right", padx=5)

        self.info_scrollable_frame = ctk.CTkScrollableFrame(
            self.info_frame, 
            fg_color=self.colors['bg_card'],
            scrollbar_button_color=self.colors['accent'],
            scrollbar_button_hover_color=self.colors['accent'],
        )
        
        self.info_scrollable_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        
        # Use this function to add more serials to view
        self.add_info_cards()
    
    def add_info_cards(self):
        self.info_items = [
            ("MAC ADDRESS", self.images.get('network'), "MAC", self.colors['gold']),
            ("MOTHERBOARD", self.images.get('mobo'), "MOTHERBOARD", self.colors['gold']),
            ("SYSTEM UUID", self.images.get('id'), "UUID", self.colors['gold']),
            ("SSD/HDD", self.images.get('ssd'), "DISKS", self.colors['gold']),
            ("BIOS", self.images.get('bios'), "BIOS", self.colors['gold']),
            ("MEMORY", self.images.get('ram'), "MEMORY", self.colors['gold']),
            ("CPU ID", self.images.get('bios'), "CPU_ID", self.colors['gold']),
            ("ENCLOSURE", self.images.get('system'), "ENCLOSURE", self.colors['gold']),
        ]
        
        columns = []
        for _ in range(2):
            col = ctk.CTkFrame(self.info_scrollable_frame, fg_color="transparent")
            col.pack(side="left", fill="both", expand=True, padx=5)
            columns.append(col)

        # Distribute items between columns
        for i, (label, icon, key, color) in enumerate(self.info_items):
            target_col = columns[i % 2]
            card, lbl_widget = self.create_modern_info_card(target_col, label, icon, self.pc_info.get(key), color)
            self.cards[key] = card
            self.card_labels[key] = lbl_widget

    def create_modern_info_card(self, parent, label, icon, value, accent_color):
        """Create a modern info card with neon accents - now shows full serials (multi-line)"""
        card_frame = ctk.CTkFrame(
            parent,
            corner_radius=12,
            fg_color=self.colors['bg_input'],
            border_width=1,
            border_color=accent_color,
        )
        card_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Label row
        label_frame = ctk.CTkFrame(card_frame, fg_color="transparent")
        label_frame.pack(fill="x", padx=10, pady=(8, 4))
        
        ctk.CTkLabel(
            label_frame,
            text=" " + label,
            compound='left',
            image=icon,
            font=("Consolas", 12, "bold"),
            text_color=accent_color,
            anchor="w"
        ).pack(side="left")
        
        # Value display - allow wrapping and multiple lines to show more content
        value_text = value if value else "Unknown"
        val_label = ctk.CTkLabel(
            card_frame,
            text=value_text,
            font=("Consolas", 11),
            text_color=self.colors['text_primary'],
            anchor="w",
            width=250,
            wraplength=250,
            justify='left'
        )
        val_label.pack(fill="x", padx=10, pady=(0, 10))
        
        return card_frame, val_label
    
    def create_actions_section(self):
        """Create simplified action buttons section with compact layout at bottom center"""
        # Main container for right panel
        main_container = ctk.CTkFrame(self.actions_frame, fg_color="transparent")
        main_container.pack(fill="x", expand=True, padx=10, pady=10)
        
        # Compact buttons container at the center
        self.buttons_container = ctk.CTkFrame(main_container, fg_color="transparent")
        self.buttons_container.pack(pady=10, fill='x')
        self.buttons_container.grid_columnconfigure(0, weight=1)
        self.buttons_container.grid_columnconfigure(1, weight=1)
        self.buttons_container.grid_columnconfigure(2, weight=1)
        self.buttons_container.grid_columnconfigure(3, weight=1)
        
        # Compact main buttons (reduced height)
        self.spoof_btn = ctk.CTkButton(
            self.buttons_container,
            text="SPOOF",
            compound='left',
            image=self.images.get('start'),
            command=self.start_spoofing,
            width=140,
            height=32,
            font=("Orbitron", 14, "bold"),
            fg_color=self.colors['bg_card'],
            hover_color=self.colors['secondary'],
            border_width=1,
            border_color=self.colors['accent'],
            corner_radius=18,
        )
        self.spoof_btn.grid(row=0, column=0)
        
        self.regen_btn = ctk.CTkButton(
            self.buttons_container,
            text="REGENERATE",
            image=self.images.get('regenerate'),
            compound='left',
            command=self.start_spoofing,
            width=140,
            height=32,
            font=("Orbitron", 14, "bold"),
            fg_color=self.colors['bg_card'],
            hover_color=self.colors['secondary'],
            border_width=1,
            border_color=self.colors['accent'],
            corner_radius=18,
        )
        self.regen_btn.grid(row=0, column=1)
        
        # If driver already active change main button state
        if self.spoofer.check_spoofer_installed():
            self.spoof_btn.configure(text="REMOVE", 
                image=self.images.get('restore'), 
                fg_color=self.colors['warning'], 
                hover_color="#ca1a1a", 
                text_color="#ffffff", 
                command=self.remove_spoof
            )
        else:
            self.regen_btn.configure(state="disabled")

        self.adv_btn = ctk.CTkButton(
            self.buttons_container,
            text="ADVANCED",
            image=self.images.get('system'), # Reusing system icon
            compound='left',
            command=self.open_custom_spoof_window,
            width=140,
            height=32,
            font=("Orbitron", 14, "bold"),
            fg_color=self.colors['bg_card'],
            hover_color=self.colors['secondary'],
            border_width=1,
            border_color=self.colors['accent'],
            corner_radius=18,
        )
        self.adv_btn.grid(row=0, column=2)

        # Save serials button smaller as well
        self.save_btn = ctk.CTkButton(
            self.buttons_container,
            text="SERIALS",
            image=self.images.get('save'),
            compound='left',
            command=self.save_or_compare,
            width=140,
            height=32,
            font=("Orbitron", 14, "bold"),
            fg_color=self.colors['bg_card'],
            hover_color=self.colors['secondary'],
            border_width=1,
            border_color=self.colors['accent'],
            corner_radius=18,
        )
        self.save_btn.grid(row=0, column=3)
    
    def create_status_bar(self):
        """Create modern status bar with animations"""
        status_frame = ctk.CTkFrame(
            self,
            height=36,
            corner_radius=0,
            fg_color=self.colors['bg_card'],
            border_width=1,
            border_color=self.colors['border']
        )
        status_frame.pack(fill="x", padx=0, pady=0, side="bottom")
        status_frame.pack_propagate(False)
        
        # Status indicator
        self.status_indicator = ctk.CTkLabel(
            status_frame,
            text="●",
            font=("Arial", 14),
            text_color=self.colors['success']
        )
        self.status_indicator.pack(side="left", padx=(12, 6), pady=6)
        
        # Status text with modern font
        self.status_label = ctk.CTkLabel(
            status_frame,
            textvariable=self.status_text,
            font=("Consolas", 10, "bold"),
            text_color=self.colors['text_primary'],
            anchor="w"
        )
        self.status_label.pack(side="left", fill="x", expand=True, pady=6)
        
    def update_status(self, message, status_type="info"):
        """Update status bar with color coding"""
        colors = {
            "info": self.colors['text_primary'],
            "success": self.colors['success'],
            "warning": self.colors['warning'],
            "error": self.colors['warning']
        }
        
        indicator_colors = {
            "info": self.colors['accent'],
            "success": self.colors['success'],
            "warning": self.colors['warning'],
            "error": self.colors['warning']
        }
        
        self.status_text.set(message)
        self.status_label.configure(text_color=colors.get(status_type, colors["info"]))
        self.status_indicator.configure(text_color=indicator_colors.get(status_type, indicator_colors["info"]))
        self.update()
    
    def start_spoofing(self):
        """Start spoofing process with modern animations"""
        if self.spoofing_in_progress:
            return
            
        self.spoofing_in_progress = True
        self.spoof_btn.configure(
            image=self.images.get('start'),
            fg_color=self.colors['accent'],
            state="disabled",
            text="SPOOFING.."
        )
        
        self.update_status("🚀 INITIALIZING SPOOFING SEQUENCE...", "info")
        
        # Start spoofing in background
        threading.Thread(target=self.simulate_spoofing, daemon=True).start()
    
    def simulate_spoofing(self):
        try:
            self.update_status("🎭 MODIFYING SYSTEM IDENTIFIERS...", "info")
            sw, status = self.spoofer.install_service(config=self.custom_config)
            if sw:
                self.update_access_serial()

                for step in status:
                    self.update_status(step, "info")
                    time.sleep(0.5)  # Realistic timing

                stages = [
                    "⚡ APPLYING SYSTEM CHANGES...",
                    "✅ SPOOFING COMPLETED SUCCESSFULLY!",
                ]
                for message in stages:
                    self.update_status(message, "info")
                    time.sleep(0.5)  # Realistic timing

                messagebox.showinfo(
                    "SUCCESS", 
                    "System identifiers have been successfully spoofed!\n\n"
                    "Your digital fingerprint has been changed."
                )
                self.spoofing_in_progress = False
                self.spoof_btn.configure(text="REMOVE",
                    image=self.images.get('restore'),
                    fg_color=self.colors['warning'],
                    hover_color="#ca1a1a",
                    text_color="#ffffff",
                    state="normal",
                    command=self.remove_spoof
                )
                self.regen_btn.configure(state="normal")
                self.update_system_changes()
            else:
                self.update_status(f"❌ Failed to spoof", "error")
                messagebox.showerror("Spoof error!", "".join(status))
        except Exception as e:
            self.update_status(f"❌ GENERAL ERROR", "error")
            Details.debug_print(f"GENERAL ERROR: {str(e)}")

    def save_or_compare(self):
        """Ask user whether to save current serials or compare with saved file"""
        switcher = ctk.CTkFrame(self.buttons_container, fg_color=self.buttons_container.cget("fg_color"), corner_radius=15)
        switcher.place(relx=0.5, rely=0.5, anchor="center", relwidth=1)
        switcher.grid_columnconfigure(0, weight=1)
        switcher.grid_columnconfigure(1, weight=1)
        switcher.grid_columnconfigure(2, weight=1)
        switcher.grid_columnconfigure(3, weight=1)
        switcher.grid_columnconfigure(4, weight=1)

        save_btn = ctk.CTkButton(
            switcher,
            text="Save",
            compound='left',
            command=self.save_serials,
            width=100,
            height=32,
            font=("Orbitron", 14, "bold"),
            fg_color=self.colors['accent'],
            hover_color="#0f7bd8",
            text_color="#ffffff",
            corner_radius=18,
        )
        save_btn.grid(row=0, column=0)
        
        compare_btn = ctk.CTkButton(
            switcher,
            text="Compare",
            compound='left',
            command=self.compare_serials,
            width=100,
            height=32,
            font=("Orbitron", 14, "bold"),
            fg_color=self.colors['accent'],
            hover_color="#0f7bd8",
            text_color="#ffffff",
            corner_radius=18,
        )
        compare_btn.grid(row=0, column=1)
        
        import_btn = ctk.CTkButton(
            switcher,
            text="Export",
            compound='left',
            command=self.export_serials,
            width=100,
            height=32,
            font=("Orbitron", 14, "bold"),
            fg_color=self.colors['accent'],
            hover_color="#0f7bd8",
            text_color="#ffffff",
            corner_radius=18,
        )
        import_btn.grid(row=0, column=2)
        
        import_btn = ctk.CTkButton(
            switcher,
            text="Import",
            compound='left',
            command=self.import_serials,
            width=100,
            height=32,
            font=("Orbitron", 14, "bold"),
            fg_color=self.colors['accent'],
            hover_color="#0f7bd8",
            text_color="#ffffff",
            corner_radius=18,
        )
        import_btn.grid(row=0, column=3)

        compare_btn = ctk.CTkButton(
            switcher,
            text="Exit",
            compound='left',
            command=switcher.destroy,
            width=100,
            height=32,
            font=("Orbitron", 14, "bold"),
            fg_color=self.colors['warning'],
            hover_color="#d44e00",
            text_color="#ffffff",
            corner_radius=18,
        )
        compare_btn.grid(row=0, column=4)

    def compare_serials(self):
        try:
            filepath = filedialog.askopenfilename(
                title="Select saved serials file",
                filetypes=[("INI files", "*.ini"), ("All files", "*.*")]
            )
            if not filepath:
                return

            saved_data = {}
            with open(filepath, "r", encoding="utf-8") as f:
                for line in f:
                    if "=" in line:
                        key, value = line.strip().split("=", 1)
                        saved_data[key] = value

            number_of_mismatches = 0
            for label, icon, key, default_color in self.info_items:
                current_value = str(self.pc_info.get(key, "Unknown"))
                if ',' in current_value:
                    current_value = current_value.split(',')[0].strip()
                saved_value = str(saved_data.get(key, "N/A")).replace(',', '').strip()
                
                card = self.cards.get(key)
                if not card:
                    continue

                if current_value != saved_value:
                    number_of_mismatches += 1
                    new_color = self.colors['accent'] 
                else:
                    new_color = default_color
                card.configure(border_color=new_color)

            messagebox.showinfo("RESULT", f"Total Score: {number_of_mismatches} / {len(self.info_items)}\n")
            self.update_status("🔍 Comparison finished. Changed values highlighted.", "success")

        except Exception as e:
            self.update_status(f"❌ COMPARE FAILED", "error")
            Details.debug_print(f"Compare failed: {str(e)}")
    
    def save_serials(self):
        """Save current system serials to a file in simple key=value format"""
        try:
            # Create filename with timestamp
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"serials_backup_{timestamp}.ini"

            # Build key=value lines
            lines = [
                f"MAC={self.pc_info.get('MAC', 'Unknown')}",
                f"MOTHERBOARD={self.pc_info.get('MOTHERBOARD', 'Unknown')}",
                f"UUID={self.pc_info.get('UUID', 'Unknown')}",
                f"DISKS={self.pc_info.get('DISKS', 'Unknown')}",
                f"BIOS={self.pc_info.get('BIOS', 'Unknown')}",
                f"MEMORY={self.pc_info.get('MEMORY', 'Unknown')}",
                f"CPU_ID={self.pc_info.get('CPU_ID', 'Unknown')}",
                f"ENCLOSURE={self.pc_info.get('ENCLOSURE', 'Unknown')}",
            ]

            content = "\n".join(lines)

            # Save to file
            with open(filename, "w", encoding="utf-8") as f:
                f.write(content)

            self.update_status(f"💾 SERIALS SAVED TO: {filename}", "success")
            messagebox.showinfo(
                "SERIALS SAVED",
                f"Serials saved to:\n{os.path.abspath(filename)}\n\n"
            )

        except Exception as e:
            self.update_status(f"❌ SAVE FAILED", "error")
            messagebox.showerror("SAVE ERROR", f"Failed to save serials")
    
    def export_serials(self):
        file = filedialog.asksaveasfilename(initialdir=str("backups"),
                                        filetypes=[("Saved configs", "*.json")])
        exported_file = self.bum.backup_hardware_info(filename=file)
        messagebox.showinfo("Done", f"Serials config exported ({exported_file})")
        
    def import_serials(self):        
        if self.spoofing_in_progress:
            return
            
        self.spoofing_in_progress = True
        self.update_status("🔄 IMPORTING SERIALS...", "info")
        file = filedialog.askopenfilename(initialdir=str("backups"),
                                        filetypes=[("Saved configs", "*.json")])
        if file:
            is_restored, message = self.bum.restore_hardware_info(file)
            if not is_restored:
                messagebox.showerror("Error!", message)
            else:
                messagebox.showinfo("Done", "Serials config restored successfully.")
                self.spoofer.set_spoof_status(True)
                self.update_access_serial()
                self.spoofing_in_progress = False
                self.update_status("🔄 IMPORTED SERIALS...", "success")

                self.spoof_btn.configure(text="REMOVE",
                    image=self.images.get('restore'),
                    fg_color=self.colors['warning'],
                    hover_color="#ca1a1a",
                    text_color="#ffffff",
                    state="normal",
                    command=self.remove_spoof
                )
                self.regen_btn.configure(state="normal")

            self.update_system_changes()
    
    def remove_spoof(self):
        """Remove spoofing with confirmation"""
        if messagebox.askyesno(
            "CONFIRM RESTORATION", 
            "This will restore all original system identifiers.\n\nContinue with restoration?"
        ):
            self.update_status("🔄 RESTORING ORIGINAL IDENTIFIERS...", "warning")
            threading.Thread(target=self.simulate_restore, daemon=True).start()
    
    def simulate_restore(self):
        """Simulate restore process"""
        try:
            self.spoof_btn.configure(
                state="disabled",
                fg_color="#740A5D",
                text="RESTORING.."
            )
            time.sleep(2)
            time.sleep(2)
            if self.spoofer.uninstall_service():
                self.update_access_serial()
                self.regen_btn.configure(state="disabled")
                self.update_status("✅ ORIGINAL IDENTIFIERS RESTORED", "success")
                messagebox.showinfo(
                    "RESTORATION COMPLETE", 
                    "All identifiers have been restored to original values"
                )
                self.spoof_btn.configure(
                    state="normal",
                    image=self.images.get('start'),
                    fg_color=self.colors['bg_card'],
                    hover_color=self.colors['secondary'],
                    text="SPOOF",
                    command=self.start_spoofing
                )
                self.update_system_changes()
        except Exception as e:
            self.update_status(f"❌ RESTORE FAILED", "error")
            messagebox.showerror("ERROR", "Failed to restore")
            Details.debug_print(f"Restore failed: {str(e)}")

    def open_custom_spoof_window(self):
        if self.spoofing_in_progress:
            return

        w = ctk.CTkToplevel(self)
        w.title("Advanced Spoofing Configuration")
        w.geometry("650x650")
        w.resizable(False, True)
        w.iconbitmap(Details.imgsPath + "favicon.ico")
        
        # Center popup
        w.update_idletasks()
        width = w.winfo_width()
        height = w.winfo_height()
        x = (w.winfo_screenwidth() // 2) - (width // 2)
        y = (w.winfo_screenheight() // 2) - (height // 2)
        w.geometry(f"+{x}+{y}")
        
        w.configure(fg_color=self.colors['bg_dark'])
        w.grab_set() # Modal
        
        # Variables for UI
        # We initialize with existing config or defaults (False for all)
        vars_map = {}
        
        def get_conf(key, default=False):
            return self.custom_config.get(key, default)
            
        # Structure: (Key, Label, HasEntry)
        components = [
            ("spoof_mac", "Network MAC Addresses", True),  # Changed to True for sub-fields
            ("spoof_win", "Windows Internals (Registry, ProductID, etc)", False),
            ("spoof_parts", "Disk Partitions (Volume IDs)", False),
            ("spoof_smbios", "SMBIOS Data (BaseBoard, CPU, BIOS, System)", True),
            ("spoof_disk", "Physical Disk Serials", True),
            ("spoof_mem", "Memory RAM Serials", True),
        ]
        
        # Helper to detect available network adapters
        def detect_adapters():
            adapters = {"ethernet": False, "wifi": False, "bluetooth": False}
            try:
                wifi_keywords = ['wlan', 'wi-fi', 'wifi', 'wireless']
                eth_keywords = ['eth', 'en', 'ethernet']
                bt_keywords = ['bluetooth', 'bt']
                
                for if_name in psutil.net_if_addrs().keys():
                    lower_name = if_name.lower()
                    if any(k in lower_name for k in wifi_keywords):
                        adapters["wifi"] = True
                    elif any(k in lower_name for k in eth_keywords):
                        adapters["ethernet"] = True
                    elif any(k in lower_name for k in bt_keywords):
                        adapters["bluetooth"] = True
            except:
                pass
            return adapters
        
        # Helper to validate MAC address format
        def validate_mac(mac_str):
            import re
            pattern = r'^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$'
            return bool(re.match(pattern, mac_str))
        
        # Specific sub-fields for SMBIOS/Disk/Mem if they are enabled
        # We need a way to show them.
        
        scroll = ctk.CTkScrollableFrame(w, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=10, pady=10)
        
        header = ctk.CTkLabel(scroll, text="SELECT COMPONENTS TO SPOOF", font=("Orbitron", 16, "bold"), text_color=self.colors['primary'])
        header.pack(pady=10)
        
        # Main Toggles
        self.toggle_vars = {}
        self.entry_vars = {}
        
        for key, label, has_sub in components:
            frame = ctk.CTkFrame(scroll, fg_color=self.colors['bg_card'])
            frame.pack(fill="x", pady=5)
            
            val = ctk.BooleanVar(value=get_conf(key, False))
            self.toggle_vars[key] = val
            
            cb = ctk.CTkCheckBox(
                frame, 
                text=label, 
                variable=val,
                corner_radius=15,
                border_width=1,
                font=("Consolas", 12, "bold"),
                hover_color=self.colors['accent'],
                fg_color=self.colors['primary'],
                text_color=self.colors['text_primary']
            )
            cb.pack(anchor="w", padx=10, pady=10)
            
            # If this component has sub-fields (entries), add them
            if key == "spoof_mac":
                sub_frame = ctk.CTkFrame(frame, fg_color="transparent")
                sub_frame.pack(fill="x", padx=30, pady=(0, 10))
                
                # Detect available adapters
                available_adapters = detect_adapters()
                
                # MAC address fields
                mac_fields = []
                if available_adapters["ethernet"]:
                    mac_fields.append(("mac_ethernet", "Ethernet MAC"))
                if available_adapters["wifi"]:
                    mac_fields.append(("mac_wifi", "WiFi MAC"))
                if available_adapters["bluetooth"]:
                    mac_fields.append(("mac_bluetooth", "Bluetooth MAC"))
                
                if not mac_fields:
                    ctk.CTkLabel(sub_frame, text="No network adapters detected.", text_color=self.colors['warning']).pack()
                
                for f_key, f_label in mac_fields:
                    f_row = ctk.CTkFrame(sub_frame, fg_color="transparent")
                    f_row.pack(fill="x", pady=2)
                    
                    ctk.CTkLabel(f_row, text=f_label+":", width=120, anchor="w", text_color=self.colors['text_secondary']).pack(side="left")
                    
                    e_var = ctk.StringVar(value=self.custom_config.get(f_key, ""))
                    self.entry_vars[f_key] = e_var
                    
                    entry = ctk.CTkEntry(
                        f_row, 
                        textvariable=e_var, 
                        height=28, 
                        fg_color=self.colors['bg_input'], 
                        border_color=self.colors['border'],
                        placeholder_text="XX:XX:XX:XX:XX:XX"
                    )
                    entry.pack(side="left", fill="x", expand=True, padx=5)
                    
                    # Validation callback
                    def on_mac_change(var=e_var, ent=entry):
                        mac_val = var.get()
                        if mac_val and not validate_mac(mac_val):
                            ent.configure(border_color=self.colors['warning'])
                        else:
                            ent.configure(border_color=self.colors['border'])
                    
                    e_var.trace_add("write", lambda *args, v=e_var, e=entry: on_mac_change(v, e))
                    
                    # Randomize button
                    def rnd_mac(v=e_var):
                        import random
                        mac = ":".join([f"{random.randint(0x00, 0xff):02X}" for _ in range(6)])
                        v.set(mac)
                    
                    ctk.CTkButton(f_row, text="🎲", width=30, height=28, command=rnd_mac, fg_color=self.colors['bg_input'], hover_color=self.colors['accent']).pack(side="right")
            
            elif key == "spoof_smbios":
                sub_frame = ctk.CTkFrame(frame, fg_color="transparent")
                sub_frame.pack(fill="x", padx=30, pady=(0, 10))
                
                # Fields
                fields = [
                    ("cpu_serial", "CPU Serial"),
                    ("baseboard_serial", "Baseboard Serial"),
                    ("bios_serial", "BIOS Serial"),
                    ("uuid_serial", "System UUID"),
                    ("enclosure_serial", "Enclosure Serial")
                ]
                
                for f_key, f_label in fields:
                    f_row = ctk.CTkFrame(sub_frame, fg_color="transparent")
                    f_row.pack(fill="x", pady=2)
                    
                    ctk.CTkLabel(f_row, text=f_label+":", width=120, anchor="w", text_color=self.colors['text_secondary']).pack(side="left")
                    
                    e_var = ctk.StringVar(value=self.custom_config.get(f_key, ""))
                    self.entry_vars[f_key] = e_var
                    
                    entry = ctk.CTkEntry(f_row, textvariable=e_var, height=28, fg_color=self.colors['bg_input'], border_color=self.colors['border'])
                    entry.pack(side="left", fill="x", expand=True, padx=5)
                    
                    # Randomize button
                    def rnd(v=e_var, k=f_key):
                         # Simple randomizer helper
                         if "uuid" in k:
                             # Generate UUID like
                             import uuid
                             v.set(str(uuid.uuid4()).upper())
                         else:
                             import random, string
                             v.set(''.join(random.choices(string.ascii_uppercase + string.digits, k=10)))
                             
                    ctk.CTkButton(f_row, text="🎲", width=30, height=28, command=rnd, fg_color=self.colors['bg_input'], hover_color=self.colors['accent']).pack(side="right")

            elif key == "spoof_disk":
                sub_frame = ctk.CTkFrame(frame, fg_color="transparent")
                sub_frame.pack(fill="x", padx=30, pady=(0, 10))
                
                try:
                    disks = self.spoofer.MOFM.get_hardware_info("disk_drive")
                    if isinstance(disks, dict): disks = [disks] # Handle single result returned as dict
                    elif not disks: disks = []
                except:
                    disks = []
                
                if not disks:
                     ctk.CTkLabel(sub_frame, text="No disks detected.", text_color=self.colors['warning']).pack()

                for i, disk in enumerate(disks):
                    d_model = disk.get('Model', 'Unknown')
                    # Truncate model if too long
                    if len(d_model) > 20: d_model = d_model[:18] + ".."
                    
                    f_row = ctk.CTkFrame(sub_frame, fg_color="transparent")
                    f_row.pack(fill="x", pady=2)
                    
                    label_text = f"Disk {i} [{d_model}]:"
                    ctk.CTkLabel(f_row, text=label_text, width=150, anchor="w", text_color=self.colors['text_secondary']).pack(side="left")
                    
                    k_name = f"disk_{i}_serial"
                    e_var = ctk.StringVar(value=self.custom_config.get(k_name, ""))
                    self.entry_vars[k_name] = e_var
                    
                    entry = ctk.CTkEntry(f_row, textvariable=e_var, height=28, fg_color=self.colors['bg_input'], border_color=self.colors['border'])
                    entry.pack(side="left", fill="x", expand=True, padx=5)
                    
                    def rnd_disk(v=e_var):
                        # Disk format often varies, simple alphanumeric
                        import random, string
                        chars = string.ascii_uppercase + string.digits
                        v.set(''.join(random.choices(chars, k=18)))
                    ctk.CTkButton(f_row, text="🎲", width=30, height=28, command=rnd_disk, fg_color=self.colors['bg_input'], hover_color=self.colors['accent']).pack(side="right")

            elif key == "spoof_mem":
                sub_frame = ctk.CTkFrame(frame, fg_color="transparent")
                sub_frame.pack(fill="x", padx=30, pady=(0, 10))
                
                try:
                    mems = self.spoofer.MOFM.get_hardware_info("physical_memory")
                    if isinstance(mems, dict): mems = [mems]
                    elif not mems: mems = []
                except:
                    mems = []
                    
                if not mems:
                     ctk.CTkLabel(sub_frame, text="No memory modules detected.", text_color=self.colors['warning']).pack()

                for i, mem in enumerate(mems):
                    # RAM doesn't always have a friendly model name, use capacity or just index
                    f_row = ctk.CTkFrame(sub_frame, fg_color="transparent")
                    f_row.pack(fill="x", pady=2)
                    
                    label_text = f"RAM Stick {i}:"
                    ctk.CTkLabel(f_row, text=label_text, width=150, anchor="w", text_color=self.colors['text_secondary']).pack(side="left")
                    
                    k_name = f"mem_{i}_serial"
                    e_var = ctk.StringVar(value=self.custom_config.get(k_name, ""))
                    self.entry_vars[k_name] = e_var
                    
                    entry = ctk.CTkEntry(f_row, textvariable=e_var, height=28, fg_color=self.colors['bg_input'], border_color=self.colors['border'])
                    entry.pack(side="left", fill="x", expand=True, padx=5)
                    
                    def rnd_mem(v=e_var):
                        import random, string
                        v.set(''.join(random.choices(string.digits, k=8)))
                    ctk.CTkButton(f_row, text="🎲", width=30, height=28, command=rnd_mem, fg_color=self.colors['bg_input'], hover_color=self.colors['accent']).pack(side="right")

        # Save Button
        ctk.CTkButton(
            w,
            text="APPLY CONFIGURATION",
            font=("Orbitron", 14, "bold"),
            height=40,
            fg_color=self.colors['success'],
            hover_color="#00a34c",
            command=lambda: self.save_custom_config(w)
        ).pack(fill="x", padx=20, pady=20)
        
    def save_custom_config(self, window):
        # Gather all values
        new_conf = {}
        for k, var in self.toggle_vars.items():
            new_conf[k] = var.get()
            
        for k, var in self.entry_vars.items():
            new_conf[k] = var.get().strip()
            
        self.custom_config = new_conf
        messagebox.showinfo("Configuration Saved", "Custom spoofing settings have been applied.\nThey will be used in the next spoofing session.")
        window.destroy()


if __name__ == "__main__":
    app = HydraSpoofer()
    app.mainloop()