# Clinova Architecture Overview

## Phase 1: Foundation & Authentication

Clinova uses a clean monorepo architecture with a centralized Python FastAPI backend serving three independent client applications backed by PostgreSQL.

### Core Entity Relationships

```
USER
 ├── PATIENT  -> patient_profiles (1:1)
 └── HOSPITAL -> hospitals        (1:1)
 └── refresh_tokens               (1:N)
```

### Client Applications

1. **Patient Web (`clients/patient-web`)**:
   - Technology: React + TypeScript + Vite + TanStack Query
   - Audience: Patients accessing through desktop and web browsers

2. **Hospital Web (`clients/hospital-web`)**:
   - Technology: React + TypeScript + Vite + TanStack Query
   - Audience: Hospital administrative and facility personnel

3. **Patient Mobile (`clients/patient-mobile`)**:
   - Technology: React Native + Expo + TypeScript
   - Audience: Patients accessing through mobile devices (iOS / Android)

### Backend Service (`backend/`)

- Framework: FastAPI
- Data Layer: SQLAlchemy 2.0 Async + asyncpg
- Schema Migrations: Alembic
- Cryptography: Argon2id (`pwdlib[argon2]`) + PyJWT
