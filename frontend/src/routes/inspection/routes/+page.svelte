<script lang="ts">
  import { onMount } from 'svelte';
  import DataTable from '$lib/components/DataTable.svelte';
  import Modal from '$lib/components/Modal.svelte';
  import { inspectionRouteApi, cageApi } from '$lib/stores/api';
  import type { InspectionRoute, Cage } from '$lib/types';

  let routes: InspectionRoute[] = [];
  let cages: Cage[] = [];
  let loading = true;
  let errorMsg: string | null = null;
  let modalOpen = false;
  let editingRoute: Partial<InspectionRoute> | null = null;

  let formData: Partial<InspectionRoute> = {
    name: '',
    description: '',
    cages: []
  };

  let selectedCages: number[] = [];

  const columns = [
    { key: 'id', label: 'ID' },
    { key: 'name', label: '路线名称' },
    { key: 'description', label: '描述' },
    {
      key: 'cages',
      label: '包含网箱数',
      render: (val: number[]) => val?.length || 0
    },
    {
      key: 'creator_name',
      label: '创建人',
      render: (val: string) => val || '-'
    },
    {
      key: 'created_at',
      label: '创建时间',
      render: (val: string) => new Date(val).toLocaleDateString('zh-CN')
    },
    {
      key: 'actions',
      label: '操作',
      render: () =>
        '<button class="text-yellow-600 hover:text-yellow-800 mr-3">编辑</button>' +
        '<button class="text-red-600 hover:text-red-800">删除</button>'
    }
  ];

  async function loadData() {
    loading = true;
    try {
      const [routesRes, cagesRes] = await Promise.all([
        inspectionRouteApi.getAll(),
        cageApi.getAll()
      ]);
      routes = routesRes.data.results;
      cages = cagesRes.data.results;
    } catch (err) {
      console.error('Failed to load data:', err);
      errorMsg = '加载数据失败，请稍后重试';
    } finally {
      loading = false;
    }
  }

  function openModal(route?: InspectionRoute) {
    if (route) {
      editingRoute = route;
      formData = { ...route };
      selectedCages = [...route.cages];
    } else {
      editingRoute = null;
      formData = { name: '', description: '', cages: [] };
      selectedCages = [];
    }
    modalOpen = true;
  }

  async function handleSubmit() {
    try {
      formData.cages = selectedCages;
      if (editingRoute?.id) {
        await inspectionRouteApi.update(editingRoute.id, formData);
      } else {
        await inspectionRouteApi.create(formData);
      }
      modalOpen = false;
      loadData();
    } catch (error) {
      console.error('Failed to save route:', error);
      alert('保存失败');
    }
  }

  async function handleDelete(id: number) {
    if (confirm('确定要删除这个巡检路线吗？')) {
      try {
        await inspectionRouteApi.delete(id);
        loadData();
      } catch (error) {
        console.error('Failed to delete route:', error);
        alert('删除失败');
      }
    }
  }

  function handleRowClick(row: InspectionRoute) {
    const target = event?.target as HTMLElement;
    if (target.textContent === '编辑') {
      openModal(row);
    } else if (target.textContent === '删除') {
      handleDelete(row.id);
    }
  }

  function toggleCage(cageId: number) {
    if (selectedCages.includes(cageId)) {
      selectedCages = selectedCages.filter((id) => id !== cageId);
    } else {
      selectedCages = [...selectedCages, cageId];
    }
  }

  onMount(() => {
    loadData();
  });
</script>

<div class="space-y-6">
  <div class="flex items-center justify-between">
    <div class="flex items-center gap-4">
      <a href="/inspection" class="p-2 hover:bg-gray-100 rounded-lg transition-colors">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
        </svg>
      </a>
      <h2 class="text-2xl font-bold text-gray-900">巡检路线管理</h2>
    </div>
    <button
      on:click={() => openModal()}
      class="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors flex items-center gap-2"
    >
      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
      </svg>
      新增路线
    </button>
  </div>

  <DataTable
    columns={columns}
    data={routes}
    loading={loading}
    searchable={true}
    searchPlaceholder="搜索路线名称..."
    onRowClick={handleRowClick}
  />
</div>

<Modal bind:open={modalOpen} title={editingRoute ? '编辑路线' : '新增路线'} size="xl">
  <form on:submit|preventDefault={handleSubmit} class="space-y-4">
    <div>
      <label class="block text-sm font-medium text-gray-700 mb-1">路线名称 *</label>
      <input
        type="text"
        bind:value={formData.name}
        required
        class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
      />
    </div>
    <div>
      <label class="block text-sm font-medium text-gray-700 mb-1">描述</label>
      <textarea
        bind:value={formData.description}
        rows={2}
        class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
      />
    </div>
    <div>
      <label class="block text-sm font-medium text-gray-700 mb-2">选择网箱 *</label>
      <div class="border border-gray-300 rounded-lg max-h-64 overflow-y-auto">
        {#each cages as cage}
          <label class="flex items-center gap-3 px-4 py-3 hover:bg-gray-50 border-b border-gray-200 last:border-b-0 cursor-pointer">
            <input
              type="checkbox"
              checked={selectedCages.includes(cage.id)}
              on:change={() => toggleCage(cage.id)}
              class="w-4 h-4 text-primary-600 rounded focus:ring-primary-500"
            />
            <span class="font-medium">{cage.code}</span>
            <span class="text-gray-500">{cage.location}</span>
          </label>
        {/each}
      </div>
      <p class="text-sm text-gray-500 mt-2">已选择 {selectedCages.length} 个网箱</p>
    </div>
  </form>

  <div slot="footer">
    <button type="button" on:click={() => (modalOpen = false)} class="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50">取消</button>
    <button type="button" on:click={handleSubmit} class="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700" disabled={selectedCages.length === 0}>
      {editingRoute ? '保存修改' : '创建'}
    </button>
  </div>
</Modal>
