# Gestione Mezzi - Canottieri Sebino

## Panoramica

La sezione "Mezzi" è stata aggiunta alla macrosezione "Risorse" per gestire due tipi di risorse:
- **Furgoni**: Veicoli per il trasporto di attrezzature, materiali e atleti
- **Gommoni**: Imbarcazioni di supporto per sicurezza e assistenza durante le attività

## Funzionalità

### Vista Principale
- **Toggle**: Passaggio tra vista Furgoni e Gommoni con conteggio mezzi
- **Pulsante Gestione**: Accesso alla gestione mezzi (solo per amministratori)
- **Card Grandi**: Visualizzazione dei mezzi in formato card con design moderno

### Informazioni Visualizzate

#### Furgoni
- **Intestazione**: Icona furgone + Marca + Modello
- **Sottotitolo**: Targa + Anno
- **Stato**: Badge colorato con stati:
  - 🟢 Verde: Libero
  - 🟡 Giallo: In manutenzione
  - 🔴 Rosso: Fuori uso
  - 🔵 Blu: In trasferta
- **Scadenze**: Elenco verticale con:
  - Nome scadenza a sinistra
  - Data nel badge colorato a destra
- **Colori scadenze**:
  - 🟢 Verde: > 1 anno
  - 🟡 Giallo: > 3 mesi
  - 🔴 Rosso: < 3 mesi

#### Gommoni
- **Intestazione**: Icona gommone + Nome
- **Sottotitolo**: Motore + Potenza
- **Stato**: Badge colorato con stati:
  - 🟢 Verde: Libero
  - 🟡 Giallo: In manutenzione
  - 🔴 Rosso: Fuori uso
- **Scadenze**: RCA e Manutenzione con stessi criteri di colore

### Gestione (Solo Admin)
- **Tabella Unificata**: Visualizzazione di tutti i mezzi in formato tabella
- **Aggiunta nuovi mezzi**: Form modali per inserimento dati
- **Modifica**: Pagine dedicate con due tab per ogni mezzo
- **Eliminazione**: Rimozione mezzi dal sistema con conferma

## Struttura Tecnica

### Modelli Database
- **Furgone**: `models.base_models.Furgone`
- **Gommone**: `models.base_models.Gommone`

### Route API

#### Vista e Lista
- `GET /risorse/mezzi` - Vista principale con toggle
- `GET /risorse/mezzi/furgoni` - Lista furgoni
- `GET /risorse/mezzi/gommoni` - Lista gommoni
- `GET /risorse/mezzi/gestione` - Gestione mezzi (admin)
- `GET /risorse/mezzi/furgone/{id}` - Dettaglio furgone
- `GET /risorse/mezzi/gommone/{id}` - Dettaglio gommone

#### Modifica (Solo Admin)
- `GET /risorse/mezzi/furgone/{id}/modifica` - Form modifica furgone
- `POST /risorse/mezzi/furgone/{id}/modifica` - Salva modifiche furgone
- `GET /risorse/mezzi/gommone/{id}/modifica` - Form modifica gommone
- `POST /risorse/mezzi/gommone/{id}/modifica` - Salva modifiche gommone

#### Gestione Scadenze (Solo Admin)
- `POST /risorse/mezzi/furgone/{id}/scadenza` - Aggiunge scadenza furgone
- `POST /risorse/mezzi/gommone/{id}/scadenza` - Aggiunge scadenza gommone

#### Eliminazione (Solo Admin)
- `DELETE /risorse/mezzi/furgone/{id}` - Elimina furgone
- `DELETE /risorse/mezzi/gommone/{id}` - Elimina gommone

### Template

#### Vista Principale
- `templates/mezzi/mezzi_main.html` - Vista principale con toggle
- `templates/mezzi/furgoni_list.html` - Lista furgoni
- `templates/mezzi/gommoni_list.html` - Lista gommoni

#### Gestione
- `templates/mezzi/gestione_mezzi.html` - Tabella unificata per gestione mezzi

#### Modifica
- `templates/mezzi/furgone_modifica.html` - Modifica furgone con due tab
- `templates/mezzi/gommone_modifica.html` - Modifica gommone con due tab

#### Dettaglio
- `templates/mezzi/furgone_detail.html` - Dettaglio furgone
- `templates/mezzi/gommone_detail.html` - Dettaglio gommone

## Database

### Tabelle
- **furgoni**: Dati furgoni con scadenze e stato
- **gommoni**: Dati gommoni con scadenze e stato

### Migrazione
- File: `alembic/versions/c19718caa743_add_mezzi_tables.py`
- Comando: `alembic upgrade head`

## Popolamento Dati

### Seed Automatico
I mezzi vengono popolati automaticamente all'avvio dell'applicazione tramite:
- `seed.seed_mezzi()` - Crea mezzi di esempio
- Chiamata in `main.py` durante l'avvio

