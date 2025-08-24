# File: routers/resources.py
from typing import List, Optional
from datetime import date, datetime, timezone
from fastapi import APIRouter, Request, Depends, Form, HTTPException, status, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session, joinedload
from fastapi.templating import Jinja2Templates
import models
from database import get_db
from dependencies import get_current_user, get_current_admin_user, require_roles
from services import barche as barche_service, users as users_service
from services.users import ALLOWED_PESI_CATEGORIES
from utils.parsing import to_float
from services import athletes_service

router = APIRouter(prefix="/risorse", tags=["Risorse"])
mezzi_router = APIRouter(tags=["Mezzi"])  # Router separato per i mezzi senza prefisso
templates = Jinja2Templates(directory="templates")




@router.get("/barche", response_class=HTMLResponse)
async def list_barche(
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    tipo_filter: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None),
    search: str = Query(""),
    sort_by: str = Query("nome"),
    sort_dir: str = Query("asc"),
):
    barche, tipi_barca = barche_service.list_barche(
        db,
        tipo_filter=tipo_filter,
        status_filter=status_filter,
        search=search,
        sort_by=sort_by,
        sort_dir=sort_dir,
    )
    
    # Carica gli equipaggi per tutte le barche
    for barca in barche:
        barca.equipaggi = athletes_service.get_equipaggi_by_barca(db, barca.id)
    barche_assegnate: List[models.Barca] = []
    if not (current_user.is_admin or current_user.is_allenatore):
        barche_assegnate = (
            db.query(models.Barca)
            .join(models.Barca.atleti_assegnati)
            .filter(models.User.id == current_user.id)
            .all()
        )
    stati_barca = [
        ("in_uso", "In uso"),
        ("in_manutenzione", "In manutenzione"),
        ("fuori_uso", "Fuori uso"),
        ("in_prestito", "In prestito"),
        ("in_trasferta", "In trasferta"),
    ]
    return templates.TemplateResponse(
        request,
        "barche/barche_list.html",
        {
            "current_user": current_user,
            "barche": barche,
            "tipi_barca": tipi_barca,
            "stati_barca": stati_barca,
            "barche_assegnate": barche_assegnate,
            "current_filters": {
                "tipo_filter": tipo_filter,
                "status_filter": status_filter,
                "search": search,
            },
            "sort_by": sort_by,
            "sort_dir": sort_dir,
        },
    )


