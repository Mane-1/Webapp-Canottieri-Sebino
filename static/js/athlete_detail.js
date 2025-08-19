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
  });
});
