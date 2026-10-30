# Advanced Stock Trading & Portfolio Management — Agent Implementation Plan

> **For the coding agent:** Read this whole file first. Execute phases in order. Do not start a phase until the previous phase's **Done-when** checks pass. After each phase: run tests, commit, and print a short status report (what was built, what was verified, what is next).

---

## 0. Project Summary

A paper-trading (virtual money) platform where users register, trade NSE stocks, and track portfolio performance with analytics.

- **Frontend:** React + Vite + TypeScript → deployed on **Vercel**
- **Backend:** FastAPI (Python) + PostgreSQL → deployed on **Render**
- **Market data:** Kaggle NSE dataset (2015–2024), replayed by a **market simulator** to behave like a live market
- **Final goal:** public Vercel URL talking to public Render API, fully working end to end

### Why paper trading + simulator
Real exchange data feeds and real brokerage need licences and paid APIs. A simulator built on the historical dataset is legitimate, free, reproducible for demos, and still shows every hard engineering problem (order matching, portfolio accounting, real-time updates).

---

## 1. Operating Rules for the Agent

1. **Inspect before assuming.** Check installed versions (`node -v`, `python --version`, `git --version`) and the dataset's actual columns before writing code that depends on them.
2. **Small commits.** One logical change per commit, conventional messages (`feat:`, `fix:`, `chore:`).
3. **Never commit secrets.** `.env` files go in `.gitignore`; provide `.env.example` files only.
4. **Money is `Decimal`/`NUMERIC`, never float.** Store prices with `NUMERIC(18,4)`.
5. **Every phase ends with verification** (tests, curl, or a browser check). Do not claim done without running it.
6. **Ask the human only for things you cannot do:** account logins (GitHub, Vercel, Render, Neon, Kaggle), pasting API keys, approving destructive actions.
7. **If blocked twice on the same error, stop** and report the error + what you tried.
8. Keep the code readable for a college viva: clear folder structure, docstrings on services, a README the student can explain.

---

## 2. Tech Stack (fixed — do not substitute without asking)

| Layer | Choice |
|---|---|
| Frontend | React 18, Vite, TypeScript, Tailwind CSS, React Router, TanStack Query, Zustand |
| Charts | `lightweight-charts` (candlesticks), `recharts` (pie/line/bar) |
| Backend | FastAPI, Uvicorn, SQLAlchemy 2.x, Alembic, Pydantic v2 |
| Auth | JWT (access + refresh), `passlib[bcrypt]` |
| DB | PostgreSQL (Neon free tier recommended; Render Postgres free tier expires after ~30 days) |
| Real-time | FastAPI WebSocket |
| Data/analytics | pandas, numpy |
| Testing | pytest + httpx (backend), Vitest + React Testing Library (frontend) |
| CI | GitHub Actions (lint + tests) |
| Hosting | Vercel (frontend), Render Web Service (backend) |

---

## 3. Repository Layout

```
stock-platform/
├── README.md
├── .gitignore
├── render.yaml
├── .github/workflows/ci.yml
├── backend/
│   ├── requirements.txt
│   ├── .env.example
│   ├── alembic.ini
│   ├── alembic/
│   ├── app/
│   │   ├── main.py
│   │   ├── core/            # config, security, db session
│   │   ├── models/          # SQLAlchemy models
│   │   ├── schemas/         # Pydantic schemas
│   │   ├── api/             # routers: auth, stocks, orders, portfolio, watchlist, analytics, admin
│   │   ├── services/        # order_engine, portfolio_service, analytics_service, market_simulator
│   │   ├── ws/              # websocket manager
│   │   └── scripts/         # seed_market_data.py
│   ├── data/                # (gitignored) raw Kaggle CSVs
│   └── tests/
└── frontend/
    ├── package.json
    ├── .env.example
    ├── vercel.json
    └── src/
        ├── api/             # axios client, typed endpoints
        ├── components/
        ├── pages/           # Login, Register, Dashboard, Market, StockDetail, Portfolio, Orders, Watchlist, Analytics
        ├── store/
        ├── hooks/
        └── lib/
```

---

## 4. Data Model (PostgreSQL)

