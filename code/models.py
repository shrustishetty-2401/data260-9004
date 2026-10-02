# This allows us to use datetime values for database timestamps.
from datetime import datetime

# These are the SQL column data types and foreign-key helper.
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text

# These create typed SQLAlchemy columns and table relationships.
from sqlalchemy.orm import Mapped, mapped_column, relationship

# This imports the shared SQLAlchemy base class.
from database import Base


# This class represents application users.
class User(Base):
    # This sets the MySQL table name.
    __tablename__ = "users"

    # This creates the automatically generated user ID.
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # This stores the user's name.
    name: Mapped[str] = mapped_column(String(120), nullable=False)

    # This stores a unique user email.
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    # This stores the password hash, never the plain password.
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    # This connects one user to many login sessions.
    sessions: Mapped[list["SessionToken"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )


# This class represents a server-side login session.
class SessionToken(Base):
    # This sets the MySQL session table name.
    __tablename__ = "sessions"

    # This stores the opaque session token.
    id: Mapped[str] = mapped_column(String(128), primary_key=True)

    # This connects the session to its user.
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )

    # This records when the session was created.
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )

    # This records when the session expires.
    expires_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )

    # This connects the session back to its user.
    user: Mapped[User] = relationship(back_populates="sessions")


# This class is the new HW5 related entity.
class Package(Base):
    # This sets the new package table name.
    __tablename__ = "packages"

    # This creates the automatically generated package ID.
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # This stores the main package name.
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    # This stores the package ecosystem, such as Python or npm.
    ecosystem: Mapped[str] = mapped_column(String(120), nullable=False)

    # This creates a unique package code.
    package_code: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
    )

    # This records when the package was created.
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    # This records when the package was last updated.
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # This connects one package to many vulnerabilities.
    vulnerabilities: Mapped[list["Vulnerability"]] = relationship(
        back_populates="package",
    )


# This class represents the main vulnerability entity.
class Vulnerability(Base):
    # This keeps the original HW4 vulnerability table name.
    __tablename__ = "vulnerabilities"

    # This creates the automatically generated vulnerability ID.
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # This connects the vulnerability to a package.
    package_id: Mapped[int] = mapped_column(
        ForeignKey("packages.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # This creates a unique vulnerability code.
    vulnerability_code: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
    )

    # This stores the numeric HW5 field with a default value.
    available_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    # This stores the original HW4 vulnerability title.
    vulnerability_title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # This keeps the original package-name field for HW4 compatibility.
    package_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    # This stores the submitter's email address.
    submitter_email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # This stores the full vulnerability description.
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # This stores the vulnerability category.
    category: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
        index=True,
    )

    # This records whether the user accepted the terms.
    terms_accepted: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
    )

    # This records the original submission time.
    submission_date: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )

    # This records when the vulnerability was created.
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    # This records when the vulnerability was last updated.
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # This connects the vulnerability back to its package.
    package: Mapped["Package"] = relationship(
        back_populates="vulnerabilities",
    )

    # This keeps the existing HW4 related-items relationship.
    related_items: Mapped[list["RelatedItem"]] = relationship(
        back_populates="vulnerability",
        cascade="all, delete-orphan",
    )


# This class represents the original HW4 related notes.
class RelatedItem(Base):
    # This keeps the original related-items table name.
    __tablename__ = "related_items"

    # This creates the automatically generated related-item ID.
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # This connects the note to a vulnerability.
    vulnerability_id: Mapped[int] = mapped_column(
        ForeignKey("vulnerabilities.id"),
        nullable=False,
        index=True,
    )

    # This stores the related note text.
    related_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # This connects the note back to its vulnerability.
    vulnerability: Mapped[Vulnerability] = relationship(
        back_populates="related_items",
    )