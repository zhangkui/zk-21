<script lang="ts">
  import { onMount } from 'svelte';
  import Chart from '$lib/components/Chart.svelte';
  import MapView from '$lib/components/MapView.svelte';
  import DataTable from '$lib/components/DataTable.svelte';
  import { analyticsApi } from '$lib/stores/api';
  import type { HighRiskArea } from '$lib/types';

  let loading = true;
  let errorMsg: string | null = null;
  let rawTrends: any[] = [];
  let rawMortalityStats: any = null;
  let rawMortalityCauses: any[] = [];
  let heatmapData: HighRiskArea[] = [];
  let farmerResponsibility: any[] = [];
  let diseaseTrendData: any;
  let mortalityData: any;

  const diseaseTypeLabels: Record<string, string> = {
    bacterial: '细菌性疾病',
    viral: '病毒性疾病',
    parasitic: '寄生虫病',
    fungal: '真菌性疾病',
    nutritional: '营养性疾病',
    environmental: '环境性疾病',
    other: '其他'
  };

  const diseaseTypeColors: Record<string, string> = {
    bacterial: 'rgba(239, 68, 68, 0.8)',
    viral: 'rgba(245, 158, 11, 0.8)',
    parasitic: 'rgba(59, 130, 246, 0.8)',
    fungal: 'rgba(34, 197, 94, 0.8)',
    nutritional: 'rgba(139, 92, 246, 0.8)',
    environmental: 'rgba(14, 165, 233, 0.8)',
    other: 'rgba(107, 114, 128, 0.8)'
  };

  const causeColors = [
    'rgba(239, 68, 68, 0.8)',
    'rgba(245, 158, 11, 0.8)',
    'rgba(59, 130, 246, 0.8)',
    'rgba(34, 197, 94, 0.8)',
    'rgba(139, 92, 246, 0.8)',
    'rgba(107, 114, 128, 0.8)',
    'rgba(236, 72, 153, 0.8)'
  ];

  $: diseaseTrendData = {
    labels: rawTrends.map((t) => t.month),
    datasets: Object.keys(diseaseTypeLabels).map((dt) => ({
      label: diseaseTypeLabels[dt],
      data: rawTrends.map((t) => (t && typeof t[dt] === 'number' ? t[dt] : 0)),
      backgroundColor: diseaseTypeColors[dt]
    }))
  };

  $: mortalityData = {
    labels: rawMortalityCauses.map((c: any) => c.cause_display),
    datasets: [
      {
        data: rawMortalityCauses.map((c: any) => c.total_mortality ?? 0),
        backgroundColor: causeColors
      }
    ]
  };

  const farmerColumns = [
    { key: 'farmer_name', label: '养殖户' },
    { key: 'sea_area', label: '所属海区' },
    { key: 'cage_count', label: '关联网箱数' },
    { key: 'disease_reports', label: '病害次数' },
    { key: 'mortality_reports', label: '死亡次数' },
    { key: 'total_mortality', label: '死亡总数(尾)' },
    {
      key: 'risk_level',
      label: '风险等级',
      render: (val: string) => {
        const map: Record<string, { label: string; class: string }> = {
          low: { label: '低', class: 'bg-green-100 text-green-800' },
          medium: { label: '中', class: 'bg-yellow-100 text-yellow-800' },
          high: { label: '高', class: 'bg-orange-100 text-orange-800' },
          critical: { label: '危急', class: 'bg-red-100 text-red-800' }
        };
        const s = map[val] || { label: val, class: 'bg-gray-100 text-gray-800' };
        return `<span class="px-2 py-1 text-xs font-medium rounded-full ${s.class}">${s.label}</span>`;
      }
    }
  ];

  function riskLabel(level: string) {
    return level === 'critical' ? '危急' : level === 'high' ? '高' : level === 'medium' ? '中' : '低';
  }

  $: heatmapMarkers = heatmapData.map((area) => ({
    lat: area.lat,
    lng: area.lng,
    riskLevel: area.risk_level,
    popup: `<div class="p-2 min-w-[180px]">
      <h4 class="font-semibold text-gray-900">${area.name}</h4>
      ${area.location ? `<p class="text-sm text-gray-600 mt-1">位置: ${area.location}</p>` : ''}
      <p class="text-sm text-gray-600">风险等级: ${riskLabel(area.risk_level)}</p>
      <p class="text-sm text-gray-600">风险分数: ${area.risk_score}</p>
      <p class="text-sm text-gray-600">异常网箱: ${area.abnormal_cages ?? area.abnormal_cage_count ?? '-'}/${area.total_cages ?? '-'}</p>
      <p class="text-sm text-gray-600">近7天病害上报: ${area.disease_reports ?? 0} 起</p>
      <p class="text-sm text-gray-600">近7天死亡上报: ${area.mortality_reports ?? 0} 起</p>
    </div>`
  }));

  async function loadData() {
    loading = true;
    errorMsg = null;
    const results = await Promise.allSettled([
      analyticsApi.getDiseaseTrends(),
      analyticsApi.getMortalityStats(),
      analyticsApi.getHeatmapData(),
      analyticsApi.getFarmerResponsibility()
    ]);

    if (results[0].status === 'fulfilled') {
      rawTrends = results[0].value.data || [];
    } else {
      console.error('病害趋势加载失败', results[0].reason);
    }

    if (results[1].status === 'fulfilled') {
      rawMortalityStats = results[1].value.data;
      rawMortalityCauses = rawMortalityStats?.cause_statistics || [];
    } else {
      console.error('死亡率统计加载失败', results[1].reason);
    }

    if (results[2].status === 'fulfilled') {
      heatmapData = results[2].value.data || [];
    } else {
      console.error('热力图加载失败', results[2].reason);
    }

    if (results[3].status === 'fulfilled') {
      farmerResponsibility = results[3].value.data || [];
    } else {
      console.error('养殖户责任加载失败', results[3].reason);
    }

    const failedCount = results.filter((r) => r.status === 'rejected').length;
    if (failedCount === results.length) {
      errorMsg = '加载数据失败，请稍后重试';
    }
    loading = false;
  }

  onMount(() => {
    loadData();
  });
