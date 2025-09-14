# File: seed.py
import os
import sys
from datetime import date, datetime, timedelta, time
from decimal import Decimal
import logging
import random
from sqlalchemy import or_

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
from models import *
import security

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- DATI ESTRATTI E PULITI DAL PDF ---
atleti_data = [
    # ... i tuoi dati degli atleti rimangono invariati ...
    {'nome': 'MASSIMO', 'cognome': 'ARMENI', 'data_nascita': '01/10/1968', 'email': 'massimoarmeni@icloud.com',
     'cf': 'RMNMSM68R01L117G', 'data_tess': '08/01/2025', 'scad_cert': '04/11/2025',
     'indirizzo': 'VIA OTTORINO VILLA 18 - 25124 BRESCIA'},
    {'nome': 'GIADA', 'cognome': 'BELLI', 'data_nascita': '21/08/2012', 'email': 'sonia.moretti@virgilio.it',
     'cf': 'BLLGDI12M61B157H', 'data_tess': '08/01/2025', 'scad_cert': '17/01/2026',
     'indirizzo': 'VIA NAZIONALE, 55 - 24060 PIANICO'},
    {'nome': 'MATTIA', 'cognome': 'BELLI', 'data_nascita': '21/08/2012', 'email': 'sonia.moretti@virgilio.it',
     'cf': 'BLLMTT12M21B157B', 'data_tess': '08/01/2025', 'scad_cert': '17/01/2026',
     'indirizzo': 'VIA NAZIONALE, 55 - 24060 PIANICO'},
    {'nome': 'PIETRO', 'cognome': 'BIANCHI', 'data_nascita': '06/01/2009', 'email': 'giusy.foresti@virgilio.it',
     'cf': 'BNCPTR09A06D434K', 'data_tess': '08/01/2025', 'scad_cert': '26/09/2025',
     'indirizzo': 'VIA DEI FANTONI, 5 - 24060 SOLTO COLLINA'},
    {'nome': 'TOMMASO', 'cognome': 'BIGONI', 'data_nascita': '23/01/2007', 'email': 'tommasobigoni@outlook.it',
     'cf': 'BGNTMS07A23A794E', 'data_tess': '08/01/2025', 'scad_cert': '03/06/2026',
     'indirizzo': 'VIA ANTONIO LOCATELLI, 9 - 24060 ENDINE GAIANO'},
    {'nome': 'ALESSANDRO', 'cognome': 'BONETTI', 'data_nascita': '12/02/2013', 'email': 'claudia.delasa@tiscali.it',
     'cf': 'BNTLSN13B12D434S', 'data_tess': '08/01/2025', 'scad_cert': '23/04/2026',
     'indirizzo': 'VIA MAMELI NR 7 - 24060 ROGNO'},
    {'nome': 'REBECCA', 'cognome': 'BONETTI', 'data_nascita': '24/07/2010', 'email': 'claudia.delasa@tiscali.it',
     'cf': 'BNTRCC10L64D434Q', 'data_tess': '08/01/2025', 'scad_cert': '22/08/2025',
     'indirizzo': 'VIA GOFFREDO MAMELI, 7 - 24060 ROGNO'},
    {'nome': 'ARISTIDE', 'cognome': 'BONOMELLI', 'data_nascita': '25/09/1982', 'email': 'aristidebonomelli@hotmail.com',
     'cf': 'BNMRTD82P251628S', 'data_tess': '24/03/2025', 'scad_cert': '10/03/2026',
     'indirizzo': 'VIA TONALE E MENDOLA 198 - 24060 ENDINE GAIANO'},
    {'nome': 'ANASTASIA', 'cognome': 'BUZZI', 'data_nascita': '29/06/2011', 'email': 'f.bettineschi@hotmail.it',
     'cf': 'BZZNTS11H69A794R', 'data_tess': '08/01/2025', 'scad_cert': '26/02/2025',
     'indirizzo': 'VIA DON G PEZZOTTA, 322 - 24060 RANZANICO'},
    {'nome': 'SOFIA', 'cognome': 'CABRINI', 'data_nascita': '12/03/2010', 'email': 'sofiacabrini2010@gmail.com',
     'cf': 'CBRSFO10C52G574F', 'data_tess': '20/03/2025', 'scad_cert': '25/02/2026',
     'indirizzo': 'VIA SAN DEFENDENTE NR 48 - 24023 CLUSONE'},
    {'nome': 'MARCO', 'cognome': 'CAMBIERI', 'data_nascita': '03/02/2002', 'email': 'marcocambieri2002@gmail.com',
     'cf': 'CMBMRC02B03C800T', 'data_tess': '05/06/2025', 'scad_cert': '29/05/2026',
     'indirizzo': 'VIA G. PAGLIA 6 - 24065 LOVERE'},
    {'nome': 'PAOLO', 'cognome': 'CANU', 'data_nascita': '08/10/1961', 'email': 'paolo.canu@unipd.it',
     'cf': 'CNAPLA61R08E704H', 'data_tess': '08/01/2025', 'scad_cert': '02/10/2025',
     'indirizzo': 'VIA COLLE NR 3 - 24069 TRESCORE BALNEARIO'},
    {'nome': 'AMELIA', 'cognome': 'CENSI', 'data_nascita': '27/07/2010', 'email': 'info@canottierisebino.it',
     'cf': 'CNSMLA10L67E3330', 'data_tess': '08/01/2025', 'scad_cert': '14/01/2026',
     'indirizzo': 'VIA CASINO BAGLIONI, 17 - 24062 COSTA VOLPINO'},
    {'nome': 'CHLOE ANGELICA', 'cognome': 'CHAUVET', 'data_nascita': '08/09/2010',
     'email': 'emilianegrinotti@gmail.com', 'cf': 'CHVCLN10P48G752W', 'data_tess': '08/01/2025',
     'scad_cert': '23/11/2025', 'indirizzo': 'VIA RONCHELLI NR.10 - 24060 RIVA DI SOLTO'},
    {'nome': 'BENEDETTO', 'cognome': 'CHIARELLI', 'data_nascita': '24/03/2009', 'email': 'benedetto09@gmail.com',
     'cf': 'CHRBDT09C24G574E', 'data_tess': '08/01/2025', 'scad_cert': '24/04/2026',
     'indirizzo': 'VIA GIARDINI, 9 - 24060 BOSSICO'},
    {'nome': 'CARLOS', 'cognome': 'COCCHETTI', 'data_nascita': '14/05/2014', 'email': 'maddalena-baiguini@tiscali.it',
     'cf': 'CCCCLS14E14D434F', 'data_tess': '14/01/2025', 'scad_cert': '11/01/2026',
     'indirizzo': 'VIA BREDE, 3 - 24062 COSTA VOLPINO'},
    {'nome': 'ANDREA', 'cognome': 'COLOMBI', 'data_nascita': '03/10/2013', 'email': 'semper.b@email.it',
     'cf': 'CLMNDR13R0381571', 'data_tess': '08/01/2025', 'scad_cert': '20/01/2026',
     'indirizzo': 'VIA XXV APRILE NR 8/A - 24063 CASTRO'},
    {'nome': 'GIOELE', 'cognome': 'COTTI COMETTINI', 'data_nascita': '01/02/2013', 'email': 'manuela.uberti@gmail.com',
     'cf': 'CTTGLI13B01A794Q', 'data_tess': '08/01/2025', 'scad_cert': '27/01/2026',
     'indirizzo': 'VIA ORTIGARA 8/D - 24062 COSTA VOLPINO'},
    {'nome': 'STEFANO', 'cognome': 'DELBELLO', 'data_nascita': '14/06/1986', 'email': 'stefanodelbello@gmail.com',
     'cf': 'DLBSFN86H14E7040', 'data_tess': '08/01/2025', 'scad_cert': '13/02/2026',
     'indirizzo': "VIA F.LLI CALVI, 9 - 24060 SOVERE"},
    {'nome': 'ANDREA', 'cognome': 'FACCHINETTI', 'data_nascita': '11/08/2011', 'email': 'gloria.franzoni.gf@gmail.com',
     'cf': 'FCCNDR11M11E333U', 'data_tess': '08/01/2025', 'scad_cert': '08/12/2025',
     'indirizzo': 'VIA PINETA 14 - 25050 OSSIMO'},
    {'nome': 'NICOLA', 'cognome': 'FIGAROLI', 'data_nascita': '11/05/2010', 'email': 'elena.76@gmail.com',
     'cf': 'FGRNCL10E11G574X', 'data_tess': '08/01/2025', 'scad_cert': '30/01/2026',
     'indirizzo': 'VIA SETTE COLLI, 103/B - 24060 BOSSICO'},
    {'nome': 'ALESSANDRO', 'cognome': 'FRANINI', 'data_nascita': '30/08/2010', 'email': 'fari.simo@alice.it',
     'cf': 'FRNLSN10M30D434C', 'data_tess': '08/01/2025', 'scad_cert': '12/12/2025',
     'indirizzo': 'VIA AURORA.NR 6 - 24062 COSTA VOLPINO'},
    {'nome': 'ANNA', 'cognome': 'FRANINI', 'data_nascita': '02/01/2013', 'email': 'fari.simo@alice.it',
     'cf': 'FRNNNA13A42D434Q', 'data_tess': '08/01/2025', 'scad_cert': '25/01/2026',
     'indirizzo': 'VIA AURORA NR 6 - 24062 COSTA VOLPINO'},
    {'nome': 'MICHELE', 'cognome': 'GALLIZIOLI', 'data_nascita': '19/08/2011', 'email': 'helenatorri42@gmail.com',
     'cf': 'GLLMHL11M19D434F', 'data_tess': '08/01/2025', 'scad_cert': '14/01/2026',
     'indirizzo': 'VIA GIUSEPPE GARIBALDI NR 22 24063-CASTRO'},
    {'nome': 'PAOLO', 'cognome': 'GHIDINI', 'data_nascita': '06/08/1992', 'email': 'paologhidini92@gmail.com',
     'cf': 'GHDPLA92M06E704E', 'data_tess': '08/01/2025', 'scad_cert': '13/03/2026',
     'indirizzo': 'VIA IV NOVEMBRE NR 22 - 24065 LOVERE'},
    {'nome': 'GIORGIA', 'cognome': 'GIRELLI', 'data_nascita': '30/05/1997', 'email': 'giorgiagirelliscuola@gmail.com',
     'cf': 'GRLGRG97E70D434V', 'data_tess': '08/01/2025', 'scad_cert': '03/03/2026',
     'indirizzo': 'VIA CAMILLO CAVOUR, 16A - 25047 DARFO BOARIO TERME'},
    {'nome': 'SIMONA', 'cognome': 'GUARNERI', 'data_nascita': '18/09/1971', 'email': 'guameri_simona@libero.it',
     'cf': 'GRNSMN71P58F119R', 'data_tess': '08/01/2025', 'scad_cert': '20/09/2025',
     'indirizzo': 'VIA PALAZZINE, 27 - 24060 FONTENO'},
    {'nome': 'EMMA', 'cognome': 'GUERINI', 'data_nascita': '06/10/2011', 'email': 'stefini.sara@gmail.com',
     'cf': 'GRNIMME11R46D4341', 'data_tess': '08/01/2025', 'scad_cert': '23/05/2026',
     'indirizzo': "VIA CA' POETA, 9 - 24062 COSTA VOLPINO"},
    {'nome': 'GABRIELE', 'cognome': 'GUERINI', 'data_nascita': '22/04/2010', 'email': 'stefini.sara@gmail.com',
     'cf': 'GRNGRL10D22D434L', 'data_tess': '08/01/2025', 'scad_cert': '10/03/2026',
     'indirizzo': "VIA CA' POETA NR 9 - 24062 COSTA VOLPINO"},
    {'nome': 'ALICE', 'cognome': 'IANNONE', 'data_nascita': '29/03/2013', 'email': 'nikianno@alice.it',
     'cf': 'NNNLCA13C69E333V', 'data_tess': '08/01/2025', 'scad_cert': '26/03/2026',
     'indirizzo': 'VIA PAPA GIOVANNI PAOLO 1, 29 - 24060 SOVERE'},
    {'nome': 'ANTONIO', 'cognome': 'IANNONE', 'data_nascita': '06/01/2011', 'email': 'nikianno@alice.it',
     'cf': 'NNNNTN11A06E333B', 'data_tess': '08/01/2025', 'scad_cert': '21/03/2025',
     'indirizzo': 'VIA PAPA GIOVANNI PAOLO 1, 29 - 24060 SOVERE'},
    {'nome': 'SANDRA', 'cognome': 'LEONARDI', 'data_nascita': '13/07/1975', 'email': 'a_leosan@hotmail.com',
     'cf': 'LNRSDR75L53A290Q', 'data_tess': '08/01/2025', 'scad_cert': '25/03/2026',
     'indirizzo': 'VIALE ALCIDE DE GASPERI, 36 - 25047 DARFO BOARIO TERME'},
    {'nome': 'NICOLA', 'cognome': 'MANELLA', 'data_nascita': '22/06/1990', 'email': 'nicola.manella@yahoo.it',
     'cf': 'MNLNCL90H22E704J', 'data_tess': '08/01/2025', 'scad_cert': '03/03/2026',
     'indirizzo': 'VIA TORRICELLA 25/D - 24065 LOVERE'},
    {'nome': 'GIANBATTISTA', 'cognome': 'MARTINOLI', 'data_nascita': '29/09/1963', 'email': 'martigianni@gmail.com',
     'cf': 'MRTGBT63P29E704S', 'data_tess': '08/01/2025', 'scad_cert': '03/10/2025',
     'indirizzo': 'VIA DEL SERRO, 12 - 24063 CASTRO'},
    {'nome': 'ELISA', 'cognome': 'MARZELLA', 'data_nascita': '10/04/2007', 'email': 'lella.catta@gmail.com',
     'cf': 'MRZLSE07D50C800Y', 'data_tess': '08/01/2025', 'scad_cert': '11/01/2026',
     'indirizzo': 'VIA CAMILLO CAVOUR, 71 - 24028 PONTE NOSSA'},
    {'nome': 'LUCIA', 'cognome': 'MAZZA', 'data_nascita': '25/05/2010', 'email': 'casalemazza@gmail.com',
     'cf': 'MZZLCU10E65G574J', 'data_tess': '08/01/2025', 'scad_cert': '23/09/2025',
     'indirizzo': 'VIA GAIA, 34 - 24065 LOVERE'},
    {'nome': 'ANNA', 'cognome': 'OSCAR', 'data_nascita': '18/06/1959', 'email': 'anussi@alice.it',
     'cf': 'SCRNNA59H58A794X', 'data_tess': '08/01/2025', 'scad_cert': '02/10/2025',
     'indirizzo': 'VIA COLLE NR 3 - 24069 TRESCORE BALNEARIO'},
    {'nome': 'BEATRICE', 'cognome': 'PEDRAZZANI', 'data_nascita': '14/01/2012',
     'email': 'matteo.pedrazzani75@gmail.com', 'cf': 'PDRBRC12A54A470H', 'data_tess': '08/01/2025',
     'scad_cert': '09/11/2025', 'indirizzo': 'VIA SAN GOTTARDO NR 9 - 24062 COSTA VOLPINO'},
    {'nome': 'ANNA', 'cognome': 'PERINI', 'data_nascita': '17/07/1968', 'email': 'anna.perini@icteam.it',
     'cf': 'PRNNNA68L57A794B', 'data_tess': '08/01/2025', 'scad_cert': '16/04/2026',
     'indirizzo': 'PIAZZA MADRE TERESA DI CALCUTTA 9 - 24020 VILLA DI SERIO'},
    {'nome': 'ALESSANDRA', 'cognome': 'PICINELLI', 'data_nascita': '25/10/1976',
     'email': 'picinelli.alessandra@gmail.com', 'cf': 'PCNLSN76R65E704L', 'data_tess': '08/01/2025',
     'scad_cert': '10/07/2025', 'indirizzo': 'VIA DELLA BOSCHETTA, 11 - 24062 COSTA VOLPINO'},
    {'nome': 'SERGIO', 'cognome': 'QUARENGHI', 'data_nascita': '29/11/1968', 'email': 'sergio.quarenghi@libero.it',
     'cf': 'QRNSRG68S29B157A', 'data_tess': '08/01/2025', 'scad_cert': '11/03/2026',
     'indirizzo': 'VIA VIGHENZI NR 3 - 25124 BRESCIA'},
    {'nome': 'CHIARA', 'cognome': 'RONCHETTI', 'data_nascita': '16/11/2011', 'email': 'mauroronchetti@hotmail.it',
     'cf': 'RNCCHR11S56G574A', 'data_tess': '08/01/2025', 'scad_cert': '04/03/2026',
     'indirizzo': 'VIA CAPOFERRI, 1 - 24063 CASTRO'},
    {'nome': 'GIULIA', 'cognome': 'ROTA', 'data_nascita': '29/05/2008', 'email': 'andrearotaedania@gmail.com',
     'cf': 'RTOGLI08E69D434V', 'data_tess': '08/01/2025', 'scad_cert': '08/10/2025',
     'indirizzo': 'VIA NAZIONALE NR 7 - 24062 COSTA VOLPINO'},
    {'nome': 'CHIARA', 'cognome': 'RUSCITTO', 'data_nascita': '29/01/1973', 'email': 'chiara.ruscitto@gmail.com',
     'cf': 'RSCCHR73T69L388R', 'data_tess': '07/04/2025', 'scad_cert': '01/10/2025',
     'indirizzo': 'VIA TERZAGO 3 - 24020 SCANZOROSCIATE'},
    {'nome': 'DANIELE', 'cognome': 'SBARDOLINI', 'data_nascita': '28/04/1989', 'email': 'danielesbardolini@tiscali.it',
     'cf': 'SBRDNL89D28B149H', 'data_tess': '07/04/2025', 'scad_cert': '28/03/2026',
     'indirizzo': 'VIA CASTELLAZZO NR 30 - 25055 PISOGNE'},
    {'nome': 'MATTIA', 'cognome': 'SERRA', 'data_nascita': '14/07/2010', 'email': 'smatti1410@gmail.com',
     'cf': 'SRRMTT10L14H501M', 'data_tess': '24/02/2025', 'scad_cert': '30/01/2026',
     'indirizzo': 'VIALE DANTE ALIGHIERI, 5 - 24065 LOVERE'},
    {'nome': 'GIOVANNI', 'cognome': 'SILVESTRI', 'data_nascita': '24/11/2010', 'email': 'luigisilvestri@live.com',
     'cf': 'SLVGNN10S24D434P', 'data_tess': '08/01/2025', 'scad_cert': '28/01/2026',
     'indirizzo': 'VIA FRATELLI CALVI NR 8 - 24060 PIANICO'},
    {'nome': 'EMMA', 'cognome': 'STERNI', 'data_nascita': '26/11/2008', 'email': 'emmastemi08@gmail.com',
     'cf': 'STRMME08S66I628D', 'data_tess': '08/01/2025', 'scad_cert': '10/12/2025',
     'indirizzo': 'VIA CESARE BATTISTI NR 1 - 24060 ROGNO'},
    {'nome': 'PAOLO ALBERTO', 'cognome': 'STERNI', 'data_nascita': '28/04/1979', 'email': 'paolosterni@gmail.com',
     'cf': 'STRPLB79D28I628B', 'data_tess': '19/02/2025', 'scad_cert': '27/12/2025',
     'indirizzo': 'VIA ARIA LIBERA, 12 - 24062 COSTA VOLPINO'},
    {'nome': 'LORENZO', 'cognome': 'TURLA', 'data_nascita': '09/03/2009', 'email': 'barby.foresti@gmail.com',
     'cf': 'TRLLNZ09C09E333S', 'data_tess': '08/01/2025', 'scad_cert': '23/01/2026',
     'indirizzo': 'VIA CURO, 8 - 24062 COSTA VOLPINO'},
    {'nome': 'ALESSANDRO', 'cognome': 'ZAMBETTI', 'data_nascita': '13/03/2015', 'email': 'mauramoviggia@hotmail.com',
     'cf': 'ZMBLSN15C13B157I', 'data_tess': '28/04/2025', 'scad_cert': '14/11/2025',
     'indirizzo': 'VIA MADRERA NR 52 - 24060 RANZANICO'},
    {'nome': 'LEONARDO', 'cognome': 'ZANA', 'data_nascita': '23/12/2010', 'email': 'n.zana@lucchinirs.com',
     'cf': 'ZNALRD10T23D434C', 'data_tess': '08/01/2025', 'scad_cert': '10/04/2026',
     'indirizzo': 'VIA QUAIA NR 5 - 24060 PIANICO'},
    {'nome': 'NOEMI', 'cognome': 'ZANA', 'data_nascita': '03/09/2012', 'email': 'n.zana@lucchinirs.com',
     'cf': 'ZNANMO12P43D434S', 'data_tess': '09/01/2025', 'scad_cert': '05/11/2025',
     'indirizzo': 'VIA QUAIA NR 5 - 24060 PIANICO'},
]

