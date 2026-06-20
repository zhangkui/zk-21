<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { auth } from '$lib/stores/auth';
  import { authApi } from '$lib/stores/api';

  let username = '';
  let password = '';
  let errorMsg = '';
  let loading = false;

  onMount(() => {
    if ($auth.isAuthenticated) {
      goto('/');
    }
  });

  async function handleLogin() {
    errorMsg = '';
    loading = true;
    try {
      const res = await authApi.login({ username, password });
      auth.login(res.data.user, res.data.token);
      goto('/');
    } catch (err: any) {
      if (err.response?.data?.error) {
        errorMsg = err.response.data.error;
      } else if (err.response?.data?.detail) {
        errorMsg = err.response.data.detail;
      } else {
        errorMsg = '登录失败，请检查网络或服务器状态';
      }
    } finally {
      loading = false;
    }
  }
</script>

<div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-800 via-slate-900 to-blue-900 px-4">
  <div class="max-w-md w-full">
    <div class="text-center mb-8">
      <div class="text-6xl mb-3">🐟</div>
      <h1 class="text-3xl font-bold text-white">水产养殖智慧管理平台</h1>
      <p class="text-slate-400 mt-2">请登录您的账号</p>
    </div>

    <div class="bg-white rounded-2xl shadow-2xl p-8">
      <form on:submit|preventDefault={handleLogin} class="space-y-5">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">用户名</label>
          <input
            type="text"
            bind:value={username}
            required
            placeholder="请输入用户名"
            class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">密码</label>
          <input
            type="password"
            bind:value={password}
            required
            placeholder="请输入密码"
            class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition"
          />
        </div>

        {#if errorMsg}
          <div class="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-lg text-sm">
            {errorMsg}
          </div>
        {/if}

        <button
          type="submit"
          disabled={loading}
          class="w-full py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? '登录中...' : '登录'}
        </button>
      </form>

      <div class="mt-6 pt-6 border-t border-gray-200">
        <p class="text-sm text-gray-500 text-center mb-3">默认测试账号</p>
        <div class="space-y-2 text-sm">
          <div class="flex justify-between items-center bg-slate-50 px-3 py-2 rounded">
            <span class="text-gray-600">管理员</span>
            <code class="text-primary-600 font-mono">admin / admin123456</code>
          </div>
          <div class="flex justify-between items-center bg-slate-50 px-3 py-2 rounded">
            <span class="text-gray-600">巡检员</span>
            <code class="text-primary-600 font-mono">inspector_wang / 123456</code>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>
