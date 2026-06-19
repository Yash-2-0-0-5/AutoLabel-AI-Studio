@echo off
REM AutoLabel AI Studio - Start both backend and frontend servers (Windows)

echo.
echo ==========================================
echo Starting AutoLabel AI Studio
echo ==========================================
echo.

echo Starting backend (FastAPI) on port 8000...
start "AutoLabel Backend" cmd /k "cd backend && python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000"

echo Starting frontend (Vite) on port 5173...
timeout /t 2 /nobreak
start "AutoLabel Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo ==========================================
echo Both servers starting!
echo ==========================================
echo.
echo Backend:  http://localhost:8000
echo  Docs:    http://localhost:8000/docs
echo.
echo Frontend: http://localhost:5173
echo.
echo Close either window to stop that server.
echo ==========================================
echo.
