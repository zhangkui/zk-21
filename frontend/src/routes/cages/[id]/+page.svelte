<script lang="ts">
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  import DataTable from '$lib/components/DataTable.svelte';
  import { cageApi } from '$lib/stores/api';
  import type { Cage, InspectionPoint, DiseaseReport, MortalityReport } from '$lib/types';

  let cage: Cage | null = null;
  let loading = true;
  let errorMsg: string | null = null;
  let activeTab = 'basic';

  const statusMap: Record<string, { label: string; class: string }> = {
    normal: { label: '正常', class: 'bg-green-100 text-green-800' },
    maintenance: { label: '维护中', class: 'bg-yellow-100 text-yellow-800' },
    empty: { label: '空置', class: 'bg-gray-100 text-gray-800' },
    abnormal: { label: '异常', class: 'bg-red-100 text-red-800' }
  };

  const inspectionColumns = [
    { key: 'id', label: 'ID' },
    {
      key: 'check_time',
      label: '检查时间',
      render: (val: string) => new Date(val).toLocaleString('zh-CN')
    },
    { key: 'water_temperature', label: '水温(°C)' },
    { key: 'salinity', label: '盐度(‰)' },
    { key: 'ph_value', label: 'pH值' },
    {
      key: 'water_quality',
      label: '水质',
      render: (val: string) => {
        const map: Record<string, string> = {
          excellent: '优秀', good: '良好', fair: '一般', poor: '较差', very_poor: '很差'
        };
        return map[val] || val;
      }
    },
    {
      key: 'has_abnormality',
      label: '是否异常',
      render: (val: boolean) => val
        ? '<span class="px-2 py-1 text-xs font-medium bg-red-100 text-red-800 rounded-full">是</span>'
        : '<span class="px-2 py-1 text-xs font-medium bg-green-100 text-green-800 rounded-full">否</span>'
    }
  ];

  const diseaseColumns = [
    { key: 'id', label: 'ID' },
    {
      key: 'report_time',
      label: '上报时间',
      render: (val: string) => new Date(val).toLocaleString('zh-CN')
    },
    {
      key: 'disease_type',
      label: '病害类型',
      render: (val: string) => {
        const map: Record<string, string> = {
          bacterial: '细菌性疾病', viral: '病毒性疾病', parasitic: '寄生虫病',
          fungal: '真菌性疾病', nutritional: '营养性疾病', environmental: '环境性疾病', other: '其他'
        };
        return map[val] || val;
      }
    },
    {
      key: 'severity',
      label: '严重程度',
      render: (val: string) => {
        const map: Record<string, string> = {
          mild: '轻微', moderate: '中等', severe: '严重', critical: '危急'
        };
        return map[val] || val;
      }
    },
    {
      key: 'status',
      label: '状态',
      render: (val: string) => {
        const map: Record<string, { label: string; class: string }> = {
          pending: { label: '待处理', class: 'bg-yellow-100 text-yellow-800' },
          processing: { label: '处理中', class: 'bg-blue-100 text-blue-800' },
          resolved: { label: '已解决', class: 'bg-green-100 text-green-800' },
          closed: { label: '已关闭', class: 'bg-gray-100 text-gray-800' }
        };
        const s = map[val] || { label: val, class: 'bg-gray-100 text-gray-800' };
        return `<span class="px-2 py-1 text-xs font-medium rounded-full ${s.class}">${s.label}</span>`;
      }
    }
  ];

  const mortalityColumns = [
    { key: 'id', label: 'ID' },
    {
      key: 'report_time',
      label: '上报时间',
      render: (val: string) => new Date(val).toLocaleString('zh-CN')
    },
    { key: 'mortality_count', label: '死亡数量(尾)' },
    {
      key: 'cause',
      label: '原因',
      render: (val: string) => {
        const map: Record<string, string> = {
          disease: '疾病', predation: '敌害', environment: '环境因素',
          feeding: '投喂问题', operation: '操作失误', unknown: '原因不明', other: '其他'
        };
        return map[val] || val;
      }
    },
    {
      key: 'status',
      label: '状态',
      render: (val: string) => {
        const map: Record<string, { label: string; class: string }> = {
          pending: { label: '待处理', class: 'bg-yellow-100 text-yellow-800' },
          processing: { label: '处理中', class: 'bg-blue-100 text-blue-800' },
          resolved: { label: '已解决', class: 'bg-green-100 text-green-800' },
          closed: { label: '已关闭', class: 'bg-gray-100 text-gray-800' }
        };
        const s = map[val] || { label: val, class: 'bg-gray-100 text-gray-800' };
        return `<span class="px-2 py-1 text-xs font-medium rounded-full ${s.class}">${s.label}</span>`;
      }
    }
  ];

  async function loadData() {
    const id = $page.params.id;
    if (!id) return;

    loading = true;
    try {
      const res = await cageApi.getById(parseInt(id));
      cage = res.data;
    } catch (err) {
      console.error('Failed to load cage:', err);
      errorMsg = '加载数据失败，请稍后重试';
    } finally {
      loading = false;
    }
  }

  function goBack() {
    window.location.href = '/cages';
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
{:else if cage}
  <div class="space-y-6">
    <div class="flex items-center gap-4">
      <button on:click={goBack} class="p-2 hover:bg-gray-100 rounded-lg transition-colors">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
        </svg>
      </button>
      <h2 class="text-2xl font-bold text-gray-900">{cage.code}</h2>
      {@html `<span class="px-3 py-1 text-sm font-medium rounded-full ${statusMap[cage.status]?.class || 'bg-gray-100 text-gray-800'}">${statusMap[cage.status]?.label || cage.status}</span>`}
    </div>

    <div class="bg-white rounded-xl shadow-sm border border-gray-200">
      <div class="border-b border-gray-200">
        <nav class="flex space-x-8 px-6">
          {#each [{ key: 'basic', label: '基本信息' }, { key: 'inspection', label: '巡检历史' }, { key: 'disease', label: '病害历史' }, { key: 'mortality', label: '死亡记录' }] as tab}
            <button
              on:click={() => (activeTab = tab.key)}
              class="py-4 px-1 border-b-2 font-medium text-sm transition-colors {activeTab === tab.key
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}"
            >
              {tab.label}
            </button>
          {/each}
        </nav>
      </div>

      <div class="p-6">
        {#if activeTab === 'basic'}
          <div class="space-y-6">
            <div class="grid grid-cols-2 md:grid-cols-4 gap-6">
              <div>
                <p class="text-sm text-gray-500">所属海区</p>
                <p class="font-medium">{cage.sea_area_name || '-'}</p>
              </div>
              <div>
                <p class="text-sm text-gray-500">位置</p>
                <p class="font-medium">{cage.location}</p>
              </div>
              <div>
                <p class="text-sm text-gray-500">容量</p>
                <p class="font-medium">{cage.capacity} 尾</p>
              </div>
              <div>
                <p class="text-sm text-gray-500">面积</p>
                <p class="font-medium">{cage.area || '-'} 平方米</p>
              </div>
              <div>
                <p class="text-sm text-gray-500">养殖品种</p>
                <p class="font-medium">{cage.species || '-'}</p>
              </div>
              <div>
                <p class="text-sm text-gray-500">投放日期</p>
                <p class="font-medium">{cage.stocking_date || '-'}</p>
              </div>
              <div>
                <p class="text-sm text-gray-500">创建时间</p>
                <p class="font-medium">{new Date(cage.created_at).toLocaleDateString('zh-CN')}</p>
              </div>
              <div>
                <p class="text-sm text-gray-500">更新时间</p>
                <p class="font-medium">{new Date(cage.updated_at).toLocaleDateString('zh-CN')}</p>
              </div>
            </div>
            {#if cage.farmers && cage.farmers.length > 0}
              <div class="pt-4 border-t border-gray-100">
                <p class="text-sm text-gray-500 mb-2">关联养殖户</p>
                <div class="flex flex-wrap gap-2">
                  {#each cage.farmers as f}
                    <a
                      href={`/farmers/${f.id}`}
                      class="inline-block px-3 py-1 text-sm font-medium bg-blue-100 text-blue-800 rounded-full hover:bg-blue-200 transition-colors"
                    >
                      {f.name}
                      {#if f.phone}
                        <span class="text-xs text-blue-600 ml-1">({f.phone})</span>
                      {/if}
                    </a>
                  {/each}
                </div>
              </div>
            {/if}
          </div>
        {:else if activeTab === 'inspection'}
          <DataTable columns={inspectionColumns} data={cage.inspection_points || []} />
        {:else if activeTab === 'disease'}
          <DataTable
            columns={diseaseColumns}
            data={cage.disease_reports || []}
            onRowClick={(row) => (window.location.href = `/disease/${row.id}`)}
          />
        {:else if activeTab === 'mortality'}
          <DataTable
            columns={mortalityColumns}
            data={cage.mortality_reports || []}
            onRowClick={(row) => (window.location.href = `/mortality/${row.id}`)}
          />
        {/if}
      </div>
    </div>
  </div>
{/if}
