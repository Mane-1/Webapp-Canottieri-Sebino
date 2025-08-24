# Navbar - Canottieri Sebino

## Panoramica

Il navbar è presente in tutte le pagine dell'applicazione e fornisce la navigazione principale tra le diverse sezioni.

## Struttura del Navbar

### Template Base
- **File**: `templates/layout/base.html`
- **Include**: `{% include 'partials/_navbar.html' %}`
- **Estensione**: Tutti i template estendono questo layout

### Navbar Component
- **File**: `templates/partials/_navbar.html`
- **Framework**: Bootstrap 5.3.3
- **Responsive**: Sì, con toggle per dispositivi mobili

## Sezioni del Menu

### 1. Home
- **Link**: `/dashboard`
- **Descrizione**: Pagina principale dell'applicazione

### 2. Agenda
- **Link**: `/agenda`
- **Descrizione**: Vista generale di tutti gli eventi

### 3. Allenamenti
- **Link**: `/calendario` (Calendario Allenamenti)
- **Gestione**: `/allenamenti` (solo admin/allenatore)
- **Descrizione**: Gestione e visualizzazione degli allenamenti

### 4. Turni
- **Link**: `/turni` (Calendario Turni)
- **Statistiche**: `/turni/statistiche`
- **Disponibilità**: `/turni/disponibilita`
- **Gestione**: `/turni/gestione` (solo admin)
- **Descrizione**: Gestione dei turni e disponibilità

### 5. Attività
- **Link**: `/attivita/calendario` (Calendario Attività)
- **Gestione**: `/attivita/gestione` (solo admin/allenatore)
- **Pagamenti**: `/attivita/pagamenti` (solo admin/allenatore)
- **Istruttori**: `/attivita/istruttori` (solo admin/allenatore)
- **Estrazioni**: `/attivita/estrazioni`
- **Descrizione**: Gestione delle attività commerciali

### 6. Risorse
- **Atleti**: `/risorse/athletes` (solo admin/allenatore)
- **Barche**: `/risorse/barche`
- **Mezzi**: `/risorse/mezzi`
- **Scheda Pesi**: `/risorse/pesi`
- **Descrizione**: Gestione delle risorse del club

### 7. Utenti (solo Admin)
- **Elenco**: `/admin/users`
- **Aggiungi**: `/admin/users/add`
- **Descrizione**: Gestione degli utenti del sistema

### 8. Profilo Utente
- **Profilo**: `/profilo`
- **Logout**: `/logout`
- **Descrizione**: Gestione del proprio profilo

## Visibilità Condizionale

### Per Tutti gli Utenti
- Home
- Agenda
- Calendario Allenamenti
- Calendario Turni
- Calendario Attività
- Estrazioni
- Barche
- Mezzi
- Scheda Pesi
- Profilo

### Solo Admin e Allenatori
- Gestione Allenamenti
- Turni (tutte le funzioni)
- Gestione Attività
- Pagamenti
- Gestione Istruttori
- Atleti

### Solo Admin
- Gestione Turni
- Gestione Utenti

## Responsive Design

### Desktop
- Menu completo visibile
- Dropdown per sezioni complesse
- Brand sempre visibile

### Mobile
- Toggle button per menu
- Menu collassabile
- Brand sempre visibile
- Menu utente a destra

## Stili CSS

### Bootstrap
- `navbar-expand-lg`: Espansione su schermi grandi
- `navbar-dark`: Tema scuro
- `shadow-sm`: Ombra leggera

### Personalizzato
- Colori del brand
- Hover effects
- Transizioni fluide

## Verifica Visibilità

### Controlli da Fare
1. **Template Base**: Verificare che tutti i template estendano `layout/base.html`
2. **Include Navbar**: Verificare che il navbar sia incluso in ogni pagina
3. **CSS**: Verificare che non ci siano regole che nascondono il navbar
4. **Responsive**: Testare su dispositivi mobili e desktop

### Problemi Comuni
1. **Navbar Nascosto**: Controllare CSS per `display: none`
2. **Z-index**: Verificare che il navbar sia sopra altri elementi
3. **Overflow**: Controllare che il contenitore non nasconda il navbar
4. **JavaScript**: Verificare che non ci siano script che nascondono il navbar

### Debug
1. **Console Browser**: Controllare errori JavaScript
2. **Inspector**: Verificare che il navbar sia nel DOM
3. **CSS**: Controllare regole che potrebbero nascondere il navbar
4. **Template**: Verificare che l'estensione sia corretta

## Template che Estendono il Layout Base

### Pagine Principali
- Dashboard
- Agenda
- Calendario
- Turni
- Attività
- Risorse
- Profilo

### Gestione
- Allenamenti
- Barche
- Mezzi
- Pesi
- Utenti (admin)

### Errori
- 404
- 500
- 503

## Template che Estendono Layout Admin

### Admin Layout
- `templates/layouts/_admin_layout.html`
- Estende `layout/base.html`
- Include navbar completo
- Aggiunge toolbar per funzioni admin

### Pagine Admin
- Lista Utenti
- Aggiungi Utente
- Modifica Utente

## Note Tecniche

### Bootstrap
- Versione: 5.3.3
- JavaScript: Bundle completo incluso
- CSS: CDN con fallback locale

### Responsive Breakpoints
- `lg`: 992px e superiori
- `md`: 768px e superiori
- `sm`: 576px e superiori
- `xs`: Sotto 576px

### JavaScript
- Toggle menu mobile
- Dropdown automatici
- Collapse responsive

## Manutenzione

### Aggiornamenti
1. **Bootstrap**: Aggiornare versione se necessario
2. **CSS**: Mantenere compatibilità con Bootstrap
3. **Template**: Verificare che tutti estendano il layout base

### Aggiunte Nuove Sezioni
1. Aggiungere voce nel navbar
2. Creare template che estenda `layout/base.html`
3. Verificare visibilità e responsive design
4. Testare su diversi dispositivi

### Rimozione Sezioni
1. Rimuovere voce dal navbar
2. Aggiornare template correlati
3. Verificare che non ci siano link orfani
4. Testare navigazione

## Troubleshooting

### Navbar Non Visibile
1. Verificare che il template estenda `layout/base.html`
2. Controllare che non ci siano errori di sintassi
3. Verificare che il CSS non nasconda il navbar
4. Controllare console browser per errori JavaScript

### Menu Non Responsive
1. Verificare che Bootstrap sia caricato correttamente
2. Controllare che il JavaScript sia incluso
3. Verificare che non ci siano conflitti CSS
4. Testare su dispositivi reali

### Link Non Funzionanti
1. Verificare che le route siano definite
2. Controllare che i template esistano
3. Verificare che i permessi siano corretti
4. Controllare log applicazione per errori

## Best Practices

### Template
- Sempre estendere `layout/base.html`
- Non duplicare codice del navbar
- Mantenere struttura consistente
- Usare blocchi appropriati

### CSS
- Non sovrascrivere stili Bootstrap critici
- Usare variabili CSS per colori
- Mantenere responsive design
- Testare su diversi dispositivi

### JavaScript
- Non interferire con funzionalità Bootstrap
- Mantenere codice pulito e commentato
- Gestire errori appropriatamente
- Testare funzionalità interattive