| Table | Key columns |
|---|---|
| `users` | id, email (unique), password_hash, full_name, role (`user`/`admin`), created_at |
| `accounts` | id, user_id (unique FK), cash_balance NUMERIC(18,4) default 1,000,000.00, initial_balance |
| `stocks` | id, symbol (unique), name, sector, is_active |
| `price_bars` | id, stock_id, trade_date, open, high, low, close, volume — **unique(stock_id, trade_date)**, index on (stock_id, trade_date) |
| `orders` | id, user_id, stock_id, side (`BUY`/`SELL`), type (`MARKET`/`LIMIT`/`STOP`), quantity, limit_price, stop_price, status (`PENDING`/`FILLED`/`CANCELLED`/`REJECTED`), filled_price, filled_at, created_at, reject_reason |
| `holdings` | id, user_id, stock_id, quantity, avg_cost — **unique(user_id, stock_id)** |
| `transactions` | id, user_id, order_id, stock_id, side, quantity, price, fees, executed_at |
| `watchlist_items` | id, user_id, stock_id — unique(user_id, stock_id) |
| `portfolio_snapshots` | id, user_id, snap_date, total_value, cash, invested_value — used for equity curve |
| `sim_state` | id (single row), current_sim_date, speed_seconds_per_day, is_running |

Create all with Alembic migrations (no `create_all` in production).

---

## 5. Core Business Rules

**Fees (keep simple, document in README):** brokerage 0.03% per trade + 0.1% STT on sell. Configurable constants.

**Order validation**
- BUY: `quantity * price + fees <= cash_balance`, else `REJECTED` ("Insufficient funds").
- SELL: `quantity <= holding.quantity`, else `REJECTED` ("Insufficient holdings"). No short selling.
- Quantity must be a positive integer.

**Execution**
- `MARKET`: fills immediately at current simulated price.
- `LIMIT`: BUY fills when price ≤ limit; SELL fills when price ≥ limit. Stays `PENDING` otherwise.
- `STOP` (stop-loss, SELL only): triggers when price ≤ stop_price, then fills at market.
- Pending orders are checked on every simulator tick.
- Cash for pending BUY limit orders is **reserved** (track `reserved_cash` or compute from pending orders) so users can't overspend.

**Holdings update**
- BUY: `new_avg = (old_qty*old_avg + qty*price) / (old_qty + qty)`.
- SELL: quantity reduces, avg_cost unchanged; realised P&L = `(sell_price - avg_cost) * qty - fees`.
- Whole order fill runs in **one DB transaction** with row locks (`SELECT ... FOR UPDATE` on account + holding).

**Market simulator**
- Holds a `current_sim_date`. Every N seconds (configurable, default 20s) it advances one trading day through the dataset.
- Within a day, generate intraday ticks between open→high/low→close using a bounded random walk (Brownian bridge) so prices move smoothly and always respect the day's high/low.
- After each tick: update in-memory price cache, check pending orders, broadcast via WebSocket.
- End of each simulated day: write `portfolio_snapshots` for all users.
- Admin can start/pause/reset and change speed.

---

## 6. API Contract (all under `/api/v1`)

| Method | Path | Purpose |
|---|---|---|
| POST | `/auth/register` | create user + account |
| POST | `/auth/login` | returns access + refresh tokens |
| POST | `/auth/refresh` | new access token |
| GET | `/auth/me` | current user |
| GET | `/stocks` | list, search (`?q=`), filter (`?sector=`), pagination |
| GET | `/stocks/{symbol}` | details + current price + day change |
| GET | `/stocks/{symbol}/history` | OHLCV up to current sim date (`?range=1M/6M/1Y/ALL`) |
| GET | `/market/overview` | top gainers, losers, most active, sim date |
| POST | `/orders` | place order |
| GET | `/orders` | list (filter by status) |
| DELETE | `/orders/{id}` | cancel pending order |
| GET | `/portfolio` | holdings, current value, unrealised P&L, cash |
| GET | `/portfolio/transactions` | trade history |
| GET | `/watchlist` · POST · DELETE `/watchlist/{symbol}` | manage watchlist |
| GET | `/analytics/summary` | total return, CAGR, volatility, Sharpe, max drawdown, win rate |
| GET | `/analytics/allocation` | by stock and by sector |
| GET | `/analytics/equity-curve` | portfolio value over time |
| GET | `/leaderboard` | top users by return % |
| POST | `/admin/sim/{start,pause,reset}` · PUT `/admin/sim/speed` | simulator control (admin only) |
| GET | `/health` | for Render health check |
| WS | `/ws/prices` | stream of `{symbol, price, change_pct, ts}`; token passed as query param |

Standard error shape: `{"detail": "...", "code": "INSUFFICIENT_FUNDS"}`. Document everything via FastAPI's auto `/docs`.

---

## 7. Phased Plan

### Phase 1 — Environment & Scaffolding
**Tasks**
1. Verify Node 18+/20, Python 3.11+, Git. Report versions.
2. Create the repo layout from §3, `git init`, `.gitignore` (node_modules, venv, `.env`, `data/`, `__pycache__`, `dist`).
3. Backend: create venv, install dependencies, write `requirements.txt`, minimal `main.py` with `/health`.
4. Frontend: `npm create vite@latest frontend -- --template react-ts`, add Tailwind, React Router, TanStack Query, Zustand, axios.
5. Add `.env.example` in both apps.

