function initResponsiveCalendar(el, options) {
  const {
    eventSource,
    initialDesktop = 'dayGridMonth',
    initialMobile = 'listWeek',
    rightDesktop = 'dayGridMonth,timeGridWeek,listWeek',
    rightMobile = 'listDay,listWeek',
    locale = 'it',
    ...rest
  } = options || {};

  const isMobile = window.matchMedia('(max-width: 768px)');

  const getTitleFormat = () => isMobile.matches
    ? { year: 'numeric', month: 'short', day: '2-digit' }
    : { year: 'numeric', month: 'long' };

  const getDayHeaderFormat = () => isMobile.matches
    ? { weekday: 'short', day: '2-digit' }
    : { weekday: 'long' };

  const calendar = new FullCalendar.Calendar(el, {
    handleWindowResize: true,
    height: 'auto',
    locale,
    initialView: isMobile.matches ? initialMobile : initialDesktop,
    headerToolbar: {
      left: 'prev,next today',
      center: 'title',
      right: isMobile.matches ? rightMobile : rightDesktop
    },
    titleFormat: getTitleFormat(),
    dayHeaderFormat: getDayHeaderFormat(),
    eventTimeFormat: { hour: '2-digit', minute: '2-digit', hour12: false },
    slotLabelFormat: { hour: '2-digit', minute: '2-digit', hour12: false },
    slotDuration: '00:30:00',
    dayMaxEventRows: 3,
    events: eventSource,
    ...rest
  });

  function updateOptions() {
    calendar.setOption('headerToolbar', {
      left: 'prev,next today',
      center: 'title',
      right: isMobile.matches ? rightMobile : rightDesktop
    });
    calendar.setOption('titleFormat', getTitleFormat());
    calendar.setOption('dayHeaderFormat', getDayHeaderFormat());
  }

  isMobile.addEventListener('change', () => {
    calendar.changeView(isMobile.matches ? initialMobile : initialDesktop);
    updateOptions();
  });

  calendar.render();
  return calendar;
}

window.initResponsiveCalendar = initResponsiveCalendar;
