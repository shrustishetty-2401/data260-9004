from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import get_db
from models import User
from session_auth import (
    SESSION_COOKIE_NAME,
    SESSION_TTL_SECONDS,
    create_session,
    delete_session,
    get_user_from_token,
    verify_password,
)

router = APIRouter(prefix="/api/auth", tags=["authentication"])


class LoginPayload(BaseModel):
    email: str
    password: str


def current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    token = request.cookies.get(SESSION_COOKIE_NAME)
    user = get_user_from_token(db, token)

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Login required",
        )

    return user


@router.post("/login")
def login(
    payload: LoginPayload,
    response: Response,
    db: Session = Depends(get_db),
):
    user = db.scalar(
        select(User).where(User.email == payload.email)
    )

    if user is None or not verify_password(
        payload.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    token, _ = create_session(db, user)

    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        max_age=SESSION_TTL_SECONDS,
        httponly=True,
        samesite="lax",
        secure=False,
    )

    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
    }


@router.get("/me")
def me(user: User = Depends(current_user)):
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
    }


@router.post("/logout")
def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    token = request.cookies.get(SESSION_COOKIE_NAME)
    delete_session(db, token)
    response.delete_cookie(SESSION_COOKIE_NAME)

    return {"message": "Logged out successfully"}