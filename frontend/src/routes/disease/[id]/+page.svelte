<script lang="ts">
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  import Modal from '$lib/components/Modal.svelte';
  import { diseaseReportApi } from '$lib/stores/api';
  import type { DiseaseReport } from '$lib/types';

  let report: DiseaseReport | null = null;
  let loading = true;
  let treatmentModalOpen = false;

  let treatmentForm = {
    treated_by: '',
    treatment_method: '',
    status: 'processing' as 'pending' | 'processing' | 'resolved' | 'closed'
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

  const severityMap: Record<string, { label: string; class: string }> = {
    mild: { label: '轻微', class: 'bg-green-100 text-green-800' },
    moderate: { label: '中等', class: 'bg-yellow-100 text-yellow-800' },
    severe: { label: '严重', class: 'bg-orange-100 text-orange-800' },
    critical: { label: '危急', class: 'bg-red-100 text-red-800' }
  };

  const statusMap: Record<string, { label: string; class: string }> = {
    pending: { label: '待处理', class: 'bg-yellow-100 text-yellow-800' },
    processing: { label: '处理中', class: 'bg-blue-100 text-blue-800' },
    resolved: { label: '已解决', class: 'bg-green-100 text-green-800' },
    closed: { label: '已关闭', class: 'bg-gray-100 text-gray-800' }
  };

  async function loadData() {
    const id = $page.params.id;
    if (!id) return;

    loading = true;
    try {
      const res = await diseaseReportApi.getById(parseInt(id));
      report = res.data;
    } catch (error) {
      console.error('Failed to load report:', error);
      report = {
        id: parseInt(id),
        cage: 1,
        cage_code: 'C-001',
        reporter: '张三',
        report_time: '2026-06-18T10:30:00',
        disease_type: 'bacterial',
        severity: 'severe',
        description: '发现鱼体表面有多处溃疡，食欲减退，部分鱼体发黑。约有30%的鱼出现症状。',
        status: 'pending',
        is_anomaly: true,
        anomaly_score: 78.5,
        created_at: '2026-06-18T10:30:00',
        updated_at: '2026-06-18T10:30:00'
      };
    } finally {
      loading = false;
    }
  }

  function goBack() {
    window.location.href = '/disease';
  }

  function openTreatmentModal() {
    if (report) {
      treatmentForm = {
        treated_by: report.treated_by || '',
        treatment_method: report.treatment_method || '',
        status: report.status === 'pending' ? 'processing' : report.status
      };
    }
    treatmentModalOpen = true;
  }

  async function handleTreatmentSubmit() {
    if (!report) return;

    try {
      await diseaseReportApi.update(report.id, {
        ...treatmentForm,
        treatment_time: new Date().toISOString()
      });
      treatmentModalOpen = false;
      loadData();
    } catch (error) {
      console.error('Failed to update treatment:', error);
      alert('保存失败');
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
{:else if report}
  <div class="space-y-6">
    <div class="flex items-center gap-4">
      <button on:click={goBack} class="p-2 hover:bg-gray-100 rounded-lg transition-colors">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
        </svg>
      </button>
      <h2 class="text-2xl font-bold text-gray-900">病害上报 #{report.id}</h2>
      {@html `<span class="px-3 py-1 text-sm font-medium rounded-full ${statusMap[report.status]?.class || 'bg-gray-100 text-gray-800'}">${statusMap[report.status]?.label || report.status}</span>`}
      {#if report.is_anomaly}
        <span class="px-3 py-1 text-sm font-medium bg-red-100 text-red-800 rounded-full">异常</span>
      {/if}
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h3 class="text-lg font-semibold text-gray-900 mb-4">基本信息</h3>
        <div class="space-y-4">
          <div class="grid grid-cols-2 gap-4">
            <div>
              <p class="text-sm text-gray-500">网箱编号</p>
              <p class="font-medium"><a href="/cages/{report.cage}" class="text-primary-600 hover:underline">{report.cage_code || '-'}</a></p>
            </div>
            <div>
              <p class="text-sm text-gray-500">上报人</p>
              <p class="font-medium">{report.reporter}</p>
            </div>
            <div>
              <p class="text-sm text-gray-500">上报时间</p>
              <p class="font-medium">{new Date(report.report_time).toLocaleString('zh-CN')}</p>
            </div>
            <div>
              <p class="text-sm text-gray-500">病害类型</p>
              <p class="font-medium">{diseaseTypeMap[report.disease_type] || report.disease_type}</p>
            </div>
            <div>
              <p class="text-sm text-gray-500">严重程度</p>
              {@html `<span class="px-2 py-1 text-xs font-medium rounded-full ${severityMap[report.severity]?.class}">${severityMap[report.severity]?.label}</span>`}
            </div>
            {#if report.is_anomaly}
              <div>
                <p class="text-sm text-gray-500">异常分数</p>
                <p class="font-medium text-red-600">{report.anomaly_score}</p>
              </div>
            {/if}
          </div>
          <div>
            <p class="text-sm text-gray-500 mb-1">病害描述</p>
            <p class="font-medium bg-gray-50 p-4 rounded-lg">{report.description}</p>
          </div>
          {#if report.image}
            <div>
              <p class="text-sm text-gray-500 mb-1">现场图片</p>
              <img src={report.image} alt="病害图片" class="max-w-md rounded-lg border border-gray-200" />
            </div>
          {/if}
        </div>
      </div>

      <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold text-gray-900">处理记录</h3>
          {#if report.status !== 'resolved' && report.status !== 'closed'}
            <button
              on:click={openTreatmentModal}
              class="px-4 py-2 bg-primary-600 text-white text-sm rounded-lg hover:bg-primary-700 transition-colors"
            >
              处理
            </button>
          {/if}
        </div>

        {#if report.treated_by || report.treatment_method}
          <div class="space-y-4">
            {#if report.treated_by}
              <div>
                <p class="text-sm text-gray-500">处理人</p>
                <p class="font-medium">{report.treated_by}</p>
              </div>
            {/if}
            {#if report.treatment_time}
              <div>
                <p class="text-sm text-gray-500">处理时间</p>
                <p class="font-medium">{new Date(report.treatment_time).toLocaleString('zh-CN')}</p>
              </div>
            {/if}
            {#if report.treatment_method}
              <div>
                <p class="text-sm text-gray-500">处理方案</p>
                <p class="font-medium bg-gray-50 p-4 rounded-lg">{report.treatment_method}</p>
              </div>
            {/if}
          </div>
        {:else}
          <div class="text-center py-12 text-gray-500">
            暂无处理记录
          </div>
        {/if}
      </div>
    </div>
  </div>
{/if}

<Modal open={treatmentModalOpen} title="处理病害" size="lg">
  <form on:submit|preventDefault={handleTreatmentSubmit} class="space-y-4">
    <div>
      <label class="block text-sm font-medium text-gray-700 mb-1">处理状态 *</label>
      <select
        bind:value={treatmentForm.status}
        required
        class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
      >
        <option value="processing">处理中</option>
        <option value="resolved">已解决</option>
        <option value="closed">已关闭</option>
      </select>
    </div>
    <div>
      <label class="block text-sm font-medium text-gray-700 mb-1">处理人 *</label>
      <input
        type="text"
        bind:value={treatmentForm.treated_by}
        required
        class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
      />
    </div>
    <div>
      <label class="block text-sm font-medium text-gray-700 mb-1">处理方案 *</label>
      <textarea
        bind:value={treatmentForm.treatment_method}
        rows={4}
        required
        class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
        placeholder="请详细描述处理方案"
      />
    </div>
  </form>

  <div slot="footer">
    <button type="button" on:click={() => (treatmentModalOpen = false)} class="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50">取消</button>
    <button type="button" on:click={handleTreatmentSubmit} class="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700">保存</button>
  </div>
</Modal>
