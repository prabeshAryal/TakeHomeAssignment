import asyncio
import json
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ..auth import get_current_user, require_admin
from ..database import get_db
from ..models import Candidate, CandidateStatus, Score, User
from ..schemas import (
    CandidateCreate,
    CandidateDetail,
    CandidateListResponse,
    CandidateUpdateNotes,
    ScoreCreate,
    ScoreOut,
    SummaryResponse,
)
from ..services.candidate_service import (
    candidate_to_detail,
    candidate_to_list_item,
    get_candidate_or_none,
    score_to_out,
    search_candidates,
    serialize_skills,
    soft_archive_candidate,
)

router = APIRouter(prefix="/candidates", tags=["candidates"])


@router.get("", response_model=CandidateListResponse)
def list_candidates(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    status_filter: CandidateStatus | None = Query(default=None, alias="status"),
    role_applied: str | None = None,
    skill: str | None = None,
    keyword: str | None = None,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=50),
) -> CandidateListResponse:
    items, total = search_candidates(
        db=db,
        status=status_filter,
        role_applied=role_applied,
        skill=skill,
        keyword=keyword,
        offset=offset,
        limit=limit,
    )
    return CandidateListResponse(
        items=[candidate_to_list_item(candidate) for candidate in items],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.post("", response_model=CandidateDetail, status_code=status.HTTP_201_CREATED)
def create_candidate(
    payload: CandidateCreate,
    admin: Annotated[User, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> CandidateDetail:
    candidate = Candidate(
        name=payload.name,
        email=payload.email.lower(),
        role_applied=payload.role_applied,
        status=payload.status,
        skills_json=serialize_skills(payload.skills),
        internal_notes=payload.internal_notes,
    )
    db.add(candidate)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Candidate email already exists")
    db.refresh(candidate)
    return candidate_to_detail(candidate, admin)


@router.get("/{candidate_id}/stream")
async def stream_candidate_scores(
    candidate_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> StreamingResponse:
    candidate = get_candidate_or_none(db, candidate_id)
    if not candidate or candidate.status == CandidateStatus.archived:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found")

    async def events():
        for _ in range(10):
            db.expire_all()
            fresh_candidate = get_candidate_or_none(db, candidate_id)
            if not fresh_candidate:
                break
            detail = candidate_to_detail(fresh_candidate, current_user)
            payload = json.dumps([score.model_dump(mode="json") for score in detail.scores])
            yield f"event: scores\ndata: {payload}\n\n"
            await asyncio.sleep(2)

    return StreamingResponse(events(), media_type="text/event-stream")


@router.get("/{candidate_id}", response_model=CandidateDetail)
def get_candidate(
    candidate_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> CandidateDetail:
    candidate = get_candidate_or_none(db, candidate_id)
    if not candidate or candidate.status == CandidateStatus.archived:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found")
    return candidate_to_detail(candidate, current_user)


@router.post("/{candidate_id}/scores", response_model=ScoreOut, status_code=status.HTTP_201_CREATED)
def submit_score(
    candidate_id: str,
    payload: ScoreCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ScoreOut:
    candidate = db.get(Candidate, candidate_id)
    if not candidate or candidate.status == CandidateStatus.archived:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found")

    score = Score(
        candidate_id=candidate_id,
        category=payload.category,
        score=payload.score,
        reviewer_id=current_user.id,
        note=payload.note,
    )
    db.add(score)
    db.commit()
    db.refresh(score)
    score.reviewer = current_user
    return score_to_out(score)


@router.post("/{candidate_id}/summary", response_model=SummaryResponse)
async def generate_summary(
    candidate_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> SummaryResponse:
    candidate = get_candidate_or_none(db, candidate_id)
    if not candidate or candidate.status == CandidateStatus.archived:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found")

    await asyncio.sleep(2)
    skills = ", ".join(candidate_to_list_item(candidate).skills) or "no listed skills"
    score_values = [score.score for score in candidate.scores]
    average = sum(score_values) / len(score_values) if score_values else None
    score_text = f" Current average score is {average:.1f}/5." if average else " No reviewer scores have been submitted yet."
    summary = (
        f"{candidate.name} is applying for {candidate.role_applied} with experience in {skills}."
        f"{score_text} The next review should focus on evidence of ownership, communication, and role-specific depth."
    )
    candidate.ai_summary = summary
    db.commit()
    return SummaryResponse(candidate_id=candidate.id, summary=summary)


@router.patch("/{candidate_id}/notes", response_model=CandidateDetail)
def update_internal_notes(
    candidate_id: str,
    payload: CandidateUpdateNotes,
    admin: Annotated[User, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> CandidateDetail:
    candidate = get_candidate_or_none(db, candidate_id)
    if not candidate or candidate.status == CandidateStatus.archived:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found")
    candidate.internal_notes = payload.internal_notes
    db.commit()
    db.refresh(candidate)
    return candidate_to_detail(candidate, admin)


@router.delete("/{candidate_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_candidate(
    candidate_id: str,
    admin: Annotated[User, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    candidate = db.get(Candidate, candidate_id)
    if not candidate or candidate.status == CandidateStatus.archived:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found")
    soft_archive_candidate(candidate)
    db.commit()
