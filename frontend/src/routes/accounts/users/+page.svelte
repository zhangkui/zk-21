<script lang="ts">
  import { onMount } from 'svelte';
  import DataTable from '$lib/components/DataTable.svelte';
  import Modal from '$lib/components/Modal.svelte';
  import { userApi, roleApi } from '$lib/stores/api';
  import { auth } from '$lib/stores/auth';
  import type { User, Role } from '$lib/types';

  let users: User[] = [];
  let roles: Role[] = [];
  let loading = true;
  let errorMsg: string | null = null;
  let modalOpen = false;
  let editingUser: Partial<User> | null = null;

  let formData = {
    username: '',
    email: '',
    password: '',
    password2: '',
    role_id: null as number | null,
    phone: '',
    is_active: true,
    is_staff: false
  };

  $: isAdmin = $auth.user?.is_admin || false;

  const columns = [
    { key: 'id', label: 'ID' },
    { key: 'username', label: '用户名' },
    {
      key: 'display_name',
      label: '显示名称',
      render: (val: string) => val || '<span class="text-gray-400">-</span>'
    },
    {
      key: 'role_name',
      label: '角色',
      render: (val: string) =>
        val
          ? `<span class="inline-block px-2 py-0.5 text-xs font-medium bg-blue-100 text-blue-800 rounded-full">${val}</span>`
          : '<span class="text-gray-400">-</span>'
    },
    {
      key: 'profile_phone',
      label: '手机号',
      render: (val: string) => val || '<span class="text-gray-400">-</span>'
    },
    {
      key: 'is_active',
      label: '状态',
      render: (val: boolean) =>
        val
          ? '<span class="px-2 py-1 text-xs font-medium bg-green-100 text-green-800 rounded-full">启用</span>'
          : '<span class="px-2 py-1 text-xs font-medium bg-gray-100 text-gray-800 rounded-full">禁用</span>'
    },
    {
      key: 'is_admin',
      label: '管理员',
      render: (val: boolean) =>
        val
          ? '<span class="px-2 py-1 text-xs font-medium bg-purple-100 text-purple-800 rounded-full">是</span>'
          : '<span class="px-2 py-1 text-xs font-medium bg-gray-100 text-gray-800 rounded-full">否</span>'
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
      const [usersRes, rolesRes] = await Promise.all([
        userApi.getAll(),
        roleApi.getAll()
      ]);
      users = usersRes.data.results;
      roles = rolesRes.data.results;
    } catch (err) {
      console.error('Failed to load data:', err);
      errorMsg = '加载数据失败，请稍后重试';
    } finally {
      loading = false;
    }
  }

  function resetForm() {
    formData = {
      username: '',
      email: '',
      password: '',
      password2: '',
      role_id: null,
      phone: '',
      is_active: true,
      is_staff: false
    };
  }

  function openModal(user?: User) {
    if (user) {
      editingUser = user;
      formData = {
        username: user.username || '',
        email: user.email || '',
        password: '',
        password2: '',
        role_id: user.role_id ?? user.role?.id ?? null,
        phone: user.profile_phone || user.phone || '',
        is_active: user.is_active ?? true,
        is_staff: user.is_staff ?? false
      };
    } else {
      editingUser = null;
      resetForm();
    }
    modalOpen = true;
  }

  async function handleSubmit() {
    if (!editingUser && formData.password !== formData.password2) {
      alert('两次输入的密码不一致');
      return;
    }
    if (editingUser && formData.password && formData.password !== formData.password2) {
      alert('两次输入的密码不一致');
      return;
    }

    try {
      if (editingUser?.id) {
        const updateData: Record<string, any> = {
          username: formData.username,
          email: formData.email,
          is_active: formData.is_active,
          is_staff: formData.is_staff,
          role_id: formData.role_id,
          phone: formData.phone
        };
        if (formData.password) {
          updateData.password = formData.password;
          updateData.password2 = formData.password2;
        }
        await userApi.update(editingUser.id, updateData);
      } else {
        await userApi.create({
          username: formData.username,
          email: formData.email,
          password: formData.password,
          password2: formData.password2,
          is_active: formData.is_active,
          is_staff: formData.is_staff,
          role_id: formData.role_id,
          phone: formData.phone
        });
      }
      modalOpen = false;
      loadData();
    } catch (error: any) {
      console.error('Failed to save user:', error);
      const detail = error?.response?.data;
      let msg = '保存失败';
      if (typeof detail === 'string') {
        msg = detail;
      } else if (detail && typeof detail === 'object') {
        msg = Object.entries(detail)
          .map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(', ') : v}`)
          .join('；');
      }
      alert(msg);
    }
  }

  async function handleDelete(id: number) {
    if (confirm('确定要删除这个账号吗？')) {
      try {
        await userApi.delete(id);
        loadData();
      } catch (error) {
        console.error('Failed to delete user:', error);
        alert('删除失败');
      }
    }
  }

  function handleRowClick(row: User) {
    const target = event?.target as HTMLElement;
    if (target.textContent === '编辑') {
      openModal(row);
    } else if (target.textContent === '删除') {
      handleDelete(row.id);
    }
  }

  onMount(() => {
    if (isAdmin) {
      loadData();
    } else {
      loading = false;
    }
  });
</script>

{#if !isAdmin}
  <div class="flex items-center justify-center py-20">
    <div class="text-center">
      <svg class="w-16 h-16 mx-auto mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
      </svg>
      <p class="text-lg font-medium text-gray-700">权限不足</p>
      <p class="text-sm text-gray-500 mt-1">您没有权限访问此页面</p>
    </div>
  </div>
{:else}
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <h2 class="text-2xl font-bold text-gray-900">账号管理</h2>
      <div class="flex items-center gap-3">
        <a
          href="/accounts/roles"
          class="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors flex items-center gap-2"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
          </svg>
          角色管理
        </a>
        <button
          on:click={() => openModal()}
          class="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors flex items-center gap-2"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
          </svg>
          新增账号
        </button>
      </div>
    </div>

    {#if errorMsg}
      <div class="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
        {errorMsg}
      </div>
    {/if}

    <DataTable
      columns={columns}
      data={users}
      {loading}
      searchable={true}
      searchPlaceholder="搜索用户名、手机号..."
      onRowClick={handleRowClick}
    />
  </div>

  <Modal open={modalOpen} title={editingUser ? '编辑账号' : '新增账号'} size="lg">
    <form on:submit|preventDefault={handleSubmit} class="space-y-4">
      <div class="grid grid-cols-2 gap-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">用户名 *</label>
          <input
            type="text"
            bind:value={formData.username}
            required
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
          />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">邮箱</label>
          <input
            type="email"
            bind:value={formData.email}
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
          />
        </div>
      </div>

      <div class="grid grid-cols-2 gap-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">
            密码 {editingUser ? '（留空则不修改）' : '*'}
          </label>
          <input
            type="password"
            bind:value={formData.password}
            required={!editingUser}
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
          />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">
            确认密码 {editingUser ? '（留空则不修改）' : '*'}
          </label>
          <input
            type="password"
            bind:value={formData.password2}
            required={!editingUser}
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
          />
        </div>
      </div>

      <div class="grid grid-cols-2 gap-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">角色</label>
          <select
            bind:value={formData.role_id}
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
          >
            <option value={null}>请选择角色</option>
            {#each roles as role}
              <option value={role.id}>{role.name}</option>
            {/each}
          </select>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">手机号</label>
          <input
            type="tel"
            bind:value={formData.phone}
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
          />
        </div>
      </div>

      <div class="flex items-center gap-6 pt-2">
        <label class="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            bind:checked={formData.is_active}
            class="w-4 h-4 text-primary-600 rounded focus:ring-primary-500"
          />
          <span class="text-sm font-medium text-gray-700">启用账号</span>
        </label>
        <label class="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            bind:checked={formData.is_staff}
            class="w-4 h-4 text-primary-600 rounded focus:ring-primary-500"
          />
          <span class="text-sm font-medium text-gray-700">员工身份</span>
        </label>
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
        {editingUser ? '保存修改' : '创建'}
      </button>
    </div>
  </Modal>
{/if}
