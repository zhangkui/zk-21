<script lang="ts">
  import { onMount } from 'svelte';
  import DataTable from '$lib/components/DataTable.svelte';
  import Modal from '$lib/components/Modal.svelte';
  import { farmerApi, seaAreaApi } from '$lib/stores/api';
  import type { Farmer, SeaArea } from '$lib/types';

  let farmers: Farmer[] = [];
  let seaAreas: SeaArea[] = [];
  let loading = true;
  let errorMsg: string | null = null;
  let modalOpen = false;
  let editingFarmer: Partial<Farmer> | null = null;

  let formData: Partial<Farmer> = {
    name: '',
    phone: '',
    id_card: '',
    sea_area: undefined,
    scale: '',
    registration_date: undefined,
    contact_info: ''
  };

  const columns = [
    { key: 'id', label: 'ID' },
    { key: 'name', label: '姓名' },
    { key: 'phone', label: '联系电话' },
    { key: 'id_card', label: '身份证号' },
    { key: 'sea_area_name', label: '所属海区' },
    { key: 'scale', label: '养殖规模' },
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
      const [farmersRes, seaAreasRes] = await Promise.all([
        farmerApi.getAll(),
        seaAreaApi.getAll()
      ]);
      farmers = farmersRes.data.results.map((f) => ({
        ...f,
        sea_area_name: f.sea_area ? seaAreasRes.data.results.find((s) => s.id === f.sea_area)?.name : '-'
      }));
      seaAreas = seaAreasRes.data.results;
    } catch (err) {
      console.error('Failed to load data:', err);
      errorMsg = '加载数据失败，请稍后重试';
    } finally {
      loading = false;
    }
  }

  function openModal(farmer?: Farmer) {
    if (farmer) {
      editingFarmer = farmer;
      formData = { ...farmer };
    } else {
      editingFarmer = null;
      formData = {
        name: '',
        phone: '',
        id_card: '',
        sea_area: undefined,
        scale: '',
        registration_date: undefined,
        contact_info: ''
      };
    }
    modalOpen = true;
  }

  async function handleSubmit() {
    try {
      if (editingFarmer?.id) {
        await farmerApi.update(editingFarmer.id, formData);
      } else {
        await farmerApi.create(formData);
      }
      modalOpen = false;
      loadData();
    } catch (error) {
      console.error('Failed to save farmer:', error);
      alert('保存失败');
    }
  }

  async function handleDelete(id: number) {
    if (confirm('确定要删除这个养殖户吗？')) {
      try {
        await farmerApi.delete(id);
        loadData();
      } catch (error) {
        console.error('Failed to delete farmer:', error);
        alert('删除失败');
      }
    }
  }

  function handleRowClick(row: Farmer) {
    const target = event?.target as HTMLElement;
    if (target.textContent === '查看') {
      window.location.href = `/farmers/${row.id}`;
    } else if (target.textContent === '编辑') {
      openModal(row);
    } else if (target.textContent === '删除') {
      handleDelete(row.id);
    } else {
      window.location.href = `/farmers/${row.id}`;
    }
  }

  onMount(() => {
    loadData();
  });
</script>

<div class="space-y-6">
  <div class="flex items-center justify-between">
    <h2 class="text-2xl font-bold text-gray-900">养殖户管理</h2>
    <button
      on:click={() => openModal()}
      class="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors flex items-center gap-2"
    >
      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
      </svg>
      新增养殖户
    </button>
  </div>

  <DataTable
    columns={columns}
    data={farmers}
    loading={loading}
    searchable={true}
    searchPlaceholder="搜索姓名、电话、身份证号..."
    onRowClick={handleRowClick}
  />
</div>

<Modal open={modalOpen} title={editingFarmer ? '编辑养殖户' : '新增养殖户'} size="lg">
  <form on:submit|preventDefault={handleSubmit} class="space-y-4">
    <div class="grid grid-cols-2 gap-4">
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">姓名 *</label>
        <input
          type="text"
          bind:value={formData.name}
          required
          class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
        />
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">联系电话 *</label>
        <input
          type="tel"
          bind:value={formData.phone}
          required
          class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
        />
      </div>
    </div>

    <div class="grid grid-cols-2 gap-4">
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">身份证号 *</label>
        <input
          type="text"
          bind:value={formData.id_card}
          required
          class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
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

    <div class="grid grid-cols-2 gap-4">
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">养殖规模</label>
        <input
          type="text"
          bind:value={formData.scale}
          class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
          placeholder="如：大型、中型、小型"
        />
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">注册日期</label>
        <input
          type="date"
          bind:value={formData.registration_date}
          class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
        />
      </div>
    </div>

    <div>
      <label class="block text-sm font-medium text-gray-700 mb-1">其他联系方式</label>
      <textarea
        bind:value={formData.contact_info}
        rows={2}
        class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
        placeholder="微信、QQ、邮箱等"
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
      {editingFarmer ? '保存修改' : '创建'}
    </button>
  </div>
</Modal>
