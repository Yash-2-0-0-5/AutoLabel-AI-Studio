#!/bin/bash

# AutoLabel AI Studio - Start both backend and frontend servers

set -e

echo "=========================================="
echo "Starting AutoLabel AI Studio"
echo "=========================================="

# Check if ports are available
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        return 0
    else
        return 1
    fi
}

echo ""
echo "Checking ports..."
if check_port 8000; then
    echo "⚠️  Port 8000 (backend) already in use"
fi

if check_port 5173; then
    echo "⚠️  Port 5173 (frontend) already in use"
fi

echo ""
echo "Starting backend (FastAPI)..."
echo "  - Running: cd backend && python -m uvicorn main:app --reload"
cd backend && python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000 > ../backend.log 2>&1 &
BACKEND_PID=$!
echo "  - Backend PID: $BACKEND_PID"

echo ""
echo "Starting frontend (Vite)..."
echo "  - Running: cd frontend && npm run dev"
cd ../frontend && npm run dev > ../frontend.log 2>&1 &
FRONTEND_PID=$!
echo "  - Frontend PID: $FRONTEND_PID"

echo ""
echo "=========================================="
echo "Both servers started!"
echo "=========================================="
echo ""
echo "Backend:  http://localhost:8000"
echo "  Docs:   http://localhost:8000/docs"
echo "  Health: http://localhost:8000/health"
echo ""
echo "Frontend: http://localhost:5173"
echo ""
echo "Logs:"
echo "  Backend:  ../backend.log"
echo "  Frontend: ../frontend.log"
echo ""
echo "To stop, press Ctrl+C or run: kill $BACKEND_PID $FRONTEND_PID"
echo "=========================================="
echo ""

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID
