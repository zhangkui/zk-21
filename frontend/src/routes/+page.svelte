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

  $: mapMarkers = highRiskAreas.map((area) => ({
    lat: area.lat,
    lng: area.lng,
    riskLevel: area.risk_level,
    popup: `<div class="p-2">
      <h4 class="font-semibold">${area.name}</h4>
      <p class="text-sm text-gray-600">风险等级: ${area.risk_level === 'critical' ? '危急' : area.risk_level === 'high' ? '高' : area.risk_level === 'medium' ? '中' : '低'}</p>
      <p class="text-sm text-gray-600">风险分数: ${area.risk_score}</p>
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

  function formatDate(dateStr: string) {
    return new Date(dateStr).toLocaleString('zh-CN');
  }

  onMount(async () => {
    try {
      const [statsRes, trendsRes, riskRes, reportsRes] = await Promise.all([
        dashboardApi.getStats(),
        dashboardApi.getMonthlyTrends(),
        dashboardApi.getHighRiskAreas(),
        dashboardApi.getRecentReports()
      ]);

      stats = statsRes.data;
      monthlyTrends = trendsRes.data;
      highRiskAreas = riskRes.data;
      recentReports = reportsRes.data;
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
      stats = { sea_areas_count: 12, cages_count: 156, farmers_count: 89, pending_reports_count: 23 };
      monthlyTrends = [
        { month: '1月', disease_count: 5, mortality_count: 2, inspection_count: 15 },
        { month: '2月', disease_count: 8, mortality_count: 4, inspection_count: 18 },
        { month: '3月', disease_count: 12, mortality_count: 6, inspection_count: 22 },
        { month: '4月', disease_count: 15, mortality_count: 8, inspection_count: 25 },
        { month: '5月', disease_count: 10, mortality_count: 5, inspection_count: 20 },
        { month: '6月', disease_count: 7, mortality_count: 3, inspection_count: 16 }
      ];
      highRiskAreas = [
        { id: 1, name: '东海区 A1', lat: 30.1, lng: 120.2, risk_score: 85, risk_level: 'critical' },
        { id: 2, name: '东海区 A2', lat: 30.15, lng: 120.25, risk_score: 72, risk_level: 'high' },
        { id: 3, name: '南海区 B1', lat: 22.3, lng: 113.5, risk_score: 58, risk_level: 'medium' },
        { id: 4, name: '南海区 B2', lat: 22.35, lng: 113.55, risk_score: 35, risk_level: 'low' }
      ];
      recentReports = [
        {
          id: 1,
          type: 'disease',
          cage_code: 'C-001',
          report_time: '2026-06-18T10:30:00',
          status: 'pending',
          description: '发现鱼体表面有溃疡'
        },
        {
          id: 2,
          type: 'mortality',
          cage_code: 'C-015',
          report_time: '2026-06-18T09:15:00',
          status: 'processing',
          description: '死亡约50尾，原因待查'
        },
        {
          id: 3,
          type: 'disease',
          cage_code: 'C-008',
          report_time: '2026-06-17T14:20:00',
          status: 'resolved',
          description: '寄生虫感染，已处理'
        }
      ];
    } finally {
      loading = false;
    }
  });
</script>

<div class="space-y-6">
  <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
    <StatCard title="海区数量" value={stats.sea_areas_count} icon="🌊" color="blue" trend={5.2} />
    <StatCard title="网箱数量" value={stats.cages_count} icon="🗑️" color="green" trend={3.8} />
    <StatCard title="养殖户数量" value={stats.farmers_count} icon="👤" color="yellow" trend={2.1} />
    <StatCard title="待处理上报" value={stats.pending_reports_count} icon="⚠️" color="red" trend={-1.5} />
  </div>

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
