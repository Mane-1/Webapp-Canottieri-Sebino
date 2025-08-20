# Checklist Test Manuali - Macro-sezione Attività

## 🚀 Pre-requisiti

### Database e Setup
- [ ] Database SQLite creato e popolato con dati di seed
- [ ] Ruolo "Istruttore" aggiunto al sistema
- [ ] Utenti di test con ruoli appropriati (Admin, Allenatore, Istruttore)
- [ ] Dati di seed per attività, qualifiche e requisiti caricati

### Accesso e Autenticazione
- [ ] Login con utente Admin
- [ ] Login con utente Allenatore  
- [ ] Login con utente Istruttore
- [ ] Logout funzionante

---

## 📱 Test Responsive Design

### Vista Mobile (default "lista")
- [ ] **Calendario Attività**: Switch automatico a vista elenco su mobile
- [ ] **Filtri**: Form filtri responsive e utilizzabili
- [ ] **Modal**: Apertura e chiusura corretta su dispositivi touch
- [ ] **Navigazione**: Menu dropdown funzionante su mobile

### Vista Desktop (default "calendario")
- [ ] **FullCalendar**: Visualizzazione corretta del calendario
- [ ] **Eventi**: Eventi visualizzati con colori e dettagli corretti
- [ ] **Interazioni**: Click su eventi, drag & drop (se implementato)
- [ ] **Switch vista**: Passaggio tra calendario e elenco funzionante

---

## 🔐 Test Ruoli e Permessi

### Admin
- [ ] **Accesso completo**: Tutte le sezioni accessibili
- [ ] **Gestione attività**: CRUD completo funzionante
- [ ] **Gestione qualifiche**: Assegnazione/rimozione utenti
- [ ] **Report**: Estrazioni e pagamenti accessibili

### Allenatore
- [ ] **Accesso limitato**: Solo sezioni appropriate
- [ ] **Gestione attività**: CRUD attività e requisiti
- [ ] **Assegnazioni**: Gestione personale per attività
- [ ] **Visualizzazione pagamenti**: Stato completo accessibile

### Istruttore
- [ ] **Accesso limitato**: Solo calendario e estrazioni personali
- [ ] **Calendario**: Visualizzazione attività disponibili
- [ ] **Autocandidatura**: Possibilità di autocandidarsi per ruoli compatibili
- [ ] **Estrazioni**: Solo proprie ore visibili

---

## 📅 Test Calendario Attività

### Vista Calendario
- [ ] **Eventi visualizzati**: Attività mostrate con colori corretti
- [ ] **Click eventi**: Apertura modal con dettagli completi
- [ ] **Filtri applicati**: Filtri per tipo, stato, copertura funzionanti
- [ ] **Navigazione**: Cambio mese/anno funzionante

### Vista Elenco
- [ ] **Raggruppamento**: Attività raggruppate per data
- [ ] **Dettagli**: Informazioni essenziali visibili (titolo, tipo, stato)
- [ ] **Click elementi**: Apertura modal dettagli
- [ ] **Responsive**: Layout adattato a schermi piccoli

### Modal Dettagli
- [ ] **Tab Generale**: Informazioni base attività
- [ ] **Tab Copertura**: Requisiti e assegnazioni
- [ ] **Tab Risorse**: Placeholder per risorse future
- [ ] **Tab Pagamento**: Dettagli fatturazione e stato

---

## ⚙️ Test Gestione Attività

### Creazione Attività
- [ ] **Form completo**: Tutti i campi richiesti presenti
- [ ] **Validazione**: Errori mostrati per campi mancanti/invalidi
- [ ] **Requisiti dinamici**: Aggiunta/rimozione requisiti funzionante
- [ ] **Salvataggio**: Attività creata e visualizzata nel calendario

### Modifica Attività
- [ ] **Form pre-popolato**: Dati esistenti caricati correttamente
- [ ] **Aggiornamento**: Modifiche salvate e applicate
- [ ] **Validazione**: Controlli su orari e dati
- [ ] **Rollback**: Annullamento modifiche funzionante

### Eliminazione Attività
- [ ] **Conferma**: Dialog di conferma eliminazione
- [ ] **Cascata**: Requisiti e assegnazioni eliminati correttamente
- [ ] **Aggiornamento UI**: Attività rimossa da calendario/elenco
- [ ] **Permessi**: Solo Admin/Allenatore possono eliminare

