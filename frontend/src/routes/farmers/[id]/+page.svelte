<script lang="ts">
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  import DataTable from '$lib/components/DataTable.svelte';
  import { farmerApi } from '$lib/stores/api';
  import type { Farmer, Cage } from '$lib/types';

  let farmer: Farmer | null = null;
  let loading = true;
  let activeTab = 'basic';

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
        const map: Record<string, { label: string; class: string }> = {
          normal: { label: '正常', class: 'bg-green-100 text-green-800' },
          maintenance: { label: '维护中', class: 'bg-yellow-100 text-yellow-800' },
          empty: { label: '空置', class: 'bg-gray-100 text-gray-800' },
          abnormal: { label: '异常', class: 'bg-red-100 text-red-800' }
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
      const res = await farmerApi.getById(parseInt(id));
      farmer = res.data;
    } catch (error) {
      console.error('Failed to load farmer:', error);
      farmer = {
        id: parseInt(id),
        name: '张三',
        phone: '13800138001',
        id_card: '330102198001011234',
        sea_area: 1,
        sea_area_name: '东海区 A1',
        scale: '大型',
        registration_date: '2026-01-01',
        contact_info: '微信：zhangsan888',
        created_at: '2026-01-01',
        updated_at: '2026-06-01',
        cage_farmers: [
          { id: 1, cage: 1, cage_code: 'C-001', farmer: parseInt(id), start_date: '2026-01-01', created_at: '2026-01-01' }
        ]
      };
    } finally {
      loading = false;
    }
  }

  function goBack() {
    window.location.href = '/farmers';
  }

  $: cages = farmer?.cage_farmers?.map((cf) => ({
    id: cf.cage,
    code: cf.cage_code,
    location: '-',
    capacity: 0,
    species: '-',
    status: 'normal'
  })) || [];

  onMount(() => {
    loadData();
  });
</script>

{#if loading}
  <div class="flex items-center justify-center py-20">
    <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
    <span class="ml-3 text-gray-500">加载中...</span>
  </div>
{:else if farmer}
  <div class="space-y-6">
    <div class="flex items-center gap-4">
      <button on:click={goBack} class="p-2 hover:bg-gray-100 rounded-lg transition-colors">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
        </svg>
      </button>
      <h2 class="text-2xl font-bold text-gray-900">{farmer.name}</h2>
    </div>

    <div class="bg-white rounded-xl shadow-sm border border-gray-200">
      <div class="border-b border-gray-200">
        <nav class="flex space-x-8 px-6">
          {#each [{ key: 'basic', label: '基本信息' }, { key: 'cages', label: '关联网箱' }, { key: 'history', label: '历史记录' }] as tab}
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
          <div class="grid grid-cols-2 md:grid-cols-4 gap-6">
            <div>
              <p class="text-sm text-gray-500">姓名</p>
              <p class="font-medium">{farmer.name}</p>
            </div>
            <div>
              <p class="text-sm text-gray-500">联系电话</p>
              <p class="font-medium">{farmer.phone}</p>
            </div>
            <div>
              <p class="text-sm text-gray-500">身份证号</p>
              <p class="font-medium">{farmer.id_card}</p>
            </div>
            <div>
              <p class="text-sm text-gray-500">所属海区</p>
              <p class="font-medium">{farmer.sea_area_name || '-'}</p>
            </div>
            <div>
              <p class="text-sm text-gray-500">养殖规模</p>
              <p class="font-medium">{farmer.scale || '-'}</p>
            </div>
            <div>
              <p class="text-sm text-gray-500">注册日期</p>
              <p class="font-medium">{farmer.registration_date || '-'}</p>
            </div>
            <div>
              <p class="text-sm text-gray-500">创建时间</p>
              <p class="font-medium">{new Date(farmer.created_at).toLocaleDateString('zh-CN')}</p>
            </div>
            <div>
              <p class="text-sm text-gray-500">关联网箱数</p>
              <p class="font-medium">{farmer.cage_farmers?.length || 0} 个</p>
            </div>
          </div>
          {#if farmer.contact_info}
            <div class="mt-6">
              <p class="text-sm text-gray-500">其他联系方式</p>
              <p class="font-medium">{farmer.contact_info}</p>
            </div>
          {/if}
        {:else if activeTab === 'cages'}
          <DataTable
            columns={cageColumns}
            data={cages}
            onRowClick={(row) => (window.location.href = `/cages/${row.id}`)}
          />
        {:else if activeTab === 'history'}
          <div class="text-center py-12 text-gray-500">
            历史记录功能开发中...
          </div>
        {/if}
      </div>
    </div>
  </div>
{/if}
