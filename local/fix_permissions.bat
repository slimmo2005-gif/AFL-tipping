@echo off
:: Run this file as Administrator (right-click -> Run as administrator)
:: Fixes read-only ACLs on the AFL folder after copying from work/USB.

set "TARGET=%~dp0"
if exist "C:\Users\Tim\AFL\app.py" set "TARGET=C:\Users\Tim\AFL"

echo Fixing permissions on: %TARGET%
takeown /F "%TARGET%" /R /D Y
icacls "%TARGET%" /reset /T /C
icacls "%TARGET%" /grant "%USERNAME%:(OI)(CI)F" /T
echo.
echo Done. You can run start.bat from that folder.
pause
