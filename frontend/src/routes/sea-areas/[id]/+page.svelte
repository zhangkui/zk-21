<script lang="ts">
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  import MapView from '$lib/components/MapView.svelte';
  import DataTable from '$lib/components/DataTable.svelte';
  import { seaAreaApi } from '$lib/stores/api';
  import type { SeaArea, Cage, FarmerInfo } from '$lib/types';

  let seaArea: SeaArea | null = null;
  let loading = true;
  let errorMsg: string | null = null;

  const cageColumns = [
    { key: 'id', label: 'ID' },
    { key: 'code', label: '网箱编号' },
    {
      key: 'farmers',
      label: '养殖户',
      render: (_: any, row: Cage) => {
        if (row.farmers && row.farmers.length > 0) {
          return row.farmers
            .map(
              (f: FarmerInfo) =>
                `<span class="inline-block px-2 py-0.5 mx-0.5 text-xs font-medium bg-blue-100 text-blue-800 rounded-full cursor-pointer hover:bg-blue-200" data-farmer-id="${f.id}">${f.name}</span>`
            )
            .join('');
        }
        return '<span class="text-gray-400">-</span>';
      }
    },
    { key: 'location', label: '位置' },
    { key: 'capacity', label: '容量(尾)' },
    { key: 'species', label: '养殖品种' },
    {
      key: 'status',
      label: '状态',
      render: (val: string) => {
        const statusMap: Record<string, { label: string; class: string }> = {
          normal: { label: '正常', class: 'bg-green-100 text-green-800' },
          maintenance: { label: '维护中', class: 'bg-yellow-100 text-yellow-800' },
          empty: { label: '空置', class: 'bg-gray-100 text-gray-800' },
          abnormal: { label: '异常', class: 'bg-red-100 text-red-800' }
        };
        const s = statusMap[val] || { label: val, class: 'bg-gray-100 text-gray-800' };
        return `<span class="px-2 py-1 text-xs font-medium rounded-full ${s.class}">${s.label}</span>`;
      }
    }
  ];

  let polygons: [number, number][][] = [];
  let mapMarkers: { lat: number; lng: number; popup?: string; riskLevel?: string }[] = [];
  let center: [number, number] = [30.0, 120.0];

  $: if (seaArea) {
    polygons = seaArea.boundary && seaArea.boundary.length >= 3 ? [seaArea.boundary as [number, number][]] : [];
  }

  $: if (seaArea) {
    mapMarkers = [];
    if (seaArea.boundary && seaArea.boundary.length >= 3) {
      const lats = seaArea.boundary.map((p: [number, number]) => p[0]);
      const lngs = seaArea.boundary.map((p: [number, number]) => p[1]);
      const centerLat = (Math.min(...lats) + Math.max(...lats)) / 2;
      const centerLng = (Math.min(...lngs) + Math.max(...lngs)) / 2;
      center = [centerLat, centerLng];
      mapMarkers = [
        {
          lat: centerLat,
          lng: centerLng,
          popup: `<div class="p-2"><h4 class="font-semibold">${seaArea.name}</h4><p class="text-sm">面积: ${seaArea.area} 公顷</p><p class="text-sm">网箱: ${seaArea.cages?.length || 0} 个</p></div>`,
          riskLevel: 'low'
        }
      ];
    } else if (seaArea.lat_min && seaArea.lng_min) {
      center = [
        (seaArea.lat_min + (seaArea.lat_max || seaArea.lat_min)) / 2,
        (seaArea.lng_min + (seaArea.lng_max || seaArea.lng_min)) / 2
      ];
      mapMarkers = [
        {
          lat: center[0],
          lng: center[1],
          popup: `<div class="p-2"><h4 class="font-semibold">${seaArea.name}</h4><p class="text-sm">面积: ${seaArea.area} 公顷</p></div>`,
          riskLevel: 'low'
        }
      ];
    }
  }

  async function loadData() {
    const id = $page.params.id;
    if (!id) return;

    loading = true;
    try {
      const res = await seaAreaApi.getById(parseInt(id));
      seaArea = res.data;
    } catch (err) {
      console.error('Failed to load sea area:', err);
      errorMsg = '加载数据失败，请稍后重试';
    } finally {
      loading = false;
    }
  }

  function handleCageRowClick(row: Cage) {
    const target = event?.target as HTMLElement;
    if (target.dataset.farmerId) {
      window.location.href = `/farmers/${target.dataset.farmerId}`;
      return;
    }
    window.location.href = `/cages/${row.id}`;
  }

  function goBack() {
    window.location.href = '/sea-areas';
  }

  onMount(() => {
    loadData();
  });
