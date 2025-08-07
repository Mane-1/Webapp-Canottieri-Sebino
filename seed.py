# File: seed.py
import os
import sys
from datetime import date, datetime
import logging

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
import models
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
    {'nome': 'ELPIS', 'tipo': '1x', 'costruttore': 'Salani', 'anno': 2022},
    {'nome': 'ZEUS', 'tipo': '2x', 'costruttore': 'Filippi', 'anno': 2019},
    {'nome': 'KRONOS', 'tipo': '4x', 'costruttore': 'Salani', 'anno': 2021},
    {'nome': 'EROS', 'tipo': '2-', 'costruttore': 'Salani', 'anno': 2023},
    {'nome': 'POSEIDONE', 'tipo': '8+', 'costruttore': 'Filippi', 'anno': 2018},
    {'nome': 'ARES', 'tipo': '1x', 'costruttore': 'Salani', 'anno': 2022},
    {'nome': 'ARTEMIDE', 'tipo': '4-', 'costruttore': 'Filippi', 'anno': 2020},
    {'nome': 'APOLLO', 'tipo': '2x', 'costruttore': 'Salani', 'anno': 2021},
    {'nome': 'PEGASO', 'tipo': '4x', 'costruttore': 'Filippi', 'anno': 2019},
    {'nome': 'ORIONE', 'tipo': '1x', 'costruttore': 'Salani', 'anno': 2023},
]


def seed_barche(db: Session):
    logger.info("Popolamento barche...")
    if db.query(models.Barca).count() > 0:
        logger.info("Tabella barche già popolata. Skippo.")
        return
    try:
        barche_da_creare = [models.Barca(**data) for data in barche_data]
        db.add_all(barche_da_creare)
        db.commit()
        logger.info(f"{len(barche_da_creare)} barche popolate con successo.")
    except Exception as e:
        logger.error(f"Errore durante il popolamento delle barche: {e}")
        db.rollback()


def seed_categories(db: Session):
    logger.info("Popolamento categorie...")
    if db.query(models.Categoria).count() > 0:
        logger.info("Tabella categorie già popolata. Skippo.")
        return
    categorie = [
        models.Categoria(nome="Allievo A", eta_min=0, eta_max=10, ordine=1, macro_group="Under 14"),
        models.Categoria(nome="Allievo B1", eta_min=11, eta_max=11, ordine=2, macro_group="Under 14"),
        models.Categoria(nome="Allievo B2", eta_min=12, eta_max=12, ordine=3, macro_group="Under 14"),
        models.Categoria(nome="Allievo C", eta_min=13, eta_max=13, ordine=4, macro_group="Under 14"),
        models.Categoria(nome="Cadetto", eta_min=14, eta_max=14, ordine=5, macro_group="Under 14"),
        models.Categoria(nome="Ragazzo", eta_min=15, eta_max=16, ordine=6, macro_group="Over 14"),
        models.Categoria(nome="Junior", eta_min=17, eta_max=18, ordine=7, macro_group="Over 14"),
        models.Categoria(nome="Under 23", eta_min=19, eta_max=23, ordine=8, macro_group="Over 14"),
        models.Categoria(nome="Senior", eta_min=24, eta_max=27, ordine=9, macro_group="Over 14"),
        models.Categoria(nome="Master", eta_min=28, eta_max=150, ordine=10, macro_group="Master"),
    ]
    db.add_all(categorie)
    db.commit()


def seed_macro_groups(db: Session):
    logger.info("Popolamento macrogruppi...")
    if db.query(models.MacroGroup).count() > 0:
        logger.info("Tabella macro_groups già popolata. Skippo.")
        return
    groups = {
        "Under 14": ["Allievo A", "Allievo B1", "Allievo B2", "Allievo C", "Cadetto"],
        "Over 14": ["Ragazzo", "Junior", "Under 23", "Senior"],
        "Master": ["Master"],
    }
    for name, subcats in groups.items():
        mg = models.MacroGroup(name=name)
        db.add(mg)
        db.flush()
        for sub in subcats:
            db.add(models.SubGroup(name=sub, macro_group_id=mg.id))
    db.commit()


def main():
    logger.info("Avvio script di seeding completo...")
    logger.info("ATTENZIONE: Verranno cancellati tutti i dati esistenti nel database.")
    input("Premi Invio per continuare, o CTRL+C per annullare...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    logger.info("Tabelle create.")

    db = SessionLocal()
    try:
        # Popola Ruoli
        ruoli_da_creare = ['atleta', 'allenatore', 'admin']
        for nome_ruolo in ruoli_da_creare:
            if not db.query(models.Role).filter_by(name=nome_ruolo).first():
                db.add(models.Role(name=nome_ruolo))
        db.commit()
        logger.info("Ruoli popolati.")

        # Popola Categorie
        seed_categories(db)

        # Popola Macro Gruppi e Sottogruppi
        seed_macro_groups(db)

        # Crea Utente Admin
        if not db.query(models.User).filter(models.User.username == "gabriele").first():
            admin_role = db.query(models.Role).filter_by(name='admin').one()
            allenatore_role = db.query(models.Role).filter_by(name='allenatore').one()
            admin_user = models.User(
                username="gabriele", hashed_password=security.get_password_hash("manenti"),
                first_name="Gabriele", last_name="Manenti", email="gabriele.manenti@example.com",
                date_of_birth=date(1990, 1, 1), roles=[admin_role, allenatore_role]
            )
            db.add(admin_user)
            db.commit()
            logger.info("Utente admin 'gabriele' creato.")

        # Popola Atleti
        atleta_role = db.query(models.Role).filter_by(name='atleta').one()
        emails_usate = {"gabriele.manenti@example.com"}
        atleti_creati = 0
        for atleta in atleti_data:
            nome = atleta['nome'].title()
            cognome = atleta['cognome'].title()
            username_base = f"{nome.split(' ')[0]}.{cognome.split(' ')[0]}".lower().replace("'", "")
            username = username_base
            counter = 1
            while db.query(models.User).filter(models.User.username == username).first():
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

            if db.query(models.User).filter(models.User.email == final_email).first():
                continue

            new_user = models.User(
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

        # Popola Barche
        seed_barche(db)

    except Exception as e:
        logger.error(f"Errore durante il seeding: {e}")
        db.rollback()
    finally:
        db.close()
    logger.info("Seeding completato!")


if __name__ == "__main__":
    main()