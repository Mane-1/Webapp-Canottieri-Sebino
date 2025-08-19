(function () {
  const el = document.getElementById('calendar');
  if (!el) return;

  const isXs = () => window.matchMedia('(max-width: 575.98px)').matches;
  const isSmMd = () => window.matchMedia('(min-width: 576px) and (max-width: 991.98px)').matches;

  const toolbarMobile = { start: 'title', center: '', end: 'today prev,next' };
  const toolbarDesktop = { start: 'prev,next today', center: 'title', end: 'dayGridMonth,timeGridWeek,listWeek' };

  const modal = window.showEventModal ? window.showEventModal : null;

  const calendar = new FullCalendar.Calendar(el, {
    themeSystem: 'bootstrap5',
    initialView: isXs() ? 'listWeek' : (isSmMd() ? 'timeGridWeek' : 'dayGridMonth'),
    headerToolbar: isXs() ? toolbarMobile : toolbarDesktop,
    height: 'auto',
    stickyHeaderDates: true,
    navLinks: true,
    nowIndicator: true,
    firstDay: 1, // lunedì
    slotMinTime: '06:00:00',
    slotMaxTime: '22:00:00',
    expandRows: true,
    dayMaxEventRows: true,
    displayEventEnd: true,
    eventTimeFormat: { hour: '2-digit', minute: '2-digit', hour12: false },
    eventSources: [{
      url: '/api/allenamenti',
      failure: () => console.error('Errore nel caricare gli eventi')
    }],
    eventClick(info) {
      if (!modal) return;
      const props = info.event.extendedProps || {};
      modal({
        id: info.event.id,
        title: info.event.title,
        date: info.event.start.toLocaleDateString('it-IT', {
          weekday: 'long', day: '2-digit', month: 'long', year: 'numeric'
        }),
        time: props.orario || '',
        categories: props.categories || 'Nessuna',
        catlist: props.catlist || [],
        coaches: props.coaches || 'Nessuno',
        recurrence: props.is_recurrent || 'No',
        start: info.event.start.toISOString(),
        type: 'allenamento'
      });
    }
  });

  calendar.render();

  // Adatta la vista quando cambia la larghezza
  const resizeHandler = () => {
    const v = isXs() ? 'listWeek' : (isSmMd() ? 'timeGridWeek' : 'dayGridMonth');
    calendar.changeView(v);
    calendar.setOption('headerToolbar', isXs() ? toolbarMobile : toolbarDesktop);
  };
  window.addEventListener('resize', resizeHandler);
})();