# --- DATI BARCHE INTEGRATI ---
barche_data = [
    {"nome": "Gemma", "tipo": "1x", "costruttore": "Filippi", "anno": 2006},
    {"nome": "Nuovo", "tipo": "1x", "costruttore": "Filippi", "anno": 2007},
    {"nome": "Baba", "tipo": "1x", "costruttore": "Filippi", "anno": 2009},
    {"nome": "Betty", "tipo": "1x", "costruttore": "Filippi", "anno": 2007},
    {"nome": "6", "tipo": "1x", "costruttore": "Filippi", "anno": 2003},
    {"nome": "5", "tipo": "1x", "costruttore": "Filippi", "anno": 2002},
    {"nome": "7", "tipo": "1x", "costruttore": "Filippi", "anno": 2004},
    {"nome": "Forza e Costanza", "tipo": "2x", "costruttore": "Filippi", "anno": 2008},
    {"nome": "Tiziana Ciro", "tipo": "2x", "costruttore": "Filippi", "anno": 2010},
    {"nome": "Maria Luisa", "tipo": "2x", "costruttore": "Filippi", "anno": 2008},
    {"nome": "Felice", "tipo": "2x-", "costruttore": "Filippi", "anno": 2011},
    {"nome": "Macon", "tipo": "4x", "costruttore": "Filippi", "anno": 2002},
    {"nome": "Edo", "tipo": "4x-", "costruttore": "Filippi", "anno": 2007},
    {"nome": "OTTO", "tipo": "8+", "costruttore": "Filippi", "anno": 2015},
]


