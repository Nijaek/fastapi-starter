# FastAPI Starter — Project Plan

> A production-ready REST API template. Clone it, customize it, ship faster.

## Project Overview

**Project Name:** `fastapi-starter`

**Goal:** Create a reusable FastAPI boilerplate that eliminates repetitive setup and enforces consistent patterns across projects.

**Tech Stack:**
- Python 3.12+
- FastAPI
- SQLAlchemy 2.0 (async)
- Pydantic v2
- PostgreSQL
- Docker & Docker Compose
- Alembic (migrations)
- Pytest (testing)
- Ruff (linting/formatting)

---

## Project Structure

Create this exact folder structure:

```
fastapi-starter/
├── app/
│   ├── __init__.py
│   ├── main.py
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── router.py
│   │       ├── health.py
│   │       ├── auth.py
│   │       └── users.py
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── security.py
│   │   └── exceptions.py
│   │
│   ├── db/
│   │   ├── __init__.py
│   │   ├── session.py
│   │   └── base.py
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   └── user.py
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── common.py
│   │   ├── auth.py
│   │   └── user.py
│   │
│   └── services/
│       ├── __init__.py
│       ├── base.py
│       └── user_service.py
│
├── alembic/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       └── .gitkeep
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_health.py
│   ├── test_auth.py
│   └── test_users.py
│
├── .env.example
├── .gitignore
├── .pre-commit-config.yaml
├── alembic.ini
├── docker-compose.yml
├── docker-compose.dev.yml
├── Dockerfile
├── Makefile
├── pyproject.toml
├── requirements.txt
├── requirements-dev.txt
└── README.md
```

---

## Phase 1: Core Foundation

### Task 1.1: Create `requirements.txt`

```
fastapi==0.111.0
uvicorn[standard]==0.30.0
pydantic==2.7.0
pydantic-settings==2.3.0
sqlalchemy==2.0.30
asyncpg==0.29.0
alembic==1.13.1
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.9
redis==5.0.4
httpx==0.27.0
```

### Task 1.2: Create `requirements-dev.txt`

```
-r requirements.txt
pytest==8.2.0
pytest-asyncio==0.23.6
pytest-cov==5.0.0
ruff==0.4.4
pre-commit==3.7.0
```

### Task 1.3: Create `app/core/config.py`

```python
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Project
    PROJECT_NAME: str = "FastAPI Starter"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10

    # Auth
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    CORS_ORIGINS: list[str] = ["*"]

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
```

### Task 1.4: Create `app/db/session.py`

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.core.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

### Task 1.5: Create `app/db/base.py`

```python
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
```

### Task 1.6: Create `app/models/base.py`

```python
from datetime import datetime
from sqlalchemy import Column, DateTime, Integer
from sqlalchemy.sql import func


class TimestampMixin:
    """Add created_at and updated_at to any model."""
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class BaseModel(TimestampMixin):
    """Base model with id and timestamps."""
    id = Column(Integer, primary_key=True, index=True)
```

### Task 1.7: Create `app/core/exceptions.py`

```python
from fastapi import HTTPException, status


class NotFoundError(HTTPException):
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class BadRequestError(HTTPException):
    def __init__(self, detail: str = "Bad request"):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class UnauthorizedError(HTTPException):
    def __init__(self, detail: str = "Not authenticated"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class ForbiddenError(HTTPException):
    def __init__(self, detail: str = "Not enough permissions"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class ConflictError(HTTPException):
    def __init__(self, detail: str = "Resource already exists"):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)
```

### Task 1.8: Create `app/schemas/common.py`

```python
from pydantic import BaseModel
from typing import Generic, TypeVar
from datetime import datetime

T = TypeVar("T")


class MessageResponse(BaseModel):
    message: str


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    per_page: int
    pages: int


class PaginationParams(BaseModel):
    page: int = 1
    per_page: int = 20


class TimestampSchema(BaseModel):
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
```

### Task 1.9: Create `app/api/v1/health.py`

```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.db.session import get_db
from app.schemas.common import MessageResponse

router = APIRouter()


@router.get("/", response_model=MessageResponse)
async def health_check():
    """Basic health check."""
    return {"message": "healthy"}


@router.get("/ready", response_model=MessageResponse)
async def readiness_check(db: AsyncSession = Depends(get_db)):
    """Readiness check - verifies database connection."""
    try:
        await db.execute(text("SELECT 1"))
        return {"message": "ready"}
    except Exception as e:
        return {"message": f"not ready: {str(e)}"}
```

