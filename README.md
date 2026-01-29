# FastAPI Starter

A production-ready REST API template. Clone it, customize it, ship faster.

## Prerequisites

- Docker and Docker Compose
- Make (optional, for convenience commands)
- Python 3.12+ (only for local development without Docker)

## Why This Exists

Every new project shouldn't start from zero. This template solves:

- **Repetitive setup** - Auth, database, Docker already configured
- **Decision fatigue** - Folder structure and patterns pre-decided
- **Inconsistency** - Same patterns across all your projects
- **Slow starts** - Clone and start building features immediately

## Features

- **Modern Python** - Python 3.12+, type hints throughout
- **Async everything** - SQLAlchemy 2.0 async, FastAPI async endpoints
- **Secure by default** - JWT auth with token revocation, strong password policy, rate limiting
- **Production-ready** - Docker, health checks, structured logging
- **Well-tested** - Async pytest setup included

## Quick Start

```bash
# Clone or fork this template
git clone <your-repo-url> my-project
cd my-project

# Copy environment file
cp .env.example .env

# Generate a secure SECRET_KEY and add it to .env
openssl rand -hex 32

# Start everything
make dev

# API running at http://localhost:8000
# Docs at http://localhost:8000/api/v1/docs
```

## What's Included

| Feature | Implementation |
|---------|---------------|
| Framework | FastAPI |
| ORM | SQLAlchemy 2.0 (async) |
| Validation | Pydantic v2 |
| Auth | JWT (access + refresh tokens) with Redis-based revocation |
| Database | PostgreSQL |
| Cache | Redis |
| Migrations | Alembic |
| Containers | Docker & Docker Compose |
| Testing | Pytest (async) |
| Linting | Ruff |
| Rate Limiting | slowapi |

## Project Structure

```
app/
├── api/v1/          # Route handlers
├── core/            # Config, security, exceptions, validators
├── db/              # Database setup
├── models/          # SQLAlchemy models
├── schemas/         # Pydantic schemas
└── services/        # Business logic
```

## API Endpoints

### Health
- `GET /api/v1/health` - Basic health check
- `GET /api/v1/health/ready` - Readiness check (DB connection)

### Auth
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Get tokens (JSON body)
- `POST /api/v1/auth/login/form` - Get tokens (OAuth2 form data)
- `POST /api/v1/auth/refresh` - Refresh access token
- `POST /api/v1/auth/logout` - Revoke refresh token
- `GET /api/v1/auth/me` - Get current user

### Users
- `GET /api/v1/users` - List users (admin only)
- `GET /api/v1/users/{id}` - Get user (own profile or admin)
- `PATCH /api/v1/users/{id}` - Update user (own profile or admin)
- `DELETE /api/v1/users/{id}` - Delete user (admin only)

## Security

This template includes security best practices:

- **Password Policy**: Minimum 12 characters, must contain uppercase, lowercase, digit, and special character
- **Token Revocation**: Redis-based refresh token revocation with logout endpoint
- **IDOR Protection**: Users can only access their own profile unless admin
- **Rate Limiting**: Configurable rate limits on auth endpoints
- **No Default Secrets**: `SECRET_KEY` is required and must be at least 32 characters
- **Security Headers**: X-Content-Type-Options, X-Frame-Options, X-XSS-Protection, Referrer-Policy, Permissions-Policy, HSTS (production only)

## Common Commands

```bash
make dev             # Start dev environment (hot reload)
make prod            # Start production environment
make down            # Stop all containers
make logs            # View container logs
make test            # Run tests
make lint            # Run linter
make format          # Format code
make migrate         # Run database migrations
make migration m="add posts table"  # Create new migration
```

## Testing

```bash
# Run all tests (in Docker)
make test

# Run tests with verbose output
docker compose exec api pytest -v

# Run specific test file
docker compose exec api pytest tests/test_auth.py -v

# Run with coverage
docker compose exec api pytest --cov=app --cov-report=term-missing
```

## Local Development (without Docker)

If you prefer running without Docker:

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Set up environment variables (need local PostgreSQL and Redis)
export DATABASE_URL="postgresql+asyncpg://user:pass@localhost:5432/dbname"
export REDIS_URL="redis://localhost:6379/0"
export SECRET_KEY="your-32-character-secret-key-here"

# Run migrations
alembic upgrade head

# Start the server
uvicorn app.main:app --reload
```

## Customizing

1. **Update config** - Edit `app/core/config.py` with your settings
2. **Add models** - Create new models in `app/models/`
3. **Add schemas** - Create Pydantic schemas in `app/schemas/`
4. **Add services** - Business logic in `app/services/`
5. **Add routes** - New endpoints in `app/api/v1/`
6. **Register routes** - Add to `app/api/v1/router.py`

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection string | Yes |
| `SECRET_KEY` | JWT signing key (min 32 chars) | Yes |
| `REDIS_URL` | Redis connection string (auth + rate limiting) | Yes |
| `DEBUG` | Enable debug mode | No (default: `false`) |
| `CORS_ORIGINS` | Allowed origins (JSON array) | No (default: `[]`, no CORS) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token TTL | No (default: `30`) |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token TTL | No (default: `7`) |
| `RATE_LIMIT_PER_MINUTE` | Auth endpoint rate limit | No (default: `60`) |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | No (default: `INFO`) |
| `PROJECT_NAME` | API title shown in docs | No (default: `FastAPI Starter`) |
| `DB_POOL_SIZE` | Database connection pool size | No (default: `5`) |
| `DB_MAX_OVERFLOW` | Max overflow connections | No (default: `10`) |

## Contributing

Contributions are welcome. Please open an issue first to discuss what you'd like to change.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/improvement`)
3. Make your changes
4. Run tests (`make test`)
5. Commit your changes
6. Push to the branch
7. Open a Pull Request

## License

MIT - Use it however you want.
