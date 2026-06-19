# AutoLabel AI Studio

A full-stack application for intelligent data labeling and annotation using AI.

## Project Structure

```
AutoLabel AI Studio/
├── backend/              # FastAPI backend
│   ├── requirements.txt
│   ├── Dockerfile
│   └── main.py
├── frontend/             # React + Vite frontend
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── src/
├── docker-compose.yml    # Multi-container setup
├── .env.example          # Environment variables template
└── README.md
```

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 20+
- Docker & Docker Compose (optional)

### Local Development

1. **Backend Setup**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   uvicorn main:app --reload
   ```

2. **Frontend Setup**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

3. **Set Environment Variables**
   ```bash
   cp .env.example .env
   # Edit .env and add your GEMINI_API_KEY
   ```

### Docker Setup

```bash
docker-compose up
```

This will start both services:
- Backend: http://localhost:8000
- Frontend: http://localhost:3000

## Features

- AI-powered data labeling
- Multi-format data import (CSV, Excel, JSON)
- Real-time collaborative annotation
- Model training and evaluation
- Batch processing
- Audit logging

## API Documentation

Once the backend is running, visit:
- http://localhost:8080/docs (Swagger UI)
- http://localhost:8080/redoc (ReDoc)

## Development

See individual README files in `backend/` and `frontend/` directories for detailed development guides.

## License

Proprietary
