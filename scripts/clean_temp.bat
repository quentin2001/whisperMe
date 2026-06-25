@echo off
echo Cleaning temp_sandbox...
if exist "temp_sandbox\*.wav" del /q "temp_sandbox\*.wav" 2>nul
if exist "temp_sandbox\*.m4a" del /q "temp_sandbox\*.m4a" 2>nul
if exist "temp_sandbox\*.mp3" del /q "temp_sandbox\*.mp3" 2>nul
if exist "temp_sandbox\.cache" rd /s /q "temp_sandbox\.cache" 2>nul
if exist "temp_sandbox\.matplotlib" rd /s /q "temp_sandbox\.matplotlib" 2>nul
if exist "temp_sandbox\NVIDIA" rd /s /q "temp_sandbox\NVIDIA" 2>nul
if exist "temp_sandbox\torch" rd /s /q "temp_sandbox\torch" 2>nul
echo Done!
pause
