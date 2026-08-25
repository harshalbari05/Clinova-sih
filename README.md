# Clinova Platform

Clinova is a unified healthcare management ecosystem designed to provide secure, role-separated interactions between patients and healthcare facilities.

## Repository Architecture (Monorepo)

```
Clinova-sih/
├── backend/                  # Central FastAPI Backend & PostgreSQL Data Layer
│   ├── app/                  # Application code (API, Core, DB, Models, Schemas, Services)
│   ├── alembic/              # Database schema migrations
│   └── tests/                # Automated backend test suite
├── clients/
│   ├── patient-web/          # React + TypeScript + Vite Patient Portal
│   ├── hospital-web/         # React + TypeScript + Vite Hospital Admin Dashboard
│   └── patient-mobile/       # React Native + Expo + TypeScript Patient Mobile App
├── docs/                     # Architectural documentation & API specifications
└── .github/                  # CI/CD Workflows
```

## Platform Matrix

| Application | Target Users | Technology Stack | Purpose |
| :--- | :--- | :--- | :--- |
| **Backend API** | Shared Central Service | Python 3.12+, FastAPI, SQLAlchemy 2.0 Async, asyncpg | Authentication, business logic, RBAC, and data persistence |
| **Patient Web** | Patients | React, TypeScript, Vite, TanStack Query | Patient registration, authentication, and personal profile |
| **Hospital Web** | Hospital Admins / Staff | React, TypeScript, Vite, TanStack Query | Hospital registration, authentication, and facility dashboard |
| **Patient Mobile** | Patients | React Native, Expo, TypeScript, SecureStore | Mobile-first patient registration, secure authentication, and profile |

## Current Status: Phase 1 Foundation & Authentication
- **Step 1**: Monorepo Structure Initialization (Completed)
- **Step 2**: Backend Foundation & Configuration (Pending)
- **Step 3**: PostgreSQL Async Connection (Pending)
- **Step 4**: SQLAlchemy 2.0 Async Models (Pending)
- **Step 5**: Alembic Migrations (Pending)
- **Step 6**: Authentication & Security Services (Pending)
- **Step 7**: Patient Authentication API (Pending)
- **Step 8**: Hospital Authentication API (Pending)
- **Step 9**: Patient Web Portal (Pending)
- **Step 10**: Hospital Web Dashboard (Pending)
- **Step 11**: Patient Mobile App (Pending)
- **Step 12**: Integration Testing (Pending)
- **Step 13**: Documentation & Cleanup (Pending)
