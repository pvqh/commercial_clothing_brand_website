// Field Core Web Vitals (research R12): sends LCP, INP and CLS with the route name and a
// mobile/desktop class only. No cookies, identifiers or addresses are sent.
(function reportWebVitals() {
  if (!window.webVitals || !navigator.sendBeacon) return;
  const route = document.body.dataset.route;
  if (!route) return;
  const device = window.matchMedia("(min-width: 1024px)").matches ? "desktop" : "mobile";

  function send(metric) {
    const body = JSON.stringify({ metric: metric.name, value: metric.value, route, device });
    navigator.sendBeacon("/rum/", new Blob([body], { type: "application/json" }));
  }

  window.webVitals.onLCP(send);
  window.webVitals.onINP(send);
  window.webVitals.onCLS(send);
})();
