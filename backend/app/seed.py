import os
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from .auth import get_password_hash
from .models import Candidate, CandidateStatus, Score, User, UserRole
from .services.candidate_service import serialize_skills


def env_value(name: str, default: str) -> str:
    return os.getenv(name, default).strip()


def seed_database(db: Session) -> None:
    if db.scalar(select(User).limit(1)):
        return

    admin = User(
        email=env_value("DEMO_ADMIN_EMAIL", "admin@example.com").lower(),
        hashed_password=get_password_hash(env_value("DEMO_ADMIN_PASSWORD", "admin1234")),
        role=UserRole.admin,
    )
    reviewer = User(
        email=env_value("DEMO_REVIEWER_EMAIL", "reviewer@example.com").lower(),
        hashed_password=get_password_hash(env_value("DEMO_REVIEWER_PASSWORD", "reviewer1234")),
        role=UserRole.reviewer,
    )
    reviewer_two = User(
        email=env_value("DEMO_REVIEWER2_EMAIL", "reviewer2@example.com").lower(),
        hashed_password=get_password_hash(env_value("DEMO_REVIEWER2_PASSWORD", "reviewer21234")),
        role=UserRole.reviewer,
    )
    db.add_all([admin, reviewer, reviewer_two])
    db.flush()

    now = datetime.now(timezone.utc)
    candidates = [
        Candidate(
            name="Aarav Shrestha",
            email="aarav.shrestha@example.com",
            role_applied="Full Stack Engineer",
            status=CandidateStatus.new,
            skills_json=serialize_skills(["React", "FastAPI", "PostgreSQL"]),
            internal_notes="Strong project portfolio. Ask about async patterns.",
            ai_summary="",
            created_at=now - timedelta(days=1),
        ),
        Candidate(
            name="Maya Gurung",
            email="maya.gurung@example.com",
            role_applied="Backend Engineer",
            status=CandidateStatus.reviewed,
            skills_json=serialize_skills(["Python", "DynamoDB", "Docker"]),
            internal_notes="Good infrastructure experience.",
            ai_summary="Maya looks strongest on backend fundamentals and cloud-oriented data modeling.",
            created_at=now - timedelta(days=2),
        ),
        Candidate(
            name="Nisha Karki",
            email="nisha.karki@example.com",
            role_applied="Frontend Engineer",
            status=CandidateStatus.hired,
            skills_json=serialize_skills(["React", "TypeScript", "Design Systems"]),
            internal_notes="Offer accepted.",
            ai_summary="Nisha is a frontend-heavy candidate with excellent UI systems experience.",
            created_at=now - timedelta(days=5),
        ),
        Candidate(
            name="Samir Rai",
            email="samir.rai@example.com",
            role_applied="Full Stack Engineer",
            status=CandidateStatus.rejected,
            skills_json=serialize_skills(["Node.js", "React", "SQLite"]),
            internal_notes="Technically promising, but not aligned with current role needs.",
            ai_summary="Samir shows broad full-stack exposure, with gaps around production ownership.",
            created_at=now - timedelta(days=8),
        ),
    ]
    db.add_all(candidates)
    db.flush()

    db.add_all(
        [
            Score(
                candidate_id=candidates[1].id,
                category="Backend depth",
                score=4,
                reviewer_id=reviewer.id,
                note="Comfortable with API design and persistence trade-offs.",
            ),
            Score(
                candidate_id=candidates[1].id,
                category="Communication",
                score=5,
                reviewer_id=reviewer_two.id,
                note="Clear and structured responses.",
            ),
            Score(
                candidate_id=candidates[2].id,
                category="Frontend craft",
                score=5,
                reviewer_id=reviewer.id,
                note="Excellent component thinking.",
            ),
        ]
    )
    db.commit()
