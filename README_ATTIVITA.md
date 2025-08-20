# Macro-sezione Attività - Canottieri Sebino

## Panoramica

Questa implementazione aggiunge una macro-sezione completa per la gestione delle attività al sistema esistente Canottieri Sebino. La sezione include gestione completa di attività, qualifiche, assegnazioni e pagamenti.

## Funzionalità Implementate

### 1. Calendario Attività
- **Vista Calendario**: Integrazione con FullCalendar per visualizzazione desktop
- **Vista Elenco**: Lista raggruppata per data per dispositivi mobili
- **Filtri**: Per tipo, stato, copertura e testo
- **Modal dettagli**: Con tabs per Generale, Copertura, Risorse e Pagamento
- **Autocandidatura**: Istruttori possono autocandidarsi per attività compatibili

### 2. Gestione Attività
- **CRUD completo**: Creazione, lettura, aggiornamento, eliminazione
- **Tabella amministrativa**: Con badge per stato, copertura e pagamento
- **Filtri avanzati**: Per data, tipo, stato, pagamento e testo
- **Progress bar**: Visualizzazione copertura requisiti

### 3. Pagamenti
- **KPI dashboard**: Conteggi e importi totali
- **Stati pagamento**: Da effettuare, da verificare, confermato
- **Filtri temporali**: Per data e stato pagamento
- **Dettagli fatturazione**: P.IVA, SDI/PEC, indirizzo

### 4. Estrazioni
- **Report ore**: Per istruttore e periodo specifico
- **Export CSV**: Download diretto dei dati
- **Filtri**: Per utente, mese e anno
- **Vista personale**: Istruttori vedono solo le proprie ore

### 5. Gestione Istruttori
- **Elenco istruttori**: Con filtri per qualifica
- **Gestione qualifiche**: Assegnazione/rimozione dinamica
- **Profilo utente**: Link diretto al profilo esistente
- **Modal qualifiche**: Gestione inline delle competenze

## Struttura Tecnica

### Modelli Database
- `ActivityType`: Tipi di attività con colori
- `QualificationType`: Tipi di qualifica disponibili
- `Activity`: Attività principale con tutti i dettagli
- `UserQualification`: Qualifiche assegnate agli utenti
- `ActivityRequirement`: Requisiti per ogni attività
- `ActivityAssignment`: Assegnazioni utente-requisito

### API Endpoints
- **Attività**: CRUD completo con filtri e paginazione
- **Requisiti**: Gestione requisiti per attività
- **Assegnazioni**: Gestione assegnazioni utenti
- **Qualifiche**: Gestione qualifiche utenti
- **Autocandidatura**: Endpoint per self-assignment
- **Estrazioni**: Report ore con filtri
- **Pagamenti**: KPI e riepilogo

### Template HTML
- **Calendario**: Vista calendario/elenco con modal dettagli
- **Gestione**: Tabella amministrativa con filtri
- **Dettaglio**: Pagina completa con tabs
- **Pagamenti**: Dashboard KPI e lista
- **Estrazioni**: Report con export
- **Istruttori**: Gestione qualifiche e profili

### JavaScript
- **activities_calendar.js**: Gestione calendario e vista elenco
- **FullCalendar**: Integrazione per vista calendario
- **Responsive**: Switch automatico tra vista calendario e elenco
- **Modal**: Gestione dettagli attività con tabs

## Ruoli e Permessi

### Admin
- Accesso completo a tutte le funzionalità
- Gestione utenti e qualifiche
- Modifica di tutte le attività

### Allenatore
- CRUD attività e requisiti
- Gestione assegnazioni
- Visualizzazione pagamenti (stato completo)
- Gestione istruttori

### Istruttore
- Visualizzazione calendario attività
- Autocandidatura per ruoli compatibili
- Visualizzazione proprie ore
- Accesso limitato alle funzionalità amministrative

## Installazione e Setup

### 1. Aggiornamento Database
```bash
# Le nuove tabelle vengono create automaticamente all'avvio
# oppure eseguire manualmente:
python -c "from database import engine, Base; from models.activities import *; Base.metadata.create_all(bind=engine)"
```