def seed_barche(db: Session):
    logger.info("Popolamento barche...")
    if db.query(Barca).count() > 0:
        logger.info("Tabella barche già popolata. Skippo.")
        return
    try:
        barche_da_creare = [Barca(**data) for data in barche_data]
        db.add_all(barche_da_creare)
        db.commit()
        logger.info(f"{len(barche_da_creare)} barche popolate con successo.")
    except Exception as e:
        logger.error(f"Errore durante il popolamento delle barche: {e}")
        db.rollback()


def seed_pesi(db: Session):
    """Popola gli esercizi della scheda pesi."""
    logger.info("Popolamento esercizi pesi...")
    if db.query(EsercizioPesi).count() > 0:
        logger.info("Tabella esercizi pesi già popolata. Skippo.")
        return
    esercizi = [
        {"ordine": 1, "nome": "Trazioni"},
        {"ordine": 2, "nome": "Pressa orizzontale"},
        {"ordine": 3, "nome": "Pulley"},
        {"ordine": 4, "nome": "Squat"},
        {"ordine": 5, "nome": "Leg extension"},
        {"ordine": 6, "nome": "Panca piana"},
        {"ordine": 7, "nome": "Pressa 45°"},
    ]
    db.add_all([EsercizioPesi(**e) for e in esercizi])
    db.commit()

