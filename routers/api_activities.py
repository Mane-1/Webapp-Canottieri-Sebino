"""Router API per la gestione delle attività."""

from datetime import date, datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import and_, or_, func

from database import get_db
from dependencies import get_current_user, require_roles
from models.activities import (
    Activity, ActivityType, QualificationType, ActivityRequirement, 
    ActivityAssignment, UserQualification
)
from schemas.activities import (
    ActivityCreate, ActivityUpdate, ActivityRead, ActivityFilter,
    ActivityRequirementCreate, ActivityRequirementUpdate, ActivityRequirementRead,
    AssignmentCreate, AssignmentRead, SelfAssignRequest, SelfAssignResponse,
    ExtractionFilter, ExtractionRow, PaymentKPI, PaymentSummary
)
from services.availability import (
    has_time_conflict, compute_activity_coverage, 
    get_available_users_for_requirement, can_user_self_assign,
    get_user_activity_hours
)
import models

router = APIRouter(prefix="/api/attivita", tags=["API Attività"])


# --- ENDPOINTS PER LE ATTIVITÀ ---

@router.get("/", response_model=List[ActivityRead])
async def get_activities(
    current_user: models.User = Depends(require_roles("admin", "allenatore", "istruttore")),
    db: Session = Depends(get_db),
    # Filtri
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    type_ids: Optional[List[int]] = Query(None),
    states: Optional[List[str]] = Query(None),
    payment_states: Optional[List[str]] = Query(None),
    text: Optional[str] = Query(None),
    user_id: Optional[int] = Query(None),
    # Paginazione
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """Ottiene la lista delle attività con filtri."""
    query = db.query(Activity).options(
        selectinload(Activity.activity_type),
        selectinload(Activity.requirements).selectinload(ActivityRequirement.qualification_type),
        selectinload(Activity.assignments).selectinload(ActivityAssignment.user)
    )
    
    # Applica filtri
    if date_from:
        query = query.filter(Activity.date >= date_from)
    if date_to:
        query = query.filter(Activity.date <= date_to)
    if type_ids:
        query = query.filter(Activity.type_id.in_(type_ids))
    if states:
        query = query.filter(Activity.state.in_(states))
    if payment_states:
        query = query.filter(Activity.payment_state.in_(payment_states))
    if text:
        text_filter = f"%{text}%"
        query = query.filter(
            or_(
                Activity.title.ilike(text_filter),
                Activity.short_description.ilike(text_filter),
                Activity.customer_name.ilike(text_filter)
            )
        )
    if user_id:
        query = query.join(ActivityAssignment).filter(ActivityAssignment.user_id == user_id)
    
    # Ordina per data
    activities = query.order_by(Activity.date.desc()).offset(skip).limit(limit).all()
    
    # Calcola copertura per ogni attività
    for activity in activities:
        assigned, required, percent = compute_activity_coverage(db, activity.id)
        activity.coverage_percentage = percent
        activity.total_required = required
        activity.total_assigned = assigned
    
    return activities


@router.post("/", response_model=ActivityRead, status_code=status.HTTP_201_CREATED)
async def create_activity(
    activity_data: ActivityCreate,
    current_user: models.User = Depends(require_roles("admin", "allenatore")),
    db: Session = Depends(get_db)
):
    """Crea una nuova attività."""
    # Verifica che il tipo di attività esista
    activity_type = db.query(ActivityType).filter(ActivityType.id == activity_data.type_id).first()
    if not activity_type:
        raise HTTPException(status_code=400, detail="Tipo di attività non valido")
    
    # Crea l'attività
    activity = Activity(**activity_data.dict())
    db.add(activity)
    db.commit()
    db.refresh(activity)
    
    # Carica le relazioni per la risposta
    db.refresh(activity)
    activity = db.query(Activity).options(
        selectinload(Activity.activity_type),
        selectinload(Activity.requirements),
        selectinload(Activity.assignments)
    ).filter(Activity.id == activity.id).first()
    
    return activity


@router.get("/{activity_id}", response_model=ActivityRead)
async def get_activity(
    activity_id: int,
    current_user: models.User = Depends(require_roles("admin", "allenatore", "istruttore")),
    db: Session = Depends(get_db)
):
    """Ottiene i dettagli di un'attività."""
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
    
    return activity


@router.put("/{activity_id}", response_model=ActivityRead)
async def update_activity(
    activity_id: int,
    activity_data: ActivityUpdate,
    current_user: models.User = Depends(require_roles("admin", "allenatore")),
    db: Session = Depends(get_db)
):
    """Aggiorna un'attività."""
    activity = db.query(Activity).filter(Activity.id == activity_id).first()
    if not activity:
        raise HTTPException(status_code=404, detail="Attività non trovata")
    
    # Aggiorna i campi
    update_data = activity_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(activity, field, value)
    
    activity.updated_at = datetime.now()
    db.commit()
    db.refresh(activity)
    
    # Carica le relazioni per la risposta
    activity = db.query(Activity).options(
        selectinload(Activity.activity_type),
        selectinload(Activity.requirements).selectinload(ActivityRequirement.qualification_type),
        selectinload(Activity.assignments).selectinload(ActivityAssignment.user)
    ).filter(Activity.id == activity.id).first()
    
    # Calcola copertura
    assigned, required, percent = compute_activity_coverage(db, activity.id)
    activity.coverage_percentage = percent
    activity.total_required = required
    activity.total_assigned = assigned
    
    return activity


@router.delete("/{activity_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_activity(
    activity_id: int,
    current_user: models.User = Depends(require_roles("admin", "allenatore")),
    db: Session = Depends(get_db)
):
    """Elimina un'attività."""
    activity = db.query(Activity).filter(Activity.id == activity_id).first()
    if not activity:
        raise HTTPException(status_code=404, detail="Attività non trovata")
    
    db.delete(activity)
    db.commit()


# --- ENDPOINTS PER I REQUISITI ---

@router.get("/{activity_id}/requirements", response_model=List[ActivityRequirementRead])
async def get_activity_requirements(
    activity_id: int,
    current_user: models.User = Depends(require_roles("admin", "allenatore", "istruttore")),
    db: Session = Depends(get_db)
):
    """Ottiene i requisiti di un'attività."""
    requirements = db.query(ActivityRequirement).options(
        selectinload(ActivityRequirement.qualification_type)
    ).filter(ActivityRequirement.activity_id == activity_id).all()
    
    # Calcola il numero di assegnazioni per ogni requisito
    for req in requirements:
        assigned_count = db.query(func.count(ActivityAssignment.id)).filter(
            ActivityAssignment.requirement_id == req.id
        ).scalar() or 0
        req.assigned_count = assigned_count
    
    return requirements


@router.post("/{activity_id}/requirements", response_model=ActivityRequirementRead, status_code=status.HTTP_201_CREATED)
async def create_activity_requirement(
    activity_id: int,
    requirement_data: ActivityRequirementCreate,
    current_user: models.User = Depends(require_roles("admin", "allenatore")),
    db: Session = Depends(get_db)
):
    """Aggiunge un requisito a un'attività."""
    # Verifica che l'attività esista
    activity = db.query(Activity).filter(Activity.id == activity_id).first()
    if not activity:
        raise HTTPException(status_code=404, detail="Attività non trovata")
    
    # Verifica che il tipo di qualifica esista
    qualification_type = db.query(QualificationType).filter(
        QualificationType.id == requirement_data.qualification_type_id
    ).first()
    if not qualification_type:
        raise HTTPException(status_code=400, detail="Tipo di qualifica non valido")
    
    # Crea il requisito
    requirement = ActivityRequirement(
        activity_id=activity_id,
        **requirement_data.dict()
    )
    db.add(requirement)
    db.commit()
    db.refresh(requirement)
    
    # Carica le relazioni per la risposta
    requirement = db.query(ActivityRequirement).options(
        selectinload(ActivityRequirement.qualification_type)
    ).filter(ActivityRequirement.id == requirement.id).first()
    
    return requirement


@router.put("/requirements/{requirement_id}", response_model=ActivityRequirementRead)
async def update_requirement(
    requirement_id: int,
    requirement_data: ActivityRequirementUpdate,
    current_user: models.User = Depends(require_roles("admin", "allenatore")),
    db: Session = Depends(get_db)
):
    """Aggiorna un requisito di attività."""
    requirement = db.query(ActivityRequirement).filter(ActivityRequirement.id == requirement_id).first()
    if not requirement:
        raise HTTPException(status_code=404, detail="Requisito non trovato")
    
    # Verifica che la nuova quantità non sia inferiore alle assegnazioni esistenti
    assigned_count = db.query(func.count(ActivityAssignment.id)).filter(
        ActivityAssignment.requirement_id == requirement_id
    ).scalar() or 0
    
    if requirement_data.quantity < assigned_count:
        raise HTTPException(
            status_code=400, 
            detail=f"Impossibile ridurre la quantità a {requirement_data.quantity}. Ci sono già {assigned_count} assegnazioni."
        )
    
    # Aggiorna il requisito
    requirement.quantity = requirement_data.quantity
    db.commit()
    db.refresh(requirement)
    
    # Carica le relazioni per la risposta
    requirement = db.query(ActivityRequirement).options(
        selectinload(ActivityRequirement.qualification_type)
    ).filter(ActivityRequirement.id == requirement.id).first()
    
    return requirement


@router.delete("/requirements/{requirement_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_requirement(
    requirement_id: int,
    current_user: models.User = Depends(require_roles("admin", "allenatore")),
    db: Session = Depends(get_db)
):
    """Elimina un requisito di attività."""
    requirement = db.query(ActivityRequirement).filter(ActivityRequirement.id == requirement_id).first()
    if not requirement:
        raise HTTPException(status_code=404, detail="Requisito non trovato")
    
    # Verifica che non ci siano assegnazioni
    assigned_count = db.query(func.count(ActivityAssignment.id)).filter(
        ActivityAssignment.requirement_id == requirement_id
    ).scalar() or 0
    
    if assigned_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Impossibile eliminare il requisito. Ci sono {assigned_count} assegnazioni attive."
        )
    
    db.delete(requirement)
    db.commit()


