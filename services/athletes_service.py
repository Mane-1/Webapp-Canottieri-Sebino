from __future__ import annotations
from datetime import date, datetime, timezone
from typing import List, Optional, Tuple, Dict
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import extract

import models
from services.attendance_service import get_roster_for_training, compute_status_for_athlete


def current_category_for_user(db: Session, user: models.User, ref: date) -> Optional[models.Categoria]:
    if not user.date_of_birth:
        return None
    age = ref.year - user.date_of_birth.year - (
        (ref.month, ref.day) < (user.date_of_birth.month, user.date_of_birth.day)
    )
    return (
        db.query(models.Categoria)
        .filter(models.Categoria.eta_min <= age, models.Categoria.eta_max >= age)
        .first()
    )


def get_athlete_attendance_stats(
    db: Session, athlete_id: int, year: int, month: int | None = None, tipi: List[str] | None = None
) -> dict:
    trainings_query = db.query(models.Allenamento).filter(
        extract("year", models.Allenamento.data) == year
    )
    if month:
        trainings_query = trainings_query.filter(extract("month", models.Allenamento.data) == month)
    if tipi:
        trainings_query = trainings_query.filter(models.Allenamento.tipo.in_(tipi))
    trainings = trainings_query.options(joinedload(models.Allenamento.categories)).all()

    athlete = db.get(models.User, athlete_id)
    if not athlete:
        raise ValueError("Athlete not found")

    kpi = {"sessions": 0, "present": 0, "absent": 0}
    monthly: dict[int, dict[str, int]] = {}
    by_type: dict[str, dict[str, int]] = {}
    sessions_list: list[dict] = []

    for training in trainings:
        roster = get_roster_for_training(db, training)
        if athlete not in roster:
            continue
        status = compute_status_for_athlete(db, training.id, athlete_id)
        attendance = (
            db.query(models.Attendance)
            .filter_by(training_id=training.id, athlete_id=athlete_id)
            .first()
        )
        if attendance:
            source = attendance.source
            change_count = attendance.change_count
        else:
            source = models.AttendanceSource.system
            change_count = 0
        kpi["sessions"] += 1
        if status == models.AttendanceStatus.present:
            kpi["present"] += 1
        else:
            kpi["absent"] += 1
        month_idx = training.data.month
        monthly.setdefault(month_idx, {"present": 0, "absent": 0})
        if status == models.AttendanceStatus.present:
            monthly[month_idx]["present"] += 1
        else:
            monthly[month_idx]["absent"] += 1
        by_type.setdefault(training.tipo, {"present": 0, "absent": 0})
        if status == models.AttendanceStatus.present:
            by_type[training.tipo]["present"] += 1
        else:
            by_type[training.tipo]["absent"] += 1
        sessions_list.append(
            {
                "date": training.data.isoformat(),
                "tipo": training.tipo,
                "categories": [c.nome for c in training.categories],
                "status": status.value,
                "source": source.value,
                "change_count": change_count,
                "time_range": training.orario,
            }
        )

    presence_rate = kpi["present"] / kpi["sessions"] if kpi["sessions"] else 0

    monthly_list = [
        {"month": m, "present": d.get("present", 0), "absent": d.get("absent", 0)}
        for m, d in sorted(monthly.items())
    ]
    by_type_list = [
        {"type": t, "present": d.get("present", 0), "absent": d.get("absent", 0)}
        for t, d in sorted(by_type.items())
    ]

    return {
        "kpi": {
            "sessions": kpi["sessions"],
            "present": kpi["present"],
            "absent": kpi["absent"],
            "presence_rate": presence_rate,
        },
        "monthly": monthly_list,
        "by_type": by_type_list,
        "sessions": sessions_list,
    }


def get_atleti_e_categorie(db: Session) -> Tuple[List[Dict], List[str]]:
    """Restituisce atleti e categorie per il form di assegnazione barche"""
    # Filtra solo utenti non sospesi (attivi)
    atleti = db.query(models.User).filter(models.User.is_suspended == False).all()
    
    # Estrai le categorie uniche
    categorie = set()
    for atleta in atleti:
        if atleta.manual_category:
            categorie.add(atleta.manual_category)
    
    # Converti atleti in dizionari per il template
    atleti_dict = []
    for atleta in atleti:
        atleti_dict.append({
            'id': atleta.id,
            'first_name': atleta.first_name,
            'last_name': atleta.last_name,
            'category': atleta.manual_category or 'Non specificata'
        })
    
    return atleti_dict, sorted(list(categorie))