def seed_categories(db: Session):
    logger.info("Popolamento categorie...")
    if db.query(Categoria).count() > 0:
        logger.info("Tabella categorie già popolata. Skippo.")
        return
    categorie = [
        Categoria(nome="Allievo A", eta_min=0, eta_max=10, ordine=1, macro_group="Under 14"),
        Categoria(nome="Allievo B1", eta_min=11, eta_max=11, ordine=2, macro_group="Under 14"),
        Categoria(nome="Allievo B2", eta_min=12, eta_max=12, ordine=3, macro_group="Under 14"),
        Categoria(nome="Allievo C", eta_min=13, eta_max=13, ordine=4, macro_group="Under 14"),
        Categoria(nome="Cadetto", eta_min=14, eta_max=14, ordine=5, macro_group="Under 14"),
        Categoria(nome="Ragazzo", eta_min=15, eta_max=16, ordine=6, macro_group="Over 14"),
        Categoria(nome="Junior", eta_min=17, eta_max=18, ordine=7, macro_group="Over 14"),
        Categoria(nome="Under 23", eta_min=19, eta_max=23, ordine=8, macro_group="Over 14"),
        Categoria(nome="Senior", eta_min=24, eta_max=27, ordine=9, macro_group="Over 14"),
        Categoria(nome="Master", eta_min=28, eta_max=150, ordine=10, macro_group="Master"),
    ]
    db.add_all(categorie)
    db.commit()


def seed_turni(db: Session):
    """Crea i turni predefiniti dell'estate 2025 se la tabella è vuota."""
    if db.query(Turno).count() > 0:
        logger.info("Tabella turni già popolata. Skippo.")
        return
    logger.info("Popolamento turni estivi 2025...")
    start = date(2025, 6, 1)
    end = date(2025, 9, 15)
    day = start
    while day <= end:
        if day.weekday() != 0:
            db.add(Turno(data=day, fascia_oraria="Mattina"))
            email="info@canottierisebino.it",
        day += timedelta(days=1)
    db.commit()

    # Assegna casualmente gli allenatori a tutti i turni fino al 15 settembre 2025
    allenatori = (
        db.query(User)
        .join(User.roles)
        .filter(Role.name == "allenatore")
        .all()
    )
    if allenatori:
        limite = end
        turni_da_assegnare = (
            db.query(Turno)
            .filter(Turno.data <= limite)
            .all()
        )
        for turno in turni_da_assegnare:
            turno.user = random.choice(allenatori)
        db.commit()


def seed_default_allenamenti(db: Session):
    """Inserisce alcuni allenamenti di esempio se non presenti."""
    if db.query(Allenamento).count() > 0:
        logger.info("Allenamenti già presenti. Skippo seeding di esempio.")
        return
    logger.info("Popolamento allenamenti di esempio...")
    categorie = {c.nome: c for c in db.query(Categoria).all()}
    esempi = [
        ("Barca", date(2025, 6, 5), "08:00-10:00", ["Allievo A"]),
        ("Corsa", date(2025, 6, 6), "10:00-11:00", ["Junior", "Senior"]),
        ("Pesi", date(2025, 6, 7), "17:00-18:30", ["Master"]),
    ]
    allenatori = (
        db.query(User)
        .join(User.roles)
        .filter(Role.name == "allenatore")
        .all()
    )
    for idx, (tipo, giorno, orario, cats) in enumerate(esempi):
        a = Allenamento(tipo=tipo, data=giorno, orario=orario)
        for nome in cats:
            cat = categorie.get(nome)
            if cat:
                a.categories.append(cat)
        if allenatori:
            a.coaches.append(allenatori[idx % len(allenatori)])
        db.add(a)
    db.commit()


