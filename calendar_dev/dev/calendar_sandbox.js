window.CALENDAR_SKIP_AUTO_BOOTSTRAP = true;

const params = new URLSearchParams(window.location.search);
const debugEnabled = params.get('debug') === '1';
const defaultDate = window.__CALENDAR_DEFAULT_DATE || '2024-05-01';
const sandboxTrips = Array.isArray(window.__CALENDAR_SANDBOX_TRIPS)
  ? window.__CALENDAR_SANDBOX_TRIPS
  : [];

const ensureLiveReload = () => {
  if (params.get('livereload') !== '1') return;
  const host = params.get('livereload-host') || window.location.hostname;
  const port = params.get('livereload-port') || '35729';
  const script = document.createElement('script');
  script.src = `http://${host}:${port}/livereload.js?snipver=1`;
  script.onerror = () => script.remove();
  document.head.appendChild(script);
};

const bootstrap = async () => {
  const module = await import('./calendar_dev.js');
  module.bootstrapCalendar({
    defaultDate,
    sandboxTrips,
    debug: debugEnabled,
  });
  ensureLiveReload();
};

bootstrap();
