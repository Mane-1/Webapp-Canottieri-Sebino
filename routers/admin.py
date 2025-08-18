# File: routers/admin.py
from typing import List, Optional
from datetime import date, timedelta
from fastapi import APIRouter, Request, Depends, Form, Query, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from fastapi.templating import Jinja2Templates
import models, security
from database import get_db
from dependencies import get_current_admin_user

router = APIRouter(prefix="/admin", tags=["Amministrazione"])
templates = Jinja2Templates(directory="templates")


@router.get("/users", response_class=HTMLResponse)
async def admin_users_list(request: Request, db: Session = Depends(get_db),
                           admin_user: models.User = Depends(get_current_admin_user), role_ids: List[int] = Query([]),
                           categories: List[str] = Query([]), enrollment_year_str: Optional[str] = Query(None),
                           cert_expiring: bool = Query(False), sort_by: str = Query("last_name"),
                           sort_dir: str = Query("asc")):
    query = db.query(models.User).options(joinedload(models.User.roles))
    enrollment_year = int(enrollment_year_str) if enrollment_year_str and enrollment_year_str.isdigit() else None

    # Applica filtri
    if role_ids: query = query.join(models.user_roles).filter(models.user_roles.c.role_id.in_(role_ids))
    if enrollment_year: query = query.filter(models.User.enrollment_year == enrollment_year)
    if cert_expiring: query = query.filter(models.User.certificate_expiration <= (date.today() + timedelta(days=60)))

    # Applica ordinamento
    if sort_by not in ['category']:  # Ordina nel DB solo se non è una property calcolata
        if sort_by == 'name':
            order_logic = [models.User.last_name.desc(), models.User.first_name.desc()] if sort_dir == "desc" else [
                models.User.last_name.asc(), models.User.first_name.asc()]
            query = query.order_by(*order_logic)
        else:
            sort_column = getattr(models.User, sort_by, models.User.last_name)
            query = query.order_by(sort_column.desc() if sort_dir == "desc" else sort_column.asc())

    users = query.all()

    # Filtro e ordinamento in Python per le property calcolate
    if categories: users = [user for user in users if user.category in categories]
    if sort_by == 'category':
        users.sort(key=lambda u: u.category or "", reverse=(sort_dir == 'desc'))

    all_roles = db.query(models.Role).order_by(models.Role.name).all()
    all_years = sorted([y[0] for y in db.query(models.User.enrollment_year).distinct().all() if y[0] is not None],
                       reverse=True)
    all_users_for_categories = db.query(models.User).options(joinedload(models.User.roles)).all()
    all_categories = sorted(
        list(set(u.category for u in all_users_for_categories if u.category and u.category != "N/D")))

    return templates.TemplateResponse("admin/users_list.html",
                                      {"request": request, "users": users, "current_user": admin_user,
                                       "all_roles": all_roles, "all_categories": all_categories, "all_years": all_years,
                                       "current_filters": {"role_ids": role_ids, "categories": categories,
                                                           "enrollment_year": enrollment_year,
                                                           "cert_expiring": cert_expiring}, "sort_by": sort_by,
                                       "sort_dir": sort_dir, "today": date.today()})


@router.get("/users/add", response_class=HTMLResponse)
async def admin_add_user_form(request: Request, db: Session = Depends(get_db),
                              admin_user: models.User = Depends(get_current_admin_user)):
    roles = db.query(models.Role).order_by(models.Role.name).all()
    return templates.TemplateResponse("admin/user_add.html",
                                      {"request": request, "current_user": admin_user, "all_roles": roles, "user": {},
                                       "user_role_ids": set()})


