@echo off
setlocal

REM Launch the PowerShell runner with a per-process execution-policy bypass.
REM %~dp0 resolves to the directory containing this .bat file, so the script
REM works regardless of the current working directory.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run.ps1" %*

endlocal
