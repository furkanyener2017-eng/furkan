@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Akilli Cay Bardagi yerel sunucusu baslatiliyor...
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 server.py
  goto :eof
)
where python >nul 2>nul
if %errorlevel%==0 (
  python server.py
  goto :eof
)
echo.
echo Python bulunamadi. Python 3 kurup tekrar deneyin.
pause
