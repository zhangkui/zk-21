<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import type { HighRiskArea } from '$lib/types';

  export let markers: { lat: number; lng: number; popup?: string; riskLevel?: string }[] = [];
  export let polygons: [number, number][][] = [];
  export let polygonStyle: { color?: string; fillColor?: string; fillOpacity?: number; weight?: number } = {};
  export let center: [number, number] = [30.0, 120.0];
  export let zoom = 10;
  export let height = '400px';

  let mapContainer: HTMLDivElement;
  let map: any = null;
  let markerLayer: any = null;
  let polygonLayer: any = null;
  let L: any = null;
  let isBrowser = false;

  const riskColors: Record<string, string> = {
    low: '#22c55e',
    medium: '#f59e0b',
    high: '#ef4444',
    critical: '#7c2d12'
  };

  $: if (isBrowser && L && map && markerLayer) {
    updateMarkers();
  }

  $: if (isBrowser && L && map && polygonLayer) {
    updatePolygons();
  }

  function createRiskIcon(riskLevel?: string) {
    if (!L) return null;
    const color = riskColors[riskLevel || 'low'] || '#22c55e';
    return L.divIcon({
      className: 'custom-marker',
      html: `<div style="width: 20px; height: 20px; background: ${color}; border: 2px solid white; border-radius: 50%; box-shadow: 0 2px 4px rgba(0,0,0,0.3);"></div>`,
      iconSize: [20, 20],
      iconAnchor: [10, 10]
    });
  }

  function updateMarkers() {
    if (!map || !markerLayer || !L) return;

    markerLayer.clearLayers();

    markers.forEach((m) => {
      const icon = createRiskIcon(m.riskLevel);
      if (!icon) return;
      const marker = L.marker([m.lat, m.lng], { icon });
      if (m.popup) {
        marker.bindPopup(m.popup);
      }
      marker.addTo(markerLayer);
    });

    fitAllBounds();
  }

  function updatePolygons() {
    if (!map || !polygonLayer || !L) return;

    polygonLayer.clearLayers();

    const defaultStyle = {
      color: polygonStyle.color || '#2563eb',
      fillColor: polygonStyle.fillColor || '#3b82f6',
      fillOpacity: polygonStyle.fillOpacity ?? 0.2,
      weight: polygonStyle.weight || 2
    };

    polygons.forEach((poly) => {
      if (poly && poly.length >= 3) {
        L.polygon(poly, defaultStyle).addTo(polygonLayer);
      }
    });

    fitAllBounds();
  }

  function fitAllBounds() {
    if (!map || !L) return;

    const allBounds: [number, number][] = [];

    markers.forEach((m) => {
      allBounds.push([m.lat, m.lng]);
    });

    polygons.forEach((poly) => {
      if (poly) {
        poly.forEach((pt) => allBounds.push(pt));
      }
    });

    if (allBounds.length > 0) {
      const bounds = L.latLngBounds(allBounds);
      map.fitBounds(bounds, { padding: [50, 50] });
    }
  }

  onMount(async () => {
    isBrowser = true;
    const leaflet = await import('leaflet');
    L = leaflet.default;

    map = L.map(mapContainer).setView(center, zoom);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap contributors'
    }).addTo(map);

    markerLayer = L.layerGroup().addTo(map);
    polygonLayer = L.layerGroup().addTo(map);

    updateMarkers();
    updatePolygons();
  });

  onDestroy(() => {
    if (map) {
      map.remove();
      map = null;
    }
  });
</script>

<div bind:this={mapContainer} style="height: {height};" class="w-full rounded-lg overflow-hidden border border-gray-200"></div>
