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
            this.initCalendar();
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
            
            // Aggiorna il calendario
            if (this.calendar) {
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
            const params = new URLSearchParams({
                date_from: start.toISOString().split('T')[0],
                date_to: end.toISOString().split('T')[0],
                ...this.filters
            });
            
            // Aggiungi filtro copertura se presente
            if (this.filters.coverage) {
                params.append('coverage', this.filters.coverage);
            }
            
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
            failureCallback(error);
        }
    }
    
    filterByCoverage(activities, coverageFilter) {
        switch (coverageFilter) {
            case '100':
                return activities.filter(a => a.coverage_percentage >= 100);
            case 'partial':
                return activities.filter(a => a.coverage_percentage > 0 && a.coverage_percentage < 100);
            case 'low':
                return activities.filter(a => a.coverage_percentage === 0);
            default:
                return activities;
        }
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
        
        // Aggiungi tooltip con informazioni
        element.title = `${event.title}\n${event.extendedProps.type}\nStato: ${state}\nCopertura: ${event.extendedProps.coverage}%`;
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
        
        if (activities.length === 0) {
            container.innerHTML = '<div class="col-12"><p class="text-muted text-center">Nessuna attività trovata.</p></div>';
            return;
        }
        
        // Raggruppa per data
        const groupedActivities = this.groupActivitiesByDate(activities);
        
        Object.keys(groupedActivities).forEach(date => {
            const dateGroup = document.createElement('div');
            dateGroup.className = 'col-12 mb-3';
            
            const dateHeader = document.createElement('h6');
            dateHeader.className = 'text-muted border-bottom pb-2';
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
                            <i class="bi bi-clock"></i> ${activity.start_time} - ${activity.end_time} | 
                            <i class="bi bi-tag"></i> ${activity.activity_type?.name || 'N/A'}
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
                        <i class="bi bi-eye"></i> Dettagli
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
        // Implementa un sistema di toast/notifiche
        console.log(`${type.toUpperCase()}: ${message}`);
        // Puoi integrare con il sistema di toast esistente del progetto
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
        instructors.sort((a, b) => a.full_name.localeCompare(b.full_name));
        
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
                                <h6 class="mb-0">${instructor.full_name}</h6>
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