# --- ENDPOINTS PER LE ASSEGNAZIONI ---

@router.get("/{activity_id}/assignments", response_model=List[AssignmentRead])
async def get_activity_assignments(
    activity_id: int,
    current_user: models.User = Depends(require_roles("admin", "allenatore", "istruttore")),
    db: Session = Depends(get_db)
):
    """Ottiene le assegnazioni di un'attività."""
    assignments = db.query(ActivityAssignment).options(
        selectinload(ActivityAssignment.user)
    ).filter(ActivityAssignment.activity_id == activity_id).all()
    
    # Arricchisci con il nome dell'utente
    for assignment in assignments:
        assignment.user_name = assignment.user.full_name
    
    return assignments


@router.post("/assignments", response_model=AssignmentRead, status_code=status.HTTP_201_CREATED)
async def create_assignment(
    assignment_data: AssignmentCreate,
    current_user: models.User = Depends(require_roles("admin", "allenatore")),
    db: Session = Depends(get_db)
):
    """Crea una nuova assegnazione."""
    # Verifica che l'attività esista
    activity = db.query(Activity).filter(Activity.id == assignment_data.activity_id).first()
    if not activity:
        raise HTTPException(status_code=404, detail="Attività non trovata")
    
    # Verifica che il requisito esista e appartenga all'attività
    requirement = db.query(ActivityRequirement).filter(
        and_(
            ActivityRequirement.id == assignment_data.requirement_id,
            ActivityRequirement.activity_id == assignment_data.activity_id
        )
    ).first()
    if not requirement:
        raise HTTPException(status_code=404, detail="Requisito non trovato")
    
    # Verifica che l'utente esista
    user = db.query(models.User).filter(models.User.id == assignment_data.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utente non trovato")
    
    # Verifica che l'utente abbia la qualifica richiesta
    has_qualification = db.query(UserQualification).filter(
        and_(
            UserQualification.user_id == assignment_data.user_id,
            UserQualification.qualification_type_id == requirement.qualification_type_id
        )
    ).first()
    if not has_qualification:
        raise HTTPException(
            status_code=400, 
            detail="L'utente non possiede la qualifica richiesta per questo requisito"
        )
    
    # Verifica che il requisito non sia già pieno
    assigned_count = db.query(func.count(ActivityAssignment.id)).filter(
        ActivityAssignment.requirement_id == assignment_data.requirement_id
    ).scalar() or 0
    
    if assigned_count >= requirement.quantity:
        raise HTTPException(
            status_code=400,
            detail="Il requisito è già completamente coperto"
        )
    
    # Verifica assenza conflitti orari
    if has_time_conflict(db, assignment_data.user_id, activity.date, activity.date):
        raise HTTPException(
            status_code=400,
            detail="Conflitto orario con altri impegni dell'utente"
        )
    
    # Verifica che non ci sia già un'assegnazione per questo utente e requisito
    existing_assignment = db.query(ActivityAssignment).filter(
        and_(
            ActivityAssignment.activity_id == assignment_data.activity_id,
            ActivityAssignment.requirement_id == assignment_data.requirement_id,
            ActivityAssignment.user_id == assignment_data.user_id
        )
    ).first()
    
    if existing_assignment:
        raise HTTPException(
            status_code=400,
            detail="L'utente è già assegnato a questo requisito"
        )
    
    # Crea l'assegnazione
    assignment = ActivityAssignment(**assignment_data.dict())
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    
    # Carica le relazioni per la risposta
    assignment = db.query(ActivityAssignment).options(
        selectinload(ActivityAssignment.user)
    ).filter(ActivityAssignment.id == assignment.id).first()
    
    assignment.user_name = assignment.user.full_name
    
    return assignment


@router.delete("/assignments/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_assignment(
    assignment_id: int,
    current_user: models.User = Depends(require_roles("admin", "allenatore")),
    db: Session = Depends(get_db)
):
    """Elimina un'assegnazione."""
    assignment = db.query(ActivityAssignment).filter(ActivityAssignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assegnazione non trovata")
    
    db.delete(assignment)
    db.commit()


# --- ENDPOINT PER L'AUTOCANDIDATURA ---

@router.post("/{activity_id}/self-assign", response_model=SelfAssignResponse)
async def self_assign_activity(
    activity_id: int,
    self_assign_data: SelfAssignRequest,
    current_user: models.User = Depends(require_roles("admin", "allenatore", "istruttore")),
    db: Session = Depends(get_db)
):
    """Endpoint per l'autocandidatura di un utente a un'attività."""
    # Verifica che l'utente stia tentando di autocandidarsi per se stesso
    if self_assign_data.user_id and self_assign_data.user_id != current_user.id:
        if not (current_user.is_admin or current_user.is_allenatore):
            raise HTTPException(
                status_code=403,
                detail="Puoi autocandidarti solo per te stesso"
            )
    
    user_id = self_assign_data.user_id or current_user.id
    
    # Verifica se può autocandidarsi
    can_assign, message, requirement_id = can_user_self_assign(
        db, user_id, activity_id, self_assign_data.requirement_id
    )
    
    if not can_assign:
        return SelfAssignResponse(
            success=False,
            message=message,
            requirement_id=requirement_id
        )
    
    # Ottieni il requisito
    requirement = db.query(ActivityRequirement).filter(
        ActivityRequirement.id == requirement_id
    ).first()
    
    # Crea l'assegnazione
    assignment = ActivityAssignment(
        activity_id=activity_id,
        requirement_id=requirement_id,
        user_id=user_id
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    
    # Carica le relazioni per la risposta
    assignment = db.query(ActivityAssignment).options(
        selectinload(ActivityAssignment.user)
    ).filter(ActivityAssignment.id == assignment.id).first()
    
    assignment.user_name = assignment.user.full_name
    
    return SelfAssignResponse(
        success=True,
        message="Autocandidatura effettuata con successo",
        assignment=assignment,
        requirement_id=requirement_id
    )


# --- ENDPOINTS PER LE QUALIFICHE ---

@router.get("/qualifiche", response_model=List[QualificationTypeRead])
async def get_qualification_types(
    current_user: models.User = Depends(require_roles("admin", "allenatore", "istruttore")),
    db: Session = Depends(get_db)
):
    """Ottiene la lista dei tipi di qualifica."""
    qualification_types = db.query(QualificationType).filter(QualificationType.is_active == True).all()
    return qualification_types


@router.post("/utenti/{user_id}/qualifiche", status_code=status.HTTP_201_CREATED)
async def assign_user_qualification(
    user_id: int,
    qualification_type_id: int = Query(...),
    current_user: models.User = Depends(require_roles("admin", "allenatore")),
    db: Session = Depends(get_db)
):
    """Assegna una qualifica a un utente."""
    # Verifica che l'utente esista
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utente non trovato")
    
    # Verifica che il tipo di qualifica esista
    qualification_type = db.query(QualificationType).filter(
        QualificationType.id == qualification_type_id
    ).first()
    if not qualification_type:
        raise HTTPException(status_code=404, detail="Tipo di qualifica non trovato")
    
    # Verifica che la qualifica non sia già assegnata
    existing_qualification = db.query(UserQualification).filter(
        and_(
            UserQualification.user_id == user_id,
            UserQualification.qualification_type_id == qualification_type_id
        )
    ).first()
    
    if existing_qualification:
        raise HTTPException(
            status_code=400,
            detail="L'utente possiede già questa qualifica"
        )
    
    # Assegna la qualifica
    user_qualification = UserQualification(
        user_id=user_id,
        qualification_type_id=qualification_type_id
    )
    db.add(user_qualification)
    db.commit()
    
    return {"message": "Qualifica assegnata con successo"}


@router.delete("/utenti/{user_id}/qualifiche/{qualification_type_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_user_qualification(
    user_id: int,
    qualification_type_id: int,
    current_user: models.User = Depends(require_roles("admin", "allenatore")),
    db: Session = Depends(get_db)
):
    """Rimuove una qualifica da un utente."""
    # Verifica che la qualifica sia assegnata
    user_qualification = db.query(UserQualification).filter(
        and_(
            UserQualification.user_id == user_id,
            UserQualification.qualification_type_id == qualification_type_id
        )
    ).first()
    
    if not user_qualification:
        raise HTTPException(status_code=404, detail="Qualifica non trovata")
    
    # Verifica che non ci siano assegnazioni attive che richiedono questa qualifica
    active_assignments = db.query(ActivityAssignment).join(ActivityRequirement).filter(
        and_(
            ActivityAssignment.user_id == user_id,
            ActivityRequirement.qualification_type_id == qualification_type_id
        )
    ).first()
    
    if active_assignments:
        raise HTTPException(
            status_code=400,
            detail="Impossibile rimuovere la qualifica. L'utente ha assegnazioni attive che la richiedono."
        )
    
    db.delete(user_qualification)
    db.commit()


# --- ENDPOINTS PER LE ESTRAZIONI ---

@router.get("/estrazioni", response_model=List[ExtractionRow])
async def get_extractions(
    current_user: models.User = Depends(require_roles("admin", "allenatore", "istruttore")),
    db: Session = Depends(get_db),
    user_id: Optional[int] = Query(None),
    month: Optional[int] = Query(None),
    year: Optional[int] = Query(None)
):
    """Ottiene le estrazioni ore per un utente e periodo specifico."""
    # Se l'utente è istruttore, mostra solo le sue ore
    if current_user.is_istruttore and not current_user.is_admin and not current_user.is_allenatore:
        user_id = current_user.id
    
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id è richiesto")
    
    # Ottieni le ore
    hours_data = get_user_activity_hours(db, user_id, month, year)
    
    # Converti in formato ExtractionRow
    extraction_rows = []
    for data in hours_data:
        extraction_rows.append(ExtractionRow(
            date=data['date'],
            activity_title=data['activity_title'],
            qualification_name=data['qualification_name'],
            hours=data['hours'],
            activity_id=data['activity_id']
        ))
    
    return extraction_rows


# --- ENDPOINTS PER I PAGAMENTI ---

@router.get("/pagamenti", response_model=PaymentSummary)
async def get_payments_summary(
    current_user: models.User = Depends(require_roles("admin", "allenatore")),
    db: Session = Depends(get_db),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    payment_state: Optional[str] = Query(None)
):
    """Ottiene il riepilogo dei pagamenti."""
    # Query base
    query = db.query(Activity).options(
        selectinload(Activity.activity_type)
    )
    
    # Applica filtri
    if date_from:
        query = query.filter(Activity.date >= date_from)
    if date_to:
        query = query.filter(Activity.date <= date_to)
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
    
    kpi = PaymentKPI(
        total_activities=total_activities,
        total_amount=total_amount,
        pending_count=pending_count,
        pending_amount=pending_amount,
        confirmed_count=confirmed_count,
        confirmed_amount=confirmed_amount
    )
    
    return PaymentSummary(kpi=kpi, activities=activities)
