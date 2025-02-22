import subprocess
import sys


print("[1] Deploy")
print("[2] Test")
sw = input("\n> ")

def run_nuitka(disable_console=False):
    cmd = "py -m nuitka --onefile --enable-plugin=tk-inter --windows-icon-from-ico=imgs\\favicon.ico --include-data-file=Volumeid.exe=Volumeid.exe --include-data-dir=imgs=imgs --include-data-dir=\"E:\programming\python\Projects\AntiDebuggingProtection\"=AntiDebuggingProtection --output-filename=\"Hydra Spoofer\" --windows-uac-admin"
    if disable_console:
        cmd += " --windows-console-mode=disable"
    cmd += " hub.py"

    # Use Popen for real-time output streaming
    process = subprocess.Popen(
        cmd, 
        shell=True, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.STDOUT, 
        text=True,
        bufsize=0  # Unbuffered for immediate output
    )
    
    # Stream output in real-time, character by character if needed
    while True:
        output = process.stdout.readline()
        if output == '' and process.poll() is not None:
            break
        if output:
            print(output, end='', flush=True)
    
    # Get return code
    rc = process.poll()
    
    if disable_console:
        mode = "[PRODUCTION]"
    else:
        mode = "[TEST]"

    if rc == 0:
        print(f"\n✅ {mode} Build completed successfully!")
    else:
        print(f"\n❌ {mode} Build failed with exit code {rc}")

if sw == "1":
    run_nuitka(disable_console=True)
elif sw == "2":
    run_nuitka()