def get_equipaggi_by_barca(db: Session, barca_id: int) -> List[models.Equipaggio]:
    """Restituisce tutti gli equipaggi di una barca"""
    return db.query(models.Equipaggio).filter(models.Equipaggio.barca_id == barca_id).all()


def create_equipaggio(db: Session, equipaggio_data: dict) -> models.Equipaggio:
    """Crea un nuovo equipaggio"""
    equipaggio = models.Equipaggio(**equipaggio_data)
    db.add(equipaggio)
    db.commit()
    db.refresh(equipaggio)
    return equipaggio


def update_equipaggio(db: Session, equipaggio_id: int, equipaggio_data: dict) -> Optional[models.Equipaggio]:
    """Aggiorna un equipaggio esistente"""
    equipaggio = db.query(models.Equipaggio).filter(models.Equipaggio.id == equipaggio_id).first()
    if not equipaggio:
        return None
    
    for field, value in equipaggio_data.items():
        setattr(equipaggio, field, value)
    
    equipaggio.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(equipaggio)
    return equipaggio


def delete_equipaggio(db: Session, equipaggio_id: int) -> bool:
    """Elimina un equipaggio"""
    equipaggio = db.query(models.Equipaggio).filter(models.Equipaggio.id == equipaggio_id).first()
    if not equipaggio:
        return False
    
    db.delete(equipaggio)
    db.commit()
    return True


def get_equipaggio_by_id(db: Session, equipaggio_id: int) -> Optional[models.Equipaggio]:
    """Restituisce un equipaggio per ID"""
    return db.query(models.Equipaggio).filter(models.Equipaggio.id == equipaggio_id).first()


def get_atleti_disponibili_for_posto(db: Session, barca_id: int, posto: str, equipaggio_id: int = None) -> List[models.User]:
    """Restituisce gli atleti disponibili per un determinato posto in una barca"""
    # Query base per atleti non sospesi (attivi)
    query = db.query(models.User).filter(models.User.is_suspended == False)
    
    # Escludi atleti già assegnati a questo posto in altri equipaggi della stessa barca
    if equipaggio_id:
        # Se stiamo modificando un equipaggio, escludi solo gli altri equipaggi
        subquery = db.query(models.Equipaggio).filter(
            models.Equipaggio.barca_id == barca_id,
            models.Equipaggio.id != equipaggio_id
        )
    else:
        # Se stiamo creando un nuovo equipaggio, escludi tutti gli equipaggi esistenti
        subquery = db.query(models.Equipaggio).filter(models.Equipaggio.barca_id == barca_id)
    
    # Aggiungi filtri per escludere atleti già assegnati
    if posto == 'capovoga':
        query = query.filter(~models.User.id.in_(subquery.with_entities(models.Equipaggio.capovoga_id)))
    elif posto == 'secondo':
        query = query.filter(~models.User.id.in_(subquery.with_entities(models.Equipaggio.secondo_id)))
    elif posto == 'terzo':
        query = query.filter(~models.User.id.in_(subquery.with_entities(models.Equipaggio.terzo_id)))
    elif posto == 'quarto':
        query = query.filter(~models.User.id.in_(subquery.with_entities(models.Equipaggio.quarto_id)))
    elif posto == 'quinto':
        query = query.filter(~models.User.id.in_(subquery.with_entities(models.Equipaggio.quinto_id)))
    elif posto == 'sesto':
        query = query.filter(~models.User.id.in_(subquery.with_entities(models.Equipaggio.sesto_id)))
    elif posto == 'settimo':
        query = query.filter(~models.User.id.in_(subquery.with_entities(models.Equipaggio.settimo_id)))
    elif posto == 'prodiere':
        query = query.filter(~models.User.id.in_(subquery.with_entities(models.Equipaggio.prodiere_id)))
    elif posto == 'timoniere':
        query = query.filter(~models.User.id.in_(subquery.with_entities(models.Equipaggio.timoniere_id)))
    
    return query.all()
