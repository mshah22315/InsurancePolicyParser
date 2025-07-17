@echo off
echo Starting Insurance Policy Parser - Backend and Frontend
echo ======================================================
echo.

REM Start backend in a new window
echo Starting backend server...
start "Backend Server" cmd /k "call venv\Scripts\activate.bat && pip install -r requirements.txt && python run.py"

REM Wait a moment for backend to start
timeout /t 3 /nobreak > nul

REM Start frontend in a new window
echo Starting frontend server...
start "Frontend Server" cmd /k "cd frontend && npm install && npm run build && npm run dev"

echo.
echo Both servers are starting...
echo Backend: http://localhost:5001
echo Frontend: http://localhost:5173
echo.
echo Press any key to exit this launcher...
pause > nul 