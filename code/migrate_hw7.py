from sqlalchemy import inspect, text

from database import Base, SessionLocal, engine
from models import User
import bcrypt


PASSWORD = "data260"


def column_exists(
    table_name: str,
    column_name: str,
) -> bool:
    columns = inspect(engine).get_columns(table_name)

    return any(column["name"] == column_name for column in columns)


def index_exists(
    table_name: str,
    index_name: str,
) -> bool:
    indexes = inspect(engine).get_indexes(table_name)

    return any(index.get("name") == index_name for index in indexes)


def hashed_password(password: str) -> str:
    return bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt(),
    ).decode("utf-8")


def main() -> None:
    Base.metadata.create_all(bind=engine)

    if not column_exists("users", "username"):
        with engine.begin() as connection:
            connection.execute(
                text(
                    """
                    ALTER TABLE users
                    ADD COLUMN username VARCHAR(120) NULL
                    """
                )
            )

    if not column_exists("users", "role"):
        with engine.begin() as connection:
            connection.execute(
                text(
                    """
                    ALTER TABLE users
                    ADD COLUMN role VARCHAR(20) NULL
                    """
                )
            )

    with engine.begin() as connection:
        connection.execute(
            text(
                """
                UPDATE users
                SET username = SUBSTRING_INDEX(email, '@', 1)
                WHERE username IS NULL
                """
            )
        )

        connection.execute(
            text(
                """
                UPDATE users
                SET role = 'reader'
                WHERE role IS NULL
                """
            )
        )

        connection.execute(
            text(
                """
                ALTER TABLE users
                MODIFY COLUMN username VARCHAR(120) NOT NULL
                """
            )
        )

        connection.execute(
            text(
                """
                ALTER TABLE users
                MODIFY COLUMN role VARCHAR(20) NOT NULL
                """
            )
        )

    if not index_exists("users", "uq_users_username"):
        with engine.begin() as connection:
            connection.execute(
                text(
                    """
                    CREATE UNIQUE INDEX uq_users_username
                    ON users (username)
                    """
                )
            )

    password_hash = hashed_password(PASSWORD)

    with SessionLocal() as db:
        users = [
            {
                "name": "Shrusti Shetty",
                "username": "reader",
                "email": "reader@example.com",
                "role": "reader",
            },
            {
                "name": "HW7 Writer",
                "username": "writer",
                "email": "writer@example.com",
                "role": "writer",
            },
            {
                "name": "HW7 Moderator",
                "username": "moderator",
                "email": "moderator@example.com",
                "role": "moderator",
            },
        ]

        for item in users:
            existing = db.query(User).filter(User.username == item["username"]).first()

            if existing is None:
                db.add(
                    User(
                        name=item["name"],
                        username=item["username"],
                        email=item["email"],
                        password_hash=password_hash,
                        role=item["role"],
                    )
                )
            else:
                existing.name = item["name"]
                existing.email = item["email"]
                existing.password_hash = password_hash
                existing.role = item["role"]

        db.commit()

    print("HW7 users migration completed.")
    print("Password for all test users: data260")
    print("Users: reader, writer, moderator")


if __name__ == "__main__":
    main()
