document.addEventListener('DOMContentLoaded', () => {
  const yearSel = document.getElementById('year');
  if (!yearSel) return;
  const monthSel = document.getElementById('month');
  const catSel = document.getElementById('category');
  const typeSel = document.getElementById('type');
  const exportBtn = document.getElementById('export-csv');
  let monthlyChart, byTypeTrainingsChart, byTypeHoursChart;

  async function loadStats() {
    const params = new URLSearchParams({ year: yearSel.value });
    if (monthSel.value) params.append('month', monthSel.value);
    Array.from(catSel.selectedOptions).forEach(o => params.append('categoria', o.value));
    Array.from(typeSel.selectedOptions).forEach(o => params.append('tipo', o.value));
    const resp = await fetch(`/api/trainings/stats?${params.toString()}`);
    if (!resp.ok) return;
    const data = await resp.json();
    document.getElementById('kpi-trainings').innerText = data.kpi.trainings;
    document.getElementById('kpi-hours').innerText = data.kpi.total_hours.toFixed(1);
    document.getElementById('kpi-present').innerText = data.kpi.present;
    document.getElementById('kpi-absent').innerText = data.kpi.absent;
    const mLabels = data.monthly.map(m => m.month);
    const mPresent = data.monthly.map(m => m.present);
    const mAbsent = data.monthly.map(m => m.absent);
    if (monthlyChart) monthlyChart.destroy();
    monthlyChart = new Chart(document.getElementById('monthlyChart'), {
      type: 'bar',
      data: {
        labels: mLabels,
        datasets: [
          { label: 'Presenti', data: mPresent, backgroundColor: 'rgba(54,162,235,0.5)' },
          { label: 'Assenti', data: mAbsent, backgroundColor: 'rgba(255,99,132,0.5)' }
        ]
      },
      options: { scales: { x: { stacked: true }, y: { stacked: true } } }
    });
    const typeLabels = data.by_type.map(t => t.type);
    const trainingsData = data.by_type.map(t => t.trainings);
    const hoursData = data.by_type.map(t => t.hours);
    if (byTypeTrainingsChart) byTypeTrainingsChart.destroy();
    byTypeTrainingsChart = new Chart(document.getElementById('byTypeTrainingsChart'), {
      type: 'doughnut',
      data: { labels: typeLabels, datasets: [{ data: trainingsData }] }
    });
    if (byTypeHoursChart) byTypeHoursChart.destroy();
    byTypeHoursChart = new Chart(document.getElementById('byTypeHoursChart'), {
      type: 'doughnut',
      data: { labels: typeLabels, datasets: [{ data: hoursData }] }
    });
    exportBtn.href = `/api/trainings/stats.csv?${params.toString()}`;
  }

  [yearSel, monthSel, catSel, typeSel].forEach(el => {
    el.addEventListener('change', loadStats);
  });
  loadStats();
});
