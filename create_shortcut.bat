@echo off
chcp 65001 >nul 2>&1
echo ===================================================
echo 🚀 Creating Desktop Shortcut for whisperMe...
echo ===================================================

powershell -NoProfile -ExecutionPolicy Bypass -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut([System.IO.Path]::Combine([System.Environment]::GetFolderPath('Desktop'), 'whisperMe.lnk')); $Shortcut.TargetPath = '%~dp0start.bat'; $Shortcut.WorkingDirectory = '%~dp0'; $Shortcut.IconLocation = '%~dp0frontend\public\favicon.ico'; $Shortcut.Save()"

echo.
echo 🟢 Done! A shortcut named 'whisperMe' has been created on your Desktop with the product logo.
echo 🟢 You can now launch the application directly from your Desktop!
echo ===================================================
echo.
pause