def seed_test_allenamenti(db: Session):
    """Genera 300 allenamenti di test dal 18 agosto 2025 in poi."""
    if db.query(Allenamento).count() >= 300:
        logger.info("Allenamenti di test già presenti. Skippo.")
        return
    logger.info("Generazione di 300 allenamenti di test...")
    descrizioni = [
        ("Barca", "Fondo 16 km"),
        ("Barca", "Colpi 30-10"),
        ("Barca", "Colpi 20-10"),
        ("Circuito", "Circuito 4x15es"),
        ("Pesi", "Pesi 6x8 rip"),
        ("Barca", "Interval 5x5 min"),
        ("Barca", "Tecnica in singolo 10 km"),
        ("Remoergometro", "Remoergometro 3x20 min"),
        ("Corsa", "Corsa 10 km"),
        ("Barca", "Fartlek 45 min"),
    ]
    orari = ["06:00-08:00", "08:30-10:30", "15:00-17:00", "17:30-19:30"]
    categories = db.query(Categoria).all()
    coaches = (
        db.query(User)
        .join(User.roles)
        .filter(Role.name == "allenatore")
        .all()
    )
    day = date(2025, 8, 18)
    created = 0
    while created < 300:
        sessions_today = random.randint(1, 2)
        for _ in range(sessions_today):
            if created >= 300:
                break
            tipo, descr = random.choice(descrizioni)
            allen = Allenamento(
                tipo=tipo,
                descrizione=descr,
                data=day,
                orario=random.choice(orari),
            )
            cats = random.sample(
                categories,
                k=min(len(categories), random.randint(1, 3)),
            )
            for c in cats:
                allen.categories.append(c)
            if coaches:
                for coach in random.sample(
                    coaches, k=random.randint(1, min(2, len(coaches)))
                ):
                    allen.coaches.append(coach)
            db.add(allen)
            created += 1
        day += timedelta(days=1)
    db.commit()


def main():
    logger.info("Avvio script di seeding completo...")
    logger.info("ATTENZIONE: Verranno cancellati tutti i dati esistenti nel database.")
    input("Premi Invio per continuare, o CTRL+C per annullare...")
    
    # Gestione più sicura del database
    try:
        Base.metadata.drop_all(bind=engine)
        logger.info("Tabelle esistenti rimosse.")
    except Exception as e:
        logger.warning(f"Errore durante la rimozione delle tabelle: {e}")
    
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Tabelle create.")
    except Exception as e:
        logger.error(f"Errore durante la creazione delle tabelle: {e}")
        return

    db = SessionLocal()
    try:
        # Popola Ruoli
        ruoli_da_creare = ['atleta', 'allenatore', 'istruttore', 'admin']
        for nome_ruolo in ruoli_da_creare:
            if not db.query(Role).filter_by(name=nome_ruolo).first():
                db.add(Role(name=nome_ruolo))
        db.commit()
        logger.info("Ruoli popolati.")

        # Popola categorie e dati base
        seed_categories(db)
        seed_pesi(db)

        # Crea Utente Admin Gabriele Manenti
        admin_username = "gabriele.manenti"
        admin_password = "gabriele123"
        if not db.query(User).filter(User.username == admin_username).first():
            admin_role = db.query(Role).filter_by(name='admin').one()
            allenatore_role = db.query(Role).filter_by(name='allenatore').one()
            istruttore_role = db.query(Role).filter_by(name='istruttore').one()
            admin_user = User(
                username=admin_username, 
                hashed_password=security.get_password_hash(admin_password),
                first_name="Gabriele", 
                last_name="Manenti", 
                email="gabriele.manenti@example.com",
                date_of_birth=date(2005, 3, 10), 
                roles=[admin_role, allenatore_role, istruttore_role]
            )
            db.add(admin_user)
            db.commit()
            logger.info(f"Utente admin '{admin_username}' (Gabriele Manenti) creato con ruoli Admin, Allenatore e Istruttore.")

        # Popola Atleti
        atleta_role = db.query(Role).filter_by(name='atleta').one()
        emails_usate = {"gabriele.manenti@example.com"}
        atleti_creati = 0
        for atleta in atleti_data:
            nome = atleta['nome'].title()
            cognome = atleta['cognome'].title()
            username_base = f"{nome.split(' ')[0]}.{cognome.split(' ')[0]}".lower().replace("'", "")
            username = username_base
            counter = 1
            while db.query(User).filter(User.username == username).first():
                username = f"{username_base}{counter}"
                counter += 1

            original_email = atleta['email']
            final_email = original_email
            if final_email in emails_usate:
                try:
                    local_part, domain = original_email.split('@')
                    email_counter = 1
                    while True:
                        final_email = f"{local_part}+{email_counter}@{domain}"
                        if final_email not in emails_usate: break
                        email_counter += 1
                except ValueError:
                    continue

            if db.query(User).filter(User.email == final_email).first():
                continue

            new_user = User(
                username=username, hashed_password=security.get_password_hash(username),
                first_name=nome, last_name=cognome, email=final_email,
                date_of_birth=datetime.strptime(atleta['data_nascita'], '%d/%m/%Y').date(),
                tax_code=atleta.get('cf'),
                membership_date=datetime.strptime(atleta['data_tess'], '%d/%m/%Y').date(),
                certificate_expiration=datetime.strptime(atleta['scad_cert'], '%d/%m/%Y').date(),
                address=atleta.get('indirizzo', '').replace('\n', ' ')
            )
            new_user.roles.append(atleta_role)
            db.add(new_user)
            emails_usate.add(final_email)
            atleti_creati += 1

        db.commit()
        logger.info(f"{atleti_creati} atleti popolati con successo.")
        # Aggiungi allenatori predefiniti
        allenatore_role = db.query(Role).filter_by(name='allenatore').one()
        coaches_data = [
            {
                'username': 'alberto.carizzoni',
                'first_name': 'Alberto',
                'last_name': 'Carizzoni',
                'email': 'alberto.carizzoni@example.com',
                'date_of_birth': date(2003, 5, 17),
            },
            {
                'username': 'anna.manenti',
                'first_name': 'Anna',
                'last_name': 'Manenti',
                'email': 'anna.manenti@example.com',
                'date_of_birth': date(2007, 5, 21),
            },
        ]
        for coach in coaches_data:
            if not db.query(User).filter_by(username=coach['username']).first():
                user = User(
                    username=coach['username'],
                    hashed_password=security.get_password_hash(coach['username']),
                    first_name=coach['first_name'],
                    last_name=coach['last_name'],
                    email=coach['email'],
                    date_of_birth=coach['date_of_birth'],
                )
                user.roles.append(allenatore_role)
                db.add(user)

        # Attribuisci ruolo allenatore a Tommaso Bigoni e Marco Cambieri
        for nome, cognome in [("Tommaso", "Bigoni"), ("Marco", "Cambieri")]:
            atleta = db.query(User).filter_by(first_name=nome, last_name=cognome).first()
            if atleta and allenatore_role not in atleta.roles:
                atleta.roles.append(allenatore_role)

        db.commit()
        logger.info("Allenatori aggiunti e ruoli aggiornati.")
        
        # Assegna ruolo Istruttore a tutti gli Allenatori
        istruttore_role = db.query(Role).filter_by(name='istruttore').first()
        if istruttore_role:
            allenatori = db.query(User).join(User.roles).filter(Role.name == 'allenatore').all()
            for allenatore in allenatori:
                if istruttore_role not in allenatore.roles:
                    allenatore.roles.append(istruttore_role)
                    logger.info(f"Ruolo Istruttore assegnato a {allenatore.first_name} {allenatore.last_name}")
            db.commit()
            logger.info(f"Ruolo Istruttore assegnato a {len(allenatori)} allenatori.")

        # Popola turni e allenamenti di test (richiedono allenatori)
        seed_turni(db)
        seed_test_allenamenti(db)

        # Popola Barche
        seed_barche(db)
        
        # Popola dati per le attività
        seed_activities_data(db)

    except Exception as e:
        logger.error(f"Errore durante il seeding: {e}")
        db.rollback()
    finally:
        db.close()
    logger.info("Seeding completato!")


