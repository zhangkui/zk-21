<script lang="ts">
  import { onMount } from 'svelte';
  import DataTable from '$lib/components/DataTable.svelte';
  import Modal from '$lib/components/Modal.svelte';
  import { cageApi, seaAreaApi, farmerApi } from '$lib/stores/api';
  import type { Cage, SeaArea, Farmer } from '$lib/types';

  let cages: Cage[] = [];
  let seaAreas: SeaArea[] = [];
  let farmers: Farmer[] = [];
  let loading = true;
  let errorMsg: string | null = null;
  let modalOpen = false;
  let editingCage: Partial<Cage> | null = null;
  let statusFilter = '';
  let farmerFilter = '';

  let formData: Partial<Cage> & { farmer_ids?: number[] } = {
    code: '',
    sea_area: undefined,
    location: '',
    capacity: 0,
    species: '',
    stocking_date: undefined,
    status: 'normal',
    area: undefined,
    farmer_ids: []
  };

  const statusOptions = [
    { value: 'normal', label: '正常' },
    { value: 'maintenance', label: '维护中' },
    { value: 'empty', label: '空置' },
    { value: 'abnormal', label: '异常' }
  ];

  const statusMap: Record<string, { label: string; class: string }> = {
    normal: { label: '正常', class: 'bg-green-100 text-green-800' },
    maintenance: { label: '维护中', class: 'bg-yellow-100 text-yellow-800' },
    empty: { label: '空置', class: 'bg-gray-100 text-gray-800' },
    abnormal: { label: '异常', class: 'bg-red-100 text-red-800' }
  };

  const columns = [
    { key: 'id', label: 'ID' },
    { key: 'code', label: '网箱编号' },
    { key: 'sea_area_name', label: '所属海区' },
    {
      key: 'farmers',
      label: '养殖户',
      render: (_: any, row: Cage) => {
        if (row.farmers && row.farmers.length > 0) {
          return row.farmers
            .map(
              (f) =>
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
        const s = statusMap[val] || { label: val, class: 'bg-gray-100 text-gray-800' };
        return `<span class="px-2 py-1 text-xs font-medium rounded-full ${s.class}">${s.label}</span>`;
      }
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

  $: filteredCages = cages.filter((c) => {
    if (statusFilter && c.status !== statusFilter) return false;
    if (farmerFilter) {
      const fid = parseInt(farmerFilter);
      if (!c.farmers || !c.farmers.some((f) => f.id === fid)) return false;
    }
    return true;
  });

  async function loadData() {
    loading = true;
    try {
      const [cagesRes, seaAreasRes, farmersRes] = await Promise.all([
        cageApi.getAll(),
        seaAreaApi.getAll(),
        farmerApi.getAll()
      ]);
      seaAreas = seaAreasRes.data.results;
      farmers = farmersRes.data.results;
      cages = cagesRes.data.results.map((c) => ({
        ...c,
        sea_area_name: c.sea_area ? seaAreas.find((s) => s.id === c.sea_area)?.name : '-'
      }));
    } catch (err) {
      console.error('Failed to load data:', err);
      errorMsg = '加载数据失败，请稍后重试';
    } finally {
      loading = false;
    }
  }

  function openModal(cage?: Cage) {
    if (cage) {
      editingCage = cage;
      formData = {
        ...cage,
        farmer_ids: cage.farmers?.map((f) => f.id) || []
      };
    } else {
      editingCage = null;
      formData = {
        code: '',
        sea_area: undefined,
        location: '',
        capacity: 0,
        species: '',
        stocking_date: undefined,
        status: 'normal',
        area: undefined,
        farmer_ids: []
      };
    }
    modalOpen = true;
  }

  function toggleFarmer(farmerId: number) {
    if (!formData.farmer_ids) formData.farmer_ids = [];
    const idx = formData.farmer_ids.indexOf(farmerId);
    if (idx >= 0) {
      formData.farmer_ids.splice(idx, 1);
    } else {
      formData.farmer_ids.push(farmerId);
    }
    formData = { ...formData };
  }

  async function handleSubmit() {
    try {
      if (editingCage?.id) {
        await cageApi.update(editingCage.id, formData);
      } else {
        await cageApi.create(formData);
      }
      modalOpen = false;
      loadData();
    } catch (error) {
      console.error('Failed to save cage:', error);
      alert('保存失败');
    }
  }

  async function handleDelete(id: number) {
    if (confirm('确定要删除这个网箱吗？')) {
      try {
        await cageApi.delete(id);
        loadData();
      } catch (error) {
        console.error('Failed to delete cage:', error);
        alert('删除失败');
      }
    }
  }

  function handleRowClick(row: Cage) {
    const target = event?.target as HTMLElement;
    if (target.dataset.farmerId) {
      window.location.href = `/farmers/${target.dataset.farmerId}`;
      return;
    }
    if (target.textContent === '查看') {
      window.location.href = `/cages/${row.id}`;
    } else if (target.textContent === '编辑') {
      openModal(row);
    } else if (target.textContent === '删除') {
      handleDelete(row.id);
    } else {
      window.location.href = `/cages/${row.id}`;
    }
  }

  onMount(() => {
    loadData();
  });
</script>

<div class="space-y-6">
  <div class="flex items-center justify-between">
    <h2 class="text-2xl font-bold text-gray-900">网箱档案管理</h2>
    <div class="flex items-center gap-4">
      <select
        bind:value={farmerFilter}
        class="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
      >
        <option value="">全部养殖户</option>
        {#each farmers as f}
          <option value={f.id}>{f.name}</option>
        {/each}
      </select>
      <select
        bind:value={statusFilter}
        class="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
      >
        <option value="">全部状态</option>
        {#each statusOptions as opt}
          <option value={opt.value}>{opt.label}</option>
        {/each}
      </select>
      <button
        on:click={() => openModal()}
        class="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors flex items-center gap-2"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        新增网箱
      </button>
    </div>
  </div>

  <DataTable
    columns={columns}
    data={filteredCages}
    loading={loading}
    searchable={true}
    searchPlaceholder="搜索网箱编号、位置、品种..."
    onRowClick={handleRowClick}
  />
</div>

<Modal open={modalOpen} title={editingCage ? '编辑网箱' : '新增网箱'} size="lg">
  <form id="cage-form" on:submit|preventDefault={handleSubmit} class="space-y-4">
    <div class="grid grid-cols-2 gap-4">
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">网箱编号 *</label>
        <input
          type="text"
          bind:value={formData.code}
          required
          class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
          placeholder="如：C-001"
        />
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">所属海区</label>
        <select
          bind:value={formData.sea_area}
          class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
        >
          <option value={undefined}>请选择海区</option>
          {#each seaAreas as sa}
            <option value={sa.id}>{sa.name}</option>
          {/each}
        </select>
      </div>
    </div>

    <div>
      <label class="block text-sm font-medium text-gray-700 mb-1">位置 *</label>
      <input
        type="text"
        bind:value={formData.location}
        required
        class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
        placeholder="请输入位置"
      />
    </div>

    <div class="grid grid-cols-3 gap-4">
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">容量(尾) *</label>
        <input
          type="number"
          bind:value={formData.capacity}
          required
          class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
        />
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">面积(平方米)</label>
        <input
          type="number"
          step="0.01"
          bind:value={formData.area}
          class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
        />
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">状态 *</label>
        <select
          bind:value={formData.status}
          required
          class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
        >
          {#each statusOptions as opt}
            <option value={opt.value}>{opt.label}</option>
          {/each}
        </select>
      </div>
    </div>

    <div class="grid grid-cols-2 gap-4">
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">养殖品种</label>
        <input
          type="text"
          bind:value={formData.species}
          class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
          placeholder="如：大黄鱼、石斑鱼"
        />
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">投放日期</label>
        <input
          type="date"
          bind:value={formData.stocking_date}
          class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
        />
      </div>
    </div>

    <div>
      <label class="block text-sm font-medium text-gray-700 mb-2">关联养殖户</label>
      <div class="border border-gray-300 rounded-lg p-3 max-h-40 overflow-y-auto bg-gray-50">
        {#if farmers.length === 0}
          <p class="text-sm text-gray-500">暂无养殖户数据</p>
        {:else}
          <div class="grid grid-cols-2 md:grid-cols-3 gap-2">
            {#each farmers as f}
              <label class="flex items-center gap-2 cursor-pointer hover:bg-white px-2 py-1 rounded">
                <input
                  type="checkbox"
                  checked={formData.farmer_ids?.includes(f.id)}
                  on:change={() => toggleFarmer(f.id)}
                  class="w-4 h-4 text-primary-600 rounded border-gray-300 focus:ring-primary-500"
                />
                <span class="text-sm text-gray-700">{f.name} ({f.phone})</span>
              </label>
            {/each}
          </div>
        {/if}
      </div>
      <p class="mt-1 text-xs text-gray-500">可多选，勾选关联的养殖户</p>
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
      {editingCage ? '保存修改' : '创建'}
    </button>
  </div>
</Modal>
