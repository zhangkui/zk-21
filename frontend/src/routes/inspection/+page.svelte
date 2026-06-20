<script lang="ts">
  import { onMount } from 'svelte';
  import DataTable from '$lib/components/DataTable.svelte';
  import Modal from '$lib/components/Modal.svelte';
  import { inspectionRecordApi, inspectionRouteApi, cageApi, userApi } from '$lib/stores/api';
  import { auth } from '$lib/stores/auth';
  import type { InspectionRecord, InspectionRoute, Cage, InspectionPoint, User } from '$lib/types';

  let records: InspectionRecord[] = [];
  let routes: InspectionRoute[] = [];
  let cages: Cage[] = [];
  let users: User[] = [];
  let loading = true;
  let errorMsg: string | null = null;
  let modalOpen = false;
  let executionModalOpen = false;
  let selectedRecord: InspectionRecord | null = null;
  let currentCageIndex = 0;
  let currentPoint: Partial<InspectionPoint> = {};

  $: isAdmin = $auth.user?.is_admin || false;

  let formData: Partial<InspectionRecord> = {
    route: undefined,
    inspector: undefined,
    status: 'pending',
    remarks: ''
  };

  const statusOptions = [
    { value: 'pending', label: '待开始' },
    { value: 'in_progress', label: '进行中' },
    { value: 'completed', label: '已完成' },
    { value: 'cancelled', label: '已取消' }
  ];

  const waterQualityOptions = [
    { value: 'excellent', label: '优秀' },
    { value: 'good', label: '良好' },
    { value: 'fair', label: '一般' },
    { value: 'poor', label: '较差' },
    { value: 'very_poor', label: '很差' }
  ];

  const statusMap: Record<string, { label: string; class: string }> = {
    pending: { label: '待开始', class: 'bg-gray-100 text-gray-800' },
    in_progress: { label: '进行中', class: 'bg-blue-100 text-blue-800' },
    completed: { label: '已完成', class: 'bg-green-100 text-green-800' },
    cancelled: { label: '已取消', class: 'bg-red-100 text-red-800' }
  };

  const columns = [
    { key: 'id', label: 'ID' },
    { key: 'route_name', label: '巡检路线' },
    { key: 'inspector_name', label: '巡检人' },
    {
      key: 'start_time',
      label: '开始时间',
      render: (val: string) => val ? new Date(val).toLocaleString('zh-CN') : '-'
    },
    {
      key: 'end_time',
      label: '结束时间',
      render: (val: string) => val ? new Date(val).toLocaleString('zh-CN') : '-'
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
      key: 'actions',
      label: '操作',
      render: (_val: unknown, row: InspectionRecord) => {
        if (row.status === 'pending' || row.status === 'in_progress') {
          return '<button class="text-primary-600 hover:text-primary-800 mr-3">执行</button>' +
                 '<button class="text-yellow-600 hover:text-yellow-800 mr-3">编辑</button>' +
                 '<button class="text-red-600 hover:text-red-800">删除</button>';
        }
        return '<button class="text-gray-600 hover:text-gray-800">查看</button>';
      }
    }
  ];

  async function loadData() {
    loading = true;
    try {
      const [recordsRes, routesRes, cagesRes, usersRes] = await Promise.all([
        inspectionRecordApi.getAll(),
        inspectionRouteApi.getAll(),
        cageApi.getAll(),
        userApi.getAll()
      ]);
      records = recordsRes.data.results.map((r) => ({
        ...r,
        route_name: routesRes.data.results.find((rt) => rt.id === r.route)?.name || '-'
      }));
      routes = routesRes.data.results;
      cages = cagesRes.data.results;
      users = usersRes.data.results;
    } catch (err) {
      console.error('Failed to load data:', err);
      errorMsg = '加载数据失败，请稍后重试';
    } finally {
      loading = false;
    }
  }

  function openModal(record?: InspectionRecord) {
    if (record) {
      formData = { ...record };
    } else {
      formData = {
        route: undefined,
        inspector: isAdmin ? undefined : ($auth.user?.id || undefined),
        status: 'pending',
        remarks: ''
      };
    }
    modalOpen = true;
  }

  async function handleSubmit() {
    try {
      if (formData.route) {
        await inspectionRecordApi.create(formData);
        modalOpen = false;
        loadData();
      }
    } catch (error) {
      console.error('Failed to save record:', error);
      alert('保存失败');
    }
  }

  async function handleDelete(id: number) {
    if (confirm('确定要删除这个巡检记录吗？')) {
      try {
        await inspectionRecordApi.delete(id);
        loadData();
      } catch (error) {
        console.error('Failed to delete record:', error);
        alert('删除失败');
      }
    }
  }

  function startExecution(record: InspectionRecord) {
    selectedRecord = record;
    currentCageIndex = 0;
    currentPoint = {
      record: record.id,
      cage: undefined,
      check_time: new Date().toISOString(),
      has_abnormality: false
    };
    executionModalOpen = true;
  }

  function handleRowClick(row: InspectionRecord) {
    const target = event?.target as HTMLElement;
    if (target.textContent === '执行') {
      startExecution(row);
    } else if (target.textContent === '编辑') {
      openModal(row);
    } else if (target.textContent === '删除') {
      handleDelete(row.id);
    }
  }

  $: currentRoute = selectedRecord ? routes.find((r) => r.id === selectedRecord!.route) : null;
  $: currentRouteCages = currentRoute?.cages || [];
  $: currentCageId = currentRouteCages[currentCageIndex];
  $: currentCage = cages.find((c) => c.id === currentCageId);

  function nextCage() {
    if (currentCageIndex < currentRouteCages.length - 1) {
      currentCageIndex++;
      currentPoint = {
        record: selectedRecord?.id,
        cage: currentRouteCages[currentCageIndex],
        check_time: new Date().toISOString(),
        has_abnormality: false
      };
    }
  }

  function prevCage() {
    if (currentCageIndex > 0) {
      currentCageIndex--;
    }
  }

  async function savePoint() {
    try {
      currentPoint.cage = currentRouteCages[currentCageIndex];
      currentPoint.check_time = new Date().toISOString();
      currentPoint.has_abnormality = !!(currentPoint.abnormal_condition && currentPoint.abnormal_condition.length > 0);
      console.log('Saving inspection point:', currentPoint);
      
      if (currentCageIndex >= currentRouteCages.length - 1) {
        if (selectedRecord) {
          await inspectionRecordApi.update(selectedRecord.id, {
            status: 'completed',
            end_time: new Date().toISOString()
          });
        }
        executionModalOpen = false;
        loadData();
      } else {
        nextCage();
      }
    } catch (error) {
      console.error('Failed to save point:', error);
      alert('保存失败');
    }
  }

  onMount(() => {
    loadData();
  });
