"""Router HTML per la gestione delle attività."""

from datetime import date, datetime
from typing import Optional
from fastapi import APIRouter, Depends, Request, HTTPException, status, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import and_, or_, func
from decimal import Decimal

from database import get_db
from dependencies import get_current_user, require_roles
from models import (
    Activity, ActivityType, QualificationType, ActivityRequirement, 
    ActivityAssignment, UserQualification, User, Role
)
from services.availability import compute_activity_coverage, get_user_activity_hours
from utils.render import render

router = APIRouter(prefix="/attivita", tags=["Attività"])


@router.get("/calendario", response_class=HTMLResponse)
async def activities_calendar(
    request: Request,
    current_user: User = Depends(require_roles("admin", "allenatore", "istruttore")),
    db: Session = Depends(get_db)
):
    """Pagina calendario attività."""
    # Ottieni i tipi di attività per i filtri
    activity_types = db.query(ActivityType).filter(ActivityType.is_active == True).all()
    
    context = {
        "activity_types": activity_types,
        "current_user": current_user
    }
    
    return render(request, "attivita/calendario.html", ctx=context)


@router.get("/gestione", response_class=HTMLResponse)
async def activities_management(
    request: Request,
    current_user: User = Depends(require_roles("admin", "allenatore")),
    db: Session = Depends(get_db),
    # Filtri
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    type_id: Optional[int] = Query(None),
    state: Optional[str] = Query(None),
    payment_state: Optional[str] = Query(None),
    text: Optional[str] = Query(None)
):
    """Pagina gestione attività."""
    # Query base
    query = db.query(Activity).options(
        selectinload(Activity.activity_type),
        selectinload(Activity.requirements).selectinload(ActivityRequirement.qualification_type),
        selectinload(Activity.assignments)
    )
    
    # Applica filtri
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, "%Y-%m-%d").date()
            query = query.filter(Activity.date >= date_from_obj)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, "%Y-%m-%d").date()
            query = query.filter(Activity.date <= date_to_obj)
        except ValueError:
            pass
    
    if type_id:
        if isinstance(type_id, list):
            query = query.filter(Activity.type_id.in_(type_id))
        else:
            query = query.filter(Activity.type_id == type_id)
    
    if state:
        if isinstance(state, list):
            query = query.filter(Activity.state.in_(state))
        else:
            query = query.filter(Activity.state == state)
    
    if payment_state:
        if isinstance(payment_state, list):
            query = query.filter(Activity.payment_state.in_(payment_state))
        else:
            query = query.filter(Activity.payment_state == payment_state)
    
    if text:
        text_filter = f"%{text}%"
        query = query.filter(
            or_(
                Activity.title.ilike(text_filter),
                Activity.short_description.ilike(text_filter),
                Activity.customer_name.ilike(text_filter)
            )
        )
    
    # Ordina per data
    activities = query.order_by(Activity.date.desc()).all()
    
    # Calcola copertura per ogni attività
    for activity in activities:
        assigned, required, percent = compute_activity_coverage(db, activity.id)
        activity.coverage_percentage = percent
        activity.total_required = required
        activity.total_assigned = assigned
    
    # Ottieni i tipi per i filtri
    activity_types = db.query(ActivityType).filter(ActivityType.is_active == True).all()
    
    context = {
        "activities": activities,
        "activity_types": activity_types,
        "current_user": current_user,
        "filters": {
            "date_from": date_from,
            "date_to": date_to,
            "type_id": type_id,
            "state": state,
            "payment_state": payment_state,
            "text": text
        }
    }
    
    return render(request, "attivita/gestione.html", ctx=context)


@router.get("/dettaglio/{activity_id}", response_class=HTMLResponse)
async def activity_detail(
    request: Request,
    activity_id: int,
    current_user: User = Depends(require_roles("admin", "allenatore")),
    db: Session = Depends(get_db)
):
    """Pagina dettaglio attività."""
    activity = db.query(Activity).options(
        selectinload(Activity.activity_type),
        selectinload(Activity.requirements).selectinload(ActivityRequirement.qualification_type),
        selectinload(Activity.assignments).selectinload(ActivityAssignment.user)
    ).filter(Activity.id == activity_id).first()
    
    if not activity:
        raise HTTPException(status_code=404, detail="Attività non trovata")
    
    # Calcola copertura
    assigned, required, percent = compute_activity_coverage(db, activity.id)
    activity.coverage_percentage = percent
    activity.total_required = required
    activity.total_assigned = assigned
    
    # Ottieni utenti disponibili per ogni requisito
    for requirement in activity.requirements:
        assigned_users = [a.user_id for a in activity.assignments if a.requirement_id == requirement.id]
        requirement.assigned_count = len(assigned_users)
        
        # Ottieni utenti qualificati disponibili
        from services.availability import get_available_users_for_requirement
        available_users = get_available_users_for_requirement(
            db, requirement.id, activity.id, assigned_users
        )
        requirement.available_users = available_users
    
    # Ottieni tutti i tipi di qualifica per i filtri
    qualification_types = db.query(QualificationType).filter(QualificationType.is_active == True).all()
    
    context = {
        "activity": activity,
        "qualification_types": qualification_types
    }
    
    return render(request, "attivita/dettaglio.html", ctx=context)


