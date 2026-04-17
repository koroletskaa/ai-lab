@echo off
REM Script to run frontend and backend (Windows)
echo ============================================================
echo Emotional tracker - Starting servers
echo ============================================================
echo.

REM Check if virtual environment exists
if exist "website\backend\.venv\Scripts\activate.bat" (
    echo Virtual environment found
    call website\backend\.venv\Scripts\activate.bat
) else (
    echo Virtual environment not found
    echo    Creating it in website\backend\.venv ...
    cd website\backend
    python -m venv .venv
    call .venv\Scripts\activate.bat
    cd ..\..
)

echo Installing backend dependencies (including python-dotenv)...
pip install -r website\backend\requirements.txt -q
echo.

REM Start backend in new window
echo Starting backend server...
start "Backend Server" cmd /k "cd /d website\backend && python main.py"

REM Start SSH reverse tunnel to your own server (optional)
REM Edit tunnel_to_server.py and set SSH_USER/SSH_HOST/REMOTE_PORT before using.
echo Starting SSH tunnel to your server...
if exist ".venv\Scripts\python.exe" (
    start "SSH Tunnel" cmd /k "cd /d %~dp0 && .venv\Scripts\python tunnel_to_server.py"
) else (
    start "SSH Tunnel" cmd /k "cd /d %~dp0 && python tunnel_to_server.py"
)

REM Delay
timeout /t 3 /nobreak >nul

REM Start frontend in new window
echo Starting frontend server...
start "Frontend Server" cmd /k "cd /d website\frontend && python -m http.server 8080"

REM Open browser tabs for frontend and API docs
start "" "http://localhost:8080"

echo.
echo ============================================================
echo Servers started!
echo ============================================================
echo.
echo Backend API: http://localhost:8000
echo API Docs:    http://localhost:8000/docs
echo Frontend:    http://localhost:8080
echo.
echo Both servers are running in separate windows
echo Close the windows to stop the servers
echo.
pause

