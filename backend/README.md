# Clinova Backend API

Central FastAPI backend service handling authentication, role-based access control, and PostgreSQL data persistence for the Clinova platform.

---

## 1. Prerequisites
- **Python**: 3.12+
- **PostgreSQL**: 15+ (Production/staging relational store)
- **Node.js / npm**: Required for client web applications

---

## 2. Authentication Architecture

Clinova utilizes a secure, stateless JWT Bearer token authentication system with bcrypt password hashing:

```
           [ Client Application ]
                     │
    Bearer Token / HTTP Credentials
                     │
                     ▼
             [ FastAPI Router ]
          (/api/v1/auth/...)
                     │
                     ▼
          [ FastAPI Dependencies ]
            (deps.get_current_user)
                     │
                     ▼
          [ AuthService Layer ]
    (Password verification, JWT generation)
                     │
                     ▼
       [ SQLAlchemy 2.0 Async ORM ]
         (User, Patient, Hospital)
                     │
                     ▼
           [ PostgreSQL Database ]
```

### Key Security Features
- **Stateless JWT Tokens**: Signed with HMAC-SHA256 (`HS256`).
- **Minimum Essential Claims**: Token payload contains `sub` (User UUID), `role`, `user_type`, and `hospital_id` (when applicable). Sensitive medical details are never included in tokens.
- **Bcrypt Hashing**: Passwords are encrypted with individual salts. Passwords and hashes are never returned across any API responses.
- **Dual User Flow**:
  - **Patients**: 1-to-1 relationship with `Patient` demographic profile.
  - **Hospitals**: Associated via `HospitalUser` join table with granular roles (`hospital_admin`, `doctor`, `hospital_staff`).

---

## 3. Environment Configuration

The backend reads configuration from `.env` via `pydantic-settings`. Configure the following variables:

```env
# Application
PROJECT_NAME="Clinova API"
API_V1_STR="/api/v1"
ENVIRONMENT="development"
DEBUG=True

# Database Configuration (PostgreSQL Async)
DATABASE_URL="postgresql+asyncpg://postgres:your_secure_password@localhost:5432/clinova_db"
POSTGRES_SERVER="localhost"
POSTGRES_PORT=5432
POSTGRES_USER="postgres"
POSTGRES_PASSWORD="your_secure_password"
POSTGRES_DB="clinova_db"

# JWT & Authentication Configuration
JWT_SECRET_KEY="your_super_secret_jwt_key_min_32_characters_long"
JWT_ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS Allowed Origins
BACKEND_CORS_ORIGINS="http://localhost:5173,http://localhost:5174,http://127.0.0.1:5173,http://127.0.0.1:5174"
```

---

## 4. Local Environment Setup

### A. Create Python Virtual Environment
From the `backend/` directory:

```powershell
# Windows (PowerShell)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
```

### B. Install Dependencies
```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

### C. Configure Environment Variables
```powershell
# Windows (PowerShell)
Copy-Item .env.example .env

# Linux / macOS
cp .env.example .env
```

---

## 5. Running the Development Server

Start the FastAPI server:

```powershell
uvicorn app.main:app --reload --port 8000
```

The server will be available at `http://localhost:8000`.

---

## 6. Available Authentication Endpoints

| Method | Endpoint | Auth Required | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/auth/patient/register` | No | Register a new patient and user account |
| `POST` | `/api/v1/auth/patient/login` | No | Login patient with email or phone |
| `POST` | `/api/v1/auth/hospital/register` | No | Register a hospital facility and admin user |
| `POST` | `/api/v1/auth/hospital/login` | No | Login hospital staff or admin |
| `GET` | `/api/v1/auth/me` | Bearer JWT | Retrieve profile of authenticated user |
| `POST` | `/api/v1/auth/logout` | No | Stateless logout (client discards token) |
| `GET` | `/api/v1/health` | No | Service health check |
| `GET` | `/api/v1/health/db` | No | Database connection health check |

Interactive OpenAPI documentation:
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 7. Example API Requests

### Patient Registration
```bash
curl -X POST "http://localhost:8000/api/v1/auth/patient/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "patient@example.com",
    "phone": "+919876543210",
    "password": "StrongPassword123!",
    "full_name": "Ramesh Kumar",
    "date_of_birth": "1990-05-15",
    "gender": "male",
    "abha_id": "14-1234-5678-9012"
  }'
```

### Patient Login
```bash
curl -X POST "http://localhost:8000/api/v1/auth/patient/login" \
  -H "Content-Type: application/json" \
  -d '{
    "identifier": "patient@example.com",
    "password": "StrongPassword123!"
  }'
```

### Access Current User Profile (`/me`)
```bash
curl -X GET "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer <YOUR_ACCESS_TOKEN>"
```

### Hospital Registration
```bash
curl -X POST "http://localhost:8000/api/v1/auth/hospital/register" \
  -H "Content-Type: application/json" \
  -d '{
    "hospital_name": "Apollo Multispecialty Hospital",
    "registration_number": "HOSP-MH-2026-001",
    "hospital_phone": "+912223456789",
    "hospital_email": "contact@apollohospital.org",
    "city": "Mumbai",
    "state": "Maharashtra",
    "pincode": "400001",
    "admin_email": "admin@apollohospital.org",
    "admin_password": "AdminSecurePassword123!",
    "admin_phone": "+919812345678",
    "admin_name": "Dr. Sharma"
  }'
```

### Hospital Login
```bash
curl -X POST "http://localhost:8000/api/v1/auth/hospital/login" \
  -H "Content-Type: application/json" \
  -d '{
    "identifier": "admin@apollohospital.org",
    "password": "AdminSecurePassword123!"
  }'
```

### Logout
```bash
curl -X POST "http://localhost:8000/api/v1/auth/logout"
```

---

## 8. Running Automated Tests

Run the complete test suite:

```powershell
pytest -v
```

Run only authentication tests:

```powershell
pytest tests/test_auth.py -v
```
