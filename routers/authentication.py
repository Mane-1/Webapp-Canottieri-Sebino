# File: routers/authentication.py
from typing import Optional

from fastapi import APIRouter, Request, Depends, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import models, security
from database import get_db
from dependencies import get_optional_user
from schemas.auth import LoginInput

router = APIRouter(tags=["Autenticazione"])
templates = Jinja2Templates(directory="templates")


@router.get("/login", response_class=HTMLResponse)
async def login_form(
    request: Request,
    current_user: Optional[models.User] = Depends(get_optional_user),
):
    """Renderizza la pagina di login."""
    return templates.TemplateResponse(
        "auth/login.html", {"request": request, "current_user": current_user}
    )


@router.post("/login", response_class=RedirectResponse)
async def login(
    request: Request,
    creds: LoginInput = Depends(LoginInput.as_form),
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_optional_user),
):
    """Autentica l'utente e avvia la sessione."""
    db_user = db.query(models.User).filter(models.User.username == creds.username).first()
    if not db_user or not security.verify_password(creds.password, db_user.hashed_password):
        return templates.TemplateResponse(
            "auth/login.html",
            {
                "request": request,
                "current_user": current_user,
                "error_message": "Username o password non validi",
            },
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
    request.session["user_id"] = db_user.id
    return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/logout", response_class=RedirectResponse)
async def logout(request: Request) -> RedirectResponse:
    """Termina la sessione corrente e reindirizza al login."""
    request.session.pop("user_id", None)
    return RedirectResponse(
        url="/login?message=Logout effettuato",
        status_code=status.HTTP_303_SEE_OTHER,
    )
