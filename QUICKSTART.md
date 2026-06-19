# AutoLabel AI Studio - Quick Start Guide

## Prerequisites

- Python 3.11+
- Node.js 20+
- Git
- `.env` file with `GEMINI_API_KEY` (optional for basic testing)

## Installation

### 1. Install Backend Dependencies

```bash
cd backend
pip install -r requirements.txt
cd ..
```

### 2. Install Frontend Dependencies

```bash
cd frontend
npm install
cd ..
```

## Starting the Servers

### Option 1: Automated Script (Recommended)

#### On Windows (Git Bash or WSL):
```bash
bash start.sh
```

#### On Windows (Command Prompt):
```cmd
start.bat
```

#### On macOS/Linux:
```bash
bash start.sh
```

### Option 2: Manual - Two Terminal Windows

**Terminal 1 - Backend:**
```bash
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

### Option 3: One-Liner (Git Bash or Linux/macOS)

```bash
(cd backend && python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000) & (cd frontend && npm run dev)
```

### Option 4: Using Docker Compose

```bash
docker-compose up
```

This will start both services:
- Backend on `http://localhost:8000`
- Frontend on `http://localhost:3000`

## Accessing the Application

After starting the servers:

### Backend
- **Main API**: http://localhost:8000
- **API Docs (Swagger UI)**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

### Frontend
- **Application**: http://localhost:5173

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# Required for AI labeling
GEMINI_API_KEY=your-api-key-here

# Optional
DATABASE_URL=sqlite:///./autolabel.db
LOG_LEVEL=INFO
```

### Backend Configuration

Edit `backend/main.py` to adjust:
- CORS origins
- Host/port
- Logging level

### Frontend Configuration

Edit `frontend/vite.config.js` for:
- Proxy settings
- Port configuration
- Environment variables

## Troubleshooting

### Port Already in Use

**Port 8000 (Backend):**
```bash
# Find process using port 8000
lsof -i :8000

# Kill process
kill -9 <PID>
```

**Port 5173 (Frontend):**
```bash
# Find process using port 5173
lsof -i :5173

# Kill process
kill -9 <PID>
```

Or use a different port:
```bash
# Backend on different port
python -m uvicorn main:app --port 8001

# Frontend on different port
npm run dev -- --port 5174
```

### Dependencies Not Installing

**Backend:**
```bash
cd backend
python -m pip install --upgrade pip
pip install -r requirements.txt --force-reinstall
```

**Frontend:**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### Backend Connection Failed

Make sure backend is running and accessible:
```bash
curl http://localhost:8000/health
```

If that fails, check the backend logs and ensure:
- Python 3.11+ is installed
- All dependencies are installed
- Port 8000 is not in use

### Frontend Shows Blank Page

Check browser console for errors. Common issues:
- Backend not running (check Network tab in DevTools)
- Node modules not installed (run `npm install`)
- Port conflicts (try different port)

## Next Steps

### 1. Test Data Upload

```bash
cd test_data
curl -X POST http://localhost:8000/api/upload \
  -F "file=@reviews.csv" \
  -F "dataset_name=test_dataset"
```

### 2. Run Tests

```bash
# Test upload functionality
python test_upload.py

# Test Gemini service
python test_gemini_service.py

# Test frontend workflow
python test_frontend_workflow.py

# Test Step 5 features
python test_step5.py
```

### 3. Configure Gemini API

To enable AI labeling:
1. Get API key from https://aistudio.google.com/app/apikey
2. Add to `.env` file: `GEMINI_API_KEY=your-key`
3. Restart backend

### 4. Start Using the Application

1. Open http://localhost:5173
2. Click "Dashboard" tab
3. Upload a CSV, Excel, or JSON file
4. Click on dataset to view items
5. Click "Start AI Labeling"
6. Review and correct labels in "Review Queue"

## Development Tips

### Hot Reload

Both servers support hot reload:
- **Backend**: Changes to Python files auto-reload
- **Frontend**: Changes to React/Tailwind CSS auto-reload

Just save and refresh your browser!

### Debug Logs

View logs from the running servers:

**Backend logs:**
```bash
tail -f backend.log
```

**Frontend logs:**
Check browser console (F12)

### Database

View SQLite database:
```bash
sqlite3 backend/autolabel.db

# List tables
.tables

# View items
SELECT * FROM data_items LIMIT 5;

# Exit
.quit
```

## API Quick Reference

### Upload
```bash
curl -X POST http://localhost:8000/api/upload \
  -F "file=@data.csv" \
  -F "dataset_name=my_dataset"
```

### List Datasets
```bash
curl http://localhost:8000/api/datasets
```

### Process Dataset with AI
```bash
curl -X POST http://localhost:8000/api/datasets/1/process
```

### Get Processing Status
```bash
curl http://localhost:8000/api/datasets/1/process/status
```

### Correct a Label
```bash
curl -X PUT http://localhost:8000/api/items/1/correct \
  -H "Content-Type: application/json" \
  -d '{"corrected_label": "electronics"}'
```

### Export Dataset
```bash
# CSV
curl http://localhost:8000/api/datasets/1/export/csv > data.csv

# JSON
curl http://localhost:8000/api/datasets/1/export/json > data.json

# ML-Ready
curl http://localhost:8000/api/datasets/1/export/ml-ready > data_ml.csv

# ZIP
curl http://localhost:8000/api/datasets/1/export/zip > data.zip
```

## Production Deployment

### Frontend
```bash
cd frontend
npm run build
# Outputs to dist/ directory
```

### Backend
For production, use:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

See individual README files in `backend/` and `frontend/` for detailed deployment instructions.

## Help & Support

- **Backend Issues**: Check `backend.log` or backend console
- **Frontend Issues**: Check browser console (F12)
- **API Questions**: Visit http://localhost:8000/docs
- **Feature Documentation**: See `STEP1_*.md` through `STEP5_*.md`

## Stopping the Servers

### Automated Script
Press `Ctrl+C` in the terminal

### Manual Terminals
Press `Ctrl+C` in each terminal window

### Windows Batch File
Close the command prompt windows

### Docker
```bash
docker-compose down
```

---

**Happy labeling!** 🎉
