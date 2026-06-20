<script lang="ts">
  import Sidebar from './Sidebar.svelte';
  import Navbar from './Navbar.svelte';
</script>

<div class="flex min-h-screen bg-gray-50">
  <Sidebar />

  <div class="flex-1 ml-64 flex flex-col">
    <Navbar>
      <slot name="title" />
    </Navbar>

    <main class="flex-1 p-6 overflow-auto">
      <slot />
    </main>
  </div>
</div>
