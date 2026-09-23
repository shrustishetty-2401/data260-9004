from datetime import datetime, timedelta, timezone
import hashlib
import secrets

from sqlalchemy import select
from sqlalchemy.orm import Session

from models import SessionToken, User

SESSION_COOKIE_NAME = "session_token"
SESSION_TTL_SECONDS = 900


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def verify_password(password: str, stored_hash: str) -> bool:
    return hash_password(password) == stored_hash


def create_session(db: Session, user: User) -> tuple[str, datetime]:
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    expires_at = now + timedelta(seconds=SESSION_TTL_SECONDS)
    token = secrets.token_urlsafe(32)

    db.add(
        SessionToken(
            id=token,
            user_id=user.id,
            created_at=now,
            expires_at=expires_at,
        )
    )
    db.commit()

    return token, expires_at


def get_user_from_token(db: Session, token: str | None) -> User | None:
    if not token:
        return None

    session = db.scalar(
        select(SessionToken).where(SessionToken.id == token)
    )

    if session is None:
        return None

    now = datetime.now(timezone.utc).replace(tzinfo=None)

    if session.expires_at <= now:
        db.delete(session)
        db.commit()
        return None

    return session.user


def delete_session(db: Session, token: str | None) -> None:
    if not token:
        return

    session = db.scalar(
        select(SessionToken).where(SessionToken.id == token)
    )

    if session is not None:
        db.delete(session)
        db.commit()