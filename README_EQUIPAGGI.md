# Gestione Equipaggi - Canottieri Sebino

## Panoramica

La funzionalità di gestione degli equipaggi permette di creare e gestire equipaggi per le diverse barche del club. Ogni equipaggio è composto da atleti assegnati a specifici posti a seconda del tipo di barca.

## Tipi di Barca e Posti Richiesti

### Barche Singole (1x, 1P 7,20, Jole 1x)
- **Capovoga** (obbligatorio)

### Barche Doppie (2x, 2-, 2x-, Jole 2x)
- **Capovoga** (obbligatorio)
- **Prodiere** (obbligatorio)

### Barche Doppie con Timoniere (2+)
- **Capovoga** (obbligatorio)
- **Prodiere** (obbligatorio)
- **Timoniere** (facoltativo)

### Barche Quadruple (4x, Jole 4x)
- **Capovoga** (obbligatorio)
- **Secondo** (obbligatorio)
- **Terzo** (obbligatorio)
- **Prodiere** (obbligatorio)

### Barche Quadruple con Timoniere (4x-, 4-, 4+)
- **Capovoga** (obbligatorio)
- **Secondo** (obbligatorio)
- **Terzo** (obbligatorio)
- **Prodiere** (obbligatorio)
- **Timoniere** (facoltativo)

### Barche Otto (8+)
- **Capovoga** (obbligatorio)
- **Secondo** (obbligatorio)
- **Terzo** (obbligatorio)
- **Quarto** (obbligatorio)
- **Quinto** (obbligatorio)
- **Sesto** (obbligatorio)
- **Settimo** (obbligatorio)
- **Prodiere** (obbligatorio)
- **Timoniere** (facoltativo)

## Funzionalità Disponibili

### 1. Visualizzazione Equipaggi
- **Tab "Equipaggi" nella pagina Modifica Barca**: Mostra tutti gli equipaggi esistenti per una barca
- **Tab "Equipaggi" nella pagina Dettaglio Barca**: Visualizzazione in sola lettura degli equipaggi

### 2. Creazione Equipaggi
- **Nuovo Equipaggio**: Crea un nuovo equipaggio per una barca specifica
- **Validazione Automatica**: Il sistema verifica che tutti i posti obbligatori siano occupati
- **Controllo Duplicati**: Impedisce di assegnare lo stesso atleta a più posti nella stessa barca

### 3. Modifica Equipaggi
- **Modifica Nome**: Cambia il nome dell'equipaggio
- **Riassegnazione Posti**: Modifica gli atleti assegnati ai vari posti
- **Aggiornamento Note**: Modifica le note aggiuntive

### 4. Eliminazione Equipaggi
- **Eliminazione Sicura**: Conferma richiesta prima dell'eliminazione
- **Cascata**: L'eliminazione rimuove tutti i riferimenti agli atleti

## Interfaccia Utente

### Tab Equipaggi nella Modifica Barca
- **Gestisci Equipaggi**: Pulsante per accedere alla gestione completa
- **Anteprima**: Mostra i primi equipaggi con composizione e note
- **Stato**: Indica se ci sono equipaggi creati o meno

### Lista Equipaggi
- **Nome Equipaggio**: Identificativo univoco dell'equipaggio
- **Composizione**: Badge colorati per ogni posto occupato
- **Note**: Informazioni aggiuntive sull'equipaggio
- **Azioni**: Modifica ed eliminazione

### Form Equipaggio
- **Nome**: Campo obbligatorio per identificare l'equipaggio
- **Selezione Atleti**: Dropdown per ogni posto richiesto
- **Validazione**: Controllo automatico dei campi obbligatori
- **Note**: Campo opzionale per informazioni aggiuntive

## Gestione Database

### Tabella `equipaggi`
- **ID**: Chiave primaria auto-incrementale
- **Nome**: Nome dell'equipaggio (max 100 caratteri)
- **Barca ID**: Riferimento alla barca (FK)
- **Posti**: Campi per ogni possibile posto (capovoga, secondo, terzo, ecc.)
- **Note**: Campo di testo per informazioni aggiuntive
- **Timestamps**: Data di creazione e ultima modifica

