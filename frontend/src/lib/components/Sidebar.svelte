<script lang="ts">
  import { page } from '$app/stores';

  const menuItems = [
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

  $: currentPath = $page.url.pathname;
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
        class="flex items-center gap-3 px-4 py-3 rounded-lg transition-colors {currentPath === item.path ||
          (item.path !== '/' && currentPath.startsWith(item.path))
          ? 'bg-primary-600 text-white'
          : 'text-slate-300 hover:bg-slate-700 hover:text-white'}"
      >
        <span class="text-xl">{item.icon}</span>
        <span>{item.label}</span>
      </a>
    {/each}
  </nav>

  <div class="p-4 border-t border-slate-700">
    <div class="text-sm text-slate-400 text-center">
      © 2026 智慧养殖管理系统
    </div>
  </div>
</aside>
