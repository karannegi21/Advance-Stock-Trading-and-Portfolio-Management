# Advanced Stock Trading & Portfolio Management Platform

A high-performance paper-trading platform replaying historical NSE market data as a live exchange simulation with real-time WebSocket price broadcasts, order matching engine, portfolio accounting, and quantitative analytics.

## Architecture

- **Frontend:** React 18, Vite, TypeScript, Tailwind CSS, TanStack Query, Zustand, Lightweight Charts
- **Backend:** FastAPI, SQLAlchemy 2.x, Alembic, PostgreSQL, WebSockets
- **Market Simulator:** Historical NSE tick replay with Brownian bridge intraday ticks
- **Deployments:** Frontend on Vercel, Backend on Render, Database on PostgreSQL (Neon)

## Repository Structure

```
├── backend/          # FastAPI backend service
├── frontend/         # React + Vite frontend application
├── render.yaml       # Render backend deployment spec
└── README.md
```

## Quickstart

### Backend
```bash
cd backend
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Unix:
source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```
