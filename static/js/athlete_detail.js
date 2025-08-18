document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('measurement-form');
  if (!form) return;
  const athleteId = form.dataset.athleteId;

    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const fd = new FormData(form);
      const payload = {};
      for (const [k, v] of fd.entries()) {
        if (v) payload[k] = v;
      }
      const resp = await fetch(`/risorse/athletes/${athleteId}/measurements`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (resp.ok) {
        location.reload();
      }
    });

  // attendance stats
  let monthlyChart; let byTypeChart;
  async function loadAttendanceStats() {
    const year = document.getElementById('stats-year').value;
    const month = document.getElementById('stats-month').value;
    const types = Array.from(document.getElementById('stats-type').selectedOptions).map(o => o.value);
    const params = new URLSearchParams({ year });
    if (month) params.append('month', month);
    types.forEach(t => params.append('tipo', t));
    const resp = await fetch(`/api/athletes/${athleteId}/attendance_stats?${params.toString()}`);
    if (!resp.ok) return;
    const data = await resp.json();
    document.getElementById('kpi-sessions').innerText = data.kpi.sessions;
    document.getElementById('kpi-present').innerText = data.kpi.present;
    document.getElementById('kpi-absent').innerText = data.kpi.absent;
    document.getElementById('kpi-rate').innerText = (data.kpi.presence_rate * 100).toFixed(1) + '%';
    const labels = data.monthly.map(m => m.month);
    const presents = data.monthly.map(m => m.present);
    const absents = data.monthly.map(m => m.absent);
    if (monthlyChart) monthlyChart.destroy();
    monthlyChart = new Chart(document.getElementById('monthlyChart'), {
      type: 'bar',
      data: {
        labels,
        datasets: [
          { label: 'Presenti', data: presents, backgroundColor: 'rgba(54,162,235,0.5)' },
          { label: 'Assenti', data: absents, backgroundColor: 'rgba(255,99,132,0.5)' }
        ]
      },
      options: { scales: { x: { stacked: true }, y: { stacked: true } } }
    });
    const typeLabels = data.by_type.map(t => t.type);
    const typeData = data.by_type.map(t => t.present + t.absent);
    if (byTypeChart) byTypeChart.destroy();
    byTypeChart = new Chart(document.getElementById('byTypeChart'), {
      type: 'doughnut',
      data: { labels: typeLabels, datasets: [{ data: typeData }] },
      options: {}
    });
    const tbody = document.querySelector('#sessions-table tbody');
    tbody.innerHTML = '';
    data.sessions.forEach(s => {
      const tr = document.createElement('tr');
      tr.innerHTML = `<td>${s.date}</td><td>${s.tipo}</td><td>${s.categories.join(',')}</td><td>${s.status}</td>`;
      tbody.appendChild(tr);
    });
    const exportBtn = document.getElementById('attendance-export');
    exportBtn.href = `/api/athletes/${athleteId}/attendance.csv?${params.toString()}`;
    const csvLink = document.getElementById('attendance-csv');
    csvLink.href = exportBtn.href;
  }
  ['stats-year', 'stats-month', 'stats-type'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.addEventListener('change', loadAttendanceStats);
  });
  if (document.getElementById('stats-year')) loadAttendanceStats();
});
