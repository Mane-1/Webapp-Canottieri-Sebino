"""Calendar service helpers for ICS tokens."""
from secrets import token_urlsafe
from sqlalchemy.orm import Session
import models

def generate_token() -> str:
    """Return a new calendar token."""
    return token_urlsafe(32)

def get_or_create_calendar_token(db: Session, user: models.User) -> str:
    """Return user's calendar token, creating it if missing."""
    if not user.calendar_token:
        user.calendar_token = generate_token()
        db.commit()
        db.refresh(user)
    return user.calendar_token

def rotate_calendar_token(db: Session, user: models.User) -> str:
    """Generate and assign a new calendar token for the user."""
    user.calendar_token = generate_token()
    db.commit()
    db.refresh(user)
    return user.calendar_token
