# DealFlow360 — Backend

Modular-monolith backend implementation for DealFlow360 using FastAPI, SQLAlchemy 2.x, PostgreSQL, and Supabase Auth.

## Architecture
See `docs/specs/DealFlow360_Backend_Folder_Structure.txt` for structural specifications.

## Setup
1. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Or on Windows: .venv\Scripts\activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy environment file:
   ```bash
   cp .env.example .env
   ```
4. Run migrations:
   ```bash
   alembic upgrade head
   ```
5. Run server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
