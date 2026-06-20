<script lang="ts">
  import { onMount, onDestroy, createEventDispatcher } from 'svelte';

  export let initialBoundary: [number, number][] | null = null;
  export let center: [number, number] = [30.0, 120.0];
  export let zoom = 10;
  export let height = '400px';

  const dispatch = createEventDispatcher<{
    change: { points: [number, number][]; lat_min: number; lat_max: number; lng_min: number; lng_max: number };
  }>();

  let mapContainer: HTMLDivElement;
  let map: any = null;
  let L: any = null;
  let isBrowser = false;

  let tempPoints: [number, number][] = [];
  let tempPolyline: any = null;
  let tempMarkers: any[] = [];
  let finalPolygon: any = null;

  let searchKeyword = '';
  let searchResults: any[] = [];
  let searchLoading = false;
  let showSearchPanel = true;

  $: polygonPoints = tempPoints.length >= 3 ? [...tempPoints, tempPoints[0]] : tempPoints;

  function updateTempLayer() {
    if (!L || !map) return;

    if (tempPolyline) {
      map.removeLayer(tempPolyline);
      tempPolyline = null;
    }
    tempMarkers.forEach((m) => map.removeLayer(m));
    tempMarkers = [];

    if (tempPoints.length === 1) {
      const m = L.marker(tempPoints[0], {
        draggable: true
      }).addTo(map);
      m.on('dragend', (e: any) => {
        const pos = e.target.getLatLng();
        tempPoints[0] = [pos.lat, pos.lng];
        emitChange();
      });
      tempMarkers.push(m);
    } else if (tempPoints.length >= 2) {
      const linePoints = [...tempPoints];
      if (tempPoints.length >= 3) {
        linePoints.push(tempPoints[0]);
      }
      tempPolyline = L.polyline(linePoints, {
        color: '#2563eb',
        weight: 2,
        dashArray: tempPoints.length >= 3 ? null : '5,10'
      }).addTo(map);

      tempPoints.forEach((pt, idx) => {
        const m = L.circleMarker(pt, {
          radius: 6,
          fillColor: idx === 0 ? '#16a34a' : '#2563eb',
          color: '#fff',
          weight: 2,
          fillOpacity: 1,
          draggable: true
        }).addTo(map);
        m.on('dragend', (e: any) => {
          const pos = e.target.getLatLng();
          tempPoints[idx] = [pos.lat, pos.lng];
          updateTempLayer();
          emitChange();
        });
        m.on('click', (e: any) => {
          L.DomEvent.stopPropagation(e);
          if (tempPoints.length > 2 && idx === 0) {
            closePolygon();
          } else if (idx > 0 && !e.originalEvent.shiftKey) {
            removePoint(idx);
          }
        });
        m.bindTooltip(`点${idx + 1} (拖拽移动, 非起点点击删除)`);
        tempMarkers.push(m);
      });
    }
  }

  function closePolygon() {
    if (tempPoints.length < 3) return;
    if (finalPolygon) {
      map.removeLayer(finalPolygon);
    }
    finalPolygon = L.polygon(tempPoints, {
      color: '#2563eb',
      fillColor: '#3b82f6',
      fillOpacity: 0.2,
      weight: 2
    }).addTo(map);
    emitChange();
  }

  function removePoint(idx: number) {
    if (tempPoints.length <= 2) return;
    tempPoints.splice(idx, 1);
    if (finalPolygon) {
      map.removeLayer(finalPolygon);
      finalPolygon = null;
    }
    updateTempLayer();
    emitChange();
  }

  function clearAll() {
    tempPoints = [];
    if (tempPolyline) {
      map.removeLayer(tempPolyline);
      tempPolyline = null;
    }
    tempMarkers.forEach((m) => map.removeLayer(m));
    tempMarkers = [];
    if (finalPolygon) {
      map.removeLayer(finalPolygon);
      finalPolygon = null;
    }
    emitChange();
  }

  function emitChange() {
    if (tempPoints.length >= 3) {
      const lats = tempPoints.map((p) => p[0]);
      const lngs = tempPoints.map((p) => p[1]);
      dispatch('change', {
        points: [...tempPoints],
        lat_min: Math.min(...lats),
        lat_max: Math.max(...lats),
        lng_min: Math.min(...lngs),
        lng_max: Math.max(...lngs)
      });
    } else {
      dispatch('change', {
        points: [...tempPoints],
        lat_min: undefined as any,
        lat_max: undefined as any,
        lng_min: undefined as any,
        lng_max: undefined as any
      });
    }
  }

  async function handleSearch() {
    if (!searchKeyword.trim()) return;
    searchLoading = true;
    searchResults = [];
    try {
      const res = await fetch(
        `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(searchKeyword)}&limit=5&addressdetails=1`,
        {
          headers: {
            'Accept-Language': 'zh-CN,zh;q=0.9'
          }
        }
      );
      searchResults = await res.json();
    } catch (err) {
      console.error('Search failed:', err);
      alert('搜索失败，请稍后重试');
    } finally {
      searchLoading = false;
    }
  }

  function locateResult(r: any) {
    if (!L || !map) return;
    const lat = parseFloat(r.lat);
    const lng = parseFloat(r.lon);
    map.setView([lat, lng], 15);
    if (!tempPoints.some((p) => Math.abs(p[0] - lat) < 0.00001 && Math.abs(p[1] - lng) < 0.00001)) {
      tempPoints.push([lat, lng]);
      if (finalPolygon) {
        map.removeLayer(finalPolygon);
        finalPolygon = null;
      }
      updateTempLayer();
      emitChange();
    }
    searchResults = [];
    searchKeyword = '';
  }

  function addPointAtCenter() {
    if (!L || !map) return;
    const c = map.getCenter();
    tempPoints.push([c.lat, c.lng]);
    if (finalPolygon) {
      map.removeLayer(finalPolygon);
      finalPolygon = null;
    }
    updateTempLayer();
    emitChange();
  }

  onMount(async () => {
    isBrowser = true;
    const leaflet = await import('leaflet');
    L = leaflet.default;

    map = L.map(mapContainer).setView(center, zoom);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap contributors'
    }).addTo(map);

    map.on('click', (e: any) => {
      tempPoints.push([e.latlng.lat, e.latlng.lng]);
      if (finalPolygon) {
        map.removeLayer(finalPolygon);
        finalPolygon = null;
      }
      updateTempLayer();
      emitChange();
    });

    if (initialBoundary && initialBoundary.length >= 3) {
      tempPoints = [...initialBoundary];
      updateTempLayer();
      finalPolygon = L.polygon(tempPoints, {
        color: '#2563eb',
        fillColor: '#3b82f6',
        fillOpacity: 0.2,
        weight: 2
      }).addTo(map);
      const bounds = L.latLngBounds(tempPoints);
      map.fitBounds(bounds, { padding: [50, 50] });
      emitChange();
    }
  });

  onDestroy(() => {
    if (map) {
      map.remove();
      map = null;
    }
  });
