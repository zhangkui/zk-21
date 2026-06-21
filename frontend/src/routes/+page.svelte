<script lang="ts">
  import { onMount } from 'svelte';
  import StatCard from '$lib/components/StatCard.svelte';
  import MapView from '$lib/components/MapView.svelte';
  import Chart from '$lib/components/Chart.svelte';
  import DataTable from '$lib/components/DataTable.svelte';
  import { dashboardApi } from '$lib/stores/api';
  import type { DashboardStats, MonthlyTrend, HighRiskArea, RecentReport } from '$lib/types';

  let stats: DashboardStats = {
    sea_areas_count: 0,
    cages_count: 0,
    farmers_count: 0,
    pending_reports_count: 0
  };

  let monthlyTrends: MonthlyTrend[] = [];
  let highRiskAreas: HighRiskArea[] = [];
  let recentReports: RecentReport[] = [];
  let loading = true;
  let errorMsg: string | null = null;

  const statusColors: Record<string, string> = {
    pending: 'bg-yellow-100 text-yellow-800',
    processing: 'bg-blue-100 text-blue-800',
    resolved: 'bg-green-100 text-green-800',
    closed: 'bg-gray-100 text-gray-800'
  };

  const statusLabels: Record<string, string> = {
    pending: '待处理',
    processing: '处理中',
    resolved: '已解决',
    closed: '已关闭'
  };

  $: trendChartData = {
    labels: monthlyTrends.map((t) => t.month),
    datasets: [
      {
        label: '病害上报',
        data: monthlyTrends.map((t) => t.disease_count),
        borderColor: '#ef4444',
        backgroundColor: 'rgba(239, 68, 68, 0.1)',
        tension: 0.4,
        fill: true
      },
      {
        label: '死亡上报',
        data: monthlyTrends.map((t) => t.mortality_count),
        borderColor: '#f59e0b',
        backgroundColor: 'rgba(245, 158, 11, 0.1)',
        tension: 0.4,
        fill: true
      },
      {
        label: '巡检次数',
        data: monthlyTrends.map((t) => t.inspection_count),
        borderColor: '#3b82f6',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        tension: 0.4,
        fill: true
      }
    ]
  };

  function riskLabel(level: string) {
    return level === 'critical' ? '危急' : level === 'high' ? '高' : level === 'medium' ? '中' : '低';
  }

  $: mapMarkers = highRiskAreas.map((area) => ({
    lat: area.lat,
    lng: area.lng,
    riskLevel: area.risk_level,
    popup: `<div class="p-2 min-w-[180px]">
      <h4 class="font-semibold text-gray-900">${area.name}</h4>
      ${area.location ? `<p class="text-sm text-gray-600 mt-1">位置: ${area.location}</p>` : ''}
      <p class="text-sm text-gray-600">风险等级: ${riskLabel(area.risk_level)}</p>
      <p class="text-sm text-gray-600">风险分数: ${area.risk_score}</p>
      <p class="text-sm text-gray-600">异常网箱: ${area.abnormal_cage_count ?? area.abnormal_cages ?? '-'}/${area.total_cages ?? '-'}</p>
      <p class="text-sm text-gray-600">近7天病害上报: ${area.disease_reports ?? 0} 起</p>
      <p class="text-sm text-gray-600">近7天死亡上报: ${area.mortality_reports ?? 0} 起</p>
    </div>`
  }));

  const columns = [
    {
      key: 'type',
      label: '类型',
      render: (val: string) =>
        val === 'disease'
          ? '<span class="px-2 py-1 text-xs font-medium bg-red-100 text-red-800 rounded-full">病害</span>'
          : '<span class="px-2 py-1 text-xs font-medium bg-yellow-100 text-yellow-800 rounded-full">死亡</span>'
    },
    { key: 'cage_code', label: '网箱编号' },
    {
      key: 'report_time',
      label: '上报时间',
      render: (val: string) => new Date(val).toLocaleString('zh-CN')
    },
    {
      key: 'status',
      label: '状态',
      render: (val: string) =>
        `<span class="px-2 py-1 text-xs font-medium rounded-full ${statusColors[val] || 'bg-gray-100 text-gray-800'}">${statusLabels[val] || val}</span>`
    },
    { key: 'description', label: '描述' }
  ];

  onMount(async () => {
    const results = await Promise.allSettled([
      dashboardApi.getStats(),
      dashboardApi.getMonthlyTrends(),
      dashboardApi.getHighRiskAreas(),
      dashboardApi.getRecentReports()
    ]);

    if (results[0].status === 'fulfilled') {
      stats = results[0].value.data;
    } else {
      console.error('Failed to load stats:', results[0].reason);
      errorMsg = '加载统计数据失败，请稍后重试';
    }
    if (results[1].status === 'fulfilled') {
      monthlyTrends = results[1].value.data;
    } else {
      console.error('Failed to load monthly trends:', results[1].reason);
    }
    if (results[2].status === 'fulfilled') {
      highRiskAreas = results[2].value.data;
    } else {
      console.error('Failed to load high risk areas:', results[2].reason);
    }
    if (results[3].status === 'fulfilled') {
      recentReports = results[3].value.data;
    } else {
      console.error('Failed to load recent reports:', results[3].reason);
    }
    loading = false;
  });
</script>

<div class="space-y-6 relative">
  {#if loading}
    <div class="absolute inset-0 z-50 flex items-center justify-center bg-white/70 rounded-xl">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      <span class="ml-3 text-gray-500">加载中...</span>
    </div>
  {/if}

  <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
    <StatCard title="海区数量" value={stats.sea_areas_count} icon="🌊" color="blue" percentage={stats.sea_areas_percentage} percentageLabel="高风险占比" />
    <StatCard title="网箱数量" value={stats.cages_count} icon="🗑️" color="green" percentage={stats.cages_percentage} percentageLabel="异常占比" />
    <StatCard title="养殖户数量" value={stats.farmers_count} icon="👤" color="yellow" percentage={stats.farmers_percentage} percentageLabel="异常占比" />
    <StatCard title="待处理上报" value={stats.pending_reports_count} icon="⚠️" color="red" percentage={stats.pending_reports_percentage} percentageLabel="占总上报" />
  </div>

  {#if errorMsg}
    <div class="bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-3 text-sm">
      {errorMsg}
    </div>
  {/if}

  <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
    <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <h3 class="text-lg font-semibold text-gray-900 mb-4">高风险区域</h3>
      <MapView markers={mapMarkers} height="350px" />
    </div>

    <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <h3 class="text-lg font-semibold text-gray-900 mb-4">月度趋势</h3>
      <Chart type="line" data={trendChartData} height="350px" />
    </div>
  </div>

  <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
    <h3 class="text-lg font-semibold text-gray-900 mb-4">最近上报</h3>
    <DataTable
      columns={columns}
      data={recentReports}
      loading={loading}
      onRowClick={(row) => {
        if (row.type === 'disease') {
          window.location.href = `/disease/${row.id}`;
        } else {
          window.location.href = `/mortality/${row.id}`;
        }
      }}
    />
  </div>
</div>
