/**
 * JavaScript per la gestione del calendario delle attività
 */

class ActivitiesCalendar {
    constructor() {
        this.calendar = null;
        this.currentView = 'calendar';
        this.currentActivity = null;
        this.filters = {};
        
        this.init();
    }
    
    init() {
        try {
            console.log('Inizializzazione ActivitiesCalendar...');
            this.initViewSwitch();
            this.initFilters();
            
            // Imposta la vista predefinita in base alla dimensione dello schermo
            if (this.isMobile()) {
                this.switchView('list');
            } else {
                this.initCalendar();
            }
            
            this.bindEvents();
            this.loadSavedFilters();
            console.log('ActivitiesCalendar inizializzato con successo');
        } catch (error) {
            console.error('Errore nell\'inizializzazione di ActivitiesCalendar:', error);
        }
    }
    
    initViewSwitch() {
        const btnCalendar = document.getElementById('btn-calendar');
        const btnList = document.getElementById('btn-list');
        
        btnCalendar.addEventListener('click', () => this.switchView('calendar'));
        btnList.addEventListener('click', () => this.switchView('list'));
    }
    
    initFilters() {
        const form = document.getElementById('filters-form');
        const btnClear = document.getElementById('btn-clear-filters');
        
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            this.applyFilters();
        });
        
        btnClear.addEventListener('click', () => {
            this.clearFilters();
        });
    }
    
    initCalendar() {
        const calendarEl = document.getElementById('activities-calendar');
        
        // Determina la vista di default in base al dispositivo
        const defaultView = this.isMobile() ? 'listWeek' : 'timeGridWeek';
        
        this.calendar = new FullCalendar.Calendar(calendarEl, {
            initialView: defaultView,
            locale: 'it',
            headerToolbar: {
                left: 'prev,next today',
                center: 'title',
                right: 'dayGridMonth,timeGridWeek,timeGridDay,listWeek'
            },
            buttonText: {
                today: 'Oggi',
                month: 'Mese',
                week: 'Settimana',
                day: 'Giorno',
                list: 'Lista'
            },
            height: 'auto',
            slotMinTime: '07:00:00',
            slotMaxTime: '21:00:00',
            scrollTime: '08:00:00',
            allDaySlot: false,
            events: (info, successCallback, failureCallback) => {
                this.fetchActivities(info.start, info.end, successCallback, failureCallback);
            },
            eventClick: (info) => {
                this.showActivityDetails(info.event.id);
            },
            eventDidMount: (info) => {
                this.styleEvent(info.event, info.el);
            },
            viewDidMount: () => {
                // Aggiorna la vista quando cambia
                this.updateViewType();
            }
        });
        
        this.calendar.render();
    }
    
    bindEvents() {
        // Gestione modal
        const modal = document.getElementById('activityModal');
        modal.addEventListener('hidden.bs.modal', () => {
            this.currentActivity = null;
        });
        
        // Bottone autocandidatura
        const btnSelfAssign = document.getElementById('btn-self-assign');
        if (btnSelfAssign) {
            btnSelfAssign.addEventListener('click', () => {
                this.selfAssign();
            });
        }
        
        // Gestione note di pagamento
        const btnSaveNotes = document.getElementById('btn-save-notes');
        const btnClearNotes = document.getElementById('btn-clear-notes');
        
        if (btnSaveNotes) {
            btnSaveNotes.addEventListener('click', () => {
                this.savePaymentNotes();
            });
        }
        
        if (btnClearNotes) {
            btnClearNotes.addEventListener('click', () => {
                this.clearPaymentNotes();
            });
        }
        
        // Gestione modal assegnazione istruttori
        const assignModal = document.getElementById('assignInstructorModal');
        if (assignModal) {
            const btnConfirm = document.getElementById('btn-confirm-assignment');
            const instructorsContainer = document.getElementById('instructors-container');
            
            // Gestione selezione istruttore
            instructorsContainer.addEventListener('click', (e) => {
                if (e.target.classList.contains('instructor-badge')) {
                    // Rimuovi selezione precedente
                    instructorsContainer.querySelectorAll('.instructor-badge').forEach(badge => {
                        badge.classList.remove('selected');
                    });
                    
                    // Seleziona quello cliccato
                    e.target.classList.add('selected');
                    btnConfirm.disabled = false;
                    
                    // Salva l'ID dell'istruttore selezionato
                    this.selectedInstructorId = e.target.dataset.instructorId;
                }
            });
            
            // Gestione conferma assegnazione
            btnConfirm.addEventListener('click', () => {
                if (this.selectedInstructorId && this.currentRequirementId) {
                    this.confirmAssignment(this.selectedInstructorId, this.currentRequirementId);
                }
            });
            
            // Reset quando si chiude il modal
            assignModal.addEventListener('hidden.bs.modal', () => {
                this.selectedInstructorId = null;
                this.currentRequirementId = null;
                btnConfirm.disabled = true;
                instructorsContainer.querySelectorAll('.instructor-badge').forEach(badge => {
                    badge.classList.remove('selected');
                });
            });
        }
    }
    
    switchView(view) {
        this.currentView = view;
        
        const btnCalendar = document.getElementById('btn-calendar');
        const btnList = document.getElementById('btn-list');
        const calendarDiv = document.getElementById('activities-calendar');
        const listDiv = document.getElementById('activities-list');
        
        if (view === 'calendar') {
            btnCalendar.classList.add('active');
            btnList.classList.remove('active');
            calendarDiv.classList.remove('d-none');
            listDiv.classList.add('d-none');
            
            // Inizializza il calendario se non è ancora stato fatto
            if (!this.calendar) {
                this.initCalendar();
            } else {
                this.calendar.render();
            }
        } else {
            btnList.classList.add('active');
            btnCalendar.classList.remove('active');
            listDiv.classList.remove('d-none');
            calendarDiv.classList.add('d-none');
            
            // Carica la vista elenco
            this.loadListView();
        }
    }
    
    async fetchActivities(start, end, successCallback, failureCallback) {
        try {
            // Mostra indicatore di caricamento
            this.showLoadingIndicator();
            
            const params = new URLSearchParams({
                date_from: start.toISOString().split('T')[0],
                date_to: end.toISOString().split('T')[0]
            });
            
            // Aggiungi filtri se presenti
            Object.keys(this.filters).forEach(key => {
                if (this.filters[key] && key !== 'coverage') {
                    params.append(key, this.filters[key]);
                }
            });
            
            const response = await fetch(`/api/attivita?${params}`);
            if (!response.ok) throw new Error('Errore nel caricamento delle attività');
            
            const activities = await response.json();
            
            // Filtra per copertura se richiesto
            let filteredActivities = activities;
            if (this.filters.coverage) {
                filteredActivities = this.filterByCoverage(activities, this.filters.coverage);
            }
            
            // Converti in formato FullCalendar
            const events = filteredActivities.map(activity => ({
                id: activity.id,
                title: activity.title,
                start: `${activity.date}T${activity.start_time}`,
                end: `${activity.date}T${activity.end_time}`,
                backgroundColor: activity.activity_type?.color || '#007bff',
                borderColor: activity.activity_type?.color || '#007bff',
                extendedProps: {
                    state: activity.state,
                    type: activity.activity_type?.name,
                    coverage: activity.coverage_percentage,
                    payment_state: activity.payment_state
                }
            }));
            
            successCallback(events);
        } catch (error) {
            console.error('Errore nel caricamento delle attività:', error);
            this.showToast('Si è verificato un errore nel caricamento delle attività', 'error');
            failureCallback(error);
        } finally {
            // Nascondi indicatore di caricamento
            this.hideLoadingIndicator();
        }
    }
    
    showLoadingIndicator() {
        const calendarEl = document.getElementById('activities-calendar');
        if (!calendarEl) return;
        
        // Verifica se esiste già un indicatore
        if (document.getElementById('calendar-loading-indicator')) return;
        
        // Crea l'indicatore di caricamento
        const loadingDiv = document.createElement('div');
        loadingDiv.id = 'calendar-loading-indicator';
        loadingDiv.className = 'position-absolute top-50 start-50 translate-middle bg-white p-3 rounded shadow-sm';
        loadingDiv.innerHTML = `
            <div class="d-flex align-items-center">
                <div class="spinner-border spinner-border-sm text-primary me-2" role="status"></div>
                <span>Caricamento attività...</span>
            </div>
        `;
        
        // Assicurati che il container abbia position relative
        calendarEl.style.position = 'relative';
        calendarEl.appendChild(loadingDiv);
    }
    
    hideLoadingIndicator() {
        const indicator = document.getElementById('calendar-loading-indicator');
        if (indicator) {
            indicator.remove();
        }
    }
    
    filterByCoverage(activities, coverageFilter) {
        if (!coverageFilter) return activities;
        
        return activities.filter(activity => {
            const coverage = activity.coverage_percentage || 0;
            if (coverageFilter === '100') return coverage >= 100;
            if (coverageFilter === 'partial') return coverage > 0 && coverage < 100;
            if (coverageFilter === '0') return coverage === 0;
            return true;
        });
    }
    
    styleEvent(event, element) {
        // Stile basato sullo stato
        const state = event.extendedProps.state;
        let stateClass = '';
        
        switch (state) {
            case 'confermata':
                stateClass = 'event-confirmed';
                break;
            case 'da_confermare':
                stateClass = 'event-pending';
                break;
            case 'bozza':
                stateClass = 'event-draft';
                break;
            case 'annullata':
                stateClass = 'event-cancelled';
                break;
            case 'completata':
                stateClass = 'event-completed';
                break;
        }
        
        if (stateClass) {
            element.classList.add(stateClass);
        }
        
        // Migliora l'accessibilità aggiungendo attributi ARIA
        element.setAttribute('aria-label', `${event.title}, ${this.getStateLabel(state)}`);
        
        // Aggiungi tooltip con informazioni
        element.title = `${event.title}\n${event.extendedProps.type}\nStato: ${state}\nCopertura: ${event.extendedProps.coverage}%`;
        
        // Aggiungi icona in base al tipo di attività
        const activityType = event.extendedProps.type;
        if (activityType) {
            const typeIcon = document.createElement('span');
            typeIcon.className = 'activity-type-icon';
            
            // Scegli l'icona in base al tipo
            let iconClass = 'bi-calendar-event';
            if (activityType.toLowerCase().includes('allenamento')) {
                iconClass = 'bi-stopwatch';
            } else if (activityType.toLowerCase().includes('gara')) {
                iconClass = 'bi-trophy';
            } else if (activityType.toLowerCase().includes('corso')) {
                iconClass = 'bi-mortarboard';
            }
            
            typeIcon.innerHTML = `<i class="bi ${iconClass}"></i>`;
            typeIcon.title = activityType;
            
            // Inserisci l'icona all'inizio del titolo
            const titleElement = element.querySelector('.fc-event-title');
            if (titleElement) {
                titleElement.insertBefore(typeIcon, titleElement.firstChild);
            }
        }
    }
    
    async showActivityDetails(activityId) {
        try {
            const response = await fetch(`/api/attivita/${activityId}`);
            if (!response.ok) throw new Error('Errore nel caricamento dei dettagli');
            
            const activity = await response.json();
            this.currentActivity = activity;
            
            this.populateModal(activity);
            this.showSelfAssignButton(activity);
            this.updatePaymentTab(activity); // Aggiorna la tab pagamento
            
            const modal = new bootstrap.Modal(document.getElementById('activityModal'));
            modal.show();
        } catch (error) {
            console.error('Errore nel caricamento dei dettagli:', error);
            this.showToast('Errore nel caricamento dei dettagli', 'error');
        }
    }
    
    populateModal(activity) {
        // Tab Generale
        document.getElementById('activity-title').textContent = activity.title;
        document.getElementById('activity-description').textContent = activity.short_description || 'Nessuna descrizione';
        document.getElementById('activity-date').textContent = new Date(activity.date).toLocaleDateString('it-IT');
        document.getElementById('activity-time').textContent = `${activity.start_time} - ${activity.end_time}`;
        document.getElementById('activity-type').textContent = activity.activity_type?.name || 'N/A';
        document.getElementById('activity-state').textContent = this.getStateLabel(activity.state);
        document.getElementById('activity-participants').textContent = activity.participants_plan || 'N/A';
        document.getElementById('activity-participants-actual').textContent = activity.participants_actual || 'N/A';
        document.getElementById('activity-participants-notes').textContent = activity.participants_notes || 'Nessuna nota';
        
        // Cliente e contatti
        document.getElementById('activity-customer-name').textContent = activity.customer_name || 'N/A';
        document.getElementById('activity-customer-email').textContent = activity.customer_email || 'N/A';
        document.getElementById('activity-contact-name').textContent = activity.contact_name || 'N/A';
        document.getElementById('activity-contact-phone').textContent = activity.contact_phone || 'N/A';
        document.getElementById('activity-contact-email').textContent = activity.contact_email || 'N/A';
        
        // Tab Copertura
        this.populateRequirementsTab(activity);
        
        // Tab Pagamento
        document.getElementById('activity-payment-amount').textContent = activity.payment_amount ? `€ ${activity.payment_amount}` : 'N/A';
        document.getElementById('activity-payment-method').textContent = this.getPaymentMethodLabel(activity.payment_method);
        document.getElementById('activity-payment-state').textContent = this.getPaymentStateLabel(activity.payment_state);
        document.getElementById('activity-billing-name').textContent = activity.billing_name || 'N/A';
        document.getElementById('activity-billing-vat').textContent = activity.billing_vat_or_cf || 'N/A';
        document.getElementById('activity-billing-sdi').textContent = activity.billing_sdi_or_pec || 'N/A';
        document.getElementById('activity-billing-address').textContent = activity.billing_address || 'N/A';
        
        // Bottone modifica (solo per admin/allenatori)
        const btnEdit = document.getElementById('btn-edit-activity');
        if (this.canEditActivity()) {
            btnEdit.style.display = 'inline-block';
            btnEdit.href = `/attivita/dettaglio/${activity.id}`;
        } else {
            btnEdit.style.display = 'none';
        }
    }
    
    populateRequirementsTab(activity) {
        const requirementsList = document.getElementById('requirements-list');
        requirementsList.innerHTML = '';
        
        if (!activity.requirements || activity.requirements.length === 0) {
            requirementsList.innerHTML = '<p class="text-muted">Nessun requisito specificato per questa attività.</p>';
            return;
        }
        
        // Aggiorna badge copertura generale
        const coverageBadge = document.getElementById('coverage-badge');
        coverageBadge.textContent = `${activity.total_assigned}/${activity.total_required} (${activity.coverage_percentage}%)`;
        coverageBadge.className = `badge ${this.getCoverageClass(activity.coverage_percentage)}`;
        
        // Popola ogni requisito
        activity.requirements.forEach(requirement => {
            const template = document.getElementById('requirement-template');
            const clone = template.content.cloneNode(true);
            
            // Popola i dati
            clone.querySelector('.requirement-title').textContent = requirement.qualification_type.name;
            clone.querySelector('.requirement-description').textContent = `Quantità richiesta: ${requirement.quantity}`;
            
            const coverage = requirement.assigned_count || 0;
            const coverageEl = clone.querySelector('.requirement-coverage');
            coverageEl.textContent = `${coverage}/${requirement.quantity}`;
            coverageEl.className = `badge ${this.getCoverageClass((coverage / requirement.quantity) * 100)}`;
            
            // Mostra bottone aggiungi solo per admin/allenatori
            const btnAdd = clone.querySelector('.btn-add-assignment');
            if (this.canEditActivity()) {
                btnAdd.style.display = 'inline-block';
                btnAdd.addEventListener('click', () => {
                    this.showAddAssignmentModal(requirement.id);
                });
            }
            
            // Popola le assegnazioni
            const assignmentsList = clone.querySelector('.assignments-list');
            if (activity.assignments) {
                const relevantAssignments = activity.assignments.filter(a => a.requirement_id === requirement.id);
                relevantAssignments.forEach(assignment => {
                    const assignmentEl = this.createAssignmentElement(assignment);
                    assignmentsList.appendChild(assignmentEl);
                });
            }
            
            requirementsList.appendChild(clone);
        });
    }
    
    createAssignmentElement(assignment) {
        const template = document.getElementById('assignment-template');
        const clone = template.content.cloneNode(true);
        
        clone.querySelector('.assignment-user-name').textContent = assignment.user_name;
        clone.querySelector('.assignment-role').textContent = assignment.role_label ? `(${assignment.role_label})` : '';
        clone.querySelector('.assignment-hours').textContent = `${assignment.hours || 0}h`;
        
        // Bottone rimuovi solo per admin/allenatori
        const btnRemove = clone.querySelector('.btn-remove-assignment');
        if (this.canEditActivity()) {
            btnRemove.style.display = 'inline-block';
            btnRemove.addEventListener('click', () => {
                this.removeAssignment(assignment.id);
            });
        }
        
        return clone;
    }
    
    showSelfAssignButton(activity) {
        const selfAssignSection = document.getElementById('self-assign-section');
        
        // Verifica se l'utente può autocandidarsi
        if (this.canSelfAssign(activity)) {
            selfAssignSection.style.display = 'block';
        } else {
            selfAssignSection.style.display = 'none';
        }
    }
    
    async selfAssign() {
        if (!this.currentActivity) return;
        
        try {
            const response = await fetch(`/api/attivita/${this.currentActivity.id}/self-assign`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    activity_id: this.currentActivity.id
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showToast('Autocandidatura effettuata con successo!', 'success');
                
                // Ricarica i dettagli dell'attività
                await this.showActivityDetails(this.currentActivity.id);
                
                // Aggiorna il calendario
                if (this.calendar) {
                    this.calendar.refetchEvents();
                }
            } else {
                this.showToast(result.message, 'error');
            }
        } catch (error) {
            console.error('Errore nell\'autocandidatura:', error);
            this.showToast('Errore nell\'autocandidatura', 'error');
        }
    }
    
    async loadListView() {
        try {
            const params = new URLSearchParams({
                ...this.filters,
                limit: 100
            });
            
            const response = await fetch(`/api/attivita?${params}`);
            if (!response.ok) throw new Error('Errore nel caricamento delle attività');
            
            const activities = await response.json();
            this.renderListView(activities);
        } catch (error) {
            console.error('Errore nel caricamento della lista:', error);
            this.showToast('Errore nel caricamento della lista', 'error');
        }
    }
    
    renderListView(activities) {
        const container = document.getElementById('activities-list-content');
        container.innerHTML = '';
        
        if (!activities || activities.length === 0) {
            container.innerHTML = `
                <div class="alert alert-info text-center my-4">
                    <i class="bi bi-info-circle me-2"></i>
                    Nessuna attività trovata con i filtri selezionati
                </div>
            `;
            return;
        }
        
        // Raggruppa per data
        const groupedActivities = this.groupActivitiesByDate(activities);
        
        Object.keys(groupedActivities).forEach(date => {
            const dateGroup = document.createElement('div');
            dateGroup.className = 'col-12 mb-3';
            
            const dateHeader = document.createElement('h6');
            dateHeader.className = 'text-muted border-bottom pb-2 sticky-top bg-light pt-2';
            dateHeader.textContent = new Date(date).toLocaleDateString('it-IT', { 
                weekday: 'long', 
                year: 'numeric', 
                month: 'long', 
                day: 'numeric' 
            });
            
            dateGroup.appendChild(dateHeader);
            
            groupedActivities[date].forEach(activity => {
                const activityEl = this.createActivityListItem(activity);
                dateGroup.appendChild(activityEl);
            });
            
            container.appendChild(dateGroup);
        });
    }
    
    createActivityListItem(activity) {
        const div = document.createElement('div');
        div.className = `activity-item ${this.getStateClass(activity.state)} mb-2`;
        
        const stateLabel = this.getStateLabel(activity.state);
        const coverageClass = this.getCoverageClass(activity.coverage_percentage);
        
        // Determina il colore della barra laterale in base alla copertura
        let sidebarColor = '';
        if (activity.coverage_percentage >= 100) {
            sidebarColor = '#198754'; // Verde per 100% coperto
        } else if (activity.coverage_percentage > 0) {
            sidebarColor = '#ffc107'; // Giallo per parzialmente coperto
        } else {
            sidebarColor = '#dc3545'; // Rosso per non coperto
        }
        
        div.innerHTML = `
            <div class="d-flex justify-content-between align-items-start">
                <div class="flex-grow-1 d-flex">
                    <div class="coverage-sidebar me-3" style="width: 8px; background-color: ${sidebarColor}; border-radius: 4px 0 0 4px; min-height: 100%;"></div>
                    <div class="flex-grow-1">
                        <h6 class="mb-1">${activity.title}</h6>
                        <p class="mb-1 text-muted small">
                            <i class="bi bi-clock me-1"></i> ${activity.start_time} - ${activity.end_time} | 
                            <i class="bi bi-tag ms-2 me-1"></i> ${activity.activity_type?.name || 'N/A'}
                        </p>
                        <div class="d-flex gap-2">
                            <span class="badge bg-secondary">${stateLabel}</span>
                            <span class="badge ${coverageClass}">${activity.coverage_percentage}% coperto</span>
                            ${activity.payment_amount ? `<span class="badge bg-info">€ ${activity.payment_amount}</span>` : ''}
                        </div>
                    </div>
                </div>
                <div class="ms-3">
                    <button type="button" class="btn btn-sm btn-outline-primary" onclick="activitiesCalendar.showActivityDetails(${activity.id})">
                        Dettagli
                    </button>
                </div>
            </div>
        `;
        
        return div;
    }
    
    groupActivitiesByDate(activities) {
        const grouped = {};
        activities.forEach(activity => {
            const date = activity.date;
            if (!grouped[date]) {
                grouped[date] = [];
            }
            grouped[date].push(activity);
        });
        
        // Ordina le attività per ora all'interno di ogni data
        Object.keys(grouped).forEach(date => {
            grouped[date].sort((a, b) => a.start_time.localeCompare(b.start_time));
        });
        
        return grouped;
    }
    
    applyFilters() {
        const form = document.getElementById('filters-form');
        const formData = new FormData(form);
        
        this.filters = {};
        for (let [key, value] of formData.entries()) {
            if (value) {
                this.filters[key] = value;
            }
        }
        
        // Aggiorna la vista corrente
        if (this.currentView === 'calendar') {
            if (this.calendar) {
                this.calendar.refetchEvents();
            }
        } else {
            this.loadListView();
        }
        
        // Salva i filtri nella sessione per mantenere lo stato
        sessionStorage.setItem('activities_filters', JSON.stringify(this.filters));
    }
    
    clearFilters() {
        const form = document.getElementById('filters-form');
        form.reset();
        this.filters = {};
        
        // Aggiorna la vista corrente
        if (this.currentView === 'calendar') {
            if (this.calendar) {
                this.calendar.refetchEvents();
            }
        } else {
            this.loadListView();
        }
        
        // Rimuovi i filtri dalla sessione
        sessionStorage.removeItem('activities_filters');
    }
    
    loadSavedFilters() {
        const savedFilters = sessionStorage.getItem('activities_filters');
        if (savedFilters) {
            try {
                this.filters = JSON.parse(savedFilters);
                
                // Applica i filtri salvati al form
                const form = document.getElementById('filters-form');
                if (form) {
                    Object.keys(this.filters).forEach(key => {
                        const input = form.querySelector(`[name="${key}"]`);
                        if (input) {
                            input.value = this.filters[key];
                        }
                    });
                }
            } catch (error) {
                console.error('Errore nel caricamento dei filtri salvati:', error);
                sessionStorage.removeItem('activities_filters');
            }
        }
    }
    
    updateViewType() {
        // Aggiorna la vista quando cambia il calendario
        if (this.calendar) {
            const viewType = this.calendar.view.type;
            // Puoi aggiungere logica specifica per diverse viste del calendario
        }
    }
    
    // Utility methods
    isMobile() {
        return window.innerWidth < 768;
    }
    
    getStateLabel(state) {
        if (!state) return 'Sconosciuto';
        
        const labels = {
            'bozza': 'Bozza',
            'da_confermare': 'Da confermare',
            'confermato': 'Confermato',
            'rimandata': 'Rimandata',
            'in_corso': 'In corso',
            'annullato': 'Annullato',
            'completato': 'Completato'
        };
        return labels[state] || state;
    }
    
    getStateClass(state) {
        const classes = {
            'bozza': 'draft',
            'da_confermare': 'pending',
            'confermato': 'confirmed',
            'rimandata': 'pending',
            'in_corso': 'in-progress',
            'annullato': 'cancelled',
            'completato': 'completed'
        };
        return classes[state] || '';
    }
    
    getStateBadgeClass(state) {
        if (!state) return 'bg-secondary';
        
        const classes = {
            'bozza': 'bg-secondary',
            'da_confermare': 'bg-warning text-dark',
            'confermato': 'bg-success',
            'rimandata': 'bg-warning text-dark',
            'in_corso': 'bg-primary',
            'annullato': 'bg-danger',
            'completato': 'bg-info'
        };
        return classes[state] || 'bg-secondary';
    }
    
    getPaymentMethodLabel(method) {
        if (!method) return 'N/A';
        const labels = {
            'contanti': 'Contanti',
            'carta': 'Carta',
            'bonifico': 'Bonifico',
            'assegno': 'Assegno',
            'voucher': 'Voucher',
            'altro': 'Altro'
        };
        return labels[method] || method;
    }
    
    getPaymentStateLabel(state) {
        const labels = {
            'da_effettuare': 'Da effettuare',
            'da_verificare': 'Da verificare',
            'confermato': 'Confermato'
        };
        return labels[state] || state;
    }
    
    getCoverageClass(percentage) {
        if (percentage >= 100) return 'bg-success';
        if (percentage >= 50) return 'bg-warning';
        return 'bg-danger';
    }
    
    canEditActivity() {
        // Verifica se l'utente può modificare le attività
        // Questo dovrebbe essere verificato lato server
        return true; // Per ora sempre true, da implementare con controlli reali
    }
    
    canSelfAssign(activity) {
        // Verifica se l'utente può autocandidarsi
        // Questo dovrebbe essere verificato lato server
        return true; // Per ora sempre true, da implementare con controlli reali
    }
    
    showToast(message, type = 'info') {
        // Crea container se non esiste
        let toastContainer = document.querySelector('.toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
            toastContainer.style.zIndex = '1050';
            document.body.appendChild(toastContainer);
        }
        
        // Crea toast
        const toastId = `toast-${Date.now()}`;
        const toast = document.createElement('div');
        toast.className = `toast align-items-center border-0 show`;
        toast.id = toastId;
        
        // Imposta classe in base al tipo
        switch (type) {
            case 'success': toast.classList.add('bg-success', 'text-white'); break;
            case 'error': toast.classList.add('bg-danger', 'text-white'); break;
            case 'warning': toast.classList.add('bg-warning'); break;
            default: toast.classList.add('bg-info', 'text-white');
        }
        
        // Contenuto toast
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Chiudi"></button>
            </div>
        `;
        
        // Aggiungi al container
        toastContainer.appendChild(toast);
        
        // Rimuovi dopo 5 secondi
        setTimeout(() => {
            const toastElement = document.getElementById(toastId);
            if (toastElement) {
                toastElement.classList.remove('show');
                setTimeout(() => toastElement.remove(), 500);
            }
        }, 5000);
    }

    showAddAssignmentModal(requirementId) {
        this.currentRequirementId = requirementId;
        
        // Trova il requisito corrente
        const requirement = this.currentActivity.requirements.find(r => r.id === requirementId);
        if (!requirement) return;
        
        // Popola il modal
        document.getElementById('requirement-title').textContent = requirement.qualification_type.name;
        document.getElementById('requirement-description').textContent = `Quantità richiesta: ${requirement.quantity}`;
        
        // Carica gli istruttori disponibili
        this.loadAvailableInstructors(requirement);
        
        // Mostra il modal
        const modal = new bootstrap.Modal(document.getElementById('assignInstructorModal'));
        modal.show();
    }
    
    async loadAvailableInstructors(requirement) {
        try {
            const response = await fetch(`/api/attivita/${this.currentActivity.id}/available-instructors?requirement_id=${requirement.id}`);
            if (!response.ok) throw new Error('Errore nel caricamento degli istruttori');
            
            const data = await response.json();
            this.renderInstructorsList(data.instructors, data.conflicts);
        } catch (error) {
            console.error('Errore nel caricamento degli istruttori:', error);
            this.showToast('Errore nel caricamento degli istruttori', 'error');
        }
    }
    
    renderInstructorsList(instructors, conflicts) {
        const container = document.getElementById('instructors-container');
        container.innerHTML = '';
        
        if (instructors.length === 0) {
            container.innerHTML = '<p class="text-muted">Nessun istruttore disponibile per questa qualifica.</p>';
            return;
        }
        
        // Ordina istruttori alfabeticamente
        instructors.sort((a, b) => `${a.first_name} ${a.last_name}`.localeCompare(`${b.first_name} ${b.last_name}`));
        
        instructors.forEach(instructor => {
            const isConflicted = conflicts.includes(instructor.id);
            const instructorCard = document.createElement('div');
            instructorCard.className = `instructor-card card ${isConflicted ? 'border-danger' : 'border-success'} mb-2`;
            instructorCard.style.cursor = 'pointer';
            instructorCard.dataset.instructorId = instructor.id;
            
            instructorCard.innerHTML = `
                <div class="card-body p-3">
                    <div class="d-flex justify-content-between align-items-start">
                        <div class="flex-grow-1">
                            <div class="d-flex align-items-center mb-2">
                                <i class="bi bi-person-circle text-primary me-2 fs-5"></i>
                                <h6 class="mb-0">${instructor.first_name} ${instructor.last_name}</h6>
                                <span class="badge ${isConflicted ? 'bg-danger' : 'bg-success'} ms-2">
                                    ${isConflicted ? 'Impegnato' : 'Disponibile'}
                                </span>
                            </div>
                            <div class="mb-2">
                                <small class="text-muted">
                                    <i class="bi bi-tag me-1"></i>
                                    <strong>Risorse compatibili:</strong> ${instructor.qualifications || 'N/A'}
                                </small>
                            </div>
                            ${instructor.email ? `<small class="text-muted d-block"><i class="bi bi-envelope me-1"></i>${instructor.email}</small>` : ''}
                        </div>
                        <div class="ms-3">
                            <button type="button" class="btn btn-primary btn-sm btn-prenota" ${isConflicted ? 'disabled' : ''}>
                                <i class="bi bi-calendar-check"></i> Prenota
                            </button>
                        </div>
                    </div>
                </div>
            `;
            
            // Aggiungi event listener per la selezione
            instructorCard.addEventListener('click', (e) => {
                if (e.target.classList.contains('btn-prenota')) return; // Non selezionare se clicchi il bottone
                
                // Rimuovi selezione precedente
                container.querySelectorAll('.instructor-card').forEach(card => {
                    card.classList.remove('selected');
                });
                
                // Seleziona quello cliccato
                instructorCard.classList.add('selected');
                document.getElementById('btn-confirm-assignment').disabled = false;
                
                // Salva l'ID dell'istruttore selezionato
                this.selectedInstructorId = instructor.id;
            });
            
            // Event listener per il bottone Prenota
            const btnPrenota = instructorCard.querySelector('.btn-prenota');
            btnPrenota.addEventListener('click', (e) => {
                e.stopPropagation();
                
                // Rimuovi selezione precedente
                container.querySelectorAll('.instructor-card').forEach(card => {
                    card.classList.remove('selected');
                });
                
                // Seleziona questo istruttore
                instructorCard.classList.add('selected');
                document.getElementById('btn-confirm-assignment').disabled = false;
                this.selectedInstructorId = instructor.id;
            });
            
            container.appendChild(instructorCard);
        });
    }
    
    async confirmAssignment(instructorId, requirementId) {
        try {
            const response = await fetch(`/api/attivita/${this.currentActivity.id}/assign-instructor`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    instructor_id: instructorId,
                    requirement_id: requirementId
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showToast('Istruttore assegnato con successo!', 'success');
                
                // Chiudi il modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('assignInstructorModal'));
                modal.hide();
                
                // Ricarica i dettagli dell'attività
                await this.showActivityDetails(this.currentActivity.id);
                
                // Aggiorna il calendario
                if (this.calendar) {
                    this.calendar.refetchEvents();
                }
            } else {
                this.showToast(result.message, 'error');
            }
        } catch (error) {
            console.error('Errore nell\'assegnazione:', error);
            this.showToast('Errore nell\'assegnazione dell\'istruttore', 'error');
        }
    }

    async savePaymentNotes() {
        if (!this.currentActivity) return;
        
        const notes = document.getElementById('payment-notes').value;
        
        try {
            const response = await fetch(`/api/attivita/${this.currentActivity.id}/payment-notes`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    notes: notes
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showToast('Note salvate con successo!', 'success');
            } else {
                this.showToast(result.message, 'error');
            }
        } catch (error) {
            console.error('Errore nel salvataggio delle note:', error);
            this.showToast('Errore nel salvataggio delle note', 'error');
        }
    }
    
    clearPaymentNotes() {
        document.getElementById('payment-notes').value = '';
        this.showToast('Note cancellate', 'info');
    }
    
    updatePaymentTab(activity) {
        // Aggiorna il badge dello stato pagamento
        const statusBadge = document.getElementById('payment-status-badge');
        if (statusBadge) {
            statusBadge.textContent = this.getPaymentStateLabel(activity.payment_state);
            statusBadge.className = `badge fs-6 me-3 ${this.getPaymentStateClass(activity.payment_state)}`;
        }
        
        // Aggiorna l'ultimo aggiornamento
        const lastUpdate = document.getElementById('payment-last-update');
        if (lastUpdate) {
            lastUpdate.textContent = activity.updated_at ? new Date(activity.updated_at).toLocaleString('it-IT') : 'N/A';
        }
        
        // Aggiorna i dettagli pagamento
        const amount = document.getElementById('activity-payment-amount');
        if (amount) {
            amount.textContent = activity.payment_amount ? `€ ${parseFloat(activity.payment_amount).toFixed(2)}` : '€ 0.00';
        }
        
        const method = document.getElementById('activity-payment-method');
        if (method) {
            method.textContent = this.getPaymentMethodLabel(activity.payment_method);
        }
        
        const dueDate = document.getElementById('activity-payment-due-date');
        if (dueDate) {
            dueDate.textContent = activity.payment_due_date || 'N/A';
        }
        
        const reference = document.getElementById('activity-payment-reference');
        if (reference) {
            reference.textContent = activity.payment_reference || 'N/A';
        }
        
        // Aggiorna le note
        const notes = document.getElementById('payment-notes');
        if (notes) {
            notes.value = activity.payment_notes || '';
        }
        
        // Aggiorna la fatturazione
        const billingName = document.getElementById('activity-billing-name');
        if (billingName) {
            billingName.textContent = activity.billing_name || 'N/A';
        }
        
        const billingVat = document.getElementById('activity-billing-vat');
        if (billingVat) {
            billingVat.textContent = activity.billing_vat_or_cf || 'N/A';
        }
        
        const billingSdi = document.getElementById('activity-billing-sdi');
        if (billingSdi) {
            billingSdi.textContent = activity.billing_sdi_or_pec || 'N/A';
        }
        
        const billingAddress = document.getElementById('activity-billing-address');
        if (billingAddress) {
            billingAddress.textContent = activity.billing_address || 'N/A';
        }
    }
    
    getPaymentStateClass(state) {
        const classes = {
            'da_effettuare': 'bg-danger',
            'da_verificare': 'bg-warning text-dark',
            'confermato': 'bg-success'
        };
        return classes[state] || 'bg-secondary';
    }
}

// Inizializza quando il DOM è pronto
document.addEventListener('DOMContentLoaded', () => {
    window.activitiesCalendar = new ActivitiesCalendar();
});