### Task 1.10: Create `app/api/v1/router.py`

```python
from fastapi import APIRouter

from app.api.v1 import health, auth, users

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
```

### Task 1.11: Create `app/main.py`

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    yield
    # Shutdown


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url=f"{settings.API_V1_PREFIX}/docs",
    redoc_url=f"{settings.API_V1_PREFIX}/redoc",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/")
async def root():
    return {"message": f"{settings.PROJECT_NAME} is running"}
```

---

## Phase 2: Auth System

### Task 2.1: Create `app/models/user.py`

```python
from sqlalchemy import Column, String, Boolean, Integer
from app.db.base import Base
from app.models.base import BaseModel


class User(Base, BaseModel):
    __tablename__ = "users"

    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
```

### Task 2.2: Create `app/schemas/user.py`

```python
from pydantic import BaseModel, EmailStr
from datetime import datetime


# Request schemas
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str | None = None


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    password: str | None = None
    full_name: str | None = None


# Response schemas
class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str | None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UserInDB(UserResponse):
    hashed_password: str
```

### Task 2.3: Create `app/schemas/auth.py`

```python
from pydantic import BaseModel, EmailStr


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: int | None = None
    exp: int | None = None
    type: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str | None = None


class RefreshRequest(BaseModel):
    refresh_token: str
```

### Task 2.4: Create `app/core/security.py`

```python
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import jwt, JWTError
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_token(subject: int, token_type: str, expires_delta: timedelta) -> str:
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode = {
        "sub": str(subject),
        "exp": expire,
        "type": token_type,
    }
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_access_token(subject: int) -> str:
    return create_token(
        subject=subject,
        token_type="access",
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )


def create_refresh_token(subject: int) -> str:
    return create_token(
        subject=subject,
        token_type="refresh",
        expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )


def decode_token(token: str) -> dict[str, Any] | None:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None
```

### Task 2.5: Create `app/services/base.py`

```python
from typing import TypeVar, Generic, Type
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel

from app.db.base import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseService(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType], db: AsyncSession):
        self.model = model
        self.db = db

    async def get(self, id: int) -> ModelType | None:
        result = await self.db.execute(select(self.model).where(self.model.id == id))
        return result.scalar_one_or_none()

    async def get_multi(
        self, skip: int = 0, limit: int = 100
    ) -> tuple[list[ModelType], int]:
        # Get items
        result = await self.db.execute(
            select(self.model).offset(skip).limit(limit)
        )
        items = list(result.scalars().all())
        
        # Get total count
        count_result = await self.db.execute(
            select(func.count()).select_from(self.model)
        )
        total = count_result.scalar_one()
        
        return items, total

    async def create(self, obj_in: CreateSchemaType) -> ModelType:
        db_obj = self.model(**obj_in.model_dump())
        self.db.add(db_obj)
        await self.db.flush()
        await self.db.refresh(db_obj)
        return db_obj

    async def update(self, db_obj: ModelType, obj_in: UpdateSchemaType) -> ModelType:
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        await self.db.flush()
        await self.db.refresh(db_obj)
        return db_obj

    async def delete(self, id: int) -> bool:
        obj = await self.get(id)
        if obj:
            await self.db.delete(obj)
            await self.db.flush()
            return True
        return False
```

### Task 2.6: Create `app/services/user_service.py`

```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.services.base import BaseService
from app.core.security import hash_password, verify_password


