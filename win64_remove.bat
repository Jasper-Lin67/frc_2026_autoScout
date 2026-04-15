@echo off
set "targetDir=%~dp0"
echo WARNING: This will permanently delete everything in:
echo %targetDir%
set /p confirm="Are you sure? (Y/N): "

if /i "%confirm%" neq "Y" exit /b

:: Moves outside the directory so Windows can delete the folder
cd ..

:: Starts a separate process to delete the folder after this script closes
start /b "" cmd /c "timeout /t 2 >nul & rd /s /q "%targetDir%""

echo Uninstallation started. This window will close.
exit
