# File: routers/resources.py
from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Request, Depends, Form, HTTPException, status, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session, joinedload
from fastapi.templating import Jinja2Templates
from app.database.database import get_db
from app.dependencies.dependencies import get_current_user, get_current_admin_user
from app.database.database import get_db
from app import models
from app.security import security
router = APIRouter(prefix="/risorse", tags=["Risorse"])
templates = Jinja2Templates(directory="templates")


def get_atleti_e_categorie(db: Session):
    atleti = db.query(models.User).join(models.User.roles).filter(models.Role.name == 'atleta').order_by(
        models.User.last_name).all()
    categorie = sorted(list(set(atleta.category for atleta in atleti if atleta.category != "N/D")))
    return atleti, categorie


@router.get("/barche", response_class=HTMLResponse)
async def list_barche(request: Request, db: Session = Depends(get_db),
                      current_user: models.User = Depends(get_current_user),
                      tipi_filter: List[str] = Query([]),
                      sort_by: str = Query("nome"),
                      sort_dir: str = Query("asc")):
    query = db.query(models.Barca)

    if tipi_filter:
        query = query.filter(models.Barca.tipo.in_(tipi_filter))

    if sort_by != 'status':
        sort_column = getattr(models.Barca, sort_by, models.Barca.nome)
        if sort_dir == 'desc':
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

    barche = query.all()

    if sort_by == 'status':
        barche.sort(key=lambda b: b.status[0], reverse=(sort_dir == 'desc'))

    tipi_barca_result = db.query(models.Barca.tipo).distinct().order_by(models.Barca.tipo).all()
    tipi_barca = [t[0] for t in tipi_barca_result]

    return templates.TemplateResponse("barche/barche_list.html", {
        "request": request, "current_user": current_user, "barche": barche,
        "tipi_barca": tipi_barca, "current_filters": {"tipi_filter": tipi_filter},
        "sort_by": sort_by, "sort_dir": sort_dir
    })


@router.get("/barche/nuova", response_class=HTMLResponse)
async def nuova_barca_form(request: Request, db: Session = Depends(get_db),
                           admin_user: models.User = Depends(get_current_admin_user)):
    atleti, categorie = get_atleti_e_categorie(db)
    return templates.TemplateResponse("barche/crea_barca.html",
                                      {"request": request, "current_user": admin_user, "atleti": atleti,
                                       "categorie": categorie, "barca": {}, "assigned_atleta_ids": []})