class UserService(BaseService[User, UserCreate, UserUpdate]):
    def __init__(self, db: AsyncSession):
        super().__init__(User, db)

    async def get_by_email(self, email: str) -> User | None:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def create(self, obj_in: UserCreate) -> User:
        db_obj = User(
            email=obj_in.email,
            hashed_password=hash_password(obj_in.password),
            full_name=obj_in.full_name,
        )
        self.db.add(db_obj)
        await self.db.flush()
        await self.db.refresh(db_obj)
        return db_obj

    async def authenticate(self, email: str, password: str) -> User | None:
        user = await self.get_by_email(email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    async def update_password(self, user: User, new_password: str) -> User:
        user.hashed_password = hash_password(new_password)
        await self.db.flush()
        await self.db.refresh(user)
        return user
```

### Task 2.7: Create `app/api/deps.py`

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.security import decode_token
from app.core.exceptions import UnauthorizedError
from app.services.user_service import UserService
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    payload = decode_token(token)
    
    if not payload:
        raise UnauthorizedError("Invalid token")
    
    if payload.get("type") != "access":
        raise UnauthorizedError("Invalid token type")
    
    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedError("Invalid token payload")
    
    service = UserService(db)
    user = await service.get(int(user_id))
    
    if not user:
        raise UnauthorizedError("User not found")
    
    if not user.is_active:
        raise UnauthorizedError("User is inactive")
    
    return user


async def get_current_superuser(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    return current_user
```

### Task 2.8: Create `app/api/v1/auth.py`

```python
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.auth import Token, LoginRequest, RegisterRequest, RefreshRequest
from app.schemas.user import UserResponse
from app.services.user_service import UserService
from app.core.security import create_access_token, create_refresh_token, decode_token
from app.core.exceptions import BadRequestError, UnauthorizedError, ConflictError
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    data: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """Register a new user."""
    service = UserService(db)
    
    existing = await service.get_by_email(data.email)
    if existing:
        raise ConflictError("Email already registered")
    
    user = await service.create(data)
    return user


@router.post("/login", response_model=Token)
async def login(
    data: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """Login and get access + refresh tokens."""
    service = UserService(db)
    
    user = await service.authenticate(data.email, data.password)
    if not user:
        raise UnauthorizedError("Invalid email or password")
    
    if not user.is_active:
        raise UnauthorizedError("User is inactive")
    
    return Token(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


@router.post("/login/form", response_model=Token)
async def login_form(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """Login via form (for Swagger UI)."""
    service = UserService(db)
    
    user = await service.authenticate(form_data.username, form_data.password)
    if not user:
        raise UnauthorizedError("Invalid email or password")
    
    return Token(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    data: RefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    """Get new access token using refresh token."""
    payload = decode_token(data.refresh_token)
    
    if not payload or payload.get("type") != "refresh":
        raise UnauthorizedError("Invalid refresh token")
    
    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedError("Invalid token payload")
    
    service = UserService(db)
    user = await service.get(int(user_id))
    
    if not user or not user.is_active:
        raise UnauthorizedError("User not found or inactive")
    
    return Token(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user info."""
    return current_user
```

### Task 2.9: Create `app/api/v1/users.py`

```python
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.user import UserResponse, UserUpdate
from app.schemas.common import PaginatedResponse
from app.services.user_service import UserService
from app.core.exceptions import NotFoundError, ConflictError
from app.api.deps import get_current_user, get_current_superuser
from app.models.user import User

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[UserResponse])
async def list_users(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_superuser),
):
    """List all users (superuser only)."""
    service = UserService(db)
    skip = (page - 1) * per_page
    
    users, total = await service.get_multi(skip=skip, limit=per_page)
    pages = (total + per_page - 1) // per_page
    
    return PaginatedResponse(
        items=users,
        total=total,
        page=page,
        per_page=per_page,
        pages=pages,
    )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific user."""
    service = UserService(db)
    user = await service.get(user_id)
    
    if not user:
        raise NotFoundError("User not found")
    
    return user


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a user (own profile or superuser)."""
    if current_user.id != user_id and not current_user.is_superuser:
        raise NotFoundError("User not found")
    
    service = UserService(db)
    user = await service.get(user_id)
    
    if not user:
        raise NotFoundError("User not found")
    
    # Check email uniqueness if changing
    if data.email and data.email != user.email:
        existing = await service.get_by_email(data.email)
        if existing:
            raise ConflictError("Email already in use")
    
    # Handle password separately
    if data.password:
        await service.update_password(user, data.password)
        data.password = None
    
    updated = await service.update(user, data)
    return updated
```

---

## Phase 3: DevOps & Configuration

### Task 3.1: Create `.env.example`

```
# Project
PROJECT_NAME=FastAPI Starter
DEBUG=true

# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/fastapi_starter

# Auth
SECRET_KEY=your-super-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS
CORS_ORIGINS=["http://localhost:3000"]
```

### Task 3.2: Create `Dockerfile`

```dockerfile
# Build stage
FROM python:3.12-slim as builder

WORKDIR /app

RUN pip install --no-cache-dir --upgrade pip

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.12-slim

WORKDIR /app

# Create non-root user
RUN adduser --disabled-password --gecos "" appuser

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY --chown=appuser:appuser . .

USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Task 3.3: Create `docker-compose.yml`

```yaml
version: "3.8"

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/fastapi_starter
      - SECRET_KEY=dev-secret-key-not-for-production
      - DEBUG=false
    depends_on:
      db:
        condition: service_healthy
    restart: unless-stopped

  db:
    image: postgres:16-alpine
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=fastapi_starter
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
```

### Task 3.4: Create `docker-compose.dev.yml`

```yaml
version: "3.8"

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/fastapi_starter
      - SECRET_KEY=dev-secret-key-not-for-production
      - DEBUG=true
    depends_on:
      db:
        condition: service_healthy
    volumes:
      - .:/app
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  db:
    image: postgres:16-alpine
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=fastapi_starter
    volumes:
      - postgres_data_dev:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  postgres_data_dev:
```

### Task 3.5: Create `Makefile`

```makefile
.PHONY: help dev prod down logs test lint format migrate migration shell

help:
	@echo "Available commands:"
	@echo "  make dev        - Start development environment"
	@echo "  make prod       - Start production environment"
	@echo "  make down       - Stop all containers"
	@echo "  make logs       - View container logs"
	@echo "  make test       - Run tests"
	@echo "  make lint       - Run linter"
	@echo "  make format     - Format code"
	@echo "  make migrate    - Run database migrations"
	@echo "  make migration  - Create new migration (usage: make migration m='message')"
	@echo "  make shell      - Open shell in API container"

dev:
	docker compose -f docker-compose.dev.yml up --build

prod:
	docker compose up --build -d

down:
	docker compose down
	docker compose -f docker-compose.dev.yml down

logs:
	docker compose logs -f

test:
	pytest -v --cov=app tests/

lint:
	ruff check app tests

format:
	ruff format app tests
	ruff check --fix app tests

migrate:
	alembic upgrade head

migration:
	alembic revision --autogenerate -m "$(m)"

shell:
	docker compose exec api /bin/bash
```

### Task 3.6: Create `alembic.ini`

```ini
[alembic]
script_location = alembic
prepend_sys_path = .
version_path_separator = os

[post_write_hooks]

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

### Task 3.7: Create `alembic/env.py`

```python
import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

from app.core.config import settings
from app.db.base import Base
from app.models.user import User  # Import all models here

config = context.config
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

### Task 3.8: Create `pyproject.toml`

```toml
[project]
name = "fastapi-starter"
version = "1.0.0"
description = "A production-ready FastAPI template"
requires-python = ">=3.12"

[tool.ruff]
target-version = "py312"
line-length = 100

[tool.ruff.lint]
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
]
ignore = [
    "E501",  # line too long (handled by formatter)
]