### 2. Seed Dati Iniziali
```bash
# I dati vengono popolati automaticamente all'avvio
# oppure eseguire manualmente:
python seed.py
```

### 3. Test Funzionalità
```bash
# Test semplice dei modelli:
python test_activities.py
```

## Utilizzo

### Accesso alle Funzionalità
1. **Calendario**: `/attivita/calendario` - Vista principale per tutti gli utenti
2. **Gestione**: `/attivita/gestione` - Tabella amministrativa per admin/allenatori
3. **Pagamenti**: `/attivita/pagamenti` - Dashboard KPI per admin/allenatori
4. **Estrazioni**: `/attivita/estrazioni` - Report ore per tutti
5. **Istruttori**: `/attivita/istruttori` - Gestione qualifiche per admin/allenatori

### Workflow Tipico
1. **Creazione Attività**: Admin/Allenatore crea attività con requisiti
2. **Assegnazione**: Utenti vengono assegnati ai requisiti
3. **Autocandidatura**: Istruttori possono autocandidarsi per ruoli compatibili
4. **Monitoraggio**: Controllo copertura e stato pagamenti
5. **Estrazione**: Report ore per istruttori e periodi specifici

## Caratteristiche Tecniche

### Performance
- **Lazy Loading**: Relazioni caricate solo quando necessario
- **Indici Database**: Ottimizzati per query frequenti
- **Paginazione**: Server-side per liste amministrative
- **Caching**: FullCalendar gestisce cache eventi

### Sicurezza
- **Validazione Input**: Pydantic schemas per tutti i dati
- **Controllo Ruoli**: Decorator `require_roles` per autorizzazione
- **Sanitizzazione**: Filtri SQL parametrizzati
- **Controlli Business**: Verifica conflitti orari e qualifiche

### Responsive Design
- **Mobile First**: Vista elenco di default su mobile
- **Desktop**: Vista calendario con FullCalendar
- **Bootstrap 5**: UI moderna e coerente con il resto dell'app
- **Icone**: Bootstrap Icons per interfaccia intuitiva

## Estensioni Future (Fase 2)

### Risorse Materiali
- **Barche**: Gestione disponibilità e assegnazione
- **Attrezzature**: Inventario e prenotazioni
- **Veicoli**: Gestione trasporti e logistica

### Audit e Logging
- **ActivityAudit**: Tracciamento modifiche attività
- **Log Operazioni**: Storico completo delle operazioni
- **Notifiche**: Sistema di notifiche per cambiamenti

### Integrazione Avanzata
- **ICS Export**: Feed calendario personale con attività
- **API Webhook**: Notifiche esterne per integrazioni
- **Report Avanzati**: Analytics e statistiche dettagliate

## Troubleshooting

### Problemi Comuni
1. **Import Error**: Verificare che `models.activities` sia importato correttamente
2. **Database Error**: Controllare che le tabelle siano state create
3. **Permission Error**: Verificare ruoli utente e dipendenze
4. **FullCalendar Error**: Controllare che i file JS siano caricati correttamente

### Debug
- **Log**: Controllare console browser per errori JavaScript
- **Database**: Verificare query SQL con logging
- **API**: Testare endpoint con Postman o curl
- **Template**: Verificare variabili Jinja2 nel browser

## Contributi

### Sviluppo
1. **Fork** del repository
2. **Branch** per nuove funzionalità
3. **Test** delle modifiche
4. **Pull Request** con descrizione dettagliata

### Standard di Codice
- **PEP 8**: Stile Python coerente
- **Type Hints**: Annotazioni tipo per funzioni
- **Docstring**: Documentazione inline
- **Error Handling**: Gestione errori robusta

## Licenza

Questo codice è parte del progetto Canottieri Sebino e segue la stessa licenza del progetto principale.

## Supporto

Per supporto tecnico o domande sull'implementazione:
- **Issues**: Creare issue su GitHub
- **Documentazione**: Consultare questo README
- **Codice**: Esaminare i commenti inline nel codice