@router.get("/pagamenti", response_class=HTMLResponse)
async def activities_payments(
    request: Request,
    current_user: User = Depends(require_roles("admin", "allenatore")),
    db: Session = Depends(get_db),
    # Filtri
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    payment_state: Optional[str] = Query(None)
):
    """Pagina pagamenti attività."""
    # Query base
    query = db.query(Activity).options(
        selectinload(Activity.activity_type)
    )
    
    # Applica filtri
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, "%Y-%m-%d").date()
            query = query.filter(Activity.date >= date_from_obj)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, "%Y-%m-%d").date()
            query = query.filter(Activity.date <= date_to_obj)
        except ValueError:
            pass
    
    if payment_state:
        query = query.filter(Activity.payment_state == payment_state)
    
    activities = query.order_by(Activity.date.desc()).all()
    
    # Calcola KPI
    total_activities = len(activities)
    total_amount = sum(a.payment_amount or 0 for a in activities)
    
    pending_activities = [a for a in activities if a.payment_state == "da_effettuare"]
    pending_count = len(pending_activities)
    pending_amount = sum(a.payment_amount or 0 for a in pending_activities)
    
    confirmed_activities = [a for a in activities if a.payment_state == "confermato"]
    confirmed_count = len(confirmed_activities)
    confirmed_amount = sum(a.payment_amount or 0 for a in confirmed_activities)
    
    context = {
        "activities": activities,
        "kpi": {
            "total_activities": total_activities,
            "total_amount": total_amount,
            "pending_count": pending_count,
            "pending_amount": pending_amount,
            "confirmed_count": confirmed_count,
            "confirmed_amount": confirmed_amount
        },
        "filters": {
            "date_from": date_from,
            "date_to": date_to,
            "payment_state": payment_state
        }
    }
    
    return render(request, "attivita/pagamenti.html", ctx=context, user=current_user)


@router.get("/estrazioni", response_class=HTMLResponse)
async def activities_extractions(
    request: Request,
    current_user: User = Depends(require_roles("admin", "allenatore", "istruttore")),
    db: Session = Depends(get_db),
    # Filtri
    user_id: Optional[int] = Query(None),
    month: Optional[int] = Query(None),
    year: Optional[int] = Query(None)
):
    """Pagina estrazioni ore."""
    # Se l'utente è istruttore, mostra solo le sue ore
    if current_user.is_istruttore and not current_user.is_admin and not current_user.is_allenatore:
        user_id = current_user.id
    
    # Imposta mese e anno di default se non specificati
    if not month:
        month = datetime.now().month
    if not year:
        year = datetime.now().year
    
    # Ottieni le ore
    if user_id:
        hours_data = get_user_activity_hours(db, user_id, month, year)
        user = db.query(User).filter(User.id == user_id).first()
        user_name = f"{user.first_name} {user.last_name}" if user else f"Utente {user_id}"
    else:
        hours_data = []
        user_name = None
    
    # Ottieni lista utenti per il filtro (solo per admin/allenatori)
    users_for_filter = []
    if current_user.is_admin or current_user.is_allenatore:
        users_for_filter = db.query(User).join(UserQualification).filter(
            UserQualification.qualification_type_id.isnot(None)
        ).distinct().all()
    
    context = {
        "hours_data": hours_data,
        "user_name": user_name,
        "month": month,
        "year": year,
        "users_for_filter": users_for_filter,
        "current_user": current_user
    }
    
    return render(request, "attivita/estrazioni.html", ctx=context)


@router.get("/istruttori", response_class=HTMLResponse)
async def instructors_management(
    request: Request,
    current_user: User = Depends(require_roles("admin", "allenatore")),
    db: Session = Depends(get_db),
    qualification_id: Optional[int] = Query(None),
    search_text: Optional[str] = Query(None)
):
    """Pagina gestione istruttori."""
    # Query base per utenti con ruolo istruttore
    query = db.query(User).join(User.roles).join(Role).filter(
        Role.name == "istruttore"
    ).options(
        selectinload(User.roles),
        selectinload(User.qualifications).selectinload(UserQualification.qualification_type)
    )
    
    # Filtra per qualifica se specificata
    if qualification_id:
        query = query.join(UserQualification).filter(
            UserQualification.qualification_type_id == qualification_id
        )
    
    # Filtra per testo di ricerca
    if search_text:
        text_filter = f"%{search_text}%"
        query = query.filter(
            or_(
                User.first_name.ilike(text_filter),
                User.last_name.ilike(text_filter),
                User.email.ilike(text_filter)
            )
        )
    
    instructors = query.all()
    
    # Ottieni tutti i tipi di qualifica per i filtri
    qualification_types = db.query(QualificationType).filter(QualificationType.is_active == True).all()
    
    context = {
        "instructors": instructors,
        "qualification_types": qualification_types,
        "selected_qualification_id": qualification_id,
        "filters": {
            "qualification_id": qualification_id,
            "search_text": search_text
        }
    }
    
    return render(request, "attivita/istruttori.html", ctx=context)