### Dati di Esempio
- **7 Furgoni**: 
  - Ford Transit 2017 (FH577SJ)
  - Opel Vivaro 2008 (DT228VB)
  - Delta RB900B 2015 (AA59565)
  - Delta RB22 2016 (AF68132)
  - Fiat Ducato 2018 (AB123CD)
  - Mercedes Sprinter 2020 (EF456GH)
  - Ford Transit 2019 (IJ789KL)
- **3 Gommoni**: Sicurezza, Supporto, Emergenza
- Scadenze realistiche per il 2026

## Accesso e Permessi

### Vista Pubblica
- Tutti gli utenti autenticati possono visualizzare i mezzi
- Accesso alle informazioni di stato e scadenze

### Gestione
- Solo amministratori (`current_user.is_admin`)
- Accesso completo a creazione, modifica e eliminazione

## Navigazione

### Menu Principale
- **Risorse** → **Mezzi** → Vista principale con toggle

### Breadcrumb
- Mezzi → Gestione Mezzi → Modifica specifico mezzo

## Stile e UI

### Design System
- **Bootstrap 5**: Componenti e layout responsive
- **FontAwesome**: Icone per mezzi e azioni
- **Card Design**: Layout moderno con ombre e hover effects
- **Header Bianchi**: Design pulito senza banner colorati
- **Tabella Gestione**: Vista unificata per tutti i mezzi

### Responsive
- **Mobile**: Stack verticale delle card
- **Tablet**: 2 colonne per card
- **Desktop**: 3 colonne per card

### Icone
- **Furgoni**: Icona furgone (`fa-truck`) in colore primario
- **Gommoni**: Icona nave (`fa-ship`) in colore info

## Funzionalità Implementate

### ✅ Completate
- **Vista principale** con toggle furgoni/gommoni
- **Card design** per visualizzazione mezzi
- **Gestione mezzi** con tabella unificata
- **Modifica mezzi** con due tab per ogni mezzo
- **Gestione scadenze** con aggiunta/modifica/eliminazione
- **Eliminazione mezzi** con conferma
- **Rotte API** complete per tutte le operazioni
- **Controllo permessi** per operazioni admin

### 🔄 In Sviluppo
- **Modifica scadenze** esistenti
- **Eliminazione scadenze** individuali
- **Notifiche** per scadenze prossime
- **Import/export** dati mezzi

## Funzionalità Future

### Implementazioni Pianificate
- [ ] Modifica scadenze esistenti in tempo reale
- [ ] Eliminazione scadenze individuali
- [ ] Notifiche scadenze prossime
- [ ] Storico modifiche e audit trail
- [ ] Import/export dati mezzi
- [ ] Integrazione con calendario attività
- [ ] Sistema di prenotazione mezzi

### API Endpoints
- [ ] `PUT /api/mezzi/furgone/{id}/scadenza/{tipo}` - Modifica scadenza
- [ ] `DELETE /api/mezzi/furgone/{id}/scadenza/{tipo}` - Elimina scadenza
- [ ] Endpoint simili per gommoni

## Manutenzione

### Aggiornamenti
- Le scadenze vengono calcolate dinamicamente
- I colori si aggiornano automaticamente in base alle date
- Timestamp di creazione e modifica automatici

### Backup
- I dati sono salvati nel database SQLite
- Backup regolare raccomandato per i dati dei mezzi
- Migrazioni Alembic per aggiornamenti schema

## Note Tecniche

### Performance
- Query ottimizzate con indici su ID e targa
- Lazy loading per relazioni non critiche
- Paginazione per grandi volumi di dati (futuro)

### Sicurezza
- Validazione input sui form
- Controllo permessi per operazioni critiche
- Sanitizzazione dati prima del salvataggio
- Protezione CSRF sui form

### Compatibilità
- **Browser**: Chrome, Firefox, Safari, Edge (moderni)
- **Database**: SQLite (sviluppo), PostgreSQL (produzione)
- **Python**: 3.8+
- **FastAPI**: 0.68+

## Modifiche Recenti

### UI/UX Improvements
- ✅ Rimozione banner colorati dalle card
- ✅ Scadenze su righe separate con data nel badge
- ✅ Rimozione campo note
- ✅ Icone per furgoni e gommoni
- ✅ Design più pulito e moderno

### Pagina Dettaglio
- ✅ Informazioni accorpate in un'unica card
- ✅ Rimozione schede laterali
- ✅ Layout più compatto e leggibile

### Gestione Mezzi
- ✅ **Tabella unificata** per tutti i mezzi
- ✅ **Due tab per modifica**: Informazioni e Scadenze
- ✅ **Form funzionali** per modifica dati
- ✅ **Gestione scadenze** completa
- ✅ **Eliminazione mezzi** con conferma
- ✅ **Rotte API** implementate e funzionanti

### Funzionalità Backend
- ✅ **Route complete** per modifica ed eliminazione
- ✅ **Controllo permessi** per operazioni admin
- ✅ **Gestione errori** e rollback database
- ✅ **Validazione dati** sui form
- ✅ **Redirect intelligenti** dopo operazioni
