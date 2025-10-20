---
name: FastAPI Expert
description: Expert in FastAPI framework for building high-performance async Python APIs. Use when working with FastAPI, async Python, Pydantic, type hints, automatic API documentation, WebSockets, or when the user mentions FastAPI, async APIs, or modern Python web development.
---

# FastAPI Expert

A specialized skill for building high-performance, production-ready APIs with FastAPI. This skill covers async programming, Pydantic models, dependency injection, authentication, and FastAPI best practices.

## Instructions

### Core Workflow

1. **Understand requirements**
   - Identify API type (REST, WebSockets, GraphQL)
   - Determine database needs (async SQLAlchemy, Tortoise-ORM, MongoDB)
   - Understand authentication requirements (OAuth2, JWT)
   - Identify performance requirements

2. **Project structure**
   - Organize with proper router structure
   - Implement dependency injection
   - Use Pydantic models for validation
   - Configure CORS and middleware

3. **Implement features**
   - Create path operations with proper type hints
   - Implement Pydantic schemas for validation
   - Add authentication and authorization
   - Use background tasks for async operations
   - Implement WebSockets if needed

4. **Testing and documentation**
   - Write tests using pytest and httpx
   - Leverage automatic Swagger/OpenAPI docs
   - Configure for production deployment

### FastAPI Project Structure

```
myapp/
├── main.py                 # Application entry point
├── core/
│   ├── config.py          # Settings with Pydantic
│   ├── security.py        # Auth utilities
│   └── dependencies.py    # Shared dependencies
├── api/
│   ├── v1/
│   │   ├── __init__.py
│   │   ├── api.py         # Main API router
│   │   └── endpoints/
│   │       ├── users.py
│   │       ├── auth.py
│   │       └── items.py
├── models/                 # SQLAlchemy models
│   ├── __init__.py
│   ├── user.py
│   └── item.py
├── schemas/                # Pydantic schemas
│   ├── __init__.py
│   ├── user.py
│   └── item.py
├── crud/                   # Database operations
│   ├── __init__.py
│   ├── user.py
│   └── item.py
├── db/
│   ├── base.py            # Database session
│   └── init_db.py         # Initial data
└── tests/
    ├── conftest.py
    ├── test_users.py
    └── test_auth.py
```

### Configuration with Pydantic Settings

```python
# core/config.py
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # App
    PROJECT_NAME: str = "My FastAPI App"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Database
    DATABASE_URL: str

    # CORS
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

### Pydantic Schemas

```python
# schemas/user.py
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    full_name: Optional[str] = Field(None, max_length=100)
    is_active: bool = True

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

    @validator('password')
    def password_strength(cls, v):
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one digit')
        if not any(char.isupper() for char in v):
            raise ValueError('Password must contain at least one uppercase letter')
        return v

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    full_name: Optional[str] = Field(None, max_length=100)
    password: Optional[str] = Field(None, min_length=8)

class UserInDBBase(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # For SQLAlchemy models

class User(UserInDBBase):
    """User response model (excludes password)"""
    pass

class UserInDB(UserInDBBase):
    """User model with hashed password"""
    hashed_password: str
```

### Database Models (SQLAlchemy)

```python
# models/user.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from db.base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

# db/base.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from core.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

Base = declarative_base()

# Dependency
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```

### CRUD Operations

```python
# crud/user.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from models.user import User
from schemas.user import UserCreate, UserUpdate
from core.security import get_password_hash
from fastapi import HTTPException, status

async def get_user(db: AsyncSession, user_id: int) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()

async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()

async def get_users(
    db: AsyncSession, skip: int = 0, limit: int = 100
) -> list[User]:
    result = await db.execute(select(User).offset(skip).limit(limit))
    return result.scalars().all()

async def create_user(db: AsyncSession, user: UserCreate) -> User:
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        hashed_password=hashed_password,
        is_active=user.is_active
    )

    try:
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        return db_user
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email or username already exists"
        )

async def update_user(
    db: AsyncSession, user_id: int, user_update: UserUpdate
) -> User:
    db_user = await get_user(db, user_id)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    update_data = user_update.model_dump(exclude_unset=True)

    if "password" in update_data:
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))

    for field, value in update_data.items():
        setattr(db_user, field, value)

    await db.commit()
    await db.refresh(db_user)
    return db_user

async def delete_user(db: AsyncSession, user_id: int) -> bool:
    db_user = await get_user(db, user_id)
    if not db_user:
        return False

    await db.delete(db_user)
    await db.commit()
    return True
```

### API Endpoints with Proper Type Hints

```python
# api/v1/endpoints/users.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from db.base import get_db
from schemas.user import User, UserCreate, UserUpdate
from crud import user as crud_user
from core.dependencies import get_current_active_user

router = APIRouter()

@router.post("/", response_model=User, status_code=status.HTTP_201_CREATED)
async def create_user(
    *,
    db: Annotated[AsyncSession, Depends(get_db)],
    user_in: UserCreate,
) -> User:
    """
    Create new user.

    - **email**: valid email address (unique)
    - **username**: 3-50 characters (unique)
    - **password**: minimum 8 characters with uppercase, lowercase, and number
    - **full_name**: optional full name
    """
    # Check if user exists
    existing_user = await crud_user.get_user_by_email(db, email=user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists",
        )

    user = await crud_user.create_user(db=db, user=user_in)
    return user

