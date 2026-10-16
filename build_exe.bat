@echo off
title Building CF2Mrpack Executable...
echo [*] Installing/verifying dependencies...
pip install -r requirements.txt

echo [*] Building standalone Windows executable with PyInstaller...
pyinstaller --noconfirm --onedir --windowed --collect-all customtkinter --name "CF2Mrpack" --clean --onefile main.py

echo.
echo [SUCCESS] Build finished! Your standalone executable is located at: dist\CF2Mrpack.exe
pause
