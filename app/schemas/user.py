from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator

from app.core.validators import validate_password_strength


class UserCreate(BaseModel):
    """Schema for creating a new user."""

    email: EmailStr
    password: str
    full_name: str | None = None

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        return validate_password_strength(v)


class UserUpdate(BaseModel):
    """Schema for updating an existing user."""

    email: EmailStr | None = None
    password: str | None = None
    full_name: str | None = None

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str | None) -> str | None:
        if v is not None:
            return validate_password_strength(v)
        return v


class UserResponse(BaseModel):
    """Schema for user response (public fields only)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    full_name: str | None
    is_active: bool
    created_at: datetime


class UserInDB(UserResponse):
    """Schema for user with hashed password (internal use)."""
    hashed_password: str