@router.get("/", response_model=list[User])
async def read_users(
    db: Annotated[AsyncSession, Depends(get_db)],
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: Annotated[User, Depends(get_current_active_user)] = None,
) -> list[User]:
    """
    Retrieve users with pagination.

    - **skip**: number of records to skip (default: 0)
    - **limit**: maximum number of records to return (default: 100, max: 100)
    """
    users = await crud_user.get_users(db, skip=skip, limit=limit)
    return users

@router.get("/{user_id}", response_model=User)
async def read_user(
    user_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """
    Get user by ID.
    """
    db_user = await crud_user.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return db_user

@router.patch("/{user_id}", response_model=User)
async def update_user(
    user_id: int,
    user_in: UserUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)] = None,
) -> User:
    """
    Update user.
    """
    # Check authorization (users can only update themselves unless admin)
    if current_user.id != user_id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    db_user = await crud_user.update_user(db, user_id=user_id, user_update=user_in)
    return db_user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)] = None,
) -> None:
    """
    Delete user.
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    success = await crud_user.delete_user(db, user_id=user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
```

### Authentication with JWT

```python
# core/security.py
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

# core/dependencies.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.security import verify_password
from db.base import get_db
from crud import user as crud_user
from schemas.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = await crud_user.get_user(db, user_id=user_id)
    if user is None:
        raise credentials_exception

    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user

# api/v1/endpoints/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta

from db.base import get_db
from core.config import settings
from core.security import create_access_token, verify_password
from crud import user as crud_user
from schemas.user import User

router = APIRouter()

@router.post("/login")
async def login(
    db: AsyncSession = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
):
    """
    OAuth2 compatible token login.
    """
    user = await crud_user.get_user_by_email(db, email=form_data.username)

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": User.model_validate(user)
    }

@router.get("/me", response_model=User)
async def read_users_me(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current user.
    """
    return current_user
```

### Background Tasks

```python
from fastapi import BackgroundTasks
from typing import Annotated

def send_email(email: str, message: str):
    """Simulated email sending"""
    print(f"Sending email to {email}: {message}")
    # Actual email sending logic here

@router.post("/send-notification/")
async def send_notification(
    email: str,
    background_tasks: BackgroundTasks
):
    background_tasks.add_task(send_email, email, "Welcome to our service!")
    return {"message": "Notification sent in the background"}
```

### WebSocket Support

```python
from fastapi import WebSocket, WebSocketDisconnect

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(f"Client #{client_id} says: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"Client #{client_id} left the chat")
```

### Main Application Setup

```python
# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from core.config import settings
from api.v1.api import api_router
from db.base import engine, Base

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown
    await engine.dispose()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
async def root():
    return {"message": "Welcome to FastAPI"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

### Testing

```python
# tests/conftest.py
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from main import app
from db.base import Base, get_db
from core.config import settings

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine(TEST_DATABASE_URL, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()

@pytest_asyncio.fixture
async def client(db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()

# tests/test_users.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_user(client: AsyncClient):
    response = await client.post(
        "/api/v1/users/",
        json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "Test123456",
            "full_name": "Test User"
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["username"] == "testuser"
    assert "id" in data
    assert "hashed_password" not in data

@pytest.mark.asyncio
async def test_read_users(client: AsyncClient):
    # Create a user first
    await client.post(
        "/api/v1/users/",
        json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "Test123456"
        }
    )

    # Login to get token
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "test@example.com", "password": "Test123456"}
    )
    token = response.json()["access_token"]

    # Get users
    response = await client.get(
        "/api/v1/users/",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    assert len(response.json()) > 0
```

## Critical Rules

### Always Do
- Use type hints everywhere (FastAPI requires them)
- Leverage Pydantic for validation and serialization
- Use async/await for all I/O operations
- Implement proper dependency injection
- Use background tasks for long-running operations
- Document all endpoints (FastAPI auto-generates OpenAPI)
- Handle errors with proper HTTP status codes
- Use environment variables for configuration
- Implement proper authentication and authorization

### Never Do
- Never use synchronous database operations
- Never skip type hints (FastAPI won't work properly)
- Never store passwords in plain text
- Never expose sensitive data in responses
- Never ignore Pydantic validation errors
- Never mix sync and async code improperly
- Never hardcode configuration values
- Never skip error handling

## Knowledge Base

- **FastAPI Core**: Path operations, dependencies, middleware, background tasks
- **Async Python**: asyncio, async/await, async database drivers
- **Pydantic**: Models, validation, serialization, settings management
- **SQLAlchemy**: Async ORM, relationships, migrations with Alembic
- **Authentication**: OAuth2, JWT, password hashing
- **Testing**: pytest, pytest-asyncio, httpx
- **Performance**: Async operations, caching, connection pooling
- **Documentation**: Automatic OpenAPI/Swagger generation

## Integration with Other Skills

- **Works with**: Fullstack Guardian, Test Master, DevOps Engineer
- **Complements**: Django Expert (alternative Python framework), Code Documenter

## Best Practices Summary

1. **Type Hints**: Essential for FastAPI functionality
2. **Async Everything**: Use async for I/O operations
3. **Pydantic Models**: Validate all input/output
4. **Dependency Injection**: Use FastAPI's DI system
5. **Auto Documentation**: Leverage automatic OpenAPI docs
6. **Error Handling**: Proper HTTP exceptions
7. **Security**: JWT authentication, password hashing
8. **Testing**: Comprehensive async tests
9. **Performance**: Background tasks, caching, connection pooling
10. **Configuration**: Pydantic Settings for environment management
