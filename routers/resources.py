# File: routers/resources.py
from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Request, Depends, Form, HTTPException, status, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session, joinedload
from fastapi.templating import Jinja2Templates
import models
from database import get_db
from dependencies import get_current_user, get_current_admin_user
from services import barche as barche_service, users as users_service
from services.users import ALLOWED_PESI_CATEGORIES
from utils.parsing import to_float

router = APIRouter(prefix="/risorse", tags=["Risorse"])
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
        "barche/barche_list.html",
        {
            "request": request,
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
        .options(joinedload(models.Barca.atleti_assegnati))
        .get(barca_id)
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
        "barche/barca_detail.html",
        {"request": request, "current_user": current_user, "barca": barca, "message": message},
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
        .options(joinedload(models.Barca.atleti_assegnati))
        .get(barca_id)
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
    return templates.TemplateResponse("barche/crea_barca.html",
                                      {"request": request, "current_user": admin_user, "atleti": atleti,
                                       "categorie": categorie, "barca": {}, "assigned_atleta_ids": []})


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
            "barche/crea_barca.html",
            {
                "request": request,
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
            "barche/crea_barca.html",
            {
                "request": request,
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
            "barche/crea_barca.html",
            {
                "request": request,
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
    barca = db.query(models.Barca).options(joinedload(models.Barca.atleti_assegnati)).get(barca_id)
    if not barca: raise HTTPException(status_code=404, detail="Barca non trovata")
    atleti, categorie = users_service.get_atleti_e_categorie(db)
    assigned_atleta_ids = {atleta.id for atleta in barca.atleti_assegnati}
    return templates.TemplateResponse("barche/modifica_barca.html",
                                      {"request": request, "current_user": admin_user, "barca": barca,
                                       "atleti": atleti, "categorie": categorie,
                                       "assigned_atleta_ids": assigned_atleta_ids})


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
    barca = db.query(models.Barca).get(barca_id)
    if not barca:
        raise HTTPException(status_code=404, detail="Barca non trovata")

    if (in_manutenzione or fuori_uso) and (in_prestito or in_trasferta):
        atleti, categorie = users_service.get_atleti_e_categorie(db)
        assigned_atleta_ids = {atleta.id for atleta in barca.atleti_assegnati}
        return templates.TemplateResponse(
            "barche/modifica_barca.html",
            {
                "request": request,
                "current_user": admin_user,
                "barca": barca,
                "atleti": atleti,
                "categorie": categorie,
                "assigned_atleta_ids": assigned_atleta_ids,
                "error_message": "Stato non valido: 'In manutenzione/Fuori uso' è incompatibile con 'In prestito/trasferta'.",
            },
            status_code=400,
        )

    if not (nome.strip() and tipo.strip() and costruttore.strip() and anno_str.strip()):
        atleti, categorie = users_service.get_atleti_e_categorie(db)
        assigned_atleta_ids = {atleta.id for atleta in barca.atleti_assegnati}
        return templates.TemplateResponse(
            "barche/modifica_barca.html",
            {
                "request": request,
                "current_user": admin_user,
                "barca": barca,
                "atleti": atleti,
                "categorie": categorie,
                "assigned_atleta_ids": assigned_atleta_ids,
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
            "barche/modifica_barca.html",
            {
                "request": request,
                "current_user": admin_user,
                "barca": barca,
                "atleti": atleti,
                "categorie": categorie,
                "assigned_atleta_ids": assigned_atleta_ids,
                "error_message": "Anno non valido.",
            },
            status_code=400,
        )

    barca.nome, barca.tipo, barca.costruttore = nome, tipo, costruttore
    barca.anno = anno
    barca.remi_assegnati = remi_assegnati
    barca.atleti_assegnati = db.query(models.User).filter(models.User.id.in_(atleti_ids)).all()
    barca.in_manutenzione = in_manutenzione
    barca.fuori_uso = fuori_uso
    barca.in_prestito = in_prestito
    barca.in_trasferta = in_trasferta
    barca.disponibile_dal = (
        date.fromisoformat(disponibile_dal_str)
        if disponibile_dal_str and disponibile_dal_str.strip()
        else None
    )
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
    return RedirectResponse(url="/risorse/barche", status_code=status.HTTP_303_SEE_OTHER)


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
            selected_atleta = db.query(models.User).get(int(atleta_id))
        except (TypeError, ValueError):
            selected_atleta = None

    scheda_data = {}
    if selected_atleta:
        scheda_data = {s.esercizio_id: s for s in
                       db.query(models.SchedaPesi).filter(models.SchedaPesi.atleta_id == selected_atleta.id).all()}

    return templates.TemplateResponse(
        "pesi.html",
        {
            "request": request,
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
        "pesi_gestisci.html",
        {"request": request, "current_user": current_user, "esercizi": esercizi},
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
    esercizio = db.query(models.EsercizioPesi).get(id)
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
    esercizio = db.query(models.EsercizioPesi).get(id)
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
            selected_atleta = db.query(models.User).get(int(atleta_id))
        except (TypeError, ValueError):
            selected_atleta = None
    return templates.TemplateResponse(
        "pesi_statistiche.html",
        {
            "request": request,
            "current_user": current_user,
            "esercizi": esercizi,
            "atleti": atleti,
            "categorie": categorie,
            "selected_category": categoria,
            "selected_atleta": selected_atleta,
        },
    )