**Done-when:** `uvicorn app.main:app --reload` serves `/health` and `/docs`; `npm run dev` shows the Vite page; first commit made.

### Phase 2 — Database, Models, Migrations
**Tasks**
1. `core/config.py` (pydantic-settings) reading `DATABASE_URL`, `JWT_SECRET`, `CORS_ORIGINS`.
2. SQLAlchemy models for every table in §4.
3. Alembic init + first migration; apply to local Postgres (use Docker `postgres:16` if no local install, otherwise ask human for a Neon URL).
4. Unit test that migrations apply cleanly on an empty DB.

**Done-when:** `alembic upgrade head` succeeds; tables visible via `psql` or a DB client.

### Phase 3 — Market Data Ingestion
**Tasks**
1. **Ask the human** to place the Kaggle NSE CSVs in `backend/data/` (or provide the Kaggle CLI token).
2. Inspect the files: print columns, row counts, date range, number of symbols, null counts. **Report this before continuing.**
3. Write `scripts/seed_market_data.py`: clean data (drop nulls, enforce `high >= max(open,close)`, `low <= min(open,close)`), pick the **top ~50 symbols by traded value** (keeps the free DB under its size limit), insert `stocks` + `price_bars` in batches (`COPY` or `executemany`), idempotent (safe to re-run).
4. Add sector mapping (small static dict/CSV for the chosen symbols; mark "Unknown" if missing).

**Done-when:** `SELECT count(*) FROM price_bars` matches expected; `/stocks` and `/stocks/{symbol}/history` return data.

### Phase 4 — Authentication
**Tasks**
1. Register/login/refresh/me endpoints, bcrypt hashing, JWT with expiry, `get_current_user` dependency, role check dependency.
2. On register: create `accounts` row with starting cash.
3. Rate limit login (e.g., `slowapi`) and validate password strength.
4. Tests: register → login → me; wrong password; duplicate email; expired token.

**Done-when:** all auth tests pass.

### Phase 5 — Trading Engine & Portfolio Services
**Tasks**
1. `services/order_engine.py` implementing §5 (validation, market/limit/stop, reservation, atomic fill).
2. `services/portfolio_service.py`: holdings valuation using the current price cache, unrealised/realised P&L.
3. Routers: orders, portfolio, watchlist, market overview.
4. **Tests (critical):** buy then sell P&L math; avg-cost on multiple buys; insufficient funds/holdings; limit order stays pending then fills; stop-loss triggers; cancel releases reserved cash; concurrent orders can't overspend (use threads/async gather).

**Done-when:** ≥ 90% of engine/service code covered; all tests green.

### Phase 6 — Market Simulator + WebSocket
**Tasks**
1. `services/market_simulator.py` as an async background task started in FastAPI `lifespan`.
2. Tick generation per §5, in-memory price cache, pending-order check each tick.
3. `ws/manager.py` connection manager; `/ws/prices` with auth; broadcast batched ticks (≈1/sec) not per symbol per event.
4. Daily snapshot job at end of simulated day.
5. Admin endpoints for start/pause/reset/speed.
6. Persist `sim_state` so a Render restart resumes sensibly.

**Done-when:** a small test client connects to the WebSocket and receives price updates; a pending limit order fills automatically when price crosses.

### Phase 7 — Analytics
**Tasks** (pandas/numpy in `analytics_service.py`)
- Equity curve from `portfolio_snapshots`
- Total return %, CAGR, annualised volatility (std of daily returns × √252), Sharpe (risk-free = 6% or configurable), max drawdown, win rate from closed trades
- Allocation by stock & by sector
- Leaderboard
- Unit-test each formula against hand-computed fixtures.

**Done-when:** `/analytics/*` endpoints return correct values on a seeded test user.

### Phase 8 — Frontend
Build in this order, verifying each page in the browser:

1. **Foundation:** API client with token injection + auto-refresh on 401, auth store, protected routes, layout (sidebar, topbar showing sim date + cash), dark/light theme, toasts, loading/error states.
2. **Auth pages:** Login, Register with validation.
3. **Market page:** searchable/filterable table, gainers/losers cards, live price flicker (green/red) via WebSocket hook with auto-reconnect.
4. **Stock detail:** candlestick chart with range selector, key stats, **order ticket** (Buy/Sell, order type, quantity, estimated cost + fees, validation messages), add-to-watchlist.
5. **Portfolio:** holdings table with live P&L, cash, total value, allocation donut chart.
6. **Orders & transactions:** tabs for pending/filled/cancelled, cancel button, CSV export.
7. **Analytics:** equity curve, metric cards, sector allocation, drawdown chart.
8. **Watchlist** and **Leaderboard**.
9. **Admin panel** (role-gated): simulator controls.
10. Responsive for mobile; empty states; accessible labels.