def seed_activities_data(db: Session):
    """Popola i dati iniziali per le attività."""
    try:
        logger.info("Popolamento dati attività...")
        
        # Crea tipi di qualifica se non esistono
        if db.query(QualificationType).count() == 0:
            qualification_types = [
                QualificationType(name="Aiuto-istruttore", is_active=True),
                QualificationType(name="Istruttore canottaggio", is_active=True),
                QualificationType(name="Istruttore kayak", is_active=True),
                QualificationType(name="Timoniere vichinga", is_active=True),
                QualificationType(name="Autista gommone", is_active=True),
                QualificationType(name="Autista furgone", is_active=True),
            ]
            db.add_all(qualification_types)
            db.commit()
            logger.info("Tipi di qualifica creati.")
        
        # Crea tipi di attività se non esistono
        if db.query(ActivityType).count() == 0:
            activity_types = [
                ActivityType(name="Canottaggio", color="#007bff", is_active=True),
                ActivityType(name="Kayak", color="#28a745", is_active=True),
                ActivityType(name="SUP", color="#ffc107", is_active=True),
                ActivityType(name="Vichinga", color="#dc3545", is_active=True),
                ActivityType(name="Kayak + Vichinga", color="#6f42c1", is_active=True),
                ActivityType(name="Canottaggio + Kayak", color="#fd7e14", is_active=True),
                ActivityType(name="Corso CAS", color="#20c997", is_active=True),
                ActivityType(name="Teambuilding", color="#6c757d", is_active=True),
                ActivityType(name="Altro", color="#e83e8c", is_active=True),
            ]
            db.add_all(activity_types)
            db.commit()
            logger.info("Tipi di attività creati.")
        
        # Crea attività di esempio se non esistono
        if db.query(Activity).count() == 0:
            # Ottieni i tipi creati
            kayak_type = db.query(ActivityType).filter_by(name="Kayak").first()
            teambuilding_type = db.query(ActivityType).filter_by(name="Teambuilding").first()
            
            # Ottieni le qualifiche
            aiuto_istruttore_qual = db.query(QualificationType).filter_by(name="Aiuto-istruttore").first()
            istruttore_kayak_qual = db.query(QualificationType).filter_by(name="Istruttore kayak").first()
            autista_gommone_qual = db.query(QualificationType).filter_by(name="Autista gommone").first()
            
            # Crea attività di esempio
            tomorrow = date.today() + timedelta(days=1)
            next_week = date.today() + timedelta(days=7)
            
            corso_kayak = Activity(
                title="Corso Kayak Base - Gruppo A",
                short_description="Corso introduttivo al kayak per principianti",
                state="confermato",
                type_id=kayak_type.id,
                date=tomorrow,
                start_time=time(9, 0),
                end_time=time(12, 0),
                customer_name="Centro Sportivo Comunale",
                customer_email="info@centrosportivo.it",
                contact_name="Marco Rossi",
                contact_phone="+39 123 456 789",
                contact_email="marco.rossi@centrosportivo.it",
                participants_plan=8,
                payment_amount=400.00,
                payment_method="bonifico",
                payment_state="confermato"
            )
            db.add(corso_kayak)
            db.flush()  # Per ottenere l'ID
            
            teambuilding = Activity(
                title="Teambuilding Aziendale - Team Building",
                short_description="Attività di team building per azienda",
                state="da_confermare",
                type_id=teambuilding_type.id,
                date=next_week,
                start_time=time(14, 0),
                end_time=time(18, 0),
                customer_name="TechCorp SRL",
                customer_email="hr@techcorp.it",
                contact_name="Anna Bianchi",
                contact_phone="+39 987 654 321",
                contact_email="anna.bianchi@techcorp.it",
                participants_plan=15,
                payment_amount=800.00,
                payment_method="carta",
                payment_state="da_effettuare"
            )
            db.add(teambuilding)
            db.flush()  # Per ottenere l'ID
            
            # Crea requisiti per le attività
            req_corso_istruttore = ActivityRequirement(
                activity_id=corso_kayak.id,
                qualification_type_id=istruttore_kayak_qual.id,
                quantity=1
            )
            db.add(req_corso_istruttore)
            
            req_corso_aiuto = ActivityRequirement(
                activity_id=corso_kayak.id,
                qualification_type_id=aiuto_istruttore_qual.id,
                quantity=1
            )
            db.add(req_corso_aiuto)
            
            req_teambuilding_istruttore = ActivityRequirement(
                activity_id=teambuilding.id,
                qualification_type_id=aiuto_istruttore_qual.id,
                quantity=2
            )
            db.add(req_teambuilding_istruttore)
            
            req_teambuilding_autista = ActivityRequirement(
                activity_id=teambuilding.id,
                qualification_type_id=autista_gommone_qual.id,
                quantity=1
            )
            db.add(req_teambuilding_autista)
            
            db.commit()
        logger.info("Attività di esempio create con requisiti.")
        
        # Genera 50 attività nel periodo 20 agosto 2025 - 28 febbraio 2026
        logger.info("Generazione di 50 attività di esempio...")
        generate_sample_activities(db, 50)
        
        # Assegna qualifiche a tutti gli allenatori e istruttori
        allenatori_istruttori = db.query(User).join(User.roles).filter(
            or_(Role.name == 'allenatore', Role.name == 'istruttore')
        ).distinct().all()
        
        if allenatori_istruttori:
            # Ottieni tutte le qualifiche disponibili
            all_qualifications = db.query(QualificationType).filter_by(is_active=True).all()
            
            for user in allenatori_istruttori:
                logger.info(f"Assegnazione qualifiche a {user.first_name} {user.last_name}")
                
                for qualification in all_qualifications:
                    # Verifica se la qualifica è già assegnata
                    if not db.query(UserQualification).filter_by(
                        user_id=user.id, 
                        qualification_type_id=qualification.id
                    ).first():
                        user_qual = UserQualification(
                            user_id=user.id,
                            qualification_type_id=qualification.id,
                            obtained_date=date.today(),
                            expiry_date=date.today() + timedelta(days=365),
                            is_active=True
                        )
                        db.add(user_qual)
                        logger.info(f"  - Qualifica '{qualification.name}' assegnata")
            
            db.commit()
            logger.info(f"Tutte le qualifiche assegnate a {len(allenatori_istruttori)} utenti (allenatori e istruttori).")
        
    except Exception as e:
        logger.error(f"Errore durante il seeding delle attività: {e}")
        db.rollback()
        raise