---

## 👥 Test Gestione Istruttori

### Lista Istruttori
- [ ] **Visualizzazione**: Tutti gli istruttori visibili
- [ ] **Filtri**: Filtro per qualifica funzionante
- [ ] **Link profilo**: Collegamenti al profilo utente funzionanti
- [ ] **Gestione qualifiche**: Pulsanti per gestire qualifiche visibili

### Modal Qualifiche
- [ ] **Apertura**: Modal si apre con dati utente corretti
- [ ] **Qualifiche esistenti**: Qualifiche attuali visualizzate
- [ ] **Aggiunta**: Nuove qualifiche assegnabili
- [ ] **Rimozione**: Qualifiche rimovibili con conferma

---

## 💰 Test Pagamenti

### Dashboard KPI
- [ ] **Conteggi**: Numero totale attività corretto
- [ ] **Importi**: Somma totale pagamenti corretta
- [ ] **Stati**: Conteggi per stato pagamento corretti
- [ ] **Aggiornamento**: KPI si aggiornano con nuovi dati

### Lista Pagamenti
- [ ] **Filtri**: Filtri per data e stato funzionanti
- [ ] **Dettagli**: Informazioni pagamento complete
- [ ] **Stati**: Badge stato pagamento corretti
- [ ] **Ordinamento**: Lista ordinabile per colonne

---

## 📊 Test Estrazioni

### Filtri e Selezione
- [ ] **Filtro utente**: Selezione utente per Admin/Allenatore
- [ ] **Filtro periodo**: Selezione mese/anno funzionante
- [ ] **Applicazione filtri**: Risultati filtrati correttamente
- [ ] **Reset filtri**: Pulizia filtri funzionante

### Report Ore
- [ ] **Riepilogo**: Totale ore per periodo corretto
- [ ] **Dettaglio**: Lista attività con ore dettagliate
- [ ] **Qualifiche**: Ruolo/qualifica per ogni attività
- [ ] **Export CSV**: Download file funzionante

### Vista Personale (Istruttore)
- [ ] **Solo proprie ore**: Istruttore vede solo le proprie attività
- [ ] **Filtro periodo**: Selezione mese/anno disponibile
- [ ] **Riepilogo**: Totale ore personali corretto

---

## 🔄 Test Autocandidatura

### Processo Autocandidatura
- [ ] **Pulsante visibile**: Pulsante "Autocandidati" presente per ruoli compatibili
- [ ] **Controllo qualifiche**: Solo utenti qualificati possono autocandidarsi
- [ ] **Controllo conflitti**: Utenti con conflitti orari non possono autocandidarsi
- [ ] **Controllo capacità**: Non è possibile autocandidarsi se requisito pieno

### Feedback e Aggiornamento
- [ ] **Conferma**: Messaggio di conferma autocandidatura
- [ ] **Aggiornamento UI**: Copertura aggiornata immediatamente
- [ ] **Stato pulsante**: Pulsante diventa "Rimuovi candidatura" se già candidato
- [ ] **Rimozione**: Possibilità di rimuovere autocandidatura

---

## 🔍 Test Filtri e Ricerca

### Filtri Attività
- [ ] **Tipo attività**: Filtro per tipo funzionante
- [ ] **Stato attività**: Filtro per stato (bozza, confermato, completato)
- [ ] **Copertura**: Filtro per percentuale copertura
- [ ] **Testo libero**: Ricerca per titolo e descrizione
- [ ] **Combinazione**: Filtri multipli applicabili insieme

### Filtri Pagamenti
- [ ] **Intervallo date**: Filtro per periodo temporale
- [ ] **Stato pagamento**: Filtro per stato (da effettuare, da verificare, confermato)
- [ ] **Applicazione**: Filtri si applicano correttamente
- [ ] **Reset**: Pulizia filtri funzionante

---

## 📱 Test Integrazione

### Navbar
- [ ] **Menu Attività**: Dropdown presente per utenti autorizzati
- [ ] **Link corretti**: Tutti i link portano alle pagine giuste
- [ ] **Visibilità ruoli**: Menu visibile solo per ruoli appropriati
- [ ] **Responsive**: Menu funziona su dispositivi mobili

