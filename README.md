# 🔥 HYDRA SPOOFER

![Version](https://img.shields.io/badge/version-1.5.5-blue.svg)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)
![Python](https://img.shields.io/badge/python-3.8+-yellow.svg)

**Hardware Identity Spoofing Tool for Windows**

Change your computer's hardware fingerprint to protect privacy on websites and web services.

---

## 🎯 What Does It Do?

Hydra Spoofer changes your computer's hardware identifiers (MAC address, BIOS serial, disk serial, etc.) to prevent tracking by websites and online services.

### ✅ Works With:
- Websites and web applications
- Online services and platforms
- Browser-based fingerprinting
- Cloud services

### ❌ Does NOT Work With:
- Desktop applications and games
- Kernel-level anti-cheat systems (EAC, BattlEye, Vanguard, etc.)
- Software that directly reads hardware at kernel level
- Most modern anti-cheat protected games

**Important**: This tool is designed for web-based privacy protection, not for bypassing desktop software protections.

---

## ⚡ Features

- 🎭 **MAC Address Spoofing** - Change network adapter identifiers
- 🖥️ **SMBIOS Spoofing** - Modify BIOS, Motherboard, CPU serials
- 💾 **Disk & Memory Serials** - Change storage and RAM identifiers
- 🔐 **Windows IDs** - Modify Machine GUID, Product ID, Computer Name
- 💾 **Backup & Restore** - Save and restore original hardware IDs
- 🎯 **Custom Spoofing** - Set specific values or randomize everything

---

## 🚀 Quick Start

### Installation

1. **Clone or download this repository**
   ```bash
   git clone https://github.com/yourusername/hydra-spoofer.git
   cd hydra-spoofer
   ```

2. **Install requirements**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run as Administrator**
   ```bash
   python MOFmenu.py
   ```

### Usage

1. **Launch the program** (must run as Administrator)
2. Click **SPOOF** to randomize all hardware IDs
3. System will restart automatically
4. To restore original IDs, click **REMOVE**

**Advanced Mode**: Click **ADVANCED** to choose specific components and set custom values.

---

## ⚠️ Important Warnings

### Before You Start
- ⚠️ **Create a backup first** - Always save your original hardware IDs
- ⚠️ **Administrator required** - Must run with admin privileges
- ⚠️ **System restart needed** - Changes require reboot to take effect
- ⚠️ **Not for anti-cheat bypass** - Will NOT work with desktop games or kernel-level protection

### Limitations
- Windows Defender may flag the tool (false positive)
- Some network adapters don't support MAC spoofing
- May rarely affect Windows activation
- Desktop applications can still detect your real hardware

---

## 📖 How to Use

### Basic Spoofing (Recommended)
1. Open program as Administrator
2. Click **SPOOF** button
3. Wait for process to complete
4. System restarts with new hardware IDs

### Restore Original IDs
1. Click **REMOVE** button
2. Confirm restoration
3. System restarts with original hardware IDs

### Save/Compare Serials
1. Click **SERIALS** button
2. Choose **Save** to backup current IDs
3. Choose **Compare** to check differences with saved file
4. Use **Import/Export** to share profiles

---

## 🛠️ Requirements

- Windows 10/11 (64-bit)
- Python 3.8+
- Administrator privileges
- Internet connection (for MAC address reset)

---

## 🐛 Common Issues

**"Administrator privileges required"**
→ Right-click and select "Run as Administrator"

**MAC address not changing**
→ Your network adapter may not support MAC spoofing

**Windows Defender blocks the program**
→ Add exception in Windows Security (it's a false positive)

**Lost internet connection after spoofing**
→ Wait 30-60 seconds for network adapters to reset

---

## ⚖️ Legal Disclaimer

This tool is for **educational and privacy protection purposes only**. 

- Use responsibly and legally
- Don't use to bypass legitimate security measures
- Don't use for cheating or fraud
- You are responsible for how you use this tool

---

## 🤝 Contributing

Pull requests are welcome! Feel free to:
- Report bugs
- Suggest features
- Improve documentation
- Submit code improvements

---

## 📜 License

MIT License - Free to use and modify

---

**Made for privacy-conscious users** 🔒
