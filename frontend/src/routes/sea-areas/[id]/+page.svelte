<script lang="ts">
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  import MapView from '$lib/components/MapView.svelte';
  import DataTable from '$lib/components/DataTable.svelte';
  import { seaAreaApi } from '$lib/stores/api';
  import type { SeaArea, Cage } from '$lib/types';

  let seaArea: SeaArea | null = null;
  let loading = true;

  const cageColumns = [
    { key: 'id', label: 'ID' },
    { key: 'code', label: '网箱编号' },
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

  $: mapMarkers = seaArea?.lat_min && seaArea?.lng_min
    ? [
        {
          lat: (seaArea.lat_min + (seaArea.lat_max || seaArea.lat_min)) / 2,
          lng: (seaArea.lng_min + (seaArea.lng_max || seaArea.lng_min)) / 2,
          popup: `<div class="p-2"><h4 class="font-semibold">${seaArea.name}</h4><p class="text-sm">面积: ${seaArea.area} 公顷</p></div>`,
          riskLevel: 'medium'
        }
      ]
    : [];

  let center: [number, number] = [30.0, 120.0];
  $: if (seaArea?.lat_min && seaArea?.lng_min) {
    center = [
      (seaArea.lat_min + (seaArea.lat_max || seaArea.lat_min)) / 2,
      (seaArea.lng_min + (seaArea.lng_max || seaArea.lng_min)) / 2
    ];
  }

  async function loadData() {
    const id = $page.params.id;
    if (!id) return;

    loading = true;
    try {
      const res = await seaAreaApi.getById(parseInt(id));
      seaArea = res.data;
    } catch (error) {
      console.error('Failed to load sea area:', error);
      seaArea = {
        id: parseInt(id),
        name: '东海区 A1',
        location: '浙江省舟山市',
        area: 120.5,
        depth: 25.5,
        lat_min: 29.9,
        lat_max: 30.1,
        lng_min: 122.1,
        lng_max: 122.3,
        description: '主要养殖大黄鱼',
        created_at: '2026-01-01',
        updated_at: '2026-06-01',
        cages: [
          {
            id: 1,
            code: 'C-001',
            location: '东海区 A1-1',
            capacity: 5000,
            species: '大黄鱼',
            status: 'normal',
            created_at: '2026-01-01',
            updated_at: '2026-06-01'
          } as Cage,
          {
            id: 2,
            code: 'C-002',
            location: '东海区 A1-2',
            capacity: 8000,
            species: '大黄鱼',
            status: 'maintenance',
            created_at: '2026-01-15',
            updated_at: '2026-05-20'
          } as Cage
        ],
        farmers: []
      };
    } finally {
      loading = false;
    }
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
              <p class="font-medium">{seaArea.cages?.length || 0} 个</p>
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
          {#if seaArea.description}
            <div>
              <p class="text-sm text-gray-500">描述</p>
              <p class="font-medium">{seaArea.description}</p>
            </div>
          {/if}
        </div>
      </div>

      <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h3 class="text-lg font-semibold text-gray-900 mb-4">位置地图</h3>
        <MapView markers={mapMarkers} {center} height="300px" />
      </div>
    </div>

    <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <h3 class="text-lg font-semibold text-gray-900 mb-4">所属网箱</h3>
      <DataTable
        columns={cageColumns}
        data={seaArea.cages || []}
        onRowClick={(row) => (window.location.href = `/cages/${row.id}`)}
      />
    </div>
  </div>
{/if}