</script>

<div class="relative border border-gray-300 rounded-lg overflow-hidden">
  <div class="absolute top-3 left-3 z-[1000] bg-white rounded-lg shadow-lg p-2 w-72 max-h-[calc(100%-24px)] overflow-hidden flex flex-col">
    <div class="flex items-center justify-between mb-2">
      <span class="text-sm font-semibold text-gray-700">搜索定位</span>
      <button
        on:click={() => (showSearchPanel = !showSearchPanel)}
        class="text-xs text-gray-500 hover:text-gray-700"
        type="button"
      >
        {showSearchPanel ? '收起' : '展开'}
      </button>
    </div>
    {#if showSearchPanel}
      <div class="space-y-2">
        <div class="flex gap-1">
          <input
            type="text"
            bind:value={searchKeyword}
            on:keydown={(e) => e.key === 'Enter' && handleSearch()}
            placeholder="搜索地名、地址..."
            class="flex-1 px-2 py-1.5 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
          />
          <button
            type="button"
            on:click={handleSearch}
            disabled={searchLoading}
            class="px-3 py-1.5 text-sm bg-primary-600 text-white rounded hover:bg-primary-700 disabled:opacity-50"
          >
            {searchLoading ? '...' : '搜索'}
          </button>
        </div>
        {#if searchResults.length > 0}
          <div class="border border-gray-200 rounded max-h-40 overflow-y-auto text-sm">
            {#each searchResults as r}
              <button
                type="button"
                on:click={() => locateResult(r)}
                class="w-full text-left px-2 py-2 hover:bg-blue-50 border-b border-gray-100 last:border-0"
              >
                <p class="font-medium text-gray-800 line-clamp-1">{r.display_name?.slice(0, 40)}...</p>
                <p class="text-xs text-gray-500">{r.lat.slice(0, 7)}, {r.lon.slice(0, 7)}</p>
              </button>
            {/each}
          </div>
        {/if}
        <div class="pt-2 border-t border-gray-100 space-y-1">
          <button
            type="button"
            on:click={addPointAtCenter}
            class="w-full px-2 py-1.5 text-sm bg-green-50 text-green-700 rounded hover:bg-green-100 border border-green-200"
          >
            + 添加当前位置为顶点
          </button>
          <button
            type="button"
            on:click={closePolygon}
            disabled={tempPoints.length < 3}
            class="w-full px-2 py-1.5 text-sm bg-blue-50 text-blue-700 rounded hover:bg-blue-100 border border-blue-200 disabled:opacity-40"
          >
            ✓ 闭合多边形 ({tempPoints.length}/最少3个点)
          </button>
          <button
            type="button"
            on:click={clearAll}
            class="w-full px-2 py-1.5 text-sm bg-red-50 text-red-700 rounded hover:bg-red-100 border border-red-200"
          >
            ✕ 清空所有点
          </button>
        </div>
        {#if tempPoints.length > 0}
          <div class="pt-2 border-t border-gray-100">
            <p class="text-xs font-medium text-gray-600 mb-1">已添加顶点:</p>
            <div class="max-h-24 overflow-y-auto text-xs text-gray-500 space-y-0.5">
              {#each tempPoints as pt, idx}
                <div class="flex items-center justify-between px-1 py-0.5 hover:bg-gray-50 rounded">
                  <span>#{idx + 1}: {pt[0].toFixed(5)}, {pt[1].toFixed(5)}</span>
                  {#if tempPoints.length > 2}
                    <button
                      type="button"
                      on:click={() => removePoint(idx)}
                      class="text-red-500 hover:text-red-700 ml-2"
                    >删</button>
                  {/if}
                </div>
              {/each}
            </div>
          </div>
        {/if}
      </div>
    {/if}
  </div>

  <div bind:this={mapContainer} style="height: {height};" class="w-full"></div>
</div>

<p class="mt-2 text-xs text-gray-500">
  💡 操作提示：点击地图任意位置添加顶点 → 添加3个以上点后点击"闭合多边形" → 拖拽圆点调整位置 → 点击非起点圆点可删除该点
</p>