**Done-when:** a full manual flow works locally: register → browse → buy → see live P&L → place limit order → it fills → analytics update.

### Phase 9 — Deployment

**9a. Database (Neon)** — human creates project, copies the connection string; agent uses it as `DATABASE_URL` (with `sslmode=require`). Run migrations + seed against it.

**9b. Backend on Render**
1. Add `render.yaml` (or configure in dashboard):
   - Runtime: Python, Root dir: `backend`
   - Build: `pip install -r requirements.txt && alembic upgrade head`
   - Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - Health check path: `/api/v1/health`
2. Env vars: `DATABASE_URL`, `JWT_SECRET` (generate a long random value), `CORS_ORIGINS` (the Vercel URL, set after 9c), `ENV=production`.
3. Deploy, then run the seed script once (Render shell, or locally pointed at the Neon DB).
4. Free-tier note: the service sleeps after inactivity (first request can take ~30–60 s). Add a "server waking up" state in the frontend, and optionally an uptime pinger (UptimeRobot) to hit `/health` every 10 minutes for demo day.

**9c. Frontend on Vercel**
1. Import the GitHub repo, set Root Directory = `frontend`, framework = Vite.
2. Env vars: `VITE_API_URL=https://<render-app>.onrender.com/api/v1`, `VITE_WS_URL=wss://<render-app>.onrender.com/ws/prices`.
3. `vercel.json` with SPA rewrite: `{ "rewrites": [{ "source": "/(.*)", "destination": "/index.html" }] }`.
4. Deploy, copy the production URL.

**9d. Connect them**
1. Set Render `CORS_ORIGINS` to the exact Vercel URL (no trailing slash) → redeploy backend.
2. Confirm WebSocket works over `wss://`.
3. Run the end-to-end smoke test on the live URLs.

**Done-when:** the live Vercel site completes the full flow with no console errors and no CORS errors.

### Phase 10 — Quality, Docs, Submission Pack
1. GitHub Actions: backend `pytest`, frontend `lint` + `vitest` + `build` on every push.
2. README: overview, architecture diagram (Mermaid), setup steps, env vars, API summary, screenshots, live URLs, demo credentials.
3. Seed a **demo user** with some trades and an **admin** account for the demo.
4. Security pass: CORS locked to the Vercel origin, no secrets in git history, input validation, HTTPS only, JWT expiry.
5. Performance pass: DB indexes verified with `EXPLAIN` on the history query; frontend code-splitting for chart pages.
6. Produce `docs/` with: ER diagram, architecture diagram, API list, test report, and a 2-minute demo script.

**Done-when:** CI green, README complete, live demo script rehearsed against the deployed URLs.

---

## 8. Final Acceptance Checklist

- [ ] Register, login, and token refresh work on the live site
- [ ] Market page lists stocks and updates prices live
- [ ] Market, limit, and stop orders behave per §5
- [ ] Insufficient funds/holdings are rejected with clear messages
- [ ] Portfolio P&L matches hand calculation on a test trade
- [ ] Analytics page shows return, Sharpe, drawdown, allocation, equity curve
- [ ] Admin can pause/resume/reset the simulator
- [ ] Frontend (Vercel) ↔ Backend (Render) ↔ DB (Neon) all connected, no CORS errors
- [ ] Backend tests pass; CI green
- [ ] README + diagrams + demo script ready

---

## 9. Things the Human Must Do (agent cannot)

1. Create/sign in to: GitHub, Neon, Render, Vercel.
2. Put the Kaggle NSE CSVs in `backend/data/` (or supply Kaggle credentials).
3. Paste the Neon `DATABASE_URL` and approve deployment steps.
4. Final demo rehearsal on the live URLs.

---

## 10. Kickoff Prompt (paste this to the agent)

```
Read IMPLEMENTATION_PLAN.md fully. Start with Phase 1. Follow the Operating Rules
in section 1. After each phase, run the verification for that phase, commit, and
give me a short status report before moving on. If you need anything from me
(logins, files, keys), stop and ask clearly. Begin now.
```

---

## 11. Scope Cuts if Time Runs Short (in this order)

1. Leaderboard
2. Stop orders (keep market + limit)
3. Admin speed control (keep start/pause)
4. Mobile polish
5. Frontend tests (keep backend engine tests — they matter most)

Never cut: auth, market/limit orders, portfolio P&L, simulator, deployment, README.
