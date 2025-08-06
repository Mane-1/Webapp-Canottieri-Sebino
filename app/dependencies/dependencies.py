# app/dependencies/dependencies.py
from fastapi import Request, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.database.database import get_db
from app import models

templates = None  # viene settato in app/main.py se vuoi centralizzare

async def get_current_user(request: Request, db: Session = Depends(get_db)) -> models.User:
    user_id = request.session.get("user_id")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            detail="Non autenticato",
            headers={"Location": "/login"},
        )
    user = db.query(models.User).options(joinedload(models.User.roles))\
             .filter(models.User.id==user_id).first()
    if not user:
        request.session.pop("user_id", None)
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            detail="Utente non trovato",
            headers={"Location": "/login"},
        )
    return user

async def get_current_admin_user(current_user: models.User = Depends(get_current_user)) -> models.User:
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accesso negato.")
    return current_user
