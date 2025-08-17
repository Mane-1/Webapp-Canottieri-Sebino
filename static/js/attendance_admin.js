async function setAttendance(trainingId, athleteId, status, reason) {
  const res = await fetch(`/trainings/${trainingId}/attendance/${athleteId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status, reason })
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || 'Errore');
  }
  return res.json();
}

async function bulkAttendance(trainingId, items, reason) {
  const res = await fetch(`/trainings/${trainingId}/attendance/bulk`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ items, reason })
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || 'Errore');
  }
  return res.json();
}

async function toggleTrainingCategory(trainingId, category) {
  const res = await fetch(`/trainings/${trainingId}/categories/${encodeURIComponent(category)}`, {
    method: 'POST'
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || 'Errore');
  }
  return res.json();
}

window.setAttendance = setAttendance;
window.bulkAttendance = bulkAttendance;
window.toggleTrainingCategory = toggleTrainingCategory;