@router.get("/nuova", response_class=HTMLResponse)
async def new_activity_form(
    request: Request,
    current_user: User = Depends(require_roles("admin", "allenatore")),
    db: Session = Depends(get_db)
):
    """Form per creare una nuova attività."""
    # Ottieni i tipi di attività
    activity_types = db.query(ActivityType).filter(ActivityType.is_active == True).all()
    
    # Ottieni i tipi di qualifica
    qualification_types = db.query(QualificationType).filter(QualificationType.is_active == True).all()
    
    context = {
        "activity_types": activity_types,
        "qualification_types": qualification_types,
        "current_user": current_user
    }
    
    return render(request, "attivita/nuova.html", ctx=context)


@router.get("/modifica/{activity_id}", response_class=HTMLResponse)
async def edit_activity_form(
    request: Request,
    activity_id: int,
    current_user: User = Depends(require_roles("admin", "allenatore")),
    db: Session = Depends(get_db)
):
    """Form per modificare un'attività esistente."""
    activity = db.query(Activity).filter(Activity.id == activity_id).first()
    if not activity:
        raise HTTPException(status_code=404, detail="Attività non trovata")
    
    # Ottieni i tipi di attività
    activity_types = db.query(ActivityType).filter(ActivityType.is_active == True).all()
    
    # Ottieni i tipi di qualifica
    qualification_types = db.query(QualificationType).filter(QualificationType.is_active == True).all()
    
    context = {
        "activity": activity,
        "activity_types": activity_types,
        "qualification_types": qualification_types,
        "current_user": current_user
    }
    
    return render(request, "attivita/modifica.html", ctx=context)


@router.post("/modifica/{activity_id}", response_class=HTMLResponse)
async def update_activity(
    request: Request,
    activity_id: int,
    current_user: User = Depends(require_roles("admin", "allenatore")),
    db: Session = Depends(get_db)
):
    """Salva le modifiche a un'attività esistente."""
    # Ottieni i dati dal form
    form_data = await request.form()
    
    # Ottieni l'attività
    activity = db.query(Activity).filter(Activity.id == activity_id).first()
    if not activity:
        raise HTTPException(status_code=404, detail="Attività non trovata")
    
    try:
        # Aggiorna i campi dell'attività
        activity.title = form_data.get("title")
        activity.short_description = form_data.get("short_description")
        activity.type_id = int(form_data.get("type_id"))
        activity.state = form_data.get("state")
        activity.date = datetime.strptime(form_data.get("date"), "%Y-%m-%d").date()
        activity.start_time = datetime.strptime(form_data.get("start_time"), "%H:%M").time()
        activity.end_time = datetime.strptime(form_data.get("end_time"), "%H:%M").time()
        activity.participants_plan = int(form_data.get("participants_plan", 0)) if form_data.get("participants_plan") else 0
        activity.participants_actual = int(form_data.get("participants_actual", 0)) if form_data.get("participants_actual") else 0
        activity.participants_notes = form_data.get("participants_notes")
        activity.customer_name = form_data.get("customer_name")
        activity.customer_email = form_data.get("customer_email")
        activity.contact_name = form_data.get("contact_name")
        activity.contact_phone = form_data.get("contact_phone")
        activity.contact_email = form_data.get("contact_email")
        activity.payment_amount = Decimal(form_data.get("payment_amount", 0)) if form_data.get("payment_amount") else None
        activity.payment_method = form_data.get("payment_method")
        activity.payment_state = form_data.get("payment_state")
        activity.billing_name = form_data.get("billing_name")
        activity.billing_vat_or_cf = form_data.get("billing_vat_or_cf")
        activity.billing_sdi_or_pec = form_data.get("billing_sdi_or_pec")
        activity.billing_address = form_data.get("billing_address")
        
        # Aggiorna il timestamp
        activity.updated_at = datetime.utcnow()
        
        db.commit()
        
        # Redirect alla pagina di gestione con messaggio di successo
        return RedirectResponse(url=f"/attivita/gestione?message=Attività aggiornata con successo", status_code=303)
        
    except Exception as e:
        db.rollback()
        # Redirect con messaggio di errore
        return RedirectResponse(url=f"/attivita/modifica/{activity_id}?error=Errore nell'aggiornamento: {str(e)}", status_code=303)
