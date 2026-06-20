<script lang="ts">
  export let open = false;
  export let title = '';
  export let size: 'sm' | 'md' | 'lg' | 'xl' | '2xl' = 'md';

  const sizeClasses: Record<string, string> = {
    sm: 'max-w-sm',
    md: 'max-w-md',
    lg: 'max-w-lg',
    xl: 'max-w-3xl',
    '2xl': 'max-w-5xl'
  };

  function close() {
    open = false;
  }

  function handleBackdropClick(e: MouseEvent) {
    if ((e.target as HTMLElement).dataset.modal === 'backdrop') {
      close();
    }
  }

  export { close };
</script>

{#if open}
  <div
    data-modal="backdrop"
    class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 p-4"
    on:click={handleBackdropClick}
  >
    <div class="bg-white rounded-xl shadow-2xl w-full {sizeClasses[size]} max-h-[90vh] flex flex-col">
      <div class="flex items-center justify-between px-6 py-4 border-b border-gray-200">
        <h3 class="text-lg font-semibold text-gray-900">{title}</h3>
        <button
          on:click={close}
          class="text-gray-400 hover:text-gray-600 transition-colors"
        >
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <div class="flex-1 overflow-y-auto p-6">
        <slot />
      </div>

      {#if $$slots.footer}
        <div class="px-6 py-4 border-t border-gray-200 flex justify-end gap-3">
          <slot name="footer" />
        </div>
      {/if}
    </div>
  </div>
{/if}
