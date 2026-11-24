@echo off
cd /d %~dp0
py -m pip install --user -r requirements.txt pyinstaller
pyinstaller --noconfirm --clean --windowed --name MotionStudio --collect-all OpenGL --collect-all PySide6 src\main.py
echo.
echo EXE created in dist\MotionStudio\
pause
