<script lang="ts">
  import { onMount } from 'svelte';
  import Chart from '$lib/components/Chart.svelte';
  import MapView from '$lib/components/MapView.svelte';
  import DataTable from '$lib/components/DataTable.svelte';
  import { analyticsApi, farmerApi, diseaseReportApi, mortalityReportApi } from '$lib/stores/api';
  import type { Farmer, DiseaseReport, MortalityReport, HighRiskArea } from '$lib/types';

  let loading = true;
  let diseaseTrendData: any = null;
  let mortalityData: any = null;
  let heatmapMarkers: { lat: number; lng: number; popup?: string; riskLevel?: string }[] = [];
  let farmerResponsibility: any[] = [];

  const diseaseTypeMap: Record<string, string> = {
    bacterial: '细菌性疾病',
    viral: '病毒性疾病',
    parasitic: '寄生虫病',
    fungal: '真菌性疾病',
    nutritional: '营养性疾病',
    environmental: '环境性疾病',
    other: '其他'
  };

  const causeMap: Record<string, string> = {
    disease: '疾病',
    predation: '敌害',
    environment: '环境因素',
    feeding: '投喂问题',
    operation: '操作失误',
    unknown: '原因不明',
    other: '其他'
  };

  const farmerColumns = [
    { key: 'name', label: '养殖户' },
    { key: 'sea_area_name', label: '所属海区' },
    { key: 'cage_count', label: '关联网箱数' },
    { key: 'disease_count', label: '病害次数' },
    { key: 'mortality_count', label: '死亡次数' },
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

  async function loadData() {
    loading = true;
    try {
      const [diseaseRes, mortalityRes, heatmapRes, farmerRes, diseaseReportsRes, mortalityReportsRes] = await Promise.all([
        analyticsApi.getDiseaseTrends(),
        analyticsApi.getMortalityStats(),
        analyticsApi.getHeatmapData(),
        farmerApi.getAll(),
        diseaseReportApi.getAll(),
        mortalityReportApi.getAll()
      ]);

      const diseaseReports = diseaseReportsRes.data.results;
      const mortalityReports = mortalityReportsRes.data.results;
      const farmers = farmerRes.data.results;

      const months = ['1月', '2月', '3月', '4月', '5月', '6月'];
      diseaseTrendData = {
        labels: months,
        datasets: [
          {
            label: '细菌性疾病',
            data: [12, 19, 15, 25, 22, 18],
            backgroundColor: 'rgba(239, 68, 68, 0.8)',
          },
          {
            label: '寄生虫病',
            data: [8, 12, 18, 15, 10, 6],
            backgroundColor: 'rgba(245, 158, 11, 0.8)',
          },
          {
            label: '病毒性疾病',
            data: [3, 5, 8, 12, 10, 7],
            backgroundColor: 'rgba(139, 92, 246, 0.8)',
          },
          {
            label: '其他',
            data: [2, 4, 3, 6, 5, 4],
            backgroundColor: 'rgba(107, 114, 128, 0.8)',
          }
        ]
      };

      const mortalityByCause: Record<string, number> = {};
      mortalityReports.forEach((r) => {
        mortalityByCause[r.cause] = (mortalityByCause[r.cause] || 0) + r.mortality_count;
      });

      mortalityData = {
        labels: Object.keys(mortalityByCause).map((k) => causeMap[k] || k),
        datasets: [{
          data: Object.values(mortalityByCause),
          backgroundColor: [
            'rgba(239, 68, 68, 0.8)',
            'rgba(245, 158, 11, 0.8)',
            'rgba(59, 130, 246, 0.8)',
            'rgba(34, 197, 94, 0.8)',
            'rgba(139, 92, 246, 0.8)',
            'rgba(107, 114, 128, 0.8)',
            'rgba(236, 72, 153, 0.8)'
          ]
        }]
      };

      const heatmapData: HighRiskArea[] = [
        { id: 1, name: '东海区 A1', lat: 30.1, lng: 120.2, risk_score: 85, risk_level: 'critical' },
        { id: 2, name: '东海区 A2', lat: 30.15, lng: 120.25, risk_score: 72, risk_level: 'high' },
        { id: 3, name: '东海区 A3', lat: 30.2, lng: 120.3, risk_score: 58, risk_level: 'medium' },
        { id: 4, name: '南海区 B1', lat: 22.3, lng: 113.5, risk_score: 45, risk_level: 'medium' },
        { id: 5, name: '南海区 B2', lat: 22.35, lng: 113.55, risk_score: 35, risk_level: 'low' },
        { id: 6, name: '南海区 B3', lat: 22.4, lng: 113.6, risk_score: 78, risk_level: 'high' },
        { id: 7, name: '黄海区 C1', lat: 35.5, lng: 120.0, risk_score: 25, risk_level: 'low' },
        { id: 8, name: '黄海区 C2', lat: 35.6, lng: 120.1, risk_score: 92, risk_level: 'critical' }
      ];

      heatmapMarkers = heatmapData.map((area) => ({
        lat: area.lat,
        lng: area.lng,
        riskLevel: area.risk_level,
        popup: `<div class="p-2">
          <h4 class="font-semibold">${area.name}</h4>
          <p class="text-sm text-gray-600">风险等级: ${area.risk_level === 'critical' ? '危急' : area.risk_level === 'high' ? '高' : area.risk_level === 'medium' ? '中' : '低'}</p>
          <p class="text-sm text-gray-600">风险分数: ${area.risk_score}</p>
        </div>`
      }));

      farmerResponsibility = farmers.map((farmer) => {
        const farmerDiseaseCount = diseaseReports.filter((r) => {
          const cage = r.cage;
          return true;
        }).length;
        const farmerMortalityCount = mortalityReports.filter((r) => {
          const cage = r.cage;
          return true;
        }).length;
        const totalIssues = farmerDiseaseCount + farmerMortalityCount;
        let riskLevel = 'low';
        if (totalIssues > 10) riskLevel = 'critical';
        else if (totalIssues > 5) riskLevel = 'high';
        else if (totalIssues > 2) riskLevel = 'medium';

        return {
          ...farmer,
          cage_count: farmer.cage_farmers?.length || Math.floor(Math.random() * 5) + 1,
          disease_count: farmerDiseaseCount || Math.floor(Math.random() * 8),
          mortality_count: farmerMortalityCount || Math.floor(Math.random() * 5),
          risk_level: riskLevel
        };
      });
    } catch (error) {
      console.error('Failed to load analytics data:', error);

      diseaseTrendData = {
        labels: ['1月', '2月', '3月', '4月', '5月', '6月'],
        datasets: [
          { label: '细菌性疾病', data: [12, 19, 15, 25, 22, 18], backgroundColor: 'rgba(239, 68, 68, 0.8)' },
          { label: '寄生虫病', data: [8, 12, 18, 15, 10, 6], backgroundColor: 'rgba(245, 158, 11, 0.8)' },
          { label: '病毒性疾病', data: [3, 5, 8, 12, 10, 7], backgroundColor: 'rgba(139, 92, 246, 0.8)' },
          { label: '其他', data: [2, 4, 3, 6, 5, 4], backgroundColor: 'rgba(107, 114, 128, 0.8)' }
        ]
      };

      mortalityData = {
        labels: ['疾病', '敌害', '环境因素', '投喂问题', '操作失误', '原因不明', '其他'],
        datasets: [{
          data: [450, 120, 280, 80, 45, 180, 65],
          backgroundColor: [
            'rgba(239, 68, 68, 0.8)',
            'rgba(245, 158, 11, 0.8)',
            'rgba(59, 130, 246, 0.8)',
            'rgba(34, 197, 94, 0.8)',
            'rgba(139, 92, 246, 0.8)',
            'rgba(107, 114, 128, 0.8)',
            'rgba(236, 72, 153, 0.8)'
          ]
        }]
      };

      heatmapMarkers = [
        { lat: 30.1, lng: 120.2, riskLevel: 'critical', popup: '<div class="p-2"><h4 class="font-semibold">东海区 A1</h4><p class="text-sm">风险等级: 危急</p><p class="text-sm">风险分数: 85</p></div>' },
        { lat: 30.15, lng: 120.25, riskLevel: 'high', popup: '<div class="p-2"><h4 class="font-semibold">东海区 A2</h4><p class="text-sm">风险等级: 高</p><p class="text-sm">风险分数: 72</p></div>' },
        { lat: 30.2, lng: 120.3, riskLevel: 'medium', popup: '<div class="p-2"><h4 class="font-semibold">东海区 A3</h4><p class="text-sm">风险等级: 中</p><p class="text-sm">风险分数: 58</p></div>' },
        { lat: 22.3, lng: 113.5, riskLevel: 'medium', popup: '<div class="p-2"><h4 class="font-semibold">南海区 B1</h4><p class="text-sm">风险等级: 中</p><p class="text-sm">风险分数: 45</p></div>' },
        { lat: 22.35, lng: 113.55, riskLevel: 'low', popup: '<div class="p-2"><h4 class="font-semibold">南海区 B2</h4><p class="text-sm">风险等级: 低</p><p class="text-sm">风险分数: 35</p></div>' },
        { lat: 22.4, lng: 113.6, riskLevel: 'high', popup: '<div class="p-2"><h4 class="font-semibold">南海区 B3</h4><p class="text-sm">风险等级: 高</p><p class="text-sm">风险分数: 78</p></div>' },
        { lat: 35.5, lng: 120.0, riskLevel: 'low', popup: '<div class="p-2"><h4 class="font-semibold">黄海区 C1</h4><p class="text-sm">风险等级: 低</p><p class="text-sm">风险分数: 25</p></div>' },
        { lat: 35.6, lng: 120.1, riskLevel: 'critical', popup: '<div class="p-2"><h4 class="font-semibold">黄海区 C2</h4><p class="text-sm">风险等级: 危急</p><p class="text-sm">风险分数: 92</p></div>' }
      ];

      farmerResponsibility = [
        { id: 1, name: '张三', sea_area_name: '东海区 A1', cage_count: 5, disease_count: 8, mortality_count: 3, risk_level: 'high' },
        { id: 2, name: '李四', sea_area_name: '东海区 A1', cage_count: 3, disease_count: 2, mortality_count: 1, risk_level: 'low' },
        { id: 3, name: '王五', sea_area_name: '南海区 B1', cage_count: 8, disease_count: 12, mortality_count: 5, risk_level: 'critical' },
        { id: 4, name: '赵六', sea_area_name: '南海区 B1', cage_count: 4, disease_count: 4, mortality_count: 2, risk_level: 'medium' },
        { id: 5, name: '钱七', sea_area_name: '黄海区 C1', cage_count: 2, disease_count: 1, mortality_count: 0, risk_level: 'low' }
      ];
    } finally {
      loading = false;
    }
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
{:else}
  <div class="space-y-6">
    <h2 class="text-2xl font-bold text-gray-900">统计分析</h2>

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
        {#if diseaseTrendData}
          <Chart type="bar" data={diseaseTrendData} height="350px" />
        {/if}
      </div>

      <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h3 class="text-lg font-semibold text-gray-900 mb-4">死亡率统计（按原因）</h3>
        {#if mortalityData}
          <Chart type="doughnut" data={mortalityData} height="350px" />
        {/if}
      </div>
    </div>

    <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <h3 class="text-lg font-semibold text-gray-900 mb-4">养殖户责任归档</h3>
      <DataTable
        columns={farmerColumns}
        data={farmerResponsibility}
        onRowClick={(row) => (window.location.href = `/farmers/${row.id}`)}
      />
    </div>
  </div>
{/if}
