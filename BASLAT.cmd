@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" goto installed
where py >nul 2>nul
if errorlevel 1 goto pythonfallback
py -3 -m venv .venv
goto checkenv
:pythonfallback
python -m venv .venv
:checkenv
if errorlevel 1 goto failed
:installed
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto failed
".venv\Scripts\python.exe" run.py
if errorlevel 1 goto failed
exit /b 0
:failed
echo.
echo Baslatilamadi. Yukaridaki hata mesajini kontrol edin. Python 3.10+ gereklidir.
pause
exit /b 1
