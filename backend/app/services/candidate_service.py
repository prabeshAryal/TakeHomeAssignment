import json
from datetime import datetime, timezone

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from ..models import Candidate, CandidateStatus, Score, User, UserRole
from ..schemas import CandidateDetail, CandidateListItem, ScoreOut


def parse_skills(skills_json: str | None) -> list[str]:
    if not skills_json:
        return []
    try:
        value = json.loads(skills_json)
    except json.JSONDecodeError:
        return []
    return [str(skill) for skill in value if str(skill).strip()]


def serialize_skills(skills: list[str]) -> str:
    cleaned = sorted({skill.strip() for skill in skills if skill.strip()}, key=str.lower)
    return json.dumps(cleaned)


def candidate_to_list_item(candidate: Candidate) -> CandidateListItem:
    return CandidateListItem(
        id=candidate.id,
        name=candidate.name,
        email=candidate.email,
        role_applied=candidate.role_applied,
        status=candidate.status,
        skills=parse_skills(candidate.skills_json),
        created_at=candidate.created_at,
    )


def score_to_out(score: Score) -> ScoreOut:
    return ScoreOut(
        id=score.id,
        candidate_id=score.candidate_id,
        category=score.category,
        score=score.score,
        reviewer_id=score.reviewer_id,
        reviewer_email=score.reviewer.email if score.reviewer else None,
        note=score.note,
        created_at=score.created_at,
    )


def candidate_to_detail(candidate: Candidate, viewer: User) -> CandidateDetail:
    scores = candidate.scores
    if viewer.role == UserRole.reviewer:
        scores = [score for score in scores if score.reviewer_id == viewer.id]

    return CandidateDetail(
        **candidate_to_list_item(candidate).model_dump(),
        internal_notes=candidate.internal_notes if viewer.role == UserRole.admin else None,
        ai_summary=candidate.ai_summary,
        scores=[score_to_out(score) for score in sorted(scores, key=lambda item: item.created_at, reverse=True)],
    )


def search_candidates(
    db: Session,
    status: CandidateStatus | None = None,
    role_applied: str | None = None,
    skill: str | None = None,
    keyword: str | None = None,
    offset: int = 0,
    limit: int = 20,
) -> tuple[list[Candidate], int]:
    query = select(Candidate)

    if status:
        query = query.where(Candidate.status == status)
    else:
        query = query.where(Candidate.status != CandidateStatus.archived)

    if role_applied:
        query = query.where(func.lower(Candidate.role_applied) == role_applied.lower())

    if skill:
        query = query.where(func.lower(Candidate.skills_json).like(f"%{skill.lower()}%"))

    if keyword:
        like = f"%{keyword.lower()}%"
        query = query.where(
            or_(
                func.lower(Candidate.name).like(like),
                func.lower(Candidate.email).like(like),
                func.lower(Candidate.role_applied).like(like),
                func.lower(Candidate.skills_json).like(like),
            )
        )

    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    items = db.scalars(query.order_by(Candidate.created_at.desc()).offset(offset).limit(limit)).all()
    return list(items), total


def get_candidate_or_none(db: Session, candidate_id: str) -> Candidate | None:
    return db.scalar(
        select(Candidate)
        .options(selectinload(Candidate.scores).selectinload(Score.reviewer))
        .where(Candidate.id == candidate_id)
    )


def soft_archive_candidate(candidate: Candidate) -> None:
    candidate.status = CandidateStatus.archived
    candidate.deleted_at = datetime.now(timezone.utc)
