// Shared Google Maps JS loader — idempotent across MapView and Sahayak (one script, one promise).
export function loadGoogleMaps(key: string): Promise<any> {
  const w = window as any;
  if (w.google?.maps) return Promise.resolve(w.google);
  if (w.__setuGmaps) return w.__setuGmaps;
  w.__setuGmaps = new Promise((resolve, reject) => {
    const s = document.createElement("script");
    s.src = `https://maps.googleapis.com/maps/api/js?key=${encodeURIComponent(key)}&v=weekly`;
    s.async = true;
    s.defer = true;
    s.onload = () => resolve(w.google);
    s.onerror = () => reject(new Error("google_maps_load_failed"));
    document.head.appendChild(s);
  });
  return w.__setuGmaps;
}
