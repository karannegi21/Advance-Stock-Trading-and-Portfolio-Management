# Architecture

## Components
- Frontend: React/Vite/TS on Vercel
- Backend: FastAPI on Render
- DB: PostgreSQL on Neon
- Simulator: background asyncio task advancing sim date and broadcasting prices via WebSocket

## Flow
Register/Login -> JWT -> Browse market -> Place order -> Portfolio/P&L -> Analytics -> Admin controls simulator