</script>

<div class="space-y-6">
  <div class="flex items-center justify-between">
    <h2 class="text-2xl font-bold text-gray-900">巡检管理</h2>
    <div class="flex gap-3">
      <a
        href="/inspection/routes"
        class="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
      >
        巡检路线管理
      </a>
      <button
        on:click={() => openModal()}
        class="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors flex items-center gap-2"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        新增巡检
      </button>
    </div>
  </div>

  <DataTable
    columns={columns}
    data={records}
    loading={loading}
    searchable={true}
    searchPlaceholder="搜索巡检路线、巡检人..."
    onRowClick={handleRowClick}
  />
</div>

<Modal open={modalOpen} title="新增巡检记录" size="lg">
  <form on:submit|preventDefault={handleSubmit} class="space-y-4">
    <div class="grid grid-cols-2 gap-4">
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">巡检路线 *</label>
        <select
          bind:value={formData.route}
          required
          class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
        >
          <option value={undefined}>请选择路线</option>
          {#each routes as r}
            <option value={r.id}>{r.name}</option>
          {/each}
        </select>
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">巡检人 {isAdmin ? '*' : '(默认当前用户)'}</label>
        {#if isAdmin}
          <select
            bind:value={formData.inspector}
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
          >
            <option value={undefined}>请选择巡检人</option>
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
    <div>
      <label class="block text-sm font-medium text-gray-700 mb-1">备注</label>
      <textarea
        bind:value={formData.remarks}
        rows={2}
        class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
      />
    </div>
  </form>

  <div slot="footer">
    <button type="button" on:click={() => (modalOpen = false)} class="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50">取消</button>
    <button type="button" on:click={handleSubmit} class="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700">创建</button>
  </div>
</Modal>

<Modal open={executionModalOpen} title="执行巡检" size="xl">
  {#if selectedRecord && currentRoute && currentCage}
    <div class="space-y-6">
      <div class="flex items-center justify-between">
        <div>
          <p class="text-sm text-gray-500">巡检路线</p>
          <p class="font-semibold text-lg">{currentRoute.name}</p>
        </div>
        <div class="text-right">
          <p class="text-sm text-gray-500">进度</p>
          <p class="font-semibold">{currentCageIndex + 1} / {currentRouteCages.length}</p>
        </div>
      </div>

      <div class="bg-blue-50 rounded-lg p-4">
        <p class="text-sm text-gray-500">当前网箱</p>
        <p class="font-semibold text-lg">{currentCage.code} - {currentCage.location}</p>
      </div>

      <div class="grid grid-cols-2 gap-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">水温(°C)</label>
          <input
            type="number"
            step="0.1"
            bind:value={currentPoint.water_temperature}
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
          />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">盐度(‰)</label>
          <input
            type="number"
            step="0.1"
            bind:value={currentPoint.salinity}
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
          />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">pH值</label>
          <input
            type="number"
            step="0.1"
            bind:value={currentPoint.ph_value}
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
          />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">水质情况</label>
          <select
            bind:value={currentPoint.water_quality}
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
          >
            <option value={undefined}>请选择</option>
            {#each waterQualityOptions as opt}
              <option value={opt.value}>{opt.label}</option>
            {/each}
          </select>
        </div>
      </div>

      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">异常情况</label>
        <textarea
          bind:value={currentPoint.abnormal_condition}
          rows={3}
          class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
          placeholder="如有异常请描述，无异常请留空"
        />
      </div>
    </div>
  {/if}

  <div slot="footer" class="flex justify-between">
    <button
      type="button"
      on:click={prevCage}
      disabled={currentCageIndex === 0}
      class="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
    >
      上一个
    </button>
    <div class="flex gap-3">
      <button type="button" on:click={() => (executionModalOpen = false)} class="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50">
        取消
      </button>
      <button type="button" on:click={savePoint} class="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700">
        {currentCageIndex >= currentRouteCages.length - 1 ? '完成巡检' : '保存并继续'}
      </button>
    </div>
  </div>
</Modal>
