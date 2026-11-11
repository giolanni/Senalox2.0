@echo off
setlocal
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0crea_collegamento.ps1"
set "RESULT=%ERRORLEVEL%"
if not "%RESULT%"=="0" echo Creazione del collegamento non riuscita.
pause
exit /b %RESULT%
