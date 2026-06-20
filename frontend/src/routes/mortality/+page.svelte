<script lang="ts">
  import { onMount } from 'svelte';
  import DataTable from '$lib/components/DataTable.svelte';
  import Modal from '$lib/components/Modal.svelte';
  import { mortalityReportApi, cageApi, userApi } from '$lib/stores/api';
  import { auth } from '$lib/stores/auth';
  import type { MortalityReport, Cage, User } from '$lib/types';

  let reports: MortalityReport[] = [];
  let cages: Cage[] = [];
  let users: User[] = [];
  let loading = true;
  let errorMsg: string | null = null;
  let modalOpen = false;
  let statusFilter = '';

  $: isAdmin = $auth.user?.is_admin || false;

  let formData: Partial<MortalityReport> = {
    cage: undefined,
    reporter: undefined,
    mortality_count: 0,
    cause: 'unknown',
    description: '',
    status: 'pending'
  };

  let selectedImage: File | null = null;

  const causeOptions = [
    { value: 'disease', label: '疾病' },
    { value: 'predation', label: '敌害' },
    { value: 'environment', label: '环境因素' },
    { value: 'feeding', label: '投喂问题' },
    { value: 'operation', label: '操作失误' },
    { value: 'unknown', label: '原因不明' },
    { value: 'other', label: '其他' }
  ];

  const statusOptions = [
    { value: 'pending', label: '待处理' },
    { value: 'processing', label: '处理中' },
    { value: 'resolved', label: '已解决' },
    { value: 'closed', label: '已关闭' }
  ];

  const statusMap: Record<string, { label: string; class: string }> = {
    pending: { label: '待处理', class: 'bg-yellow-100 text-yellow-800' },
    processing: { label: '处理中', class: 'bg-blue-100 text-blue-800' },
    resolved: { label: '已解决', class: 'bg-green-100 text-green-800' },
    closed: { label: '已关闭', class: 'bg-gray-100 text-gray-800' }
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

  const columns = [
    { key: 'id', label: 'ID' },
    { key: 'cage_code', label: '网箱编号' },
    { key: 'reporter_name', label: '上报人' },
    {
      key: 'report_time',
      label: '上报时间',
      render: (val: string) => new Date(val).toLocaleString('zh-CN')
    },
    { key: 'mortality_count', label: '死亡数量(尾)' },
    {
      key: 'cause',
      label: '原因',
      render: (val: string) => causeMap[val] || val
    },
    {
      key: 'status',
      label: '状态',
      render: (val: string) => {
        const s = statusMap[val] || { label: val, class: 'bg-gray-100 text-gray-800' };
        return `<span class="px-2 py-1 text-xs font-medium rounded-full ${s.class}">${s.label}</span>`;
      }
    },
    {
      key: 'is_anomaly',
      label: '异常标记',
      render: (val: boolean) => val
        ? '<span class="px-2 py-1 text-xs font-medium bg-red-100 text-red-800 rounded-full">是</span>'
        : '<span class="px-2 py-1 text-xs font-medium bg-gray-100 text-gray-800 rounded-full">否</span>'
    }
  ];

  $: filteredReports = statusFilter
    ? reports.filter((r) => r.status === statusFilter)
    : reports;

  async function loadData() {
    loading = true;
    try {
      const [reportsRes, cagesRes, usersRes] = await Promise.all([
        mortalityReportApi.getAll(),
        cageApi.getAll(),
        userApi.getAll()
      ]);
      reports = reportsRes.data.results.map((r) => ({
        ...r,
        cage_code: cagesRes.data.results.find((c) => c.id === r.cage)?.code || '-'
      }));
      cages = cagesRes.data.results;
      users = usersRes.data.results;
    } catch (err) {
      console.error('Failed to load data:', err);
      errorMsg = '加载数据失败，请稍后重试';
    } finally {
      loading = false;
    }
  }

  function openModal() {
    formData = {
      cage: undefined,
      reporter: isAdmin ? undefined : ($auth.user?.id || undefined),
      mortality_count: 0,
      cause: 'unknown',
      description: '',
      status: 'pending'
    };
    selectedImage = null;
    modalOpen = true;
  }

  function handleImageUpload(e: Event) {
    const target = e.target as HTMLInputElement;
    if (target.files && target.files[0]) {
      selectedImage = target.files[0];
    }
  }

  async function handleSubmit() {
    try {
      const formDataToSend = new FormData();
      formDataToSend.append('cage', String(formData.cage || ''));
      if (isAdmin && formData.reporter) {
        formDataToSend.append('reporter', String(formData.reporter));
      }
      formDataToSend.append('mortality_count', String(formData.mortality_count || 0));
      formDataToSend.append('cause', formData.cause || '');
      formDataToSend.append('description', formData.description || '');
      if (selectedImage) {
        formDataToSend.append('image', selectedImage);
      }

      await mortalityReportApi.create(formDataToSend);
      modalOpen = false;
      loadData();
    } catch (error) {
      console.error('Failed to save report:', error);
      alert('保存失败');
    }
  }

  function handleRowClick(row: MortalityReport) {
    window.location.href = `/mortality/${row.id}`;
  }

  onMount(() => {
    loadData();
  });
</script>

<div class="space-y-6">
  <div class="flex items-center justify-between">
    <h2 class="text-2xl font-bold text-gray-900">死亡上报</h2>
    <div class="flex items-center gap-4">
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
        on:click={openModal}
        class="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors flex items-center gap-2"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        新增上报
      </button>
    </div>
  </div>

  <DataTable
    columns={columns}
    data={filteredReports}
    loading={loading}
    searchable={true}
    searchPlaceholder="搜索网箱编号、上报人..."
    onRowClick={handleRowClick}
  />
</div>

<Modal open={modalOpen} title="新增死亡上报" size="lg">
  <form on:submit|preventDefault={handleSubmit} class="space-y-4">
    <div class="grid grid-cols-2 gap-4">
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">网箱 *</label>
        <select
          bind:value={formData.cage}
          required
          class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
        >
          <option value={undefined}>请选择网箱</option>
          {#each cages as cage}
            <option value={cage.id}>{cage.code} - {cage.location}</option>
          {/each}
        </select>
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">上报人 {isAdmin ? '*' : '(默认当前用户)'}</label>
        {#if isAdmin}
          <select
            bind:value={formData.reporter}
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
          >
            <option value={undefined}>请选择上报人</option>
            {#each users as u}
              <option value={u.id}>{u.display_name || u.username}</option>
            {/each}
          </select>
        {:else}
          <input
            type="text"
            value={$auth.user?.display_name || $auth.user?.username || ''}
            disabled
            class="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-50 text-gray-500 outline-none"
          />
        {/if}
      </div>
    </div>
    <div class="grid grid-cols-2 gap-4">
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">死亡数量(尾) *</label>
        <input
          type="number"
          bind:value={formData.mortality_count}
          required
          min="1"
          class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
        />
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">死亡原因 *</label>
        <select
          bind:value={formData.cause}
          required
          class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
        >
          {#each causeOptions as opt}
            <option value={opt.value}>{opt.label}</option>
          {/each}
        </select>
      </div>
    </div>
    <div>
      <label class="block text-sm font-medium text-gray-700 mb-1">情况描述 *</label>
      <textarea
        bind:value={formData.description}
        rows={3}
        required
        class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
        placeholder="请详细描述情况"
      />
    </div>
    <div>
      <label class="block text-sm font-medium text-gray-700 mb-1">上传图片</label>
      <input
        type="file"
        accept="image/*"
        on:change={handleImageUpload}
        class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
      />
      {#if selectedImage}
        <p class="text-sm text-green-600 mt-1">已选择: {selectedImage.name}</p>
      {/if}
    </div>
  </form>

  <div slot="footer">
    <button type="button" on:click={() => (modalOpen = false)} class="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50">取消</button>
    <button type="button" on:click={handleSubmit} class="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700">提交上报</button>
  </div>
</Modal>
