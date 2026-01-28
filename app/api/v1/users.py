from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_superuser, get_current_user
from app.core.exceptions import ConflictError, NotFoundError
from app.db.session import get_db
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.user import UserResponse, UserUpdate
from app.services.user_service import UserService

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
    """Get a specific user by ID."""
    # Users can only view their own profile unless superuser
    if current_user.id != user_id and not current_user.is_superuser:
        raise NotFoundError("User not found")

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

    # Exclude password from the update data
    update_data = data.model_dump(exclude_unset=True, exclude={"password"})
    for field, value in update_data.items():
        setattr(user, field, value)
    await service.db.flush()
    await service.db.refresh(user)
    return user


@router.delete("/{user_id}", status_code=204)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_superuser),
):
    """Delete a user (superuser only)."""
    service = UserService(db)

    if not await service.delete(user_id):
        raise NotFoundError("User not found")

    return None
