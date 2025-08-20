"""Servizi per la gestione delle disponibilità e conflitti orari."""

from datetime import date, datetime, time
from typing import Tuple, List
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from models.activities import Activity, ActivityRequirement, ActivityAssignment
import models


def has_time_conflict(db: Session, user_id: int, start_dt: datetime, end_dt: datetime) -> bool:
    """
    Verifica se un utente ha impegni sovrapposti nel periodo specificato.
    
    Controlla sovrapposizioni in:
    - Allenamenti (e relative presenze/ruoli)
    - Turni
    - Assegnazioni attività
    
    Args:
        db: Sessione database
        user_id: ID dell'utente
        start_dt: Data/ora di inizio
        end_dt: Data/ora di fine
        
    Returns:
        True se c'è un conflitto, False altrimenti
    """
    # Converti date in datetime per il confronto
    if isinstance(start_dt, date):
        start_dt = datetime.combine(start_dt, time.min)
    if isinstance(end_dt, date):
        end_dt = datetime.combine(end_dt, time.max)
    
    # 1. Controlla conflitti con allenamenti
    allenamenti_conflict = db.query(models.Allenamento).join(
        models.allenamento_coach_association
    ).filter(
        and_(
            models.allenamento_coach_association.c.user_id == user_id,
            models.Allenamento.data == start_dt.date(),
            or_(
                # L'allenamento inizia durante il periodo richiesto
                and_(
                    models.Allenamento.ora_inizio < end_dt.time(),
                    models.Allenamento.ora_inizio >= start_dt.time()
                ),
                # L'allenamento finisce durante il periodo richiesto
                and_(
                    models.Allenamento.ora_fine > start_dt.time(),
                    models.Allenamento.ora_fine <= end_dt.time()
                ),
                # L'allenamento copre completamente il periodo richiesto
                and_(
                    models.Allenamento.ora_inizio <= start_dt.time(),
                    models.Allenamento.ora_fine >= end_dt.time()
                )
            )
        )
    ).first()
    
    if allenamenti_conflict:
        return True
    
    # 2. Controlla conflitti con turni
    turni_conflict = db.query(models.Turno).filter(
        and_(
            models.Turno.user_id == user_id,
            models.Turno.data == start_dt.date(),
            or_(
                # Il turno inizia durante il periodo richiesto
                and_(
                    models.Turno.ora_inizio < end_dt.time(),
                    models.Turno.ora_inizio >= start_dt.time()
                ),
                # Il turno finisce durante il periodo richiesto
                and_(
                    models.Turno.ora_fine > start_dt.time(),
                    models.Turno.ora_fine <= end_dt.time()
                ),
                # Il turno copre completamente il periodo richiesto
                and_(
                    models.Turno.ora_inizio <= start_dt.time(),
                    models.Turno.ora_fine >= end_dt.time()
                )
            )
        )
    ).first()
    
    if turni_conflict:
        return True
    
    # 3. Controlla conflitti con altre assegnazioni attività
    # Escludi l'attività corrente se stiamo aggiornando un'assegnazione esistente
    activities_conflict = db.query(ActivityAssignment).join(Activity).filter(
        and_(
            ActivityAssignment.user_id == user_id,
            Activity.date == start_dt.date(),
            or_(
                # L'attività inizia durante il periodo richiesto
                and_(
                    Activity.start_time < end_dt.time(),
                    Activity.start_time >= start_dt.time()
                ),
                # L'attività finisce durante il periodo richiesto
                and_(
                    Activity.end_time > start_dt.time(),
                    Activity.end_time <= end_dt.time()
                ),
                # L'attività copre completamente il periodo richiesto
                and_(
                    Activity.start_time <= start_dt.time(),
                    Activity.end_time >= end_dt.time()
                )
            )
        )
    ).first()
    
    if activities_conflict:
        return True
    
    return False


def compute_activity_coverage(db: Session, activity_id: int) -> Tuple[int, int, int]:
    """
    Calcola la copertura di un'attività.
    
    Args:
        db: Sessione database
        activity_id: ID dell'attività
        
    Returns:
        Tuple (assigned_total, required_total, percent_0_100)
    """
    # Conta i requisiti totali
    required_total = db.query(func.sum(ActivityRequirement.quantity)).filter(
        ActivityRequirement.activity_id == activity_id
    ).scalar() or 0
    
    # Conta le assegnazioni totali
    assigned_total = db.query(func.count(ActivityAssignment.id)).join(
        ActivityRequirement
    ).filter(
        ActivityRequirement.activity_id == activity_id
    ).scalar() or 0
    
    # Calcola la percentuale
    if required_total == 0:
        percent = 100
    else:
        percent = min(100, int((assigned_total / required_total) * 100))
    
    return assigned_total, required_total, percent


