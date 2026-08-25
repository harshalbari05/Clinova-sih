# Clinova Backend API

Central FastAPI backend service handling authentication, role-based access control, and PostgreSQL data persistence for the Clinova platform.

---

## 1. Prerequisites
- **Python**: 3.12+
- **PostgreSQL**: 15+ (Required in Step 3 for database migrations & models)
- **Node.js / npm**: Required for client web applications

---

## 2. Local Environment Setup

### A. Create Python Virtual Environment
From the `backend/` directory:

```bash
# Windows (PowerShell)
python -m venv .venv

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
```

### B. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### C. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
# Windows (PowerShell)
Copy-Item .env.example .env

# Linux / macOS
cp .env.example .env
```

---

## 3. Running the Development Server

Start the FastAPI application with auto-reload:

```bash
uvicorn app.main:app --reload --port 8000
```

The server will be available at `http://localhost:8000`.

---

## 4. API Endpoints & Documentation

- **Root Info**: [`http://localhost:8000/`](http://localhost:8000/)
- **Health Check Endpoint**: [`http://localhost:8000/api/v1/health`](http://localhost:8000/api/v1/health)
  ```json
  {
    "status": "ok"
  }
  ```
- **Interactive Swagger UI**: [`http://localhost:8000/docs`](http://localhost:8000/docs)
- **ReDoc API Documentation**: [`http://localhost:8000/redoc`](http://localhost:8000/redoc)
- **OpenAPI JSON Specification**: [`http://localhost:8000/api/v1/openapi.json`](http://localhost:8000/api/v1/openapi.json)

---

## 5. Running Automated Tests

```bash
pytest
```