def generate_sample_activities(db: Session, count: int = 50):
    """Genera attività di esempio nel periodo specificato."""
    try:
        from datetime import datetime, timedelta
        import random
        
        # Periodo: 20 agosto 2025 - 28 febbraio 2026
        start_date = datetime(2025, 8, 20).date()
        end_date = datetime(2026, 2, 28).date()
        
        # Ottieni tipi di attività e qualifiche
        activity_types = db.query(ActivityType).filter_by(is_active=True).all()
        qualification_types = db.query(QualificationType).filter_by(is_active=True).all()
        
        if not activity_types or not qualification_types:
            logger.warning("Tipi di attività o qualifiche non trovati per la generazione")
            return
        
        # Nomi aziende e clienti di esempio
        companies = [
            "TechCorp SRL", "SportCenter Bergamo", "Scuola Elementare Lovere", 
            "Centro Sportivo Comunale", "Azienda Agricola Sebino", "Hotel Lago d'Iseo",
            "Associazione Canottaggio Brescia", "Centro Estivo Giovanile", "Palestra Fitness Plus",
            "Circolo Nautico Lombardo", "Scuola Media Endine", "Centro Commerciale Sebino",
            "Pro Loco Costa Volpino", "Centro Anziani Riva di Solto", "Cooperativa Sociale"
        ]
        
        # Titoli attività di esempio
        activity_titles = [
            "Corso Kayak Base", "Corso Kayak Avanzato", "Corso SUP Principianti",
            "Gita Vichinga Famiglia", "Teambuilding Aziendale", "Corso CAS Base",
            "Lezione Canottaggio", "Gara Amatoriale", "Corso Timoneria",
            "Escursione Lago", "Corso Sicurezza", "Gita Scuola Elementare",
            "Evento Aziendale", "Corso Estivo", "Gara Regionale"
        ]
        
        # Genera attività
        for i in range(count):
            # Data casuale nel periodo
            days_offset = random.randint(0, (end_date - start_date).days)
            activity_date = start_date + timedelta(days=days_offset)
            
            # Tipo casuale
            activity_type = random.choice(activity_types)
            
            # Orari casuali (9:00-18:00)
            start_hour = random.randint(9, 16)
            end_hour = start_hour + random.randint(1, 3)
            
            # Stato casuale (più probabilità per bozza e confermato)
            states = ["bozza", "bozza", "da_confermare", "confermato", "confermato", "rimandata", "in_corso", "completato"]
            state = random.choice(states)
            
            # Pagamento casuale
            payment_states = ["da_effettuare", "da_verificare", "confermato"]
            payment_state = random.choice(payment_states)
            
            # Cliente casuale
            customer = random.choice(companies)
            
            # Crea attività
            activity = Activity(
                title=f"{random.choice(activity_titles)} - {customer}",
                short_description=f"Attività di esempio #{i+1} per {customer}",
                state=state,
                type_id=activity_type.id,
                date=activity_date,
                start_time=time(start_hour, 0),
                end_time=time(end_hour, 0),
                customer_name=customer,
                customer_email=f"info@{customer.lower().replace(' ', '').replace('srl', 'it')}.it",
                contact_name=f"Contatto {i+1}",
                contact_phone=f"+39 3{random.randint(10, 99)} {random.randint(100000, 999999)}",
                contact_email=f"contatto{i+1}@{customer.lower().replace(' ', '').replace('srl', 'it')}.it",
                participants_plan=random.randint(5, 25),
                payment_amount=Decimal(random.randint(200, 1500)),
                payment_method=random.choice(["bonifico", "carta", "contanti"]),
                payment_state=payment_state
            )
            
            db.add(activity)
            db.flush()  # Per ottenere l'ID
            
            # Crea requisiti casuali (1-3 qualifiche per attività)
            num_requirements = random.randint(1, 3)
            selected_qualifications = random.sample(qualification_types, min(num_requirements, len(qualification_types)))
            
            for qual in selected_qualifications:
                requirement = ActivityRequirement(
                    activity_id=activity.id,
                    qualification_type_id=qual.id,
                    quantity=random.randint(1, 3)
                )
                db.add(requirement)
        
        db.commit()
        logger.info(f"{count} attività di esempio generate con successo nel periodo {start_date} - {end_date}")
        
    except Exception as e:
        logger.error(f"Errore durante la generazione delle attività di esempio: {e}")
        db.rollback()
        raise


