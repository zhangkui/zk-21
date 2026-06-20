<script lang="ts">
  import { onMount } from 'svelte';
  import DataTable from '$lib/components/DataTable.svelte';
  import Modal from '$lib/components/Modal.svelte';
  import MapEditor from '$lib/components/MapEditor.svelte';
  import { seaAreaApi } from '$lib/stores/api';
  import type { SeaArea } from '$lib/types';

  let seaAreas: SeaArea[] = [];
  let loading = true;
  let errorMsg: string | null = null;
  let modalOpen = false;
  let editingArea: Partial<SeaArea> | null = null;

  let formData: Partial<SeaArea> = {
    name: '',
    location: '',
    area: 0,
    depth: undefined,
    boundary: undefined,
    description: ''
  };

  const columns = [
    { key: 'id', label: 'ID' },
    { key: 'name', label: '海区名称' },
    { key: 'location', label: '位置' },
    { key: 'area', label: '面积(公顷)' },
    { key: 'depth', label: '水深(米)' },
    {
      key: 'cages',
      label: '网箱数量',
      render: (_: any, row: SeaArea) => row.cages?.length || row.cage_count || 0
    },
    {
      key: 'farmers',
      label: '养殖户数量',
      render: (_: any, row: SeaArea) => row.farmers?.length || row.farmer_count || 0
    },
    {
      key: 'actions',
      label: '操作',
      render: () =>
        '<button class="text-primary-600 hover:text-primary-800 mr-3">查看</button>' +
        '<button class="text-yellow-600 hover:text-yellow-800 mr-3">编辑</button>' +
        '<button class="text-red-600 hover:text-red-800">删除</button>'
    }
  ];

  async function loadData() {
    loading = true;
    try {
      const res = await seaAreaApi.getAll();
      seaAreas = res.data.results;
    } catch (err) {
      console.error('Failed to load sea areas:', err);
      errorMsg = '加载数据失败，请稍后重试';
    } finally {
      loading = false;
    }
  }

  function openModal(area?: SeaArea) {
    if (area) {
      editingArea = area;
      formData = { ...area };
    } else {
      editingArea = null;
      formData = {
        name: '',
        location: '',
        area: 0,
        depth: undefined,
        boundary: undefined,
        description: ''
      };
    }
    modalOpen = true;
  }

  function handleMapChange(e: CustomEvent) {
    const { points } = e.detail;
    formData = {
      ...formData,
      boundary: points.length >= 3 ? points : undefined
    };
  }

  async function handleSubmit() {
    try {
      if (editingArea?.id) {
        await seaAreaApi.update(editingArea.id, formData);
      } else {
        await seaAreaApi.create(formData);
      }
      modalOpen = false;
      loadData();
    } catch (error) {
      console.error('Failed to save sea area:', error);
      alert('保存失败');
    }
  }

  async function handleDelete(id: number) {
    if (confirm('确定要删除这个海区吗？')) {
      try {
        await seaAreaApi.delete(id);
        loadData();
      } catch (error) {
        console.error('Failed to delete sea area:', error);
        alert('删除失败');
      }
    }
  }

  function handleRowClick(row: SeaArea) {
    const target = event?.target as HTMLElement;
    if (target.textContent === '查看') {
      window.location.href = `/sea-areas/${row.id}`;
    } else if (target.textContent === '编辑') {
      openModal(row);
    } else if (target.textContent === '删除') {
      handleDelete(row.id);
    } else {
      window.location.href = `/sea-areas/${row.id}`;
    }
  }

  onMount(() => {
    loadData();
  });
</script>

<div class="space-y-6">
  <div class="flex items-center justify-between">
    <h2 class="text-2xl font-bold text-gray-900">海区管理</h2>
    <button
      on:click={() => openModal()}
      class="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors flex items-center gap-2"
    >
      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
      </svg>
      新增海区
    </button>
  </div>

  <DataTable
    columns={columns}
    data={seaAreas}
    loading={loading}
    searchable={true}
    searchPlaceholder="搜索海区名称、位置..."
    onRowClick={handleRowClick}
  />
</div>

<Modal bind:open={modalOpen} title={editingArea ? '编辑海区' : '新增海区'} size="2xl">
  <form on:submit|preventDefault={handleSubmit} class="space-y-4">
    <div class="grid grid-cols-2 gap-4">
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">海区名称 *</label>
        <input
          type="text"
          bind:value={formData.name}
          required
          class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
          placeholder="请输入海区名称"
        />
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">位置 *</label>
        <input
          type="text"
          bind:value={formData.location}
          required
          class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
          placeholder="请输入位置描述"
        />
      </div>
    </div>

    <div class="grid grid-cols-2 gap-4">
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">面积(公顷) *</label>
        <input
          type="number"
          step="0.01"
          bind:value={formData.area}
          required
          class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
          placeholder="0.00"
        />
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">平均水深(米)</label>
        <input
          type="number"
          step="0.01"
          bind:value={formData.depth}
          class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
          placeholder="0.00"
        />
      </div>
    </div>

    <div>
      <label class="block text-sm font-medium text-gray-700 mb-2">
        海区范围（在地图上绘制）
        {#if formData.boundary && formData.boundary.length >= 3}
          <span class="ml-2 text-xs text-green-600 font-normal">✓ 已选择 {formData.boundary.length} 个顶点</span>
        {/if}
      </label>
      <MapEditor
        initialBoundary={formData.boundary || null}
        height="400px"
        on:change={handleMapChange}
      />
    </div>

    <div>
      <label class="block text-sm font-medium text-gray-700 mb-1">描述</label>
      <textarea
        bind:value={formData.description}
        rows={3}
        class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
        placeholder="请输入描述信息"
      />
    </div>
  </form>

  <div slot="footer">
    <button
      type="button"
      on:click={() => (modalOpen = false)}
      class="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
    >
      取消
    </button>
    <button
      type="button"
      on:click={handleSubmit}
      class="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
    >
      {editingArea ? '保存修改' : '创建'}
    </button>
  </div>
</Modal>