### Breadcrumb e Navigazione
- [ ] **Percorso corretto**: Breadcrumb mostra percorso attuale
- [ ] **Link funzionanti**: Navigazione tra pagine funzionante
- [ ] **Stato attivo**: Pagina corrente evidenziata correttamente

---

## 🚨 Test Gestione Errori

### Validazione Input
- [ ] **Campi obbligatori**: Errori per campi mancanti
- [ ] **Formato date**: Validazione formato date e orari
- [ ] **Orari logici**: Fine > inizio per attività
- [ ] **Quantità positive**: Requisiti con quantità > 0

### Gestione Errori Server
- [ ] **Errori 404**: Pagina non trovata gestita correttamente
- [ ] **Errori 403**: Accesso negato per ruoli insufficienti
- [ ] **Errori 500**: Errori server gestiti graziosamente
- [ ] **Messaggi utente**: Errori comprensibili per l'utente finale

---

## 🔒 Test Sicurezza

### Controllo Accessi
- [ ] **URL diretti**: Accesso diretto a URL protetti bloccato
- [ ] **Ruoli insufficienti**: Reindirizzamento o errore 403
- [ ] **Sessione scaduta**: Logout automatico e reindirizzamento
- [ ] **CSRF**: Protezione da attacchi CSRF (se implementata)

### Validazione Dati
- [ ] **Input malizioso**: Script e HTML non eseguiti
- [ ] **SQL Injection**: Query parametrizzate funzionanti
- [ ] **XSS**: Contenuto utente sanitizzato correttamente

---

## 📈 Test Performance

### Tempi di Caricamento
- [ ] **Pagina calendario**: Caricamento < 3 secondi
- [ ] **Modal dettagli**: Apertura < 1 secondo
- [ ] **Filtri**: Applicazione filtri < 1 secondo
- [ ] **Liste**: Paginazione per liste grandi

### Responsività UI
- [ ] **Interazioni**: Click e hover responsivi
- [ ] **Animazioni**: Transizioni fluide
- [ ] **Loading states**: Indicatori di caricamento appropriati
- [ ] **Error states**: Gestione stati di errore

---

## 🧪 Test Edge Cases

### Dati Estremi
- [ ] **Attività molto lunghe**: Titoli e descrizioni molto lunghe
- [ ] **Date estreme**: Attività in passato remoto o futuro lontano
- [ ] **Orari limite**: Attività che iniziano a mezzanotte
- [ ] **Quantità grandi**: Requisiti con quantità molto alte

### Conflitti e Vincoli
- [ ] **Doppie assegnazioni**: Prevenzione assegnazioni duplicate
- [ ] **Conflitti orari**: Rilevamento sovrapposizioni
- [ ] **Qualifiche mancanti**: Prevenzione assegnazioni non qualificate
- [ ] **Cicli referenziali**: Prevenzione riferimenti circolari

---

## 📋 Risultati Test

### Riepilogo
- **Test Totali**: ___ / ___
- **Test Superati**: ___ / ___
- **Test Falliti**: ___ / ___
- **Percentuale Successo**: ___%

### Problemi Identificati
1. **Problema 1**: ________________
   - **Severità**: Alta/Media/Bassa
   - **Descrizione**: ________________
   - **Soluzione**: ________________

2. **Problema 2**: ________________
   - **Severità**: Alta/Media/Bassa
   - **Descrizione**: ________________
   - **Soluzione**: ________________

### Raccomandazioni
- **Priorità Alta**: ________________
- **Priorità Media**: ________________
- **Priorità Bassa**: ________________

---

## ✅ Checklist Completamento

### Pre-Produzione
- [ ] Tutti i test manuali superati
- [ ] Test automatici eseguiti con successo
- [ ] Documentazione aggiornata
- [ ] Codice revisionato e pulito
- [ ] Performance accettabili
- [ ] Sicurezza verificata

### Post-Deploy
- [ ] Monitoraggio errori attivo
- [ ] Log di sistema configurati
- [ ] Backup database configurato
- [ ] Documentazione utente finale
- [ ] Training team supporto

---

**Data Test**: ___/___/____  
**Tester**: ________________  
**Versione**: ________________  
**Ambiente**: ________________
