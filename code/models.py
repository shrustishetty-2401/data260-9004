from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    sessions: Mapped[list["SessionToken"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )


class SessionToken(Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )

    user: Mapped[User] = relationship(back_populates="sessions")


class Vulnerability(Base):
    __tablename__ = "vulnerabilities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    vulnerability_title: Mapped[str] = mapped_column(String(255), nullable=False)
    package_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    submitter_email: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    terms_accepted: Mapped[bool] = mapped_column(Boolean, nullable=False)
    submission_date: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )

    related_items: Mapped[list["RelatedItem"]] = relationship(
        back_populates="vulnerability",
        cascade="all, delete-orphan",
    )


class RelatedItem(Base):
    __tablename__ = "related_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    vulnerability_id: Mapped[int] = mapped_column(
        ForeignKey("vulnerabilities.id"),
        nullable=False,
        index=True,
    )
    related_text: Mapped[str] = mapped_column(Text, nullable=False)

    vulnerability: Mapped[Vulnerability] = relationship(
        back_populates="related_items",
    )