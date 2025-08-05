# File: routers/resources.py
# Descrizione: Contiene le route per la gestione delle risorse (barche e pesi).

from typing import List, Optional
from fastapi import APIRouter, Request, Depends, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session, joinedload
from fastapi.templating import Jinja2Templates

import models
from database import get_db
from dependencies import get_current_user, get_current_admin_user

router = APIRouter(prefix="/risorse", tags=["Risorse"])
templates = Jinja2Templates(directory="templates")


@router.get("/barche", response_class=HTMLResponse)
async def list_barche(request: Request, db: Session = Depends(get_db),
                      current_user: models.User = Depends(get_current_user), tipo_filter: Optional[str] = None):
    query = db.query(models.Barca)
    if tipo_filter:
        query = query.filter(models.Barca.tipo == tipo_filter)
    barche = query.order_by(models.Barca.nome).all()
    tipi_barca = db.query(models.Barca.tipo).distinct().order_by(models.Barca.tipo).all()
    return templates.TemplateResponse("barche_list.html", {
        "request": request, "current_user": current_user, "barche": barche,
        "tipi_barca": [t[0] for t in tipi_barca], "current_filter": tipo_filter
    })


@router.get("/barche/nuova", response_class=HTMLResponse)
async def nuova_barca_form(request: Request, db: Session = Depends(get_db),
                           admin_user: models.User = Depends(get_current_admin_user)):
    atleti = db.query(models.User).join(models.User.roles).filter(models.Role.name == 'atleta').order_by(
        models.User.last_name).all()
    return templates.TemplateResponse("crea_barca.html",
                                      {"request": request, "current_user": admin_user, "atleti": atleti})


