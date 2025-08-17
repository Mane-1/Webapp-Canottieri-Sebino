from __future__ import annotations
from typing import List, Tuple, Optional
from sqlalchemy.orm import Session, selectinload
import models

def list_barche(
    db: Session,
    tipo_filter: Optional[str] = None,
    status_filter: Optional[str] = None,
    search: str = "",
    sort_by: str = "nome",
    sort_dir: str = "asc",
) -> Tuple[List[models.Barca], List[str]]:
    """Return boats filtered by type, status and search string with eager loading."""
    query = db.query(models.Barca).options(selectinload(models.Barca.atleti_assegnati))
    if tipo_filter:
        query = query.filter(models.Barca.tipo == tipo_filter)
    if status_filter:
        if status_filter == "in_uso":
            query = query.filter(
                models.Barca.in_manutenzione.is_(False),
                models.Barca.fuori_uso.is_(False),
                models.Barca.in_prestito.is_(False),
                models.Barca.in_trasferta.is_(False),
            )
        elif status_filter == "in_manutenzione":
            query = query.filter(models.Barca.in_manutenzione.is_(True))
        elif status_filter == "fuori_uso":
            query = query.filter(models.Barca.fuori_uso.is_(True))
        elif status_filter == "in_prestito":
            query = query.filter(models.Barca.in_prestito.is_(True))
        elif status_filter == "in_trasferta":
            query = query.filter(models.Barca.in_trasferta.is_(True))
    if search:
        query = query.filter(models.Barca.nome.ilike(f"%{search}%"))
    if sort_by != "status":
        sort_column = getattr(models.Barca, sort_by, models.Barca.nome)
        query = query.order_by(
            sort_column.desc() if sort_dir == "desc" else sort_column.asc()
        )
        barche = query.all()
    else:
        barche = query.all()
        barche.sort(key=lambda b: b.status[0], reverse=(sort_dir == "desc"))
    tipi_barca_result = (
        db.query(models.Barca.tipo).distinct().order_by(models.Barca.tipo).all()
    )
    tipi_barca = [t[0] for t in tipi_barca_result]
    return barche, tipi_barca