</script>

<div class="space-y-6 relative">
  {#if loading}
    <div class="absolute inset-0 z-50 flex items-center justify-center bg-white/70 rounded-xl">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      <span class="ml-3 text-gray-500">加载中...</span>
    </div>
  {/if}

  <h2 class="text-2xl font-bold text-gray-900">统计分析</h2>

  {#if errorMsg}
    <div class="bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-3 text-sm">
      {errorMsg}
    </div>
  {/if}

  <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
    <h3 class="text-lg font-semibold text-gray-900 mb-4">高风险养殖区热力图</h3>
    <MapView markers={heatmapMarkers} center={[30.0, 118.0]} zoom={6} height="400px" />
    <div class="flex items-center gap-6 mt-4 justify-center">
      <div class="flex items-center gap-2">
        <div class="w-4 h-4 rounded-full bg-green-500"></div>
        <span class="text-sm text-gray-600">低风险</span>
      </div>
      <div class="flex items-center gap-2">
        <div class="w-4 h-4 rounded-full bg-yellow-500"></div>
        <span class="text-sm text-gray-600">中风险</span>
      </div>
      <div class="flex items-center gap-2">
        <div class="w-4 h-4 rounded-full bg-red-500"></div>
        <span class="text-sm text-gray-600">高风险</span>
      </div>
      <div class="flex items-center gap-2">
        <div class="w-4 h-4 rounded-full bg-amber-900"></div>
        <span class="text-sm text-gray-600">危急</span>
      </div>
    </div>
  </div>

  <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
    <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <h3 class="text-lg font-semibold text-gray-900 mb-4">病害趋势分析</h3>
      <Chart type="bar" data={diseaseTrendData} height="350px" />
    </div>

    <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <h3 class="text-lg font-semibold text-gray-900 mb-4">死亡率统计（按原因）</h3>
      <div class="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
        <div class="bg-gray-50 rounded-lg p-3 text-center">
          <p class="text-xs text-gray-500">总上报数</p>
          <p class="text-xl font-bold text-gray-900">{rawMortalityStats?.total_reports ?? 0}</p>
        </div>
        <div class="bg-gray-50 rounded-lg p-3 text-center">
          <p class="text-xs text-gray-500">总死亡数(尾)</p>
          <p class="text-xl font-bold text-red-600">{rawMortalityStats?.total_mortality ?? 0}</p>
        </div>
        <div class="bg-gray-50 rounded-lg p-3 text-center">
          <p class="text-xs text-gray-500">近30天上报</p>
          <p class="text-xl font-bold text-gray-900">{rawMortalityStats?.recent_30_days_reports ?? 0}</p>
        </div>
        <div class="bg-gray-50 rounded-lg p-3 text-center">
          <p class="text-xs text-gray-500">近30天死亡</p>
          <p class="text-xl font-bold text-red-600">{rawMortalityStats?.recent_30_days_mortality ?? 0}</p>
        </div>
      </div>
      <Chart type="doughnut" data={mortalityData} height="300px" />
    </div>
  </div>

  <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
    <h3 class="text-lg font-semibold text-gray-900 mb-4">养殖户责任归档</h3>
    <DataTable
      columns={farmerColumns}
      data={farmerResponsibility}
      onRowClick={(row) => (window.location.href = `/farmers/${row.farmer_id}`)}
    />
  </div>
</div>
