from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from .models import CandidateStatus, UserRole


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserOut"


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: EmailStr
    role: UserRole


class CandidateCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    role_applied: str = Field(min_length=1, max_length=120)
    status: CandidateStatus = CandidateStatus.new
    skills: list[str] = Field(default_factory=list)
    internal_notes: str | None = None


class CandidateUpdateNotes(BaseModel):
    internal_notes: str | None = Field(default=None, max_length=5000)


class ScoreCreate(BaseModel):
    category: str = Field(min_length=1, max_length=80)
    score: int = Field(ge=1, le=5)
    note: str | None = Field(default=None, max_length=2000)


class ScoreOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    candidate_id: str
    category: str
    score: int
    reviewer_id: str
    reviewer_email: EmailStr | None = None
    note: str | None
    created_at: datetime


class CandidateListItem(BaseModel):
    id: str
    name: str
    email: EmailStr
    role_applied: str
    status: CandidateStatus
    skills: list[str]
    created_at: datetime


class CandidateListResponse(BaseModel):
    items: list[CandidateListItem]
    total: int
    offset: int
    limit: int


class CandidateDetail(CandidateListItem):
    internal_notes: str | None = None
    ai_summary: str | None = None
    scores: list[ScoreOut] = Field(default_factory=list)


class SummaryResponse(BaseModel):
    candidate_id: str
    summary: str