@router.post("/barche/nuova", response_class=RedirectResponse)
async def crea_barca(request: Request, db: Session = Depends(get_db),
                     admin_user: models.User = Depends(get_current_admin_user),
                     nome: str = Form(...), tipo: str = Form(...), costruttore: Optional[str] = Form(None),
                     anno_str: Optional[str] = Form(None),
                     remi_assegnati: Optional[str] = Form(None), atleti_ids: List[int] = Form([]),
                     in_manutenzione: bool = Form(False), fuori_uso: bool = Form(False),
                     in_prestito: bool = Form(False), in_trasferta: bool = Form(False),
                     disponibile_dal_str: Optional[str] = Form(None),
                     lunghezza_puntapiedi: Optional[float] = Form(None), altezza_puntapiedi: Optional[float] = Form(None),
                     apertura_totale: Optional[float] = Form(None), altezza_scalmo_sx: Optional[float] = Form(None),
                     altezza_scalmo_dx: Optional[float] = Form(None), semiapertura_sx: Optional[float] = Form(None),
                     semiapertura_dx: Optional[float] = Form(None), appruamento_appoppamento: Optional[float] = Form(None),
                     gradi_attacco: Optional[float] = Form(None), gradi_finale: Optional[float] = Form(None),
                     boccola_sx_sopra: Optional[str] = Form(None), boccola_dx_sopra: Optional[str] = Form(None),
                     rondelle_sx: Optional[str] = Form(None), rondelle_dx: Optional[str] = Form(None),
                     altezza_carrello: Optional[float] = Form(None), avanzamento_guide: Optional[float] = Form(None)):
    if (in_manutenzione or fuori_uso) and (in_prestito or in_trasferta):
        atleti, categorie = get_atleti_e_categorie(db)
        return templates.TemplateResponse("barche/crea_barca.html", {
            "request": request, "current_user": admin_user, "atleti": atleti, "categorie": categorie, "barca": {},
            "assigned_atleta_ids": [],
            "error_message": "Stato imbarcazione non valido."
        }, status_code=400)

    anno = int(anno_str) if anno_str and anno_str.strip() else None
    disponibile_dal = date.fromisoformat(disponibile_dal_str) if disponibile_dal_str and disponibile_dal_str.strip() else None

    nuova_barca = models.Barca(
        nome=nome, tipo=tipo, costruttore=costruttore, anno=anno, remi_assegnati=remi_assegnati,
        atleti_assegnati=db.query(models.User).filter(models.User.id.in_(atleti_ids)).all(),
        in_manutenzione=in_manutenzione, fuori_uso=fuori_uso, in_prestito=in_prestito, in_trasferta=in_trasferta,
        disponibile_dal=disponibile_dal,
        lunghezza_puntapiedi=lunghezza_puntapiedi, altezza_puntapiedi=altezza_puntapiedi,
        apertura_totale=apertura_totale, altezza_scalmo_sx=altezza_scalmo_sx, altezza_scalmo_dx=altezza_scalmo_dx,
        semiapertura_sx=semiapertura_sx, semiapertura_dx=semiapertura_dx,
        appruamento_appoppamento=appruamento_appoppamento, gradi_attacco=gradi_attacco, gradi_finale=gradi_finale,
        boccola_sx_sopra=boccola_sx_sopra, boccola_dx_sopra=boccola_dx_sopra, rondelle_sx=rondelle_sx,
        rondelle_dx=rondelle_dx, altezza_carrello=altezza_carrello, avanzamento_guide=avanzamento_guide
    )
    db.add(nuova_barca)
    db.commit()
    return RedirectResponse(url="/risorse/barche", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/barche/{barca_id}/modifica", response_class=HTMLResponse, name="modifica_barca_form")
async def modifica_barca_form(barca_id: int, request: Request, db: Session = Depends(get_db),
                              admin_user: models.User = Depends(get_current_admin_user)):
    barca = db.query(models.Barca).options(joinedload(models.Barca.atleti_assegnati)).get(barca_id)
    if not barca: raise HTTPException(status_code=404, detail="Barca non trovata")
    atleti, categorie = get_atleti_e_categorie(db)
    assigned_atleta_ids = {atleta.id for atleta in barca.atleti_assegnati}
    return templates.TemplateResponse("barche/modifica_barca.html",
                                      {"request": request, "current_user": admin_user, "barca": barca,
                                       "atleti": atleti, "categorie": categorie,
                                       "assigned_atleta_ids": assigned_atleta_ids})


@router.post("/barche/{barca_id}/modifica", response_class=RedirectResponse)
async def aggiorna_barca(request: Request, barca_id: int, db: Session = Depends(get_db),
                         admin_user: models.User = Depends(get_current_admin_user),
                         nome: str = Form(...), tipo: str = Form(...), costruttore: Optional[str] = Form(None),
                         anno_str: Optional[str] = Form(None),
                         remi_assegnati: Optional[str] = Form(None), atleti_ids: List[int] = Form([]),
                         in_manutenzione: bool = Form(False), fuori_uso: bool = Form(False),
                         in_prestito: bool = Form(False), in_trasferta: bool = Form(False),
                         disponibile_dal_str: Optional[str] = Form(None),
                         lunghezza_puntapiedi: Optional[float] = Form(None), altezza_puntapiedi: Optional[float] = Form(None),
                         apertura_totale: Optional[float] = Form(None), altezza_scalmo_sx: Optional[float] = Form(None),
                         altezza_scalmo_dx: Optional[float] = Form(None), semiapertura_sx: Optional[float] = Form(None),
                         semiapertura_dx: Optional[float] = Form(None),
                         appruamento_appoppamento: Optional[float] = Form(None),
                         gradi_attacco: Optional[float] = Form(None), gradi_finale: Optional[float] = Form(None),
                         boccola_sx_sopra: Optional[str] = Form(None), boccola_dx_sopra: Optional[str] = Form(None),
                         rondelle_sx: Optional[str] = Form(None), rondelle_dx: Optional[str] = Form(None),
                         altezza_carrello: Optional[float] = Form(None), avanzamento_guide: Optional[float] = Form(None)):
    barca = db.query(models.Barca).get(barca_id)
    if not barca: raise HTTPException(status_code=404, detail="Barca non trovata")

    if (in_manutenzione or fuori_uso) and (in_prestito or in_trasferta):
        atleti, categorie = get_atleti_e_categorie(db)
        assigned_atleta_ids = {atleta.id for atleta in barca.atleti_assegnati}
        return templates.TemplateResponse("barche/modifica_barca.html", {
            "request": request, "current_user": admin_user, "barca": barca, "atleti": atleti, "categorie": categorie,
            "assigned_atleta_ids": assigned_atleta_ids,
            "error_message": "Stato non valido: 'In manutenzione/Fuori uso' è incompatibile con 'In prestito/trasferta'."
        }, status_code=400)

    # Aggiornamento campi
    barca.nome, barca.tipo, barca.costruttore = nome, tipo, costruttore
    barca.anno = int(anno_str) if anno_str and anno_str.strip() else None
    barca.remi_assegnati = remi_assegnati
    barca.atleti_assegnati = db.query(models.User).filter(models.User.id.in_(atleti_ids)).all()
    barca.in_manutenzione, barca.fuori_uso, barca.in_prestito, barca.in_trasferta = in_manutenzione, fuori_uso, in_prestito, in_trasferta
    barca.disponibile_dal = date.fromisoformat(disponibile_dal_str) if disponibile_dal_str and disponibile_dal_str.strip() else None
    barca.lunghezza_puntapiedi = lunghezza_puntapiedi
    barca.altezza_puntapiedi = altezza_puntapiedi
    barca.apertura_totale = apertura_totale
    barca.altezza_scalmo_sx = altezza_scalmo_sx
    barca.altezza_scalmo_dx = altezza_scalmo_dx
    barca.semiapertura_sx = semiapertura_sx
    barca.semiapertura_dx = semiapertura_dx
    barca.appruamento_appoppamento = appruamento_appoppamento
    barca.gradi_attacco = gradi_attacco
    barca.gradi_finale = gradi_finale
    barca.boccola_sx_sopra, barca.boccola_dx_sopra = boccola_sx_sopra, boccola_dx_sopra
    barca.rondelle_sx, barca.rondelle_dx = rondelle_sx, rondelle_dx
    barca.altezza_carrello = altezza_carrello
    barca.avanzamento_guide = avanzamento_guide

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
async def view_pesi(request: Request, db: Session = Depends(get_db),
                    current_user: models.User = Depends(get_current_user), atleta_id: Optional[int] = None):
    esercizi = db.query(models.EsercizioPesi).order_by(models.EsercizioPesi.ordine).all()
    atleti, _ = get_atleti_e_categorie(db)
    selected_atleta = None
    if current_user.is_atleta:
        selected_atleta = current_user
    if (current_user.is_admin or current_user.is_allenatore) and atleta_id:
        selected_atleta = db.query(models.User).get(atleta_id)

    scheda_data = {}
    if selected_atleta:
        scheda_data = {s.esercizio_id: s for s in
                       db.query(models.SchedaPesi).filter(models.SchedaPesi.atleta_id == selected_atleta.id).all()}

    return templates.TemplateResponse("pesi.html",
                                      {"request": request, "current_user": current_user, "esercizi": esercizi,
                                       "atleti": atleti, "selected_atleta": selected_atleta,
                                       "scheda_data": scheda_data})


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
async def add_esercizio_pesi(db: Session = Depends(get_db), admin_user: models.User = Depends(get_current_admin_user),
                             nome: str = Form(...), ordine: int = Form(...)):
    db.add(models.EsercizioPesi(nome=nome, ordine=ordine))
    db.commit()
    return RedirectResponse(url="/risorse/pesi", status_code=status.HTTP_303_SEE_OTHER)