def seed_mezzi(db: Session):
    """Popola il database con mezzi di esempio (furgoni e gommoni)"""
    try:
        # Controlla se esistono già mezzi
        if db.query(Furgone).count() > 0 or db.query(Gommone).count() > 0:
            logger.info("Mezzi già presenti nel database, saltando popolamento")
            return
        
        # Furgoni di esempio con scadenze dall'immagine
        furgoni = [
            Furgone(
                marca="Ford",
                modello="Transit",
                targa="FH577SJ",
                anno=2017,
                stato="libero",
                # Bollo - dall'immagine: "Bollo furgone FORD FH577SJ"
                scadenza_bollo=date(2025, 3, 1),
                scadenza_bollo_identificativo="1/65166/128/178105055",
                scadenza_bollo_frazionamento="annuale",
                scadenza_bollo_assicuratore="Regione Lombardia",
                # Revisione - dall'immagine: "Revisione furgone FORD FH577SJ"
                scadenza_revisione=date(2025, 10, 20),
                scadenza_revisione_identificativo="0241/10/0070522",
                scadenza_revisione_frazionamento="annuale",
                scadenza_revisione_assicuratore="Motorizzazione",
                # RCA - dall'immagine: "RCA PULMINO FORD TRANSIT TARGA FH577SJ"
                scadenza_rca=date(2025, 6, 30),
                scadenza_rca_identificativo="RCA001",
                scadenza_rca_frazionamento="semestrale",
                scadenza_rca_assicuratore="UNIPOL SAI",
                # Infortuni conducente - dall'immagine: "INFORTUNI CONDUCENTE FH577SJ"
                scadenza_infortuni_conducente=date(2025, 12, 31),
                scadenza_infortuni_conducente_identificativo="INF001",
                scadenza_infortuni_conducente_frazionamento="annuale",
                scadenza_infortuni_conducente_assicuratore="REALE MUTUA"
            ),
            Furgone(
                marca="Opel",
                modello="Vivaro",
                targa="DT228VB",
                anno=2008,
                stato="manutenzione",
                # Bollo - dall'immagine: "Bollo furgone OPEL DT228VB"
                scadenza_bollo=date(2025, 10, 30),
                scadenza_bollo_identificativo="1/65166/128/178105056",
                scadenza_bollo_frazionamento="annuale",
                scadenza_bollo_assicuratore="Regione Lombardia",
                # Revisione - dall'immagine: "Revisione furgone OPEL DT228VB"
                scadenza_revisione=date(2025, 7, 15),
                scadenza_revisione_identificativo="0241/10/0070523",
                scadenza_revisione_frazionamento="annuale",
                scadenza_revisione_assicuratore="Motorizzazione",
                # RCA - dall'immagine: "RCA PULMINO OPEL VIVARO TARGA DT228VB"
                scadenza_rca=date(2025, 11, 30),
                scadenza_rca_identificativo="RCA002",
                scadenza_rca_frazionamento="annuale",
                scadenza_rca_assicuratore="UNIPOL SAI",
                # Infortuni conducente - dall'immagine: "INFORTUNI CONDUCENTE DT228VB"
                scadenza_infortuni_conducente=date(2025, 8, 20),
                scadenza_infortuni_conducente_identificativo="INF002",
                scadenza_infortuni_conducente_frazionamento="annuale",
                scadenza_infortuni_conducente_assicuratore="REALE MUTUA"
            ),
            Furgone(
                marca="Delta",
                modello="RB900B",
                targa="AA59565",
                anno=2015,
                stato="libero",
                # Bollo - dall'immagine: "Bollo rimorchio AA59565"
                scadenza_bollo=date(2025, 6, 10),
                scadenza_bollo_identificativo="1/65166/128/178105057",
                scadenza_bollo_frazionamento="annuale",
                scadenza_bollo_assicuratore="Regione Lombardia",
                # Revisione - dall'immagine: "Revisione rimorchio AA59565"
                scadenza_revisione=date(2025, 3, 25),
                scadenza_revisione_identificativo="0241/10/0070524",
                scadenza_revisione_frazionamento="annuale",
                scadenza_revisione_assicuratore="Motorizzazione",
                # RCA - dall'immagine: "RCA RIMORCHIO DELTA RB900B TARGA AA59565"
                scadenza_rca=date(2025, 10, 15),
                scadenza_rca_identificativo="RCA003",
                scadenza_rca_frazionamento="annuale",
                scadenza_rca_assicuratore="UNIPOL SAI"
            ),
            Furgone(
                marca="Delta",
                modello="RB22",
                targa="AF68132",
                anno=2016,
                stato="trasferta",
                # Bollo - dall'immagine: "Bollo rimorchio AF68132 grande"
                scadenza_bollo=date(2025, 9, 10),
                scadenza_bollo_identificativo="1/65166/128/178105058",
                scadenza_bollo_frazionamento="annuale",
                scadenza_bollo_assicuratore="Regione Lombardia",
                # Revisione - dall'immagine: "Revisione rimorchio AF68132 grande"
                scadenza_revisione=date(2025, 4, 15),
                scadenza_revisione_identificativo="0241/10/0070525",
                scadenza_revisione_frazionamento="annuale",
                scadenza_revisione_assicuratore="Motorizzazione",
                # RCA - dall'immagine: "RCA RIMORCHIO DELTA RB22 TARGA AF68132"
                scadenza_rca=date(2025, 12, 15),
                scadenza_rca_identificativo="RCA004",
                scadenza_rca_frazionamento="annuale",
                scadenza_rca_assicuratore="UNIPOL SAI"
            )
        ]
        
        # Gommoni di esempio con scadenze dall'immagine
        gommoni = [
            Gommone(
                nome="Gommoncino Bianco",
                motore="Selva 15CV",
                potenza="15 CV",
                stato="libero",
                # RCA - dall'immagine: "RCA MOTORE SELVA 15CV MATRICOLA S/N1023837"
                scadenza_rca=date(2025, 12, 31),
                scadenza_rca_identificativo="S/N1023837",
                scadenza_rca_frazionamento="annuale",
                scadenza_rca_assicuratore="UNIPOL SAI"
            ),
            Gommone(
                nome="Gommone Selva",
                motore="Selva 20CV",
                potenza="20 CV",
                stato="libero",
                # RCA - dall'immagine: "RCA MOTORE SELVA 15CV MATRICOLA S/N1019590"
                scadenza_rca=date(2025, 11, 30),
                scadenza_rca_identificativo="S/N1019590",
                scadenza_rca_frazionamento="annuale",
                scadenza_rca_assicuratore="UNIPOL SAI"
            ),
            Gommone(
                nome="Catamarano Rosso",
                motore="Mercury 25CV",
                potenza="25 CV",
                stato="libero",
                # RCA - dall'immagine: "RCA MOTORE MERCURY 15CV MATRICOLA OP162429"
                scadenza_rca=date(2025, 10, 15),
                scadenza_rca_identificativo="OP162429",
                scadenza_rca_frazionamento="annuale",
                scadenza_rca_assicuratore="UNIPOL SAI"
            ),
            Gommone(
                nome="Motoscafo Bianco",
                motore="Selva 15CV",
                potenza="15 CV",
                stato="manutenzione",
                # RCA - dall'immagine: "RCA MOTORE SELVA 15CV MATRICOLA S/N1023837"
                scadenza_rca=date(2025, 9, 30),
                scadenza_rca_identificativo="S/N1023838",
                scadenza_rca_frazionamento="annuale",
                scadenza_rca_assicuratore="REALE MUTUA"
            ),
            Gommone(
                nome="Tohatsu",
                motore="Tohatsu 40CV",
                potenza="40 CV",
                stato="libero",
                # RCA - dall'immagine: "RCA MOTORE TOHATSU 40CV M40D MATRICOLA 02108"
                scadenza_rca=date(2025, 8, 15),
                scadenza_rca_identificativo="02108",
                scadenza_rca_frazionamento="annuale",
                scadenza_rca_assicuratore="UNIPOL SAI"
            )
        ]
        
        # Aggiungi tutti i mezzi
        db.add_all(furgoni)
        db.add_all(gommoni)
        
        db.commit()
        logger.info(f"Popolamento mezzi completato: {len(furgoni)} furgoni e {len(gommoni)} gommoni")
        
    except Exception as e:
        logger.error(f"Errore durante il popolamento dei mezzi: {e}")
        db.rollback()
        raise


if __name__ == "__main__":
    main()