</script>

{#if loading}
  <div class="flex items-center justify-center py-20">
    <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
    <span class="ml-3 text-gray-500">加载中...</span>
  </div>
{:else if seaArea}
  <div class="space-y-6">
    <div class="flex items-center gap-4">
      <button
        on:click={goBack}
        class="p-2 hover:bg-gray-100 rounded-lg transition-colors"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
        </svg>
      </button>
      <h2 class="text-2xl font-bold text-gray-900">{seaArea.name}</h2>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h3 class="text-lg font-semibold text-gray-900 mb-4">基本信息</h3>
        <div class="space-y-4">
          <div class="grid grid-cols-2 gap-4">
            <div>
              <p class="text-sm text-gray-500">位置</p>
              <p class="font-medium">{seaArea.location}</p>
            </div>
            <div>
              <p class="text-sm text-gray-500">面积</p>
              <p class="font-medium">{seaArea.area} 公顷</p>
            </div>
            <div>
              <p class="text-sm text-gray-500">平均水深</p>
              <p class="font-medium">{seaArea.depth || '-'} 米</p>
            </div>
            <div>
              <p class="text-sm text-gray-500">网箱数量</p>
              <p class="font-medium text-primary-600">
                <a class="hover:underline cursor-pointer" href="#cages-section">{seaArea.cages?.length || 0} 个</a>
              </p>
            </div>
            <div>
              <p class="text-sm text-gray-500">养殖户数量</p>
              <p class="font-medium">{seaArea.farmers?.length || 0} 户</p>
            </div>
            <div>
              <p class="text-sm text-gray-500">创建时间</p>
              <p class="font-medium">{new Date(seaArea.created_at).toLocaleDateString('zh-CN')}</p>
            </div>
          </div>
          {#if seaArea.farmers && seaArea.farmers.length > 0}
            <div class="pt-3 border-t border-gray-100">
              <p class="text-sm text-gray-500 mb-2">关联养殖户</p>
              <div class="flex flex-wrap gap-2">
                {#each seaArea.farmers as f}
                  <a
                    href={`/farmers/${f.id}`}
                    class="inline-block px-3 py-1 text-sm font-medium bg-blue-100 text-blue-800 rounded-full hover:bg-blue-200 transition-colors"
                  >
                    {f.name}
                    <span class="text-xs text-blue-600 ml-1">({f.phone})</span>
                  </a>
                {/each}
              </div>
            </div>
          {/if}
          {#if seaArea.description}
            <div class="pt-3 border-t border-gray-100">
              <p class="text-sm text-gray-500">描述</p>
              <p class="font-medium">{seaArea.description}</p>
            </div>
          {/if}
        </div>
      </div>

      <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h3 class="text-lg font-semibold text-gray-900 mb-4">
          位置地图
          {#if seaArea.boundary && seaArea.boundary.length >= 3}
            <span class="ml-2 text-xs font-normal text-green-600 bg-green-50 px-2 py-0.5 rounded">已绘制区域</span>
          {/if}
        </h3>
        <MapView
          markers={mapMarkers}
          polygons={polygons}
          polygonStyle={{ color: '#2563eb', fillColor: '#3b82f6', fillOpacity: 0.25, weight: 2 }}
          {center}
          height="300px"
        />
      </div>
    </div>

    <div id="cages-section" class="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-lg font-semibold text-gray-900">
          所属网箱
          <span class="ml-2 text-sm font-normal text-gray-500">共 {seaArea.cages?.length || 0} 个</span>
        </h3>
      </div>
      {#if seaArea.cages && seaArea.cages.length > 0}
        <DataTable
          columns={cageColumns}
          data={seaArea.cages}
          onRowClick={handleCageRowClick}
        />
        <p class="mt-3 text-xs text-gray-500">💡 点击养殖户标签可跳转到养殖户详情，点击其他区域跳转到网箱详情</p>
      {:else}
        <div class="text-center py-12 text-gray-500">
          <svg class="w-12 h-12 mx-auto mb-3 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
          </svg>
          暂无网箱数据
        </div>
      {/if}
    </div>
  </div>
{/if}
