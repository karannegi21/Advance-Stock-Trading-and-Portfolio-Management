<div align="center">

# 📈 Advanced Stock Trading & Portfolio Management Platform

**A paper-trading platform that replays historical NSE data as a live exchange simulation.**

[![Live Demo](https://img.shields.io/badge/Demo-Vercel-black?style=for-the-badge&logo=vercel)](https://advance-stock-trading-and-portfolio.vercel.app)
[![API](https://img.shields.io/badge/API-Render-46E3B7?style=for-the-badge&logo=render)](https://advance-stock-trading-and-portfolio.onrender.com/docs)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=for-the-badge&logo=typescript&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)

[🌐 Live Demo](https://advance-stock-trading-and-portfolio.vercel.app) · [📡 API Docs](https://advance-stock-trading-and-portfolio.onrender.com/docs) · [📋 Implementation Plan](IMPLEMENTATION_PLAN.md) · [🐞 Report Bug](../../issues)

</div>

---

## 📌 Table of Contents
- [About the Project](#-about-the-project)
- [Live Links](#-live-links)
- [Key Features](#-key-features)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Getting Started](#-getting-started)
- [Deployment](#-deployment)
- [Roadmap](#-roadmap)
- [Author](#-author)

---

## 📖 About the Project
This platform simulates a real stock exchange using historical NSE data. Prices are replayed tick by tick and broadcast live over WebSockets, so users can place orders, build a portfolio, and track performance without risking real money.

---

## 🚀 Live Links
- **Frontend:** https://advance-stock-trading-and-portfolio.vercel.app
- **Backend API:** https://advance-stock-trading-and-portfolio.onrender.com
- **API Docs (Swagger):** https://advance-stock-trading-and-portfolio.onrender.com/docs

> **Note:** The backend runs on Render's free tier. If it has been idle, the first request may take ~50–90 seconds to wake up.

---

## ✨ Key Features
- **Live exchange simulation:** historical NSE data replayed with Brownian-bridge intraday ticks
- **Real-time prices:** WebSocket broadcasts to every connected client
- **Order matching engine:** orders are matched against the simulated market
- **Portfolio accounting:** holdings, P&L and cash balance tracking
- **Quantitative analytics:** performance and risk metrics for your portfolio
- **Interactive charts:** candlestick charts built with Lightweight Charts

---

## 🏗 Architecture
```
 React + Vite (Vercel)
      │   REST + WebSocket
      ▼
 FastAPI (Render) ──► Market Simulator (NSE tick replay)
      │
      ▼
 PostgreSQL (Neon)
```

---

## 🛠 Tech Stack
| Layer | Technologies |
|-------|--------------|
| **Frontend** | React 18, Vite, TypeScript, Tailwind CSS, TanStack Query, Zustand, Lightweight Charts |
| **Backend** | FastAPI, SQLAlchemy 2.x, Alembic, WebSockets |
| **Market Simulator** | Historical NSE tick replay with Brownian bridge intraday ticks |
| **Database** | PostgreSQL (Neon) |
| **Deployment** | Vercel (frontend), Render (backend) |
| **CI/CD** | GitHub Actions |

---

## 📁 Project Structure
```
├── backend/              # FastAPI service (API, matching engine, simulator)
├── frontend/             # React + Vite app
├── docs/                 # Documentation
├── .github/workflows/    # CI pipelines
├── render.yaml           # Render deployment spec
├── IMPLEMENTATION_PLAN.md
└── README.md
```

---

## ⚙️ Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+
- PostgreSQL (local or a Neon connection string)

### 1. Backend
```bash
cd backend
python -m venv venv

# Windows
.\venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env        # add your DATABASE_URL
uvicorn app.main:app --reload
```
API docs run locally at `http://localhost:8000/docs`.

### 2. Frontend
```bash
cd frontend
npm install
cp .env.example .env        # set the backend URL
npm run dev
```

---

## 🌍 Deployment
- **Frontend:** Vercel
- **Backend:** Render, configured via `render.yaml`
- **Database:** Neon PostgreSQL

---

## 🗺 Roadmap
- [x] Historical data replay and live WebSocket prices
- [x] Order matching engine
- [x] Portfolio accounting

---

## 👨‍💻 Author
**Karan Singh Negi** · [GitHub](https://github.com/karannegi21)

---

⭐ If you found this project useful, consider giving it a star!
