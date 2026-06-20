<script lang="ts">
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  import { goto } from '$app/navigation';
  import '../app.css';
  import Layout from '$lib/components/Layout.svelte';
  import { auth } from '$lib/stores/auth';

  const ROLE_PAGE_PERMISSIONS: Record<string, string[]> = {
    admin: ['/', '/sea-areas', '/cages', '/farmers', '/inspection', '/inspection/routes', '/disease', '/mortality', '/analytics', '/accounts/users', '/accounts/roles'],
    inspector: ['/', '/cages', '/inspection', '/inspection/routes', '/disease', '/mortality'],
    technician: ['/', '/cages', '/disease', '/mortality', '/analytics'],
    farmer: ['/', '/cages', '/disease', '/mortality', '/inspection']
  };

  function hasAccessToPath(roleCode: string | null | undefined, isAdminFlag: boolean, path: string): boolean {
    if (isAdminFlag) return true;
    const allowed = ROLE_PAGE_PERMISSIONS[roleCode || ''] || [];
    for (const p of allowed) {
      if (p === path) return true;
      if (p !== '/' && path.startsWith(p + '/')) return true;
    }
    return false;
  }

  $: currentPath = $page.url.pathname;
  $: isLoginPage = currentPath === '/login';
  $: currentUserRole = $auth.user?.role_code || null;
  $: currentIsAdmin = $auth.user?.is_admin || false;

  onMount(() => {
    if (!isLoginPage && !$auth.isAuthenticated) {
      goto('/login');
    }
    if (isLoginPage && $auth.isAuthenticated) {
      goto('/');
    }
  });

  $: if (typeof window !== 'undefined' && !isLoginPage && !$auth.isAuthenticated) {
    goto('/login');
  }

  $: if (typeof window !== 'undefined' && !isLoginPage && $auth.isAuthenticated) {
    if (!hasAccessToPath(currentUserRole, currentIsAdmin, currentPath)) {
      goto('/');
    }
  }
</script>

{#if isLoginPage}
  <slot />
{:else}
  <Layout>
    <slot />
  </Layout>
{/if}