def get_available_users_for_requirement(
    db: Session, 
    requirement_id: int, 
    activity_id: int,
    exclude_user_ids: List[int] = None
) -> List[models.User]:
    """
    Ottiene la lista di utenti disponibili per un requisito specifico.
    
    Args:
        db: Sessione database
        requirement_id: ID del requisito
        activity_id: ID dell'attività
        exclude_user_ids: Lista di user_id da escludere
        
    Returns:
        Lista di utenti disponibili e qualificati
    """
    # Ottieni il requisito
    requirement = db.query(ActivityRequirement).filter(
        ActivityRequirement.id == requirement_id
    ).first()
    
    if not requirement:
        return []
    
    # Ottieni l'attività
    activity = db.query(Activity).filter(Activity.id == activity_id).first()
    
    if not activity:
        return []
    
    # Query base per utenti qualificati
    query = db.query(models.User).join(
        models.UserQualification
    ).filter(
        and_(
            models.UserQualification.qualification_type_id == requirement.qualification_type_id,
            models.User.is_suspended == False
        )
    )
    
    # Escludi utenti specifici
    if exclude_user_ids:
        query = query.filter(~models.User.id.in_(exclude_user_ids))
    
    # Filtra per disponibilità oraria
    available_users = []
    for user in query.all():
        if not has_time_conflict(db, user.id, activity.date, activity.date):
            available_users.append(user)
    
    return available_users


def can_user_self_assign(
    db: Session, 
    user_id: int, 
    activity_id: int,
    requirement_id: int = None
) -> Tuple[bool, str, int]:
    """
    Verifica se un utente può autocandidarsi per un'attività.
    
    Args:
        db: Sessione database
        user_id: ID dell'utente
        activity_id: ID dell'attività
        requirement_id: ID del requisito specifico (opzionale)
        
    Returns:
        Tuple (può_autocandidarsi, messaggio, requirement_id_consigliato)
    """
    # Verifica che l'utente esista
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        return False, "Utente non trovato", 0
    
    # Ottieni l'attività
    activity = db.query(Activity).filter(Activity.id == activity_id).first()
    if not activity:
        return False, "Attività non trovata", 0
    
    # Se è specificato un requisito, verifica solo quello
    if requirement_id:
        requirement = db.query(ActivityRequirement).filter(
            ActivityRequirement.id == requirement_id,
            ActivityRequirement.activity_id == activity_id
        ).first()
        
        if not requirement:
            return False, "Requisito non trovato", 0
        
        # Verifica qualifica
        has_qualification = db.query(models.UserQualification).filter(
            and_(
                models.UserQualification.user_id == user_id,
                models.UserQualification.qualification_type_id == requirement.qualification_type_id
            )
        ).first()
        
        if not has_qualification:
            return False, f"Utente non qualificato per {requirement.qualification_type.name}", requirement_id
        
        # Verifica se il requisito è già pieno
        assigned_count = db.query(func.count(ActivityAssignment.id)).filter(
            ActivityAssignment.requirement_id == requirement_id
        ).scalar() or 0
        
        if assigned_count >= requirement.quantity:
            return False, "Requisito già completamente coperto", requirement_id
        
        # Verifica conflitti orari
        if has_time_conflict(db, user_id, activity.date, activity.date):
            return False, "Conflitto orario con altri impegni", requirement_id
        
        return True, "OK", requirement_id
    
    # Se non è specificato un requisito, trova il primo disponibile
    requirements = db.query(ActivityRequirement).filter(
        ActivityRequirement.activity_id == activity_id
    ).all()
    
    for req in requirements:
        # Verifica qualifica
        has_qualification = db.query(models.UserQualification).filter(
            and_(
                models.UserQualification.user_id == user_id,
                models.UserQualification.qualification_type_id == req.qualification_type_id
            )
        ).first()
        
        if not has_qualification:
            continue
        
        # Verifica se il requisito è già pieno
        assigned_count = db.query(func.count(ActivityAssignment.id)).filter(
            ActivityAssignment.requirement_id == req.id
        ).scalar() or 0
        
        if assigned_count >= req.quantity:
            continue
        
        # Verifica conflitti orari
        if has_time_conflict(db, user_id, activity.date, activity.date):
            continue
        
        return True, "OK", req.id
    
    return False, "Nessun requisito disponibile per cui l'utente è qualificato", 0


def get_user_activity_hours(
    db: Session, 
    user_id: int, 
    month: int = None, 
    year: int = None
) -> List[dict]:
    """
    Ottiene le ore di attività di un utente per un periodo specifico.
    
    Args:
        db: Sessione database
        user_id: ID dell'utente
        month: Mese (1-12)
        year: Anno
        
    Returns:
        Lista di attività con ore
    """
    query = db.query(
        Activity.date,
        Activity.title,
        ActivityRequirement.qualification_type_id,
        ActivityAssignment.hours,
        Activity.id.label('activity_id')
    ).join(
        ActivityRequirement
    ).join(
        ActivityAssignment
    ).filter(
        ActivityAssignment.user_id == user_id
    )
    
    if month:
        query = query.filter(func.extract('month', Activity.date) == month)
    
    if year:
        query = query.filter(func.extract('year', Activity.date) == year)
    
    results = query.order_by(Activity.date).all()
    
    # Arricchisci con i nomi delle qualifiche
    enriched_results = []
    for result in results:
        qualification = db.query(models.QualificationType).filter(
            models.QualificationType.id == result.qualification_type_id
        ).first()
        
        enriched_results.append({
            'date': result.date,
            'activity_title': result.title,
            'qualification_name': qualification.name if qualification else "N/A",
            'hours': result.hours or 0,
            'activity_id': result.activity_id
        })
    
    return enriched_results
