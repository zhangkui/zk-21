<script lang="ts">
  import { onMount } from 'svelte';
  import DataTable from '$lib/components/DataTable.svelte';
  import Modal from '$lib/components/Modal.svelte';
  import { roleApi } from '$lib/stores/api';
  import { auth } from '$lib/stores/auth';
  import type { Role } from '$lib/types';

  let roles: Role[] = [];
  let loading = true;
  let errorMsg: string | null = null;
  let modalOpen = false;
  let editingRole: Partial<Role> | null = null;

  let formData: { name: string; code: string; description: string } = {
    name: '',
    code: '',
    description: ''
  };

  const roleCodeOptions = [
    { value: 'admin', label: '管理员' },
    { value: 'inspector', label: '巡检员' },
    { value: 'technician', label: '技术人员' },
    { value: 'farmer', label: '养殖户' }
  ];

  const codeLabelMap: Record<string, string> = {
    admin: '管理员',
    inspector: '巡检员',
    technician: '技术人员',
    farmer: '养殖户'
  };

  $: isAdmin = $auth.user?.is_admin || $auth.user?.role_code === 'admin';

  const columns = [
    { key: 'id', label: 'ID' },
    { key: 'name', label: '角色名称' },
    {
      key: 'code',
      label: '角色编码',
      render: (val: string) =>
        '<span class="px-2 py-1 text-xs rounded bg-gray-100 text-gray-700">' +
        (codeLabelMap[val] || val || '-') +
        '</span>'
    },
    { key: 'description', label: '描述' },
    {
      key: 'user_count',
      label: '用户数量',
      render: (val: number) =>
        '<span class="px-2 py-1 text-xs rounded bg-primary-100 text-primary-700">' +
        (val || 0) +
        '</span>'
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
      const res = await roleApi.getAll();
      roles = res.data.results;
    } catch (err) {
      console.error('Failed to load roles:', err);
      errorMsg = '加载数据失败，请稍后重试';
    } finally {
      loading = false;
    }
  }

  function openModal(role?: Role) {
    if (role) {
      editingRole = role;
      formData = {
        name: role.name,
        code: role.code,
        description: role.description || ''
      };
    } else {
      editingRole = null;
      formData = { name: '', code: '', description: '' };
    }
    modalOpen = true;
  }

  async function handleSubmit() {
    try {
      if (editingRole?.id) {
        await roleApi.update(editingRole.id, formData);
      } else {
        await roleApi.create(formData);
      }
      modalOpen = false;
      loadData();
    } catch (error) {
      console.error('Failed to save role:', error);
      alert('保存失败');
    }
  }

  async function handleDelete(role: Role) {
    const hasUsers = (role.user_count || 0) > 0;
    const warning = hasUsers
      ? '⚠️ 该角色下有 ' + role.user_count + ' 个用户，删除后相关用户将失去该角色权限。确定要删除吗？'
      : '确定要删除这个角色吗？';
    if (confirm(warning)) {
      try {
        await roleApi.delete(role.id);
        loadData();
      } catch (error) {
        console.error('Failed to delete role:', error);
        alert('删除失败');
      }
    }
  }

  function handleRowClick(row: Role) {
    const target = event?.target as HTMLElement;
    if (target.textContent === '编辑') {
      openModal(row);
    } else if (target.textContent === '删除') {
      handleDelete(row);
    }
  }

  onMount(() => {
    loadData();
  });
</script>

<div class="space-y-6">
  <div class="flex items-center justify-between">
    <h2 class="text-2xl font-bold text-gray-900">角色管理</h2>
    <div class="flex items-center gap-3">
      <a
        href="/accounts/users"
        class="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
      >
        账号管理
      </a>
      {#if isAdmin}
        <button
          on:click={() => openModal()}
          class="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors flex items-center gap-2"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
          </svg>
          新增角色
        </button>
      {/if}
    </div>
  </div>

  {#if !isAdmin}
    <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
      <p class="text-gray-500 text-lg">权限不足</p>
      <p class="text-gray-400 text-sm mt-2">您没有权限查看角色管理，请联系管理员。</p>
    </div>
  {:else}
    <DataTable
      columns={columns}
      data={roles}
      loading={loading}
      searchable={true}
      searchPlaceholder="搜索角色名称、编码..."
      onRowClick={handleRowClick}
    />
  {/if}
</div>

<Modal bind:open={modalOpen} title={editingRole ? '编辑角色' : '新增角色'} size="md">
  <form on:submit|preventDefault={handleSubmit} class="space-y-4">
    <div>
      <label class="block text-sm font-medium text-gray-700 mb-1">角色名称 *</label>
      <input
        type="text"
        bind:value={formData.name}
        required
        class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
      />
    </div>
    <div>
      <label class="block text-sm font-medium text-gray-700 mb-1">角色编码 *</label>
      <select
        bind:value={formData.code}
        required
        class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
      >
        <option value="">请选择角色编码</option>
        {#each roleCodeOptions as opt}
          <option value={opt.value}>{opt.label}（{opt.value}）</option>
        {/each}
      </select>
    </div>
    <div>
      <label class="block text-sm font-medium text-gray-700 mb-1">描述</label>
      <textarea
        bind:value={formData.description}
        rows={3}
        class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
      ></textarea>
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
      {editingRole ? '保存修改' : '创建'}
    </button>
  </div>
</Modal>