[tool.ruff.lint.isort]
known-first-party = ["app"]

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
```

### Task 3.9: Create `.gitignore`

```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
.venv/
ENV/
env/

# IDE
.idea/
.vscode/
*.swp
*.swo

# Environment
.env
.env.local
.env.*.local

# Testing
.coverage
htmlcov/
.pytest_cache/

# Database
*.db
*.sqlite3

# Logs
*.log

# Docker
docker-compose.override.yml

# OS
.DS_Store
Thumbs.db
```

---

## Phase 4: Testing

### Task 4.1: Create `tests/conftest.py`

```python
import pytest
import asyncio
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.main import app
from app.db.base import Base
from app.db.session import get_db
from app.core.security import create_access_token

# Test database URL (use SQLite for tests)
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
async def setup_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with TestingSessionLocal() as session:
        yield session


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers() -> dict:
    token = create_access_token(subject=1)
    return {"Authorization": f"Bearer {token}"}
```

### Task 4.2: Create `tests/test_health.py`

```python
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    response = await client.get("/api/v1/health/")
    assert response.status_code == 200
    assert response.json() == {"message": "healthy"}


@pytest.mark.asyncio
async def test_readiness_check(client: AsyncClient):
    response = await client.get("/api/v1/health/ready")
    assert response.status_code == 200