@router.post("/users/add", response_class=RedirectResponse)
async def admin_add_user(db: Session = Depends(get_db), admin_user: models.User = Depends(get_current_admin_user),
                         username: str = Form(...), password: str = Form(...), first_name: str = Form(...),
                         last_name: str = Form(...), date_of_birth: date = Form(...), roles_ids: List[int] = Form(...),
                         email: Optional[str] = Form(None), phone_number: Optional[str] = Form(None),
                         tax_code: Optional[str] = Form(None), enrollment_year_str: Optional[str] = Form(None),
                         membership_date_str: Optional[str] = Form(None),
                         certificate_expiration_str: Optional[str] = Form(None), address: Optional[str] = Form(None),
                         manual_category: Optional[str] = Form(None)):
    enrollment_year = int(enrollment_year_str) if enrollment_year_str else None
    membership_date = date.fromisoformat(membership_date_str) if membership_date_str else None
    certificate_expiration = date.fromisoformat(certificate_expiration_str) if certificate_expiration_str else None
    if email and db.query(models.User).filter(models.User.email == email).first(): return RedirectResponse(
        url="/admin/users/add?error=Email già in uso", status_code=status.HTTP_303_SEE_OTHER)
    if db.query(models.User).filter(models.User.username == username).first(): return RedirectResponse(
        url="/admin/users/add?error=Username già in uso", status_code=status.HTTP_303_SEE_OTHER)
    if not roles_ids: return RedirectResponse(url="/admin/users/add?error=È necessario selezionare almeno un ruolo.",
                                              status_code=status.HTTP_303_SEE_OTHER)
    selected_roles = db.query(models.Role).filter(models.Role.id.in_(roles_ids)).all()
    new_user = models.User(username=username, hashed_password=security.get_password_hash(password),
                           first_name=first_name, last_name=last_name, date_of_birth=date_of_birth,
                           roles=selected_roles, email=email, phone_number=phone_number, tax_code=tax_code,
                           enrollment_year=enrollment_year, membership_date=membership_date,
                           certificate_expiration=certificate_expiration, address=address,
                           manual_category=manual_category)
    db.add(new_user)
    db.commit()
    return RedirectResponse(url="/admin/users?message=Utente creato con successo",
                            status_code=status.HTTP_303_SEE_OTHER)


@router.get("/users/{user_id}", response_class=HTMLResponse)
async def admin_view_user(user_id: int, request: Request, db: Session = Depends(get_db),
                          admin_user: models.User = Depends(get_current_admin_user)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user: raise HTTPException(status_code=404, detail="Utente non trovato")
    return templates.TemplateResponse("admin/user_detail.html",
                                      {"request": request, "user": user, "current_user": admin_user})


@router.get("/users/{user_id}/edit", response_class=HTMLResponse)
async def admin_edit_user_form(user_id: int, request: Request, db: Session = Depends(get_db),
                               admin_user: models.User = Depends(get_current_admin_user)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user: raise HTTPException(status_code=404, detail="Utente non trovato")
    roles = db.query(models.Role).all()
    user_role_ids = {role.id for role in user.roles}
    return templates.TemplateResponse("admin/user_edit.html",
                                      {"request": request, "user": user, "current_user": admin_user, "all_roles": roles,
                                       "user_role_ids": user_role_ids})


@router.post("/users/{user_id}/edit", response_class=RedirectResponse)
async def admin_edit_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin_user: models.User = Depends(get_current_admin_user),
    first_name: str = Form(...),
    last_name: str = Form(...),
    email: str = Form(...),
    date_of_birth: date = Form(...),
    roles_ids: List[int] = Form([]),
    phone_number: Optional[str] = Form(None),
    tax_code: Optional[str] = Form(None),
    enrollment_year_str: Optional[str] = Form(None),
    membership_date_str: Optional[str] = Form(None),
    certificate_expiration_str: Optional[str] = Form(None),
    address: Optional[str] = Form(None),
    manual_category: Optional[str] = Form(None),
    password: Optional[str] = Form(None),
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utente non trovato")

    enrollment_year = int(enrollment_year_str) if enrollment_year_str else None
    membership_date = (
        date.fromisoformat(membership_date_str) if membership_date_str else None
    )
    certificate_expiration = (
        date.fromisoformat(certificate_expiration_str)
        if certificate_expiration_str
        else None
    )

    user.first_name, user.last_name, user.email, user.date_of_birth = (
        first_name,
        last_name,
        email,
        date_of_birth,
    )
    user.phone_number, user.tax_code, user.enrollment_year, user.membership_date = (
        phone_number,
        tax_code,
        enrollment_year,
        membership_date,
    )
    user.certificate_expiration, user.address = certificate_expiration, address
    user.manual_category = manual_category if manual_category else None
    if password:
        user.hashed_password = security.get_password_hash(password)
        user.failed_login_attempts = 0
        user.is_suspended = False
    user.roles = db.query(models.Role).filter(models.Role.id.in_(roles_ids)).all()
    db.commit()
    return RedirectResponse(url=f"/admin/users/{user_id}", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/users/{user_id}/delete", response_class=RedirectResponse)
async def admin_delete_user(user_id: int, db: Session = Depends(get_db),
                            admin_user: models.User = Depends(get_current_admin_user)):
    if user_id == admin_user.id: return RedirectResponse(url="/admin/users?error=Non puoi eliminare te stesso.",
                                                         status_code=status.HTTP_303_SEE_OTHER)
    user_to_delete = db.query(models.User).filter(models.User.id == user_id).first()
    if user_to_delete:
        db.delete(user_to_delete)
        db.commit()
    return RedirectResponse(url="/admin/users?message=Utente eliminato.", status_code=status.HTTP_303_SEE_OTHER)