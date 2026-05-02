@echo off
chcp 65001 >nul
title AK Company Bass Booster - EXE Builder
cd /d "%~dp0"

echo.
echo  AK Company Bass Booster - Builder v4.0
echo  =========================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo [HATA] Python bulunamadi! https://python.org
    pause & exit /b 1
)

echo [1/3] Kutuphaneler kuruluyor...
python -m pip install pyaudio numpy scipy pyinstaller --quiet --upgrade

echo [2/3] EXE olusturuluyor...
python -m PyInstaller --noconfirm --onefile --windowed ^
    --name "AK_Bass_Booster" ^
    --icon "%~dp0ak_icon.ico" ^
    --add-data "%~dp0ak_icon.ico;." ^
    --hidden-import pyaudio ^
    --hidden-import numpy ^
    --hidden-import scipy ^
    --hidden-import scipy.signal ^
    --hidden-import scipy._lib.messagestream ^
    --hidden-import tkinter ^
    "%~dp0ak_bass_booster.py"

if errorlevel 1 (
    echo [HATA] Derleme basarisiz!
    pause & exit /b 1
)

echo [3/3] Temizleniyor...
if exist "%~dp0build"       rmdir /s /q "%~dp0build"
if exist "%~dp0__pycache__" rmdir /s /q "%~dp0__pycache__"
if exist "%~dp0AK_Bass_Booster.spec" del "%~dp0AK_Bass_Booster.spec"

echo.
echo  [TAMAM] dist\AK_Bass_Booster.exe hazir!
echo.
explorer "%~dp0dist"
pause