```

### Task 4.3: Create `tests/test_auth.py`

```python
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_user(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "password": "testpassword123",
            "full_name": "Test User",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    # First registration
    await client.post(
        "/api/v1/auth/register",
        json={"email": "dupe@example.com", "password": "password123"},
    )
    
    # Duplicate registration
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "dupe@example.com", "password": "password456"},
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_login(client: AsyncClient):
    # Register first
    await client.post(
        "/api/v1/auth/register",
        json={"email": "login@example.com", "password": "password123"},
    )
    
    # Login
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "login@example.com", "password": "password123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_login_invalid_credentials(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@example.com", "password": "wrongpassword"},
    )
    assert response.status_code == 401
```

---

## Phase 5: README

### Task 5.1: Create `README.md`

```markdown
# FastAPI Starter

A production-ready REST API template. Clone it, customize it, ship faster.

## Why This Exists

Every new project shouldn't start from zero. This template solves:

- **Repetitive setup** — Auth, database, Docker already configured
- **Decision fatigue** — Folder structure and patterns pre-decided
- **Inconsistency** — Same patterns across all your projects
- **Slow starts** — Clone and start building features immediately

## Use Cases

### Side Projects & MVPs
Clone → add your domain logic → deploy. Skip the boilerplate phase entirely.

### Take-Home Interviews
Impress with professional project structure. Focus your time on solving the actual problem, not wiring up auth.

### Freelance/Client Work
Start every client project with production-grade foundations. Look professional from commit one.

### Internal Tools
Need a quick CRUD app or dashboard backend? Clone, customize, done.

### Hackathons
When you have 24 hours, spend them on features — not Googling "FastAPI JWT tutorial" again.

### Microservices
Consistent structure across services makes maintenance and onboarding easier.

## Quick Start

```bash
# Clone the template
git clone https://github.com/yourusername/fastapi-starter.git my-project
cd my-project

# Copy environment file
cp .env.example .env

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
| Auth | JWT (access + refresh tokens) |
| Database | PostgreSQL |
| Migrations | Alembic |
| Containers | Docker & Docker Compose |
| Testing | Pytest (async) |
| Linting | Ruff |

## Project Structure

```
app/
├── api/v1/          # Route handlers
├── core/            # Config, security, exceptions
├── db/              # Database setup
├── models/          # SQLAlchemy models
├── schemas/         # Pydantic schemas
└── services/        # Business logic
```

## API Endpoints

### Health
- `GET /api/v1/health/` — Basic health check
- `GET /api/v1/health/ready` — Readiness check (DB connection)

### Auth
- `POST /api/v1/auth/register` — Register new user
- `POST /api/v1/auth/login` — Get tokens
- `POST /api/v1/auth/refresh` — Refresh access token
- `GET /api/v1/auth/me` — Get current user

### Users
- `GET /api/v1/users/` — List users (admin only)
- `GET /api/v1/users/{id}` — Get user
- `PATCH /api/v1/users/{id}` — Update user

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

## Customizing

1. **Update config** — Edit `app/core/config.py` with your settings
2. **Add models** — Create new models in `app/models/`
3. **Add schemas** — Create Pydantic schemas in `app/schemas/`
4. **Add services** — Business logic in `app/services/`
5. **Add routes** — New endpoints in `app/api/v1/`
6. **Register routes** — Add to `app/api/v1/router.py`

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `SECRET_KEY` | JWT signing key | Required |
| `DEBUG` | Enable debug mode | `false` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token TTL | `30` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token TTL | `7` |

## License

MIT — Use it however you want.
```

---

## Completion Checklist

- [ ] All files created per structure
- [ ] `make dev` starts successfully
- [ ] Health endpoints respond
- [ ] Auth flow works (register, login, refresh, me)
- [ ] Tests pass
- [ ] Linter passes
- [ ] README is accurate

---

## Notes for Agent

1. Create all `__init__.py` files (can be empty)
2. Ensure imports are correct across modules
3. Run `make dev` to verify everything works
4. Run `make test` to verify tests pass
5. Run `make lint` to verify code quality
