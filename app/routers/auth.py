from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import authenticate_admin, create_access_token, get_current_admin
from app.database import get_db
from app.models import AdminUser
from app.schemas import AdminLoginRequest, AdminUserRead, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: AdminLoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    admin = authenticate_admin(db, payload.identifier, payload.password)
    if admin is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    return TokenResponse(access_token=create_access_token(str(admin.id)))


@router.get("/me", response_model=AdminUserRead)
def me(current_admin: AdminUser = Depends(get_current_admin)) -> AdminUser:
    return current_admin

