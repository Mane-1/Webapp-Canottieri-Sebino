from __future__ import annotations
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
import models

ALLOWED_PESI_CATEGORIES = [
    "Cadetto",
    "Ragazzo",
    "Junior",
    "Under 23",
    "Senior",
    "Master",
]


def get_atleti_e_categorie(
    db: Session, allowed_categories: Optional[List[str]] = None
) -> Tuple[List[models.User], List[str]]:
    """Return athletes and available categories, optionally filtering by category."""
    atleti = (
        db.query(models.User)
        .join(models.User.roles)
        .filter(models.Role.name == "atleta")
        .order_by(models.User.last_name)
        .all()
    )
    if allowed_categories:
        atleti = [a for a in atleti if a.category in allowed_categories]
        categorie = allowed_categories
    else:
        categorie = sorted({a.category for a in atleti if a.category != "N/D"})
    return atleti, categorie
