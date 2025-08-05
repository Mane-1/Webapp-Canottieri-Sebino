# File: routers/authentication.py
from fastapi import APIRouter, Request, Depends, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import models, security
from database import get_db

router = APIRouter(tags=["Autenticazione"])
templates = Jinja2Templates(directory="templates")

@router.get("/login", response_class=HTMLResponse)
async def login_form(request: Request):
    return templates.TemplateResponse("auth/login.html", {"request": request})

@router.post("/login", response_class=RedirectResponse)
async def login(request: Request, db: Session = Depends(get_db), username: str = Form(...), password: str = Form(...)):
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user or not security.verify_password(password, user.hashed_password):
        return templates.TemplateResponse("auth/login.html", {"request": request, "error_message": "Username o password non validi"}, status_code=status.HTTP_401_UNAUTHORIZED)
    request.session["user_id"] = user.id
    return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/logout", response_class=RedirectResponse)
async def logout(request: Request):
    request.session.pop("user_id", None)
    return RedirectResponse(url="/login?message=Logout effettuato", status_code=status.HTTP_303_SEE_OTHER)