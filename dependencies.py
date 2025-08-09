# File: dependencies.py
# Descrizione: Contiene le dipendenze riutilizzabili per le route FastAPI,
# in particolare per l'autenticazione e l'autorizzazione degli utenti.

from fastapi import Request, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from database import get_db
import models

async def get_current_user(request: Request, db: Session = Depends(get_db)) -> models.User:
    """
    Dipendenza per ottenere l'utente attualmente autenticato dalla sessione.
    Se l'utente non è loggato o non esiste, solleva un'eccezione HTTP
    che causa un redirect alla pagina di login.
    """
    user_id = request.session.get("user_id")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            detail="Non autenticato",
            headers={"Location": "/login"}
        )

    user = db.query(models.User).options(joinedload(models.User.roles)).filter(models.User.id == user_id).first()

    if user is None:
        request.session.pop("user_id", None)
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            detail="Utente non trovato",
            headers={"Location": "/login"}
        )
    return user


async def get_current_admin_user(current_user: models.User = Depends(get_current_user)) -> models.User:
    """
    Dipendenza che verifica se l'utente corrente ha il ruolo di 'admin'.
    Se non è un admin, solleva un'eccezione 403 Forbidden.
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accesso negato. Sono richiesti privilegi di amministratore."
        )
    return current_user


async def get_current_admin_or_coach_user(
    current_user: models.User = Depends(get_current_user),
) -> models.User:
    """Garantisce accesso ad admin e allenatori.

    Solleva 403 se l'utente non possiede almeno uno di questi ruoli."""
    if not (current_user.is_admin or current_user.is_allenatore):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accesso negato. Sono richiesti privilegi di amministratore o allenatore.",
        )
    return current_user


async def get_current_admin_or_coach_user(
    current_user: models.User = Depends(get_current_user),
) -> models.User:
    """Garantisce accesso ad admin e allenatori.

    Solleva 403 se l'utente non possiede almeno uno di questi ruoli."""
    if not (current_user.is_admin or current_user.is_allenatore):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accesso negato. Sono richiesti privilegi di amministratore o allenatore.",
        )
    return current_user
