# Clinova Backend API

Central FastAPI backend service handling authentication, role-based access control, and PostgreSQL data persistence for the Clinova platform.

## Planned Stack (Step 2 to Step 8)
- **Framework**: FastAPI (Async ASGI)
- **Database Engine**: PostgreSQL 18
- **ORM & Driver**: SQLAlchemy 2.0 Async + `asyncpg`
- **Migrations**: Alembic
- **Validation**: Pydantic v2 & `pydantic-settings`
- **Authentication**: Argon2id (`pwdlib[argon2]`) + PyJWT
- **Testing**: `pytest`, `pytest-asyncio`, `httpx`