@router.post("/barche/nuova", response_class=RedirectResponse)
async def crea_barca(
        db: Session = Depends(get_db), admin_user: models.User = Depends(get_current_admin_user),
        nome: str = Form(...), tipo: str = Form(...), costruttore: Optional[str] = Form(None),
        anno: Optional[int] = Form(None), remi_assegnati: Optional[str] = Form(None),
        atleti_ids: List[int] = Form([]),
        altezza_scalmi: Optional[float] = Form(None), altezza_carrello: Optional[float] = Form(None),
        apertura_totale: Optional[float] = Form(None), semiapertura_sx: Optional[float] = Form(None)
):
    atleti_assegnati = db.query(models.User).filter(models.User.id.in_(atleti_ids)).all()
    nuova_barca = models.Barca(
        nome=nome, tipo=tipo, costruttore=costruttore, anno=anno,
        remi_assegnati=remi_assegnati, atleti_assegnati=atleti_assegnati,
        altezza_scalmi=altezza_scalmi, altezza_carrello=altezza_carrello,
        apertura_totale=apertura_totale, semiapertura_sx=semiapertura_sx
    )
    db.add(nuova_barca)
    db.commit()
    return RedirectResponse(url="/risorse/barche", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/barche/{barca_id}/modifica", response_class=HTMLResponse)
async def modifica_barca_form(barca_id: int, request: Request, db: Session = Depends(get_db),
                              admin_user: models.User = Depends(get_current_admin_user)):
    barca = db.query(models.Barca).options(joinedload(models.Barca.atleti_assegnati)).filter(
        models.Barca.id == barca_id).first()
    if not barca: raise HTTPException(status_code=404, detail="Barca non trovata")
    atleti = db.query(models.User).join(models.User.roles).filter(models.Role.name == 'atleta').order_by(
        models.User.last_name).all()
    assigned_atleta_ids = {atleta.id for atleta in barca.atleti_assegnati}
    return templates.TemplateResponse("modifica_barca.html",
                                      {"request": request, "current_user": admin_user, "barca": barca, "atleti": atleti,
                                       "assigned_atleta_ids": assigned_atleta_ids})


@router.post("/barche/{barca_id}/modifica", response_class=RedirectResponse)
async def aggiorna_barca(
        barca_id: int, db: Session = Depends(get_db), admin_user: models.User = Depends(get_current_admin_user),
        nome: str = Form(...), tipo: str = Form(...), costruttore: Optional[str] = Form(None),
        anno: Optional[int] = Form(None), remi_assegnati: Optional[str] = Form(None),
        atleti_ids: List[int] = Form([]),
        altezza_scalmi: Optional[float] = Form(None), altezza_carrello: Optional[float] = Form(None),
        apertura_totale: Optional[float] = Form(None), semiapertura_sx: Optional[float] = Form(None)
):
    barca = db.query(models.Barca).filter(models.Barca.id == barca_id).first()
    if not barca: raise HTTPException(status_code=404, detail="Barca non trovata")
    barca.nome, barca.tipo, barca.costruttore, barca.anno = nome, tipo, costruttore, anno
    barca.remi_assegnati = remi_assegnati
    barca.altezza_scalmi, barca.altezza_carrello = altezza_scalmi, altezza_carrello
    barca.apertura_totale, barca.semiapertura_sx = apertura_totale, semiapertura_sx
    atleti_assegnati = db.query(models.User).filter(models.User.id.in_(atleti_ids)).all()
    barca.atleti_assegnati = atleti_assegnati
    db.commit()
    return RedirectResponse(url="/risorse/barche", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/barche/{barca_id}/elimina", response_class=RedirectResponse)
async def elimina_barca(barca_id: int, db: Session = Depends(get_db),
                        admin_user: models.User = Depends(get_current_admin_user)):
    barca = db.query(models.Barca).filter(models.Barca.id == barca_id).first()
    if not barca: raise HTTPException(status_code=404, detail="Barca non trovata")
    db.delete(barca)
    db.commit()
    return RedirectResponse(url="/risorse/barche", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/pesi", response_class=HTMLResponse)
async def view_pesi(request: Request, db: Session = Depends(get_db),
                    current_user: models.User = Depends(get_current_user), atleta_id: Optional[int] = None):
    esercizi = db.query(models.EsercizioPesi).order_by(models.EsercizioPesi.ordine).all()
    atleti = db.query(models.User).join(models.User.roles).filter(models.Role.name == 'atleta').order_by(
        models.User.last_name).all()
    scheda_data = {}
    selected_atleta = None
    if current_user.is_admin or current_user.is_allenatore:
        if atleta_id:
            selected_atleta = db.query(models.User).filter(models.User.id == atleta_id).first()
    elif current_user.is_atleta:
        selected_atleta = current_user

    if selected_atleta:
        schede = db.query(models.SchedaPesi).filter(models.SchedaPesi.atleta_id == selected_atleta.id).all()
        scheda_data = {s.esercizio_id: s for s in schede}

    return templates.TemplateResponse("pesi.html",
                                      {"request": request, "current_user": current_user, "esercizi": esercizi,
                                       "atleti": atleti, "selected_atleta": selected_atleta,
                                       "scheda_data": scheda_data})


@router.post("/pesi/update", response_class=RedirectResponse)
async def update_scheda_pesi(request: Request, db: Session = Depends(get_db),
                             current_user: models.User = Depends(get_current_user)):
    form_data = await request.form()
    atleta_id = int(form_data.get("atleta_id"))
    if not (current_user.is_admin or current_user.is_allenatore or current_user.id == atleta_id):
        raise HTTPException(status_code=403, detail="Non autorizzato")

    for key, value in form_data.items():
        if key.startswith("massimale_"):
            esercizio_id = int(key.split("_")[1])
            scheda = db.query(models.SchedaPesi).filter_by(atleta_id=atleta_id, esercizio_id=esercizio_id).first()
            if not scheda:
                scheda = models.SchedaPesi(atleta_id=atleta_id, esercizio_id=esercizio_id)
                db.add(scheda)
            scheda.massimale = float(value) if value else None
            scheda.carico_5_rep = float(form_data.get(f"5rep_{esercizio_id}")) if form_data.get(
                f"5rep_{esercizio_id}") else None
            scheda.carico_7_rep = float(form_data.get(f"7rep_{esercizio_id}")) if form_data.get(
                f"7rep_{esercizio_id}") else None
            scheda.carico_10_rep = float(form_data.get(f"10rep_{esercizio_id}")) if form_data.get(
                f"10rep_{esercizio_id}") else None
            scheda.carico_20_rep = float(form_data.get(f"20rep_{esercizio_id}")) if form_data.get(
                f"20rep_{esercizio_id}") else None

    db.commit()
    return RedirectResponse(url=f"/risorse/pesi?atleta_id={atleta_id}", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/pesi/add_esercizio", response_class=RedirectResponse)
async def add_esercizio_pesi(db: Session = Depends(get_db), admin_user: models.User = Depends(get_current_admin_user),
                             nome: str = Form(...), ordine: int = Form(...)):
    new_esercizio = models.EsercizioPesi(nome=nome, ordine=ordine)
    db.add(new_esercizio)
    db.commit()
    return RedirectResponse(url="/risorse/pesi", status_code=status.HTTP_303_SEE_OTHER)
