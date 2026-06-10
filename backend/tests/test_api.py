from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth import get_password_hash
from app.database import Base, get_db
from app.main import app
from app.models import Candidate, CandidateStatus, Score, User, UserRole
from app.services.candidate_service import serialize_skills


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db() -> Generator[Session, None, None]:
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestingSessionLocal() as db:
        admin = User(
            email="admin@example.com",
            hashed_password=get_password_hash("password123"),
            role=UserRole.admin,
        )
        reviewer_a = User(
            email="reviewer-a@example.com",
            hashed_password=get_password_hash("password123"),
            role=UserRole.reviewer,
        )
        reviewer_b = User(
            email="reviewer-b@example.com",
            hashed_password=get_password_hash("password123"),
            role=UserRole.reviewer,
        )
        candidate = Candidate(
            name="Test Candidate",
            email="candidate@example.com",
            role_applied="Full Stack Engineer",
            status=CandidateStatus.reviewed,
            skills_json=serialize_skills(["React", "FastAPI"]),
            internal_notes="Admin eyes only",
        )
        db.add_all([admin, reviewer_a, reviewer_b, candidate])
        db.flush()
        db.add_all(
            [
                Score(
                    candidate_id=candidate.id,
                    category="Backend",
                    score=4,
                    reviewer_id=reviewer_a.id,
                    note="Good",
                ),
                Score(
                    candidate_id=candidate.id,
                    category="Frontend",
                    score=2,
                    reviewer_id=reviewer_b.id,
                    note="Needs polish",
                ),
            ]
        )
        db.commit()

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def token_for(client: TestClient, email: str) -> str:
    response = client.post("/auth/login", json={"email": email, "password": "password123"})
    assert response.status_code == 200
    return response.json()["access_token"]


def test_admin_can_create_candidate(client: TestClient) -> None:
    token = token_for(client, "admin@example.com")
    response = client.post(
        "/candidates",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "New Person",
            "email": "new.person@example.com",
            "role_applied": "Backend Engineer",
            "skills": ["Python", "SQLite"],
            "internal_notes": "Imported from assessment round.",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "new.person@example.com"
    assert body["internal_notes"] == "Imported from assessment round."


def test_reviewer_sees_only_own_scores_and_no_internal_notes(client: TestClient) -> None:
    token = token_for(client, "reviewer-a@example.com")
    list_response = client.get("/candidates", headers={"Authorization": f"Bearer {token}"})
    candidate_id = list_response.json()["items"][0]["id"]

    response = client.get(f"/candidates/{candidate_id}", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    body = response.json()
    assert body["internal_notes"] is None
    assert len(body["scores"]) == 1
    assert body["scores"][0]["category"] == "Backend"


def test_registration_always_creates_reviewer_even_if_role_is_sent(client: TestClient) -> None:
    response = client.post(
        "/auth/register",
        json={"email": "new-reviewer@example.com", "password": "password123", "role": "admin"},
    )

    assert response.status_code == 201
    assert response.json()["user"]["role"] == "reviewer"
