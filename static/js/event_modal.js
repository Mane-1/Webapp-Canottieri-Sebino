(function () {
  document.addEventListener('DOMContentLoaded', function () {
    const isAtleta = document.body.dataset.isAtleta === 'true';
    const isStaff = document.body.dataset.isStaff === 'true';
    const modalEl = document.getElementById('eventDetailModal');
    if (!modalEl) return;
    const modal = new bootstrap.Modal(modalEl);
    const modalTitle = document.getElementById('modalTitle');
    const modalDate = document.getElementById('modalDate');
    const modalTime = document.getElementById('modalTime');
    const modalCategories = document.getElementById('modalCategories');
    const modalCoaches = document.getElementById('modalCoaches');
    const modalRecurrence = document.getElementById('modalRecurrence');
    const attendanceActions = document.getElementById('attendanceActions');
    const btnPresent = document.getElementById('btnPresent');
    const btnAbsent = document.getElementById('btnAbsent');
    const attendanceTable = document.getElementById('attendanceTable');
    const btnBulkPresent = document.getElementById('btnBulkPresent');
    const btnBulkAbsent = document.getElementById('btnBulkAbsent');
    const selectAll = document.getElementById('selectAll');
    const categoriesContainer = document.getElementById('categoriesContainer');
    const btnAddAthlete = document.getElementById('btnAddAthlete');
    const addAthleteSelect = document.getElementById('addAthleteSelect');
    const btnEditTraining = document.getElementById('btnEditTraining');
    const btnSaveChanges = document.getElementById('btnSaveChanges');
    const STATUS_LABELS = { present: 'Presente', absent: 'Assente', maybe: 'Forse' };
    let currentTrainingId = null;
    let currentEventEl = null;
    let athleteOptionsLoaded = false;
    let originalCategories = [];
    let selectedCategories = [];
    let categoriesLoaded = false;
    let allCategories = [];

    async function loadAthleteOptions() {
      if (athleteOptionsLoaded || !addAthleteSelect) return;
      const res = await fetch('/api/athletes');
      if (res.ok) {
        const list = await res.json();
        list.forEach(a => {
          const opt = document.createElement('option');
          opt.value = a.id;
          opt.textContent = a.name;
          addAthleteSelect.appendChild(opt);
        });
        athleteOptionsLoaded = true;
      }
    }
    if (addAthleteSelect) loadAthleteOptions();

    function updateButtons(status) {
      btnPresent.classList.remove('btn-success','btn-outline-success','active');
      btnAbsent.classList.remove('btn-danger','btn-outline-danger','active');
      if (status === 'present') {
        btnPresent.classList.add('btn-success','active');
        btnAbsent.classList.add('btn-outline-danger');
      } else if (status === 'absent') {
        btnAbsent.classList.add('btn-danger','active');
        btnPresent.classList.add('btn-outline-success');
      } else {
        btnPresent.classList.add('btn-outline-success');
        btnAbsent.classList.add('btn-outline-danger');
      }
    }

    btnPresent.addEventListener('click', async () => {
      try {
        await toggleAttendance(currentTrainingId, 'present');
        updateButtons('present');
        if (currentEventEl) currentEventEl.dataset.status = 'present';
      } catch (err) {
        alert(err.message);
      }
    });
    btnAbsent.addEventListener('click', async () => {
      try {
        await toggleAttendance(currentTrainingId, 'absent');
        updateButtons('absent');
        if (currentEventEl) currentEventEl.dataset.status = 'absent';
      } catch (err) {
        alert(err.message);
      }
    });

    function renderAttendance(rows) {
      if (!attendanceTable) return;
      const tbody = attendanceTable.querySelector('tbody');
      tbody.innerHTML = '';
      rows.forEach(r => {
        const tr = document.createElement('tr');
        tr.dataset.athleteId = r.athlete_id;
        if (r.status === 'present') tr.classList.add('table-success');
        if (r.status === 'absent') tr.classList.add('table-danger');
        const badgeClass = r.status === 'present' ? 'bg-success' : r.status === 'absent' ? 'bg-danger' : 'bg-secondary';
        tr.innerHTML = `<td><input type="checkbox" class="attSel"></td><td>${r.athlete_name}</td><td><span class="badge ${badgeClass}">${STATUS_LABELS[r.status] || r.status}</span></td>`;
        tbody.appendChild(tr);
      });
    }

    async function loadAttendance(trainingId) {
      const res = await fetch(`/trainings/${trainingId}/attendance`);
      if (res.ok) {
        const data = await res.json();
        renderAttendance(data);
        if (selectAll) selectAll.checked = false;
      }
    }

    async function bulkUpdate(status) {
      if (!attendanceTable) return;
      const selected = [...attendanceTable.querySelectorAll('tbody input.attSel:checked')]
        .map(cb => ({ athlete_id: parseInt(cb.closest('tr').dataset.athleteId), status }));
      if (!selected.length) return;
      try {
        await bulkAttendance(currentTrainingId, selected, null);
        if (selectAll) selectAll.checked = false;
        await loadAttendance(currentTrainingId);
      } catch (err) {
        alert(err.message);
      }
    }
    if (selectAll) {
      selectAll.addEventListener('change', () => {
        attendanceTable.querySelectorAll('tbody input.attSel').forEach(cb => cb.checked = selectAll.checked);
      });
    }
    if (btnBulkPresent) btnBulkPresent.addEventListener('click', () => bulkUpdate('present'));
    if (btnBulkAbsent) btnBulkAbsent.addEventListener('click', () => bulkUpdate('absent'));

    async function loadCategories() {
      if (categoriesLoaded || !categoriesContainer) return;
      const res = await fetch('/api/categories');
      if (res.ok) {
        allCategories = await res.json();
        categoriesLoaded = true;
      }
    }

    function renderCategories(catList) {
      if (!categoriesContainer) return;
      originalCategories = [...catList];
      selectedCategories = [...catList];
      const groupOrder = ['Over 14', 'Master', 'Under 14'];
      const groups = {};
      groupOrder.forEach(g => groups[g] = []);
      allCategories.forEach(c => {
        const g = c.group || '';
        if (!groups[g]) groups[g] = [];
        groups[g].push(c.name);
      });
      categoriesContainer.innerHTML = '';
      Object.entries(groups).forEach(([g, cats]) => {
        if (!cats.length) return;
        const div = document.createElement('div');
        div.innerHTML = `<h6 class='mb-1'>${g}</h6>`;
        cats.forEach(c => {
          const span = document.createElement('span');
          const active = selectedCategories.includes(c);
          span.className = 'badge rounded-pill fs-6 py-2 px-3 me-1 mb-1 ' + (active ? 'text-bg-primary' : 'text-bg-light text-dark border');
          span.style.cursor = 'pointer';
          span.textContent = c;
          span.addEventListener('click', () => {
            const isActive = selectedCategories.includes(c);
            if (isActive) {
              selectedCategories = selectedCategories.filter(x => x !== c);
              span.classList.remove('text-bg-primary');
              span.classList.add('text-bg-light','text-dark','border');
            } else {
              selectedCategories.push(c);
              span.classList.remove('text-bg-light','text-dark','border');
              span.classList.add('text-bg-primary');
            }
          });
          div.appendChild(span);
        });
        categoriesContainer.appendChild(div);
      });
    }

    if (btnAddAthlete) {
      btnAddAthlete.addEventListener('click', async () => {
        const id = parseInt(addAthleteSelect.value);
        if (!id) return;
        try {
          await setAttendance(currentTrainingId, id, 'maybe');
          addAthleteSelect.value = '';
          if (selectAll) selectAll.checked = false;
          await loadAttendance(currentTrainingId);
        } catch (err) {
          alert(err.message);
        }
      });
    }

    if (btnSaveChanges) {
      btnSaveChanges.addEventListener('click', async () => {
        if (!currentTrainingId) return;
        const toAdd = selectedCategories.filter(c => !originalCategories.includes(c));
        const toRemove = originalCategories.filter(c => !selectedCategories.includes(c));
        try {
          for (const c of [...toAdd, ...toRemove]) {
            await toggleTrainingCategory(currentTrainingId, c);
          }
          originalCategories = [...selectedCategories];
          modalCategories.textContent = selectedCategories.join(', ') || '-';
          if (currentEventEl) {
            currentEventEl.dataset.catlist = JSON.stringify(selectedCategories);
            currentEventEl.dataset.categories = selectedCategories.join(', ') || '-';
          }
        } catch (err) {
          alert(err.message);
        }
      });
    }

    window.showEventModal = function (data, el) {
      currentEventEl = el || null;
      modalTitle.textContent = data.title;
      modalDate.textContent = data.date;
      modalTime.textContent = data.time;
      modalCategories.textContent = data.categories || '-';
      modalCoaches.textContent = data.coaches || '-';
      modalRecurrence.textContent = data.recurrence || '-';
      if (isAtleta && data.type === 'allenamento') {
        attendanceActions.classList.remove('d-none');
        currentTrainingId = data.id;
        updateButtons(data.status);
        const disable = new Date() >= new Date(new Date(data.start).getTime() - 3*60*60*1000);
        btnPresent.disabled = disable;
        btnAbsent.disabled = disable;
      } else {
        attendanceActions.classList.add('d-none');
      }
      if (isStaff && data.type === 'allenamento') {
        currentTrainingId = data.id;
        loadAttendance(data.id);
        loadCategories().then(() => {
          const cats = data.catlist ? (Array.isArray(data.catlist) ? data.catlist : JSON.parse(data.catlist)) : [];
          renderCategories(cats);
        });
        if (btnEditTraining) {
          btnEditTraining.href = `/allenamenti/${data.id}/modifica`;
          btnEditTraining.classList.remove('d-none');
        }
        if (btnSaveChanges) btnSaveChanges.classList.remove('d-none');
      } else {
        if (btnEditTraining) btnEditTraining.classList.add('d-none');
        if (btnSaveChanges) btnSaveChanges.classList.add('d-none');
      }
      modal.show();
    };

    document.querySelectorAll('.dashboard-event').forEach(el => {
      el.addEventListener('click', () => {
        if (el.dataset.link) {
          window.location.href = el.dataset.link;
          return;
        }
        window.showEventModal(el.dataset, el);
      });
    });
  });
})();
