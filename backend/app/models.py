import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def new_id() -> str:
    return str(uuid.uuid4())


class CandidateStatus(str, enum.Enum):
    new = "new"
    reviewed = "reviewed"
    hired = "hired"
    rejected = "rejected"
    archived = "archived"


class UserRole(str, enum.Enum):
    reviewer = "reviewer"
    admin = "admin"


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), nullable=False, default=UserRole.reviewer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    scores: Mapped[list["Score"]] = relationship(back_populates="reviewer")


class Candidate(Base):
    __tablename__ = "candidates"
    __table_args__ = (
        Index("ix_candidates_status_role", "status", "role_applied"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)
    role_applied: Mapped[str] = mapped_column(String, nullable=False, index=True)
    status: Mapped[CandidateStatus] = mapped_column(
        Enum(CandidateStatus), nullable=False, default=CandidateStatus.new, index=True
    )
    skills_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    internal_notes: Mapped[str | None] = mapped_column(Text)
    ai_summary: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    scores: Mapped[list["Score"]] = relationship(back_populates="candidate", cascade="all, delete-orphan")


class Score(Base):
    __tablename__ = "scores"
    __table_args__ = (
        Index("ix_scores_candidate_created", "candidate_id", "created_at"),
        Index("ix_scores_candidate_reviewer", "candidate_id", "reviewer_id"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    candidate_id: Mapped[str] = mapped_column(String, ForeignKey("candidates.id"), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String, nullable=False, index=True)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    reviewer_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False, index=True)
    note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    candidate: Mapped[Candidate] = relationship(back_populates="scores")
    reviewer: Mapped[User] = relationship(back_populates="scores")
