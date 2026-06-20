<script lang="ts">
  import { auth } from '$lib/stores/auth';

  let userMenuOpen = false;

  function handleLogout() {
    auth.logout();
    userMenuOpen = false;
  }
</script>

<header class="bg-white shadow-sm border-b border-gray-200 sticky top-0 z-20">
  <div class="flex items-center justify-between px-6 py-4">
    <div class="flex items-center gap-4">
      <h2 class="text-xl font-semibold text-gray-800">
        <slot name="title">首页</slot>
      </h2>
    </div>

    <div class="flex items-center gap-4">
      <button class="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
        </svg>
      </button>

      <div class="relative">
        <button
          on:click={() => (userMenuOpen = !userMenuOpen)}
          class="flex items-center gap-3 p-2 hover:bg-gray-100 rounded-lg transition-colors"
        >
          <div class="w-8 h-8 bg-primary-500 rounded-full flex items-center justify-center text-white font-semibold">
            {$auth.user?.username?.[0]?.toUpperCase() || 'U'}
          </div>
          <span class="text-gray-700">{$auth.user?.username || '用户'}</span>
          <svg class="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
          </svg>
        </button>

        {#if userMenuOpen}
          <div class="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-200 py-1">
            <a href="/profile" class="block px-4 py-2 text-gray-700 hover:bg-gray-100">个人中心</a>
            <a href="/settings" class="block px-4 py-2 text-gray-700 hover:bg-gray-100">设置</a>
            <hr class="my-1 border-gray-200" />
            <button
              on:click={handleLogout}
              class="w-full text-left px-4 py-2 text-red-600 hover:bg-gray-100"
            >
              退出登录
            </button>
          </div>
        {/if}
      </div>
    </div>
  </div>
</header>

{#if userMenuOpen}
  <div class="fixed inset-0 z-10" on:click={() => (userMenuOpen = false)} />
{/if}
