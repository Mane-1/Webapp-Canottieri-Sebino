async function setAttendance(trainingId, athleteId, status, reason) {
  const res = await fetch(`/trainings/${trainingId}/attendance/${athleteId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status, reason })
  });
  return res.json();
}

async function bulkAttendance(trainingId, items, reason) {
  const res = await fetch(`/trainings/${trainingId}/attendance/bulk`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ items, reason })
  });
  return res.json();
}
