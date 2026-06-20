<script lang="ts">
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  import { goto } from '$app/navigation';
  import '../app.css';
  import Layout from '$lib/components/Layout.svelte';
  import { auth } from '$lib/stores/auth';

  $: currentPath = $page.url.pathname;
  $: isLoginPage = currentPath === '/login';

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
</script>

{#if isLoginPage}
  <slot />
{:else}
  <Layout>
    <slot />
  </Layout>
{/if}
