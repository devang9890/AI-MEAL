# AI Meal Planner — Runbook

Stack: **FastAPI + Neon Postgres + Alembic** (backend) · **Vite + React + Clerk Auth** (frontend)

---

## Project Structure

```
aIMeal/
├── backend/          FastAPI app, SQLAlchemy models, Alembic migrations
│   ├── .env          DATABASE_URL + Clerk keys (gitignored)
│   └── .env.example  Safe placeholder template
├── frontend/         Vite + React app
│   └── .env.local    VITE_CLERK_PUBLISHABLE_KEY (gitignored)
└── RUNBOOK.md        you are here
```

---

## Backend

### First-time setup

```powershell
cd backend

# Create virtual environment
python -m venv .venv

# Activate it
.venv\Scripts\Activate.ps1

# Install all dependencies
pip install -r requirements.txt
```

### Run migrations (run whenever schema changes)

```powershell
cd backend
.venv\Scripts\Activate.ps1

alembic upgrade head
```

### Start the API server

```powershell
cd backend
.venv\Scripts\Activate.ps1

uvicorn app.main:app --reload --port 8000
```

API is now live at **http://localhost:8000**

---

## Frontend

### First-time setup

```powershell
cd frontend

npm install
```

### Start the dev server

```powershell
cd frontend

npm run dev
```

App is now live at **http://localhost:5173**

---

## Health Checks

Run these after both servers are up (open two terminals).

### Backend API

```powershell
curl http://localhost:8000/api/health
curl http://localhost:8000/api/db-health
```

**Expected:**
```json
{"status": "healthy", "service": "AI Meal Planner Backend"}
{"status": "healthy", "database": "connected"}
```

### Frontend + Clerk

| Step | What to expect |
|------|----------------|
| Open http://localhost:5173 | Landing page loads, Navbar shows **Login** + **Sign Up** |
| Click **Sign Up** | Clerk embedded registration form appears |
| Create a test account | After sign-in, Navbar shows your **avatar (UserButton)** |
| Click the avatar | Clerk profile menu with **Sign out** appears |

---

## Verify Neon Postgres

Go to https://console.neon.tech -> ai-meal project -> SQL Editor tab and run:

```sql
-- Check migration version (should be 002_clerk_auth)
SELECT * FROM alembic_version;

-- List all tables
SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename;

-- Verify users table columns (password_hash must be nullable after Clerk migration)
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'users'
ORDER BY ordinal_position;
```

**Expected alembic_version:**

| version_num    |
|----------------|
| 002_clerk_auth |

**Expected users columns:**

| column_name    | is_nullable |
|----------------|-------------|
| id             | NO          |
| clerk_user_id  | YES         |
| name           | NO          |
| email          | NO          |
| password_hash  | YES         |
| created_at     | NO          |

---

## Environment Variables

### backend/.env

```env
DATABASE_URL=postgresql://neondb_owner:PASSWORD@ep-...-pooler.c-2.us-east-2.aws.neon.tech/neondb?sslmode=require
VITE_CLERK_PUBLISHABLE_KEY=pk_test_...
CLERK_SECRET_KEY=sk_test_...
```

### frontend/.env.local

```env
VITE_CLERK_PUBLISHABLE_KEY=pk_test_...
```

> Never commit .env or .env.local — both are gitignored.
> After sharing a password in chat, rotate it in the Neon console under Role -> Reset password.
