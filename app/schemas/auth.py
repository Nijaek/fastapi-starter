from pydantic import BaseModel, EmailStr, field_validator

from app.core.validators import validate_password_strength


class Token(BaseModel):
    """JWT token response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """JWT token payload."""

    sub: int | None = None
    exp: int | None = None
    type: str | None = None


class LoginRequest(BaseModel):
    """Login request body."""

    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    """User registration request body."""

    email: EmailStr
    password: str
    full_name: str | None = None

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        return validate_password_strength(v)


class RefreshRequest(BaseModel):
    """Token refresh request body."""

    refresh_token: str
