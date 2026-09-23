import hashlib

from sqlalchemy import select

from database import Base, SessionLocal, engine
from models import User


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def main() -> None:
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        existing_user = db.scalar(
            select(User).where(User.email == "student@example.com")
        )

        if existing_user is None:
            db.add(
                User(
                    name="Shrusti Shetty",
                    email="student@example.com",
                    password_hash=hash_password("data260"),
                )
            )
            db.commit()

    print("Database tables created.")
    print("Test login: student@example.com / data260")


if __name__ == "__main__":
    main()