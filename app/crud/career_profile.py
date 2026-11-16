from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.analyzer import CandidateProfile, known_skills
from app.models.career_profile import CareerProfile
from app.schemas.career_profile import CareerProfileRead, CareerProfileUpdate


def get_profile(db: Session, user_id: int) -> CareerProfile | None:
    return db.scalar(select(CareerProfile).where(CareerProfile.user_id == user_id))


def save_profile(db: Session, user_id: int, data: CareerProfileUpdate) -> CareerProfile:
    """Create or replace the user's profile."""
    profile = get_profile(db, user_id)
    if profile is None:
        profile = CareerProfile(user_id=user_id)
        db.add(profile)
    for field, value in data.model_dump().items():
        setattr(profile, field, value)
    db.commit()
    db.refresh(profile)
    return profile


def candidate(profile: CareerProfile | None) -> CandidateProfile:
    """The analyzer's view of a stored profile (empty if there is none)."""
    if profile is None:
        return CandidateProfile()
    return CandidateProfile(
        skills=list(profile.skills or []),
        years_experience=profile.years_experience,
        cv_text=profile.cv_text,
        headline=profile.headline,
        target_role=profile.target_role,
    )


def to_read(profile: CareerProfile | None) -> CareerProfileRead:
    known = known_skills(candidate(profile))
    return CareerProfileRead(
        headline=profile.headline if profile else "",
        target_role=profile.target_role if profile else "",
        years_experience=profile.years_experience if profile else None,
        skills=list(profile.skills or []) if profile else [],
        cv_text=profile.cv_text if profile else "",
        recognized_skills=sorted(known.names),
        unrecognized_skills=known.custom,
        updated_at=profile.updated_at if profile else None,
    )
