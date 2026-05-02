@echo off
chcp 65001 >nul
title AK Company Bass Booster - EXE Builder
cd /d "%~dp0"

echo.
echo  AK Company Bass Booster - Builder
echo  ====================================
echo.

set PYTHON=
for %%p in (
    "python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
    "C:\Python313\python.exe"
    "C:\Python312\python.exe"
    "C:\Python311\python.exe"
    "C:\Python310\python.exe"
) do (
    if exist %%p (
        set PYTHON=%%p
        goto :found
    )
)
py --version >nul 2>&1
if not errorlevel 1 ( set PYTHON=py & goto :found )
echo [HATA] Python bulunamadi!
pause & exit /b 1

:found
echo Python: %PYTHON%
%PYTHON% --version
echo.

echo [1/3] Kutuphaneler kuruluyor...
%PYTHON% -m pip install pyaudio numpy scipy pyinstaller --quiet --upgrade

echo [2/3] EXE olusturuluyor...
%PYTHON% -m PyInstaller --noconfirm --onefile --windowed ^
    --name "AK_Bass_Booster" ^
    --icon "%~dp0ak_icon.ico" ^
    --add-data "%~dp0ak_icon.ico;." ^
    --hidden-import pyaudio ^
    --hidden-import numpy ^
    --hidden-import scipy ^
    --hidden-import scipy.signal ^
    --hidden-import scipy.signal._signaltools ^
    --hidden-import scipy.signal._lti_conversion ^
    --hidden-import scipy.signal.windows ^
    --hidden-import scipy.linalg ^
    --hidden-import scipy.linalg._decomp ^
    --hidden-import scipy._lib.messagestream ^
    --hidden-import tkinter ^
    --hidden-import tkinter.ttk ^
    --exclude-module matplotlib ^
    --exclude-module pandas ^
    --exclude-module PIL ^
    --exclude-module cv2 ^
    --exclude-module PyQt5 ^
    --exclude-module PyQt6 ^
    --exclude-module IPython ^
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
for %%A in ("%~dp0dist\AK_Bass_Booster.exe") do echo  Boyut: %%~zA byte
echo.
explorer "%~dp0dist"
pause