@router.get("/barche/{barca_id}", response_class=HTMLResponse, name="barca_detail")
async def barca_detail(
    barca_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    barca = (
        db.query(models.Barca)
        .options(joinedload(models.Barca.atleti_assegnati), joinedload(models.Barca.equipaggi))
        .filter(models.Barca.id == barca_id)
        .first()
    )
    if not barca:
        raise HTTPException(status_code=404, detail="Barca non trovata")
    if not (
        current_user.is_admin
        or current_user.is_allenatore
        or current_user in barca.atleti_assegnati
    ):
        raise HTTPException(status_code=403, detail="Accesso negato")
    message = request.query_params.get("message")
    return templates.TemplateResponse(
        request,
        "barche/barca_detail.html",
        {"current_user": current_user, "barca": barca, "message": message},
    )


@router.post("/barche/{barca_id}", response_class=RedirectResponse, name="aggiorna_misure_barca")
async def aggiorna_misure_barca(
    barca_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    lunghezza_puntapiedi: Optional[str] = Form(None),
    altezza_puntapiedi: Optional[str] = Form(None),
    apertura_totale: Optional[str] = Form(None),
    altezza_scalmo_sx: Optional[str] = Form(None),
    altezza_scalmo_dx: Optional[str] = Form(None),
    semiapertura_sx: Optional[str] = Form(None),
    semiapertura_dx: Optional[str] = Form(None),
    appruamento_appoppamento: Optional[str] = Form(None),
    gradi_attacco: Optional[str] = Form(None),
    gradi_finale: Optional[str] = Form(None),
    boccola_sx_sopra: Optional[str] = Form(None),
    boccola_dx_sopra: Optional[str] = Form(None),
    rondelle_sx: Optional[str] = Form(None),
    rondelle_dx: Optional[str] = Form(None),
    altezza_carrello: Optional[str] = Form(None),
    avanzamento_guide: Optional[str] = Form(None),
):
    barca = (
        db.query(models.Barca)
        .options(joinedload(models.Barca.atleti_assegnati), joinedload(models.Barca.equipaggi))
        .filter(models.Barca.id == barca_id)
        .first()
    )
    if not barca:
        raise HTTPException(status_code=404, detail="Barca non trovata")
    if not (
        current_user.is_admin
        or current_user.is_allenatore
        or current_user in barca.atleti_assegnati
    ):
        raise HTTPException(status_code=403, detail="Accesso negato")

    barca.lunghezza_puntapiedi = to_float(lunghezza_puntapiedi)
    barca.altezza_puntapiedi = to_float(altezza_puntapiedi)
    barca.apertura_totale = to_float(apertura_totale)
    barca.altezza_scalmo_sx = to_float(altezza_scalmo_sx)
    barca.altezza_scalmo_dx = to_float(altezza_scalmo_dx)
    barca.semiapertura_sx = to_float(semiapertura_sx)
    barca.semiapertura_dx = to_float(semiapertura_dx)
    barca.appruamento_appoppamento = to_float(appruamento_appoppamento)
    barca.gradi_attacco = to_float(gradi_attacco)
    barca.gradi_finale = to_float(gradi_finale)
    barca.boccola_sx_sopra = boccola_sx_sopra
    barca.boccola_dx_sopra = boccola_dx_sopra
    barca.rondelle_sx = rondelle_sx
    barca.rondelle_dx = rondelle_dx
    barca.altezza_carrello = to_float(altezza_carrello)
    barca.avanzamento_guide = to_float(avanzamento_guide)

    db.commit()

    url = request.url_for("barca_detail", barca_id=barca_id)
    url = f"{url}?message=Misure+aggiornate"
    return RedirectResponse(url=url, status_code=status.HTTP_303_SEE_OTHER)


@router.get("/barche/nuova", response_class=HTMLResponse)
async def nuova_barca_form(request: Request, db: Session = Depends(get_db),
                           admin_user: models.User = Depends(get_current_admin_user)):
    atleti, categorie = users_service.get_atleti_e_categorie(db)
    return templates.TemplateResponse(
        request,
        "barche/crea_barca.html",
        {
            "current_user": admin_user,
            "atleti": atleti,
            "categorie": categorie,
            "barca": {},
            "assigned_atleta_ids": [],
        },
    )


@router.post("/barche/nuova", response_class=RedirectResponse)
async def crea_barca(
    request: Request,
    db: Session = Depends(get_db),
    admin_user: models.User = Depends(get_current_admin_user),
    nome: str = Form(...),
    tipo: str = Form(...),
    costruttore: str = Form(...),
    anno_str: str = Form(...),
    remi_assegnati: Optional[str] = Form(None),
    atleti_ids: List[int] = Form([]),
    in_manutenzione: bool = Form(False),
    fuori_uso: bool = Form(False),
    in_prestito: bool = Form(False),
    in_trasferta: bool = Form(False),
    disponibile_dal_str: Optional[str] = Form(None),
    lunghezza_puntapiedi: Optional[str] = Form(None),
    altezza_puntapiedi: Optional[str] = Form(None),
    apertura_totale: Optional[str] = Form(None),
    altezza_scalmo_sx: Optional[str] = Form(None),
    altezza_scalmo_dx: Optional[str] = Form(None),
    semiapertura_sx: Optional[str] = Form(None),
    semiapertura_dx: Optional[str] = Form(None),
    appruamento_appoppamento: Optional[str] = Form(None),
    gradi_attacco: Optional[str] = Form(None),
    gradi_finale: Optional[str] = Form(None),
    boccola_sx_sopra: Optional[str] = Form(None),
    boccola_dx_sopra: Optional[str] = Form(None),
    rondelle_sx: Optional[str] = Form(None),
    rondelle_dx: Optional[str] = Form(None),
    altezza_carrello: Optional[str] = Form(None),
    avanzamento_guide: Optional[str] = Form(None),
):
    if (in_manutenzione or fuori_uso) and (in_prestito or in_trasferta):
        atleti, categorie = users_service.get_atleti_e_categorie(db)
        return templates.TemplateResponse(
            request,
            "barche/crea_barca.html",
            {
                "current_user": admin_user,
                "atleti": atleti,
                "categorie": categorie,
                "barca": {},
                "assigned_atleta_ids": [],
                "error_message": "Stato imbarcazione non valido.",
            },
            status_code=400,
        )

    if not (nome.strip() and tipo.strip() and costruttore.strip() and anno_str.strip()):
        atleti, categorie = users_service.get_atleti_e_categorie(db)
        return templates.TemplateResponse(
            request,
            "barche/crea_barca.html",
            {
                "current_user": admin_user,
                "atleti": atleti,
                "categorie": categorie,
                "barca": {},
                "assigned_atleta_ids": [],
                "error_message": "Nome, tipo, costruttore e anno sono obbligatori.",
            },
            status_code=400,
        )

    try:
        anno = int(anno_str)
    except ValueError:
        atleti, categorie = users_service.get_atleti_e_categorie(db)
        return templates.TemplateResponse(
            request,
            "barche/crea_barca.html",
            {
                "current_user": admin_user,
                "atleti": atleti,
                "categorie": categorie,
                "barca": {},
                "assigned_atleta_ids": [],
                "error_message": "Anno non valido.",
            },
            status_code=400,
        )

    disponibile_dal = (
        date.fromisoformat(disponibile_dal_str)
        if disponibile_dal_str and disponibile_dal_str.strip()
        else None
    )

    nuova_barca = models.Barca(
        nome=nome,
        tipo=tipo,
        costruttore=costruttore,
        anno=anno,
        remi_assegnati=remi_assegnati,
        atleti_assegnati=db.query(models.User).filter(models.User.id.in_(atleti_ids)).all(),
        in_manutenzione=in_manutenzione,
        fuori_uso=fuori_uso,
        in_prestito=in_prestito,
        in_trasferta=in_trasferta,
        disponibile_dal=disponibile_dal,
        lunghezza_puntapiedi=to_float(lunghezza_puntapiedi),
        altezza_puntapiedi=to_float(altezza_puntapiedi),
        apertura_totale=to_float(apertura_totale),
        altezza_scalmo_sx=to_float(altezza_scalmo_sx),
        altezza_scalmo_dx=to_float(altezza_scalmo_dx),
        semiapertura_sx=to_float(semiapertura_sx),
        semiapertura_dx=to_float(semiapertura_dx),
        appruamento_appoppamento=to_float(appruamento_appoppamento),
        gradi_attacco=to_float(gradi_attacco),
        gradi_finale=to_float(gradi_finale),
        boccola_sx_sopra=boccola_sx_sopra,
        boccola_dx_sopra=boccola_dx_sopra,
        rondelle_sx=rondelle_sx,
        rondelle_dx=rondelle_dx,
        altezza_carrello=to_float(altezza_carrello),
        avanzamento_guide=to_float(avanzamento_guide),
    )
    db.add(nuova_barca)
    db.commit()
    return RedirectResponse(url="/risorse/barche", status_code=status.HTTP_303_SEE_OTHER)



@router.get("/barche/{barca_id}/modifica", response_class=HTMLResponse, name="modifica_barca_form")
async def modifica_barca_form(barca_id: int, request: Request, db: Session = Depends(get_db),
                              admin_user: models.User = Depends(get_current_admin_user)):
    barca = (
        db.query(models.Barca)
        .options(joinedload(models.Barca.atleti_assegnati), joinedload(models.Barca.equipaggi))
        .filter(models.Barca.id == barca_id)
        .first()
    )
    if not barca: raise HTTPException(status_code=404, detail="Barca non trovata")
    atleti, categorie = users_service.get_atleti_e_categorie(db)
    assigned_atleta_ids = {atleta.id for atleta in barca.atleti_assegnati}
    equipaggi = athletes_service.get_equipaggi_by_barca(db, barca_id)
    return templates.TemplateResponse(
        request,
        "barche/modifica_barca.html",
        {
            "current_user": admin_user,
            "barca": barca,
            "atleti": atleti,
            "categorie": categorie,
            "assigned_atleta_ids": assigned_atleta_ids,
            "equipaggi": equipaggi,
        },
    )


@router.post("/barche/{barca_id}/modifica", response_class=RedirectResponse)
async def aggiorna_barca(
    request: Request,
    barca_id: int,
    db: Session = Depends(get_db),
    admin_user: models.User = Depends(get_current_admin_user),
    nome: str = Form(...),
    tipo: str = Form(...),
    costruttore: str = Form(...),
    anno_str: str = Form(...),
    remi_assegnati: Optional[str] = Form(None),
    atleti_ids: List[int] = Form([]),
    in_manutenzione: bool = Form(False),
    fuori_uso: bool = Form(False),
    in_prestito: bool = Form(False),
    in_trasferta: bool = Form(False),
    disponibile_dal_str: Optional[str] = Form(None),
      lunghezza_puntapiedi: Optional[str] = Form(None),
      altezza_puntapiedi: Optional[str] = Form(None),
      apertura_totale: Optional[str] = Form(None),
      altezza_scalmo_sx: Optional[str] = Form(None),
      altezza_scalmo_dx: Optional[str] = Form(None),
      semiapertura_sx: Optional[str] = Form(None),
      semiapertura_dx: Optional[str] = Form(None),
      appruamento_appoppamento: Optional[str] = Form(None),
      gradi_attacco: Optional[str] = Form(None),
      gradi_finale: Optional[str] = Form(None),
      boccola_sx_sopra: Optional[str] = Form(None),
      boccola_dx_sopra: Optional[str] = Form(None),
      rondelle_sx: Optional[str] = Form(None),
      rondelle_dx: Optional[str] = Form(None),
      altezza_carrello: Optional[str] = Form(None),
      avanzamento_guide: Optional[str] = Form(None),
):
    barca = db.get(models.Barca, barca_id)
    if not barca:
        raise HTTPException(status_code=404, detail="Barca non trovata")

    if (in_manutenzione or fuori_uso) and (in_prestito or in_trasferta):
        atleti, categorie = users_service.get_atleti_e_categorie(db)
        assigned_atleta_ids = {atleta.id for atleta in barca.atleti_assegnati}
        equipaggi = athletes_service.get_equipaggi_by_barca(db, barca_id)
        return templates.TemplateResponse(
            request,
            "barche/modifica_barca.html",
            {
                "current_user": admin_user,
                "barca": barca,
                "atleti": atleti,
                "categorie": categorie,
                "assigned_atleta_ids": assigned_atleta_ids,
                "equipaggi": equipaggi,
                "error_message": "Stato non valido: 'In manutenzione/Fuori uso' è incompatibile con 'In prestito/trasferta'.",
            },
            status_code=400,
        )

    if not (nome.strip() and tipo.strip() and costruttore.strip() and anno_str.strip()):
        atleti, categorie = users_service.get_atleti_e_categorie(db)
        assigned_atleta_ids = {atleta.id for atleta in barca.atleti_assegnati}
        equipaggi = athletes_service.get_equipaggi_by_barca(db, barca_id)
        return templates.TemplateResponse(
            request,
            "barche/modifica_barca.html",
            {
                "current_user": admin_user,
                "barca": barca,
                "atleti": atleti,
                "categorie": categorie,
                "assigned_atleta_ids": assigned_atleta_ids,
                "equipaggi": equipaggi,
                "error_message": "Nome, tipo, costruttore e anno sono obbligatori.",
            },
            status_code=400,
        )

    try:
        anno = int(anno_str)
    except ValueError:
        atleti, categorie = users_service.get_atleti_e_categorie(db)
        assigned_atleta_ids = {atleta.id for atleta in barca.atleti_assegnati}
        return templates.TemplateResponse(
            request,
            "barche/modifica_barca.html",
            {
                "current_user": admin_user,
                "barca": barca,
                "atleti": atleti,
                "categorie": categorie,
                "assigned_atleta_ids": assigned_atleta_ids,
                "error_message": "Anno non valido.",
            },
            status_code=400,
        )

    barca.nome = nome.strip()
    barca.tipo = tipo.strip()
    barca.costruttore = costruttore.strip()
    barca.anno = anno if anno_str.strip() else None
    barca.remi_assegnati = remi_assegnati.strip() if remi_assegnati else None

    barca.in_manutenzione = in_manutenzione
    barca.fuori_uso = fuori_uso
    barca.in_prestito = in_prestito
    barca.in_trasferta = in_trasferta
    barca.disponibile_dal = datetime.strptime(disponibile_dal_str, "%Y-%m-%d").date() if disponibile_dal_str else None

    barca.lunghezza_puntapiedi = float(lunghezza_puntapiedi) if lunghezza_puntapiedi else None
    barca.altezza_puntapiedi = float(altezza_puntapiedi) if altezza_puntapiedi else None
    barca.apertura_totale = float(apertura_totale) if apertura_totale else None
    barca.altezza_scalmo_sx = float(altezza_scalmo_sx) if altezza_scalmo_sx else None
    barca.altezza_scalmo_dx = float(altezza_scalmo_dx) if altezza_scalmo_dx else None
    barca.semiapertura_sx = float(semiapertura_sx) if semiapertura_sx else None
    barca.semiapertura_dx = float(semiapertura_dx) if semiapertura_dx else None
    barca.appruamento_appoppamento = float(appruamento_appoppamento) if appruamento_appoppamento else None
    barca.gradi_attacco = float(gradi_attacco) if gradi_attacco else None
    barca.gradi_finale = float(gradi_finale) if gradi_finale else None
    barca.boccola_sx_sopra = boccola_sx_sopra if boccola_sx_sopra else None
    barca.boccola_dx_sopra = boccola_dx_sopra if boccola_dx_sopra else None
    barca.rondelle_sx = rondelle_sx if rondelle_sx else None
    barca.rondelle_dx = rondelle_dx if rondelle_dx else None
    barca.altezza_carrello = float(altezza_carrello) if altezza_carrello else None
    barca.avanzamento_guide = float(avanzamento_guide) if avanzamento_guide else None

    barca.atleti_assegnati.clear()
    if atleti_ids:
        atleti = db.query(models.User).filter(models.User.id.in_(atleti_ids)).all()
        barca.atleti_assegnati.extend(atleti)

    db.commit()
    return RedirectResponse(url="/risorse/barche", status_code=status.HTTP_303_SEE_OTHER)


# Route per gestire gli equipaggi
@router.get("/barche/{barca_id}/equipaggi", response_class=HTMLResponse, name="equipaggi_barca")
async def equipaggi_barca(
    barca_id: int, 
    request: Request, 
    db: Session = Depends(get_db),
    admin_user: models.User = Depends(get_current_admin_user)
):
    """Mostra la lista degli equipaggi di una barca"""
    barca = db.get(models.Barca, barca_id)
    if not barca:
        raise HTTPException(status_code=404, detail="Barca non trovata")
    
    equipaggi = athletes_service.get_equipaggi_by_barca(db, barca_id)
    
    return templates.TemplateResponse(
        request,
        "barche/equipaggi_list.html",
        {
            "current_user": admin_user,
            "barca": barca,
            "equipaggi": equipaggi,
        },
    )


@router.get("/barche/{barca_id}/equipaggi/nuovo", response_class=HTMLResponse, name="nuovo_equipaggio_form")
async def nuovo_equipaggio_form(
    barca_id: int, 
    request: Request, 
    db: Session = Depends(get_db),
    admin_user: models.User = Depends(get_current_admin_user)
):
    """Form per creare un nuovo equipaggio"""
    barca = db.get(models.Barca, barca_id)
    if not barca:
        raise HTTPException(status_code=404, detail="Barca non trovata")
    
    posti_richiesti = barca.get_posti_richiesti()
    atleti_disponibili = {}
    
    for posto in posti_richiesti.keys():
        atleti_disponibili[posto] = athletes_service.get_atleti_disponibili_for_posto(db, barca_id, posto)
    
    return templates.TemplateResponse(
        request,
        "barche/equipaggio_form.html",
        {
            "current_user": admin_user,
            "barca": barca,
            "equipaggio": None,
            "posti_richiesti": posti_richiesti,
            "atleti_disponibili": atleti_disponibili,
            "is_edit": False,
        },
    )


@router.post("/barche/{barca_id}/equipaggi/nuovo", response_class=RedirectResponse, name="crea_equipaggio")
async def crea_equipaggio(
    barca_id: int,
    request: Request,
    db: Session = Depends(get_db),
    admin_user: models.User = Depends(get_current_admin_user),
    nome: str = Form(...),
    capovoga_id: int = Form(...),
    secondo_id: Optional[int] = Form(None),
    terzo_id: Optional[int] = Form(None),
    quarto_id: Optional[int] = Form(None),
    quinto_id: Optional[int] = Form(None),
    sesto_id: Optional[int] = Form(None),
    settimo_id: Optional[int] = Form(None),
    prodiere_id: Optional[int] = Form(None),
    timoniere_id: Optional[int] = Form(None),
    note: Optional[str] = Form(None),
):
    """Crea un nuovo equipaggio"""
    barca = db.get(models.Barca, barca_id)
    if not barca:
        raise HTTPException(status_code=404, detail="Barca non trovata")
    
    equipaggio_data = {
        "nome": nome,
        "barca_id": barca_id,
        "capovoga_id": capovoga_id,
        "secondo_id": secondo_id,
        "terzo_id": terzo_id,
        "quarto_id": quarto_id,
        "quinto_id": quinto_id,
        "sesto_id": sesto_id,
        "settimo_id": settimo_id,
        "prodiere_id": prodiere_id,
        "timoniere_id": timoniere_id,
        "note": note,
    }
    
    # Rimuovi i valori None
    equipaggio_data = {k: v for k, v in equipaggio_data.items() if v is not None}
    
    athletes_service.create_equipaggio(db, equipaggio_data)
    
    return RedirectResponse(
        url=f"/risorse/barche/{barca_id}/equipaggi", 
        status_code=status.HTTP_303_SEE_OTHER
    )


@router.get("/equipaggi/{equipaggio_id}/modifica", response_class=HTMLResponse, name="modifica_equipaggio_form")
async def modifica_equipaggio_form(
    equipaggio_id: int, 
    request: Request, 
    db: Session = Depends(get_db),
    admin_user: models.User = Depends(get_current_admin_user)
):
    """Form per modificare un equipaggio esistente"""
    equipaggio = athletes_service.get_equipaggio_by_id(db, equipaggio_id)
    if not equipaggio:
        raise HTTPException(status_code=404, detail="Equipaggio non trovato")
    
    barca = equipaggio.barca
    posti_richiesti = barca.get_posti_richiesti()
    atleti_disponibili = {}
    
    for posto in posti_richiesti.keys():
        atleti_disponibili[posto] = athletes_service.get_atleti_disponibili_for_posto(
            db, barca.id, posto, equipaggio_id
        )
    
    return templates.TemplateResponse(
        request,
        "barche/equipaggio_form.html",
        {
            "current_user": admin_user,
            "barca": barca,
            "equipaggio": equipaggio,
            "posti_richiesti": posti_richiesti,
            "atleti_disponibili": atleti_disponibili,
            "is_edit": True,
        },
    )


@router.post("/equipaggi/{equipaggio_id}/modifica", response_class=RedirectResponse, name="aggiorna_equipaggio")
async def aggiorna_equipaggio(
    equipaggio_id: int,
    request: Request,
    db: Session = Depends(get_db),
    admin_user: models.User = Depends(get_current_admin_user),
    nome: str = Form(...),
    capovoga_id: int = Form(...),
    secondo_id: Optional[int] = Form(None),
    terzo_id: Optional[int] = Form(None),
    quarto_id: Optional[int] = Form(None),
    quinto_id: Optional[int] = Form(None),
    sesto_id: Optional[int] = Form(None),
    settimo_id: Optional[int] = Form(None),
    prodiere_id: Optional[int] = Form(None),
    timoniere_id: Optional[int] = Form(None),
    note: Optional[str] = Form(None),
):
    """Aggiorna un equipaggio esistente"""
    equipaggio = athletes_service.get_equipaggio_by_id(db, equipaggio_id)
    if not equipaggio:
        raise HTTPException(status_code=404, detail="Equipaggio non trovato")
    
    equipaggio_data = {
        "nome": nome,
        "capovoga_id": capovoga_id,
        "secondo_id": secondo_id,
        "terzo_id": terzo_id,
        "quarto_id": quarto_id,
        "quinto_id": quinto_id,
        "sesto_id": sesto_id,
        "settimo_id": settimo_id,
        "prodiere_id": prodiere_id,
        "timoniere_id": timoniere_id,
        "note": note,
    }
    
    # Rimuovi i valori None
    equipaggio_data = {k: v for k, v in equipaggio_data.items() if v is not None}
    
    athletes_service.update_equipaggio(db, equipaggio_id, equipaggio_data)
    
    return RedirectResponse(
        url=f"/risorse/barche/{equipaggio.barca_id}/equipaggi", 
        status_code=status.HTTP_303_SEE_OTHER
    )


@router.post("/equipaggi/{equipaggio_id}/elimina", response_class=RedirectResponse, name="elimina_equipaggio")
async def elimina_equipaggio(
    equipaggio_id: int,
    request: Request,
    db: Session = Depends(get_db),
    admin_user: models.User = Depends(get_current_admin_user),
):
    """Elimina un equipaggio"""
    equipaggio = athletes_service.get_equipaggio_by_id(db, equipaggio_id)
    if not equipaggio:
        raise HTTPException(status_code=404, detail="Equipaggio non trovato")
    
    barca_id = equipaggio.barca_id
    athletes_service.delete_equipaggio(db, equipaggio_id)
    
    return RedirectResponse(
        url=f"/risorse/barche/{barca_id}/equipaggi", 
        status_code=status.HTTP_303_SEE_OTHER
    )


@router.post("/barche/{barca_id}/elimina", response_class=RedirectResponse)
async def elimina_barca(barca_id: int, db: Session = Depends(get_db),
                        admin_user: models.User = Depends(get_current_admin_user)):
    barca = db.query(models.Barca).filter(models.Barca.id == barca_id).first()
    if not barca: raise HTTPException(status_code=404, detail="Barca non trovata")
    db.delete(barca)
    db.commit()
    return RedirectResponse(url="/risorse/barche?message=Barca eliminata con successo",
                            status_code=status.HTTP_303_SEE_OTHER)


@router.get("/pesi", response_class=HTMLResponse)
async def view_pesi(
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    atleta_id: Optional[str] = None,
    categoria: Optional[str] = None,
):
    esercizi = db.query(models.EsercizioPesi).order_by(models.EsercizioPesi.ordine).all()
    atleti, categorie = users_service.get_atleti_e_categorie(db, ALLOWED_PESI_CATEGORIES)
    if categoria:
        atleti = [a for a in atleti if a.category == categoria]
    selected_atleta = None
    if current_user.is_atleta:
        selected_atleta = current_user
    if (current_user.is_admin or current_user.is_allenatore) and atleta_id:
        try:
            selected_atleta = db.get(models.User, int(atleta_id))
        except (TypeError, ValueError):
            selected_atleta = None

    scheda_data = {}
    if selected_atleta:
        scheda_data = {s.esercizio_id: s for s in
                       db.query(models.SchedaPesi).filter(models.SchedaPesi.atleta_id == selected_atleta.id).all()}

    return templates.TemplateResponse(
        request,
        "pesi.html",
        {
            "current_user": current_user,
            "esercizi": esercizi,
            "atleti": atleti,
            "categorie": categorie,
            "selected_category": categoria,
            "selected_atleta": selected_atleta,
            "scheda_data": scheda_data,
        },
    )


@router.post("/pesi/update", response_class=RedirectResponse)
async def update_scheda_pesi(request: Request, db: Session = Depends(get_db),
                             current_user: models.User = Depends(get_current_user)):
    form_data = await request.form()
    atleta_id = int(form_data.get("atleta_id"))
    if not (current_user.is_admin or current_user.is_allenatore or current_user.id == atleta_id): raise HTTPException(
        status_code=403, detail="Non autorizzato")
    for key, value in form_data.items():
        if key.startswith("massimale_"):
            esercizio_id = int(key.split("_")[1])
            scheda = db.query(models.SchedaPesi).filter_by(atleta_id=atleta_id,
                                                           esercizio_id=esercizio_id).first() or models.SchedaPesi(
                atleta_id=atleta_id, esercizio_id=esercizio_id)
            if not scheda.id: db.add(scheda)
            scheda.massimale = float(value) if value else None
            for rep in [5, 7, 10, 20]:
                rep_value = form_data.get(f"{rep}rep_{esercizio_id}")
                setattr(scheda, f"carico_{rep}_rep", float(rep_value) if rep_value else None)
    db.commit()
    return RedirectResponse(url=f"/risorse/pesi?atleta_id={atleta_id}", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/pesi/add_esercizio", response_class=RedirectResponse)
async def add_esercizio_pesi(
    db: Session = Depends(get_db),
    admin_user: models.User = Depends(get_current_admin_user),
    nome: str = Form(...),
    ordine: int = Form(...),
):
    db.add(models.EsercizioPesi(nome=nome, ordine=ordine))
    db.commit()
    return RedirectResponse(url="/risorse/pesi", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/pesi/esercizi", response_class=HTMLResponse)
async def gestisci_esercizi(
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if not (current_user.is_admin or current_user.is_allenatore):
        raise HTTPException(status_code=403, detail="Non autorizzato")
    esercizi = db.query(models.EsercizioPesi).order_by(models.EsercizioPesi.ordine).all()
    return templates.TemplateResponse(
        request,
        "pesi_gestisci.html",
        {"current_user": current_user, "esercizi": esercizi},
    )


@router.post("/pesi/esercizi/update", response_class=RedirectResponse)
async def update_esercizio(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    id: int = Form(...),
    ordine: int = Form(...),
    nome: str = Form(...),
):
    if not (current_user.is_admin or current_user.is_allenatore):
        raise HTTPException(status_code=403, detail="Non autorizzato")
    esercizio = db.get(models.EsercizioPesi, id)
    if esercizio:
        esercizio.ordine = ordine
        esercizio.nome = nome
        db.commit()
    return RedirectResponse(url="/risorse/pesi/esercizi", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/pesi/esercizi/delete", response_class=RedirectResponse)
async def delete_esercizio(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    id: int = Form(...),
):
    if not (current_user.is_admin or current_user.is_allenatore):
        raise HTTPException(status_code=403, detail="Non autorizzato")
    esercizio = db.get(models.EsercizioPesi, id)
    if esercizio:
        db.delete(esercizio)
        db.commit()
    return RedirectResponse(url="/risorse/pesi/esercizi", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/pesi/statistiche", response_class=HTMLResponse)
async def statistiche_pesi(
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    categoria: Optional[str] = None,
    atleta_id: Optional[int] = None,
):
    esercizi = db.query(models.EsercizioPesi).order_by(models.EsercizioPesi.ordine).all()
    atleti, categorie = users_service.get_atleti_e_categorie(db, ALLOWED_PESI_CATEGORIES)
    if categoria:
        atleti = [a for a in atleti if a.category == categoria]
    selected_atleta = None
    if current_user.is_atleta:
        selected_atleta = current_user
    elif atleta_id:
        try:
            selected_atleta = db.get(models.User, int(atleta_id))
        except (TypeError, ValueError):
            selected_atleta = None
    return templates.TemplateResponse(
        request,
        "pesi_statistiche.html",
        {
            "current_user": current_user,
            "esercizi": esercizi,
            "atleti": atleti,
            "categorie": categorie,
            "selected_category": categoria,
            "selected_atleta": selected_atleta,
        },
    )

# --- ROUTE PER I MEZZI ---

@mezzi_router.get("/", response_class=HTMLResponse)
async def list_mezzi(
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    tipo_filter: str = Query("furgoni", description="Tipo di mezzo da visualizzare")
):
    """Lista dei mezzi (furgoni o gommoni)"""
    # Verifica che l'utente sia admin o allenatore
    if not (current_user.is_admin or current_user.is_allenatore):
        raise HTTPException(status_code=403, detail="Accesso negato")
    
    furgoni = db.query(models.Furgone).order_by(models.Furgone.marca, models.Furgone.modello).all()
    gommoni = db.query(models.Gommone).order_by(models.Gommone.nome).all()
    
    return templates.TemplateResponse(
        request,
        "mezzi/mezzi_main.html",
        {
            "current_user": current_user,
            "furgoni": furgoni,
            "gommoni": gommoni,
            "tipo_filter": tipo_filter,
            "page_title": "Mezzi"
        }
    )


@mezzi_router.get("/furgoni", response_class=HTMLResponse)
async def list_furgoni(
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Lista dei furgoni"""
    # Verifica che l'utente sia admin o allenatore
    if not (current_user.is_admin or current_user.is_allenatore):
        raise HTTPException(status_code=403, detail="Accesso negato")
    
    furgoni = db.query(models.Furgone).order_by(models.Furgone.marca, models.Furgone.modello).all()
    return templates.TemplateResponse(
        request,
        "mezzi/furgoni_list.html",
        {
            "current_user": current_user,
            "furgoni": furgoni,
            "tipo_filter": "furgoni",
            "page_title": "Furgoni"
        }
    )


@mezzi_router.get("/gommoni", response_class=HTMLResponse)
async def list_gommoni(
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Lista dei gommoni"""
    # Verifica che l'utente sia admin o allenatore
    if not (current_user.is_admin or current_user.is_allenatore):
        raise HTTPException(status_code=403, detail="Accesso negato")
    
    gommoni = db.query(models.Gommone).order_by(models.Gommone.nome).all()
    return templates.TemplateResponse(
        request,
        "mezzi/gommoni_list.html",
        {
            "current_user": current_user,
            "gommoni": gommoni,
            "tipo_filter": "gommoni",
            "page_title": "Gommoni"
        }
    )


@mezzi_router.get("/gestione", response_class=HTMLResponse)
async def gestione_mezzi(
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin_user)
):
    """Gestione mezzi - solo per admin"""
    furgoni = db.query(models.Furgone).order_by(models.Furgone.marca, models.Furgone.modello).all()
    gommoni = db.query(models.Gommone).order_by(models.Gommone.nome).all()
    
    return templates.TemplateResponse(
        request,
        "mezzi/gestione_mezzi.html",
        {
            "current_user": current_user,
            "furgoni": furgoni,
            "gommoni": gommoni
        }
    )


@mezzi_router.get("/furgone/{furgone_id}", response_class=HTMLResponse)
async def furgone_detail(
    furgone_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Dettaglio furgone"""
    # Verifica che l'utente sia admin o allenatore
    if not (current_user.is_admin or current_user.is_allenatore):
        raise HTTPException(status_code=403, detail="Accesso negato")
    
    furgone = db.query(models.Furgone).filter(models.Furgone.id == furgone_id).first()
    if not furgone:
        raise HTTPException(status_code=404, detail="Furgone non trovato")
    
    return templates.TemplateResponse(
        request,
        "mezzi/furgone_detail.html",
        {
            "current_user": current_user,
            "furgone": furgone,
            "today": date.today()
        }
    )


@mezzi_router.get("/gommone/{gommone_id}", response_class=HTMLResponse)
async def gommone_detail(
    gommone_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Dettaglio gommone"""
    # Verifica che l'utente sia admin o allenatore
    if not (current_user.is_admin or current_user.is_allenatore):
        raise HTTPException(status_code=403, detail="Accesso negato")
    
    gommone = db.query(models.Gommone).filter(models.Gommone.id == gommone_id).first()
    if not gommone:
        raise HTTPException(status_code=404, detail="Gommone non trovato")
    
    return templates.TemplateResponse(
        request,
        "mezzi/gommone_detail.html",
        {
            "current_user": current_user,
            "gommone": gommone,
            "today": date.today()
        }
    )


# --- ROUTE PER REGISTRO ORE GOMMONE SELVA 20CV ---

@mezzi_router.get("/gommone/{gommone_id}/ore", response_class=HTMLResponse)
async def gommone_ore_detail(
    gommone_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Dettaglio registro ore gommone - solo per allenatori e admin"""
    # Verifica che l'utente sia admin o allenatore
    if not (current_user.is_admin or current_user.is_allenatore):
        raise HTTPException(status_code=403, detail="Accesso negato")
    
    gommone = db.query(models.Gommone).filter(models.Gommone.id == gommone_id).first()
    if not gommone:
        raise HTTPException(status_code=404, detail="Gommone non trovato")
    
    # Ottieni tutti gli utilizzi ordinati per data (più recenti prima)
    utilizzi = db.query(models.GommoneOre).filter(
        models.GommoneOre.gommone_id == gommone_id
    ).order_by(models.GommoneOre.data_utilizzo.desc()).all()
    
    # Calcola statistiche
    ore_totali = sum(u.ore_utilizzo for u in utilizzi)
    
    # Ore per allenatore
    ore_per_allenatore = {}
    for utilizzo in utilizzi:
        allenatore_nome = utilizzo.allenatore.full_name
        if allenatore_nome not in ore_per_allenatore:
            ore_per_allenatore[allenatore_nome] = 0
        ore_per_allenatore[allenatore_nome] += utilizzo.ore_utilizzo
    
    return templates.TemplateResponse(
        request,
        "mezzi/gommone_ore_detail.html",
        {
            "current_user": current_user,
            "gommone": gommone,
            "utilizzi": utilizzi,
            "ore_totali": ore_totali,
            "ore_per_allenatore": ore_per_allenatore
        }
    )


@mezzi_router.post("/gommone/{gommone_id}/ore", response_class=RedirectResponse)
async def gommone_aggiungi_ore(
    gommone_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    data_utilizzo: date = Form(...),
    ore_utilizzo: float = Form(...),
    note: Optional[str] = Form(None)
):
    """Aggiunge ore di utilizzo al gommone - solo per allenatori e admin"""
    # Verifica che l'utente sia admin o allenatore
    if not (current_user.is_admin or current_user.is_allenatore):
        raise HTTPException(status_code=403, detail="Accesso negato")
    
    gommone = db.query(models.Gommone).filter(models.Gommone.id == gommone_id).first()
    if not gommone:
        raise HTTPException(status_code=404, detail="Gommone non trovato")
    
    try:
        nuovo_utilizzo = models.GommoneOre(
            gommone_id=gommone_id,
            allenatore_id=current_user.id,
            data_utilizzo=data_utilizzo,
            ore_utilizzo=ore_utilizzo,
            note=note
        )
        
        db.add(nuovo_utilizzo)
        db.commit()
        
        return RedirectResponse(url=f"/mezzi/gommone/{gommone_id}/ore?message=Ore aggiunte con successo", status_code=303)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Errore nell'aggiunta ore: {str(e)}")


# --- ROUTE PER MODIFICA MEZZI (SOLO ADMIN) ---

@mezzi_router.get("/furgone/{furgone_id}/modifica", response_class=HTMLResponse)
async def furgone_modifica_form(
    furgone_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin_user)
):
    """Form di modifica furgone - solo per admin"""
    furgone = db.query(models.Furgone).filter(models.Furgone.id == furgone_id).first()
    if not furgone:
        raise HTTPException(status_code=404, detail="Furgone non trovato")
    
    return templates.TemplateResponse(
        request,
        "mezzi/furgone_modifica.html",
        {
            "current_user": current_user,
            "furgone": furgone,
            "today": date.today()
        }
    )


@mezzi_router.post("/furgone/{furgone_id}/modifica", response_class=RedirectResponse)
async def furgone_modifica_save(
    furgone_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin_user),
    marca: str = Form(...),
    modello: str = Form(...),
    targa: str = Form(...),
    anno: int = Form(...),
    stato: str = Form(...)
):
    """Salva modifiche furgone - solo per admin"""
    furgone = db.query(models.Furgone).filter(models.Furgone.id == furgone_id).first()
    if not furgone:
        raise HTTPException(status_code=404, detail="Furgone non trovato")
    
    try:
        furgone.marca = marca
        furgone.modello = modello
        furgone.targa = targa
        furgone.anno = anno
        furgone.stato = stato
        furgone.updated_at = datetime.now(timezone.utc)
        
        db.commit()
        return RedirectResponse(url=f"/mezzi/furgone/{furgone_id}/modifica?message=Modifiche salvate con successo", status_code=303)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Errore nel salvataggio: {str(e)}")


@mezzi_router.get("/gommone/{gommone_id}/modifica", response_class=HTMLResponse)
async def gommone_modifica_form(
    gommone_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin_user)
):
    """Form di modifica gommone - solo per admin"""
    gommone = db.query(models.Gommone).filter(models.Gommone.id == gommone_id).first()
    if not gommone:
        raise HTTPException(status_code=404, detail="Gommone non trovato")
    
    return templates.TemplateResponse(
        request,
        "mezzi/gommone_modifica.html",
        {
            "current_user": current_user,
            "gommone": gommone,
            "today": date.today()
        }
    )


@mezzi_router.post("/gommone/{gommone_id}/modifica", response_class=RedirectResponse)
async def gommone_modifica_save(
    gommone_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin_user),
    nome: str = Form(...),
    motore: str = Form(None),
    potenza: str = Form(None),
    stato: str = Form(...)
):
    """Salva modifiche gommone - solo per admin"""
    gommone = db.query(models.Gommone).filter(models.Gommone.id == gommone_id).first()
    if not gommone:
        raise HTTPException(status_code=404, detail="Gommone non trovato")
    
    try:
        gommone.nome = nome
        gommone.motore = motore
        gommone.potenza = potenza
        gommone.stato = stato
        gommone.updated_at = datetime.now(timezone.utc)
        
        db.commit()
        return RedirectResponse(url=f"/mezzi/gommone/{gommone_id}/modifica?message=Modifiche salvate con successo", status_code=303)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Errore nel salvataggio: {str(e)}")


# --- ROUTE PER GESTIONE SCADENZE (SOLO ADMIN) ---

@mezzi_router.post("/furgone/{furgone_id}/scadenza", response_class=RedirectResponse)
async def furgone_aggiungi_scadenza(
    furgone_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin_user),
    tipo_scadenza: str = Form(...),
    data_scadenza: date = Form(...),
    identificativo: Optional[str] = Form(None),
    frazionamento: Optional[str] = Form(None),
    assicuratore: Optional[str] = Form(None)
):
    """Aggiunge una nuova scadenza al furgone - solo per admin"""
    furgone = db.query(models.Furgone).filter(models.Furgone.id == furgone_id).first()
    if not furgone:
        raise HTTPException(status_code=404, detail="Furgone non trovato")
    
    try:
        if tipo_scadenza == "bollo":
            furgone.scadenza_bollo = data_scadenza
            furgone.scadenza_bollo_identificativo = identificativo
            furgone.scadenza_bollo_frazionamento = frazionamento
            furgone.scadenza_bollo_assicuratore = assicuratore
        elif tipo_scadenza == "revisione":
            furgone.scadenza_revisione = data_scadenza
            furgone.scadenza_revisione_identificativo = identificativo
            furgone.scadenza_revisione_frazionamento = frazionamento
            furgone.scadenza_revisione_assicuratore = assicuratore
        elif tipo_scadenza == "rca":
            furgone.scadenza_rca = data_scadenza
            furgone.scadenza_rca_identificativo = identificativo
            furgone.scadenza_rca_frazionamento = frazionamento
            furgone.scadenza_rca_assicuratore = assicuratore
        elif tipo_scadenza == "infortuni":
            furgone.scadenza_infortuni_conducente = data_scadenza
            furgone.scadenza_infortuni_conducente_identificativo = identificativo
            furgone.scadenza_infortuni_conducente_frazionamento = frazionamento
            furgone.scadenza_infortuni_conducente_assicuratore = assicuratore
        
        furgone.updated_at = datetime.now(timezone.utc)
        db.commit()
        return RedirectResponse(url=f"/mezzi/furgone/{furgone_id}/modifica?message=Scadenza aggiunta con successo", status_code=303)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Errore nell'aggiunta scadenza: {str(e)}")


@mezzi_router.post("/gommone/{gommone_id}/scadenza", response_class=RedirectResponse)
async def gommone_aggiungi_scadenza(
    gommone_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin_user),
    tipo_scadenza: str = Form(...),
    data_scadenza: date = Form(...),
    identificativo: Optional[str] = Form(None),
    frazionamento: Optional[str] = Form(None),
    assicuratore: Optional[str] = Form(None)
):
    """Aggiunge una nuova scadenza al gommone - solo per admin"""
    gommone = db.query(models.Gommone).filter(models.Gommone.id == gommone_id).first()
    if not gommone:
        raise HTTPException(status_code=404, detail="Gommone non trovato")
    
    try:
        if tipo_scadenza == "rca":
            gommone.scadenza_rca = data_scadenza
            gommone.scadenza_rca_identificativo = identificativo
            gommone.scadenza_rca_frazionamento = frazionamento
            gommone.scadenza_rca_assicuratore = assicuratore
        elif tipo_scadenza == "manutenzione":
            gommone.scadenza_manutenzione = data_scadenza
            gommone.scadenza_manutenzione_identificativo = identificativo
            gommone.scadenza_manutenzione_frazionamento = frazionamento
            gommone.scadenza_manutenzione_assicuratore = assicuratore
        
        gommone.updated_at = datetime.now(timezone.utc)
        db.commit()
        return RedirectResponse(url=f"/mezzi/gommone/{gommone_id}/modifica?message=Scadenza aggiunta con successo", status_code=303)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Errore nell'aggiunta scadenza: {str(e)}")


# --- ROUTE PER ELIMINAZIONE MEZZI (SOLO ADMIN) ---

@mezzi_router.delete("/furgone/{furgone_id}", response_class=RedirectResponse)
async def furgone_delete(
    furgone_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin_user)
):
    """Elimina furgone - solo per admin"""
    furgone = db.query(models.Furgone).filter(models.Furgone.id == furgone_id).first()
    if not furgone:
        raise HTTPException(status_code=404, detail="Furgone non trovato")
    
    try:
        db.delete(furgone)
        db.commit()
        return RedirectResponse(url="/mezzi/gestione?message=Furgone eliminato con successo", status_code=303)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Errore nell'eliminazione: {str(e)}")


@mezzi_router.delete("/gommone/{gommone_id}", response_class=RedirectResponse)
async def gommone_delete(
    gommone_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin_user)
):
    """Elimina gommone - solo per admin"""
    gommone = db.query(models.Gommone).filter(models.Gommone.id == gommone_id).first()
    if not gommone:
        raise HTTPException(status_code=404, detail="Gommone non trovato")
    
    try:
        db.delete(gommone)
        db.commit()
        return RedirectResponse(url="/mezzi/gestione?message=Gommone eliminato con successo", status_code=303)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Errore nell'eliminazione: {str(e)}")


# --- ROUTE PER CREAZIONE MEZZI ---

@mezzi_router.post("/furgone/nuovo", response_class=RedirectResponse)
async def crea_furgone(
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin_user),
    marca: str = Form(...),
    modello: str = Form(...),
    targa: str = Form(...),
    anno: int = Form(...),
    stato: str = Form("libero"),
    scadenza_bollo: Optional[str] = Form(None),
    scadenza_revisione: Optional[str] = Form(None),
    scadenza_rca: Optional[str] = Form(None),
    scadenza_infortuni: Optional[str] = Form(None)
):
    """Crea nuovo furgone - solo per admin"""
    try:
        # Converti le date se presenti
        from datetime import datetime
        scadenza_bollo_date = None
        if scadenza_bollo:
            scadenza_bollo_date = datetime.strptime(scadenza_bollo, "%Y-%m-%d").date()
        
        scadenza_revisione_date = None
        if scadenza_revisione:
            scadenza_revisione_date = datetime.strptime(scadenza_revisione, "%Y-%m-%d").date()
        
        scadenza_rca_date = None
        if scadenza_rca:
            scadenza_rca_date = datetime.strptime(scadenza_rca, "%Y-%m-%d").date()
        
        scadenza_infortuni_date = None
        if scadenza_infortuni:
            scadenza_infortuni_date = datetime.strptime(scadenza_infortuni, "%Y-%m-%d").date()

        # Crea nuovo furgone
        nuovo_furgone = models.Furgone(
            marca=marca,
            modello=modello,
            targa=targa,
            anno=anno,
            stato=stato,
            scadenza_bollo=scadenza_bollo_date,
            scadenza_revisione=scadenza_revisione_date,
            scadenza_rca=scadenza_rca_date,
            scadenza_infortuni=scadenza_infortuni_date
        )
        
        db.add(nuovo_furgone)
        db.commit()
        
        return RedirectResponse(url="/mezzi/gestione?message=Furgone creato con successo", status_code=303)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Errore nella creazione: {str(e)}")


@mezzi_router.post("/gommone/nuovo", response_class=RedirectResponse)
async def crea_gommone(
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin_user),
    nome: str = Form(...),
    motore: Optional[str] = Form(None),
    potenza: Optional[str] = Form(None),
    stato: str = Form("libero"),
    scadenza_rca: Optional[str] = Form(None),
    scadenza_manutenzione: Optional[str] = Form(None)
):
    """Crea nuovo gommone - solo per admin"""
    try:
        # Converti le date se presenti
        from datetime import datetime
        scadenza_rca_date = None
        if scadenza_rca:
            scadenza_rca_date = datetime.strptime(scadenza_rca, "%Y-%m-%d").date()
        
        scadenza_manutenzione_date = None
        if scadenza_manutenzione:
            scadenza_manutenzione_date = datetime.strptime(scadenza_manutenzione, "%Y-%m-%d").date()

        # Crea nuovo gommone
        nuovo_gommone = models.Gommone(
            nome=nome,
            motore=motore,
            potenza=potenza,
            stato=stato,
            scadenza_rca=scadenza_rca_date,
            scadenza_manutenzione=scadenza_manutenzione_date
        )
        
        db.add(nuovo_gommone)
        db.commit()
        
        return RedirectResponse(url="/mezzi/gestione?message=Gommone creato con successo", status_code=303)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Errore nella creazione: {str(e)}")



