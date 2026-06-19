<script lang="ts">
  import { onMount } from 'svelte';
  import DataTable from '$lib/components/DataTable.svelte';
  import Modal from '$lib/components/Modal.svelte';
  import { diseaseReportApi, cageApi } from '$lib/stores/api';
  import type { DiseaseReport, Cage } from '$lib/types';

  let reports: DiseaseReport[] = [];
  let cages: Cage[] = [];
  let loading = true;
  let modalOpen = false;
  let statusFilter = '';

  let formData: Partial<DiseaseReport> = {
    cage: undefined,
    reporter: '',
    disease_type: 'bacterial',
    severity: 'mild',
    description: '',
    status: 'pending'
  };

  let selectedImage: File | null = null;

  const diseaseTypeOptions = [
    { value: 'bacterial', label: '细菌性疾病' },
    { value: 'viral', label: '病毒性疾病' },
    { value: 'parasitic', label: '寄生虫病' },
    { value: 'fungal', label: '真菌性疾病' },
    { value: 'nutritional', label: '营养性疾病' },
    { value: 'environmental', label: '环境性疾病' },
    { value: 'other', label: '其他' }
  ];

  const severityOptions = [
    { value: 'mild', label: '轻微' },
    { value: 'moderate', label: '中等' },
    { value: 'severe', label: '严重' },
    { value: 'critical', label: '危急' }
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

  const severityMap: Record<string, { label: string; class: string }> = {
    mild: { label: '轻微', class: 'bg-green-100 text-green-800' },
    moderate: { label: '中等', class: 'bg-yellow-100 text-yellow-800' },
    severe: { label: '严重', class: 'bg-orange-100 text-orange-800' },
    critical: { label: '危急', class: 'bg-red-100 text-red-800' }
  };

  const diseaseTypeMap: Record<string, string> = {
    bacterial: '细菌性疾病',
    viral: '病毒性疾病',
    parasitic: '寄生虫病',
    fungal: '真菌性疾病',
    nutritional: '营养性疾病',
    environmental: '环境性疾病',
    other: '其他'
  };

  const columns = [
    { key: 'id', label: 'ID' },
    { key: 'cage_code', label: '网箱编号' },
    { key: 'reporter', label: '上报人' },
    {
      key: 'report_time',
      label: '上报时间',
      render: (val: string) => new Date(val).toLocaleString('zh-CN')
    },
    {
      key: 'disease_type',
      label: '病害类型',
      render: (val: string) => diseaseTypeMap[val] || val
    },
    {
      key: 'severity',
      label: '严重程度',
      render: (val: string) => {
        const s = severityMap[val] || { label: val, class: 'bg-gray-100 text-gray-800' };
        return `<span class="px-2 py-1 text-xs font-medium rounded-full ${s.class}">${s.label}</span>`;
      }
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
      const [reportsRes, cagesRes] = await Promise.all([
        diseaseReportApi.getAll(),
        cageApi.getAll()
      ]);
      reports = reportsRes.data.results.map((r) => ({
        ...r,
        cage_code: cagesRes.data.results.find((c) => c.id === r.cage)?.code || '-'
      }));
      cages = cagesRes.data.results;
    } catch (error) {
      console.error('Failed to load data:', error);
      reports = [
        { id: 1, cage: 1, cage_code: 'C-001', reporter: '张三', report_time: '2026-06-18T10:30:00', disease_type: 'bacterial', severity: 'mild', description: '发现鱼体表面有溃疡', status: 'pending', is_anomaly: false, anomaly_score: 0, created_at: '2026-06-18', updated_at: '2026-06-18' },
        { id: 2, cage: 3, cage_code: 'C-003', reporter: '李四', report_time: '2026-06-17T14:20:00', disease_type: 'parasitic', severity: 'severe', description: '大量寄生虫感染', status: 'processing', is_anomaly: true, anomaly_score: 85.5, treated_by: '王医生', created_at: '2026-06-17', updated_at: '2026-06-18' },
        { id: 3, cage: 2, cage_code: 'C-002', reporter: '王五', report_time: '2026-06-15T09:00:00', disease_type: 'viral', severity: 'critical', description: '病毒性感染，大量死亡', status: 'resolved', is_anomaly: true, anomaly_score: 95.0, treated_by: '李专家', treatment_method: '使用抗病毒药物，全池消毒', treatment_time: '2026-06-16T10:00:00', created_at: '2026-06-15', updated_at: '2026-06-17' }
      ];
      cages = [
        { id: 1, code: 'C-001', location: '东海区 A1-1', capacity: 5000, status: 'normal', created_at: '2026-01-01', updated_at: '2026-06-01' },
        { id: 2, code: 'C-002', location: '东海区 A1-2', capacity: 8000, status: 'maintenance', created_at: '2026-01-15', updated_at: '2026-05-20' },
        { id: 3, code: 'C-003', location: '东海区 A1-3', capacity: 10000, status: 'abnormal', created_at: '2026-02-01', updated_at: '2026-06-10' }
      ];
    } finally {
      loading = false;
    }
  }

  function openModal() {
    formData = {
      cage: undefined,
      reporter: '',
      disease_type: 'bacterial',
      severity: 'mild',
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
      formDataToSend.append('reporter', formData.reporter || '');
      formDataToSend.append('disease_type', formData.disease_type || '');
      formDataToSend.append('severity', formData.severity || '');
      formDataToSend.append('description', formData.description || '');
      if (selectedImage) {
        formDataToSend.append('image', selectedImage);
      }

      await diseaseReportApi.create(formDataToSend);
      modalOpen = false;
      loadData();
    } catch (error) {
      console.error('Failed to save report:', error);
      alert('保存失败');
    }
  }

  function handleRowClick(row: DiseaseReport) {
    window.location.href = `/disease/${row.id}`;
  }

  onMount(() => {
    loadData();
  });
</script>

<div class="space-y-6">
  <div class="flex items-center justify-between">
    <h2 class="text-2xl font-bold text-gray-900">病害上报</h2>
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

<Modal open={modalOpen} title="新增病害上报" size="lg">
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
        <label class="block text-sm font-medium text-gray-700 mb-1">上报人 *</label>
        <input
          type="text"
          bind:value={formData.reporter}
          required
          class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
        />
      </div>
    </div>
    <div class="grid grid-cols-2 gap-4">
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">病害类型 *</label>
        <select
          bind:value={formData.disease_type}
          required
          class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
        >
          {#each diseaseTypeOptions as opt}
            <option value={opt.value}>{opt.label}</option>
          {/each}
        </select>
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">严重程度 *</label>
        <select
          bind:value={formData.severity}
          required
          class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
        >
          {#each severityOptions as opt}
            <option value={opt.value}>{opt.label}</option>
          {/each}
        </select>
      </div>
    </div>
    <div>
      <label class="block text-sm font-medium text-gray-700 mb-1">病害描述 *</label>
      <textarea
        bind:value={formData.description}
        rows={3}
        required
        class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
        placeholder="请详细描述病害情况"
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