### Vincoli e Relazioni
- **Foreign Keys**: Tutti i posti fanno riferimento alla tabella `users`
- **Barca**: Ogni equipaggio appartiene a una barca specifica
- **Unicità**: Un atleta non può essere assegnato a più posti nella stessa barca

### Indici
- **Barca ID**: Ottimizza le query per equipaggi di una barca specifica
- **ID**: Indice primario per performance generali

## Regole di Business

### Assegnazione Atleti
1. **Capovoga**: Sempre obbligatorio per tutti i tipi di barca
2. **Timoniere**: Sempre facoltativo (può essere omesso)
3. **Altri Posti**: Obbligatori secondo il tipo di barca
4. **Unicità**: Un atleta non può essere assegnato a più posti nella stessa barca

### Validazione
1. **Posti Obbligatori**: Tutti i posti richiesti devono essere occupati
2. **Atleti Disponibili**: Solo atleti non già assegnati possono essere selezionati
3. **Nome Univoco**: Ogni equipaggio deve avere un nome diverso

### Gestione Errori
1. **Validazione Form**: Controllo lato client per campi obbligatori
2. **Controllo Server**: Validazione lato server per integrità dati
3. **Messaggi Utente**: Feedback chiaro per errori e successi

## Utilizzo Pratico

### Creazione Primo Equipaggio
1. Accedere alla pagina "Modifica Barca"
2. Selezionare la tab "Equipaggi"
3. Cliccare su "Crea Primo Equipaggio"
4. Compilare il nome dell'equipaggio
5. Selezionare gli atleti per i posti obbligatori
6. Salvare l'equipaggio

### Gestione Equipaggi Esistenti
1. Accedere alla lista equipaggi della barca
2. Utilizzare i pulsanti di modifica/eliminazione
3. Aggiornare composizione e note secondo necessità

### Visualizzazione Rapida
1. Nella lista barche, la colonna "Equipaggi" mostra i primi due equipaggi
2. Icona utenti e contatore per equipaggi aggiuntivi
3. Accesso diretto alla gestione completa tramite link

## Note Tecniche

### Performance
- **Lazy Loading**: Gli equipaggi vengono caricati solo quando necessario
- **Indici Database**: Ottimizzazione per query frequenti
- **Caching**: Riduzione delle query ripetute

### Sicurezza
- **Controllo Accessi**: Solo admin e allenatori possono gestire equipaggi
- **Validazione Input**: Sanitizzazione di tutti i parametri
- **Audit Trail**: Tracciamento di creazione e modifiche

### Manutenibilità
- **Codice Modulare**: Separazione chiara tra logica e presentazione
- **Configurazione**: Posti richiesti configurabili per tipo barca
- **Estensibilità**: Facile aggiunta di nuovi tipi di barca

## Supporto e Troubleshooting

### Problemi Comuni
1. **Atleta Non Disponibile**: Verificare che non sia già assegnato ad altri equipaggi
2. **Validazione Fallita**: Controllare che tutti i posti obbligatori siano occupati
3. **Errore Database**: Verificare integrità delle relazioni e vincoli

### Log e Debug
- **Log Applicazione**: Tracciamento delle operazioni CRUD
- **Errori Database**: Messaggi dettagliati per problemi di integrità
- **Validazione**: Feedback utente per errori di input

## Roadmap Futura

### Funzionalità Pianificate
1. **Storico Equipaggi**: Tracciamento delle modifiche nel tempo
2. **Template Equipaggi**: Salvataggio di composizioni frequenti
3. **Statistiche**: Analisi dell'utilizzo degli equipaggi
4. **Notifiche**: Avvisi per cambi di composizione
5. **API REST**: Endpoint per integrazione esterna

### Miglioramenti UI/UX
1. **Drag & Drop**: Riorganizzazione visiva degli equipaggi
2. **Ricerca Avanzata**: Filtri per atleti e categorie
3. **Responsive Design**: Ottimizzazione per dispositivi mobili
4. **Temi**: Personalizzazione dell'aspetto visivo
