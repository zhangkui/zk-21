<script lang="ts">
  import { page } from '$app/stores';
  import { auth } from '$lib/stores/auth';

  const ROLE_MENU_PERMISSIONS: Record<string, string[]> = {
    admin: ['/', '/sea-areas', '/cages', '/farmers', '/inspection', '/inspection/routes', '/disease', '/mortality', '/analytics'],
    inspector: ['/', '/cages', '/inspection', '/inspection/routes', '/disease', '/mortality'],
    technician: ['/', '/cages', '/disease', '/mortality', '/analytics'],
    farmer: ['/', '/cages', '/disease', '/mortality', '/inspection']
  };

  const allMenuItems = [
    { path: '/', label: '仪表板', icon: '📊' },
    { path: '/sea-areas', label: '海区管理', icon: '🌊' },
    { path: '/cages', label: '网箱档案', icon: '🗑️' },
    { path: '/farmers', label: '养殖户管理', icon: '👤' },
    { path: '/inspection', label: '巡检管理', icon: '🔍' },
    { path: '/inspection/routes', label: '巡检路线', icon: '🗺️' },
    { path: '/disease', label: '病害上报', icon: '🦠' },
    { path: '/mortality', label: '死亡上报', icon: '⚠️' },
    { path: '/analytics', label: '统计分析', icon: '📈' }
  ];

  const adminMenuItems = [
    { path: '/accounts/users', label: '账号管理', icon: '👥' },
    { path: '/accounts/roles', label: '角色管理', icon: '🔑' }
  ];

  function isMenuActive(currentPath: string, menuPath: string): boolean {
    if (menuPath === '/') {
      return currentPath === '/';
    }
    if (menuPath === '/inspection') {
      return currentPath === '/inspection' || currentPath.startsWith('/inspection/') && !currentPath.startsWith('/inspection/routes');
    }
    if (menuPath === '/inspection/routes') {
      return currentPath === '/inspection/routes' || currentPath.startsWith('/inspection/routes/');
    }
    return currentPath === menuPath || currentPath.startsWith(menuPath + '/');
  }

  function filterMenuByRole(roleCode: string | null | undefined, isAdminFlag: boolean) {
    if (isAdminFlag) return allMenuItems;
    const allowed = ROLE_MENU_PERMISSIONS[roleCode || ''] || [];
    return allMenuItems.filter((item) => allowed.includes(item.path));
  }

  $: currentPath = $page.url.pathname;
  $: isAdmin = $auth.user?.is_admin || $auth.user?.is_superuser || false;
  $: userRoleCode = $auth.user?.role_code || null;
  $: menuItems = filterMenuByRole(userRoleCode, isAdmin);
</script>

<aside class="w-64 bg-slate-800 text-white h-screen flex flex-col fixed left-0 top-0 z-30">
  <div class="p-4 border-b border-slate-700">
    <h1 class="text-xl font-bold flex items-center gap-2">
      <span class="text-2xl">🐟</span>
      水产养殖智慧管理平台
    </h1>
  </div>

  <nav class="flex-1 p-4 space-y-1 overflow-y-auto">
    {#each menuItems as item}
      <a
        href={item.path}
        class="flex items-center gap-3 px-4 py-3 rounded-lg transition-colors {isMenuActive(currentPath, item.path)
          ? 'bg-primary-600 text-white'
          : 'text-slate-300 hover:bg-slate-700 hover:text-white'}"
      >
        <span class="text-xl">{item.icon}</span>
        <span>{item.label}</span>
      </a>
    {/each}

    {#if isAdmin}
      <div class="pt-4 pb-2 px-4 text-xs text-slate-500 uppercase tracking-wider">系统管理</div>
      {#each adminMenuItems as item}
        <a
          href={item.path}
          class="flex items-center gap-3 px-4 py-3 rounded-lg transition-colors {isMenuActive(currentPath, item.path)
            ? 'bg-primary-600 text-white'
            : 'text-slate-300 hover:bg-slate-700 hover:text-white'}"
        >
          <span class="text-xl">{item.icon}</span>
          <span>{item.label}</span>
        </a>
      {/each}
    {/if}
  </nav>

  <div class="p-4 border-t border-slate-700">
    <div class="text-sm text-slate-400 text-center">
      © 2026 智慧养殖管理系统
    </div>
  </div>
</aside>
