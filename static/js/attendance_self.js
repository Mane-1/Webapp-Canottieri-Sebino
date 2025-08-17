async function toggleAttendance(trainingId, newStatus) {
  const res = await fetch(`/trainings/${trainingId}/attendance/toggle`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ new_status: newStatus })
  });
  if (!res.ok) {
    const data = await res.json();
    throw new Error(data.detail || 'Errore');
  }
  return res.json();
}
