<script lang="ts">
  import { onMount } from 'svelte';

  export let columns: { key: string; label: string; render?: (value: any, row: any) => any }[] = [];
  export let data: any[] = [];
  export let loading = false;
  export let searchable = false;
  export let searchPlaceholder = '搜索...';
  export let onRowClick: ((row: any) => void) | undefined = undefined;

  let searchQuery = '';
  let currentPage = 1;
  export let pageSize = 10;

  $: filteredData = data.filter((row) => {
    if (!searchQuery) return true;
    return columns.some((col) => {
      const value = row[col.key];
      return value?.toString().toLowerCase().includes(searchQuery.toLowerCase());
    });
  });

  $: totalPages = Math.ceil(filteredData.length / pageSize);
  $: paginatedData = filteredData.slice((currentPage - 1) * pageSize, currentPage * pageSize);

  function prevPage() {
    if (currentPage > 1) currentPage--;
  }

  function nextPage() {
    if (currentPage < totalPages) currentPage++;
  }

  function goToPage(page: number) {
    currentPage = page;
  }

  $: if (searchQuery) currentPage = 1;
</script>

<div class="bg-white rounded-lg shadow-sm border border-gray-200">
  {#if searchable}
    <div class="p-4 border-b border-gray-200">
      <div class="relative">
        <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
        <input
          type="text"
          bind:value={searchQuery}
          placeholder={searchPlaceholder}
          class="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
        />
      </div>
    </div>
  {/if}

  <div class="overflow-x-auto">
    {#if loading}
      <div class="flex items-center justify-center py-12">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
        <span class="ml-3 text-gray-500">加载中...</span>
      </div>
    {:else if paginatedData.length === 0}
      <div class="text-center py-12 text-gray-500">
        暂无数据
      </div>
    {:else}
      <table class="w-full">
        <thead class="bg-gray-50 border-b border-gray-200">
          <tr>
            {#each columns as col}
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                {col.label}
              </th>
            {/each}
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-200">
          {#each paginatedData as row, rowIdx}
            <tr
              class="hover:bg-gray-50 transition-colors {onRowClick ? 'cursor-pointer' : ''}"
              on:click={() => onRowClick?.(row)}
            >
              {#each columns as col}
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {#if col.render}
                    {@html col.render(row[col.key], row)}
                  {:else}
                    {row[col.key]}
                  {/if}
                </td>
              {/each}
            </tr>
          {/each}
        </tbody>
      </table>
    {/if}
  </div>

  {#if totalPages > 1}
    <div class="px-6 py-4 border-t border-gray-200 flex items-center justify-between">
      <div class="text-sm text-gray-500">
        共 {filteredData.length} 条记录，第 {currentPage} / {totalPages} 页
      </div>
      <div class="flex items-center gap-2">
        <button
          on:click={prevPage}
          disabled={currentPage === 1}
          class="px-3 py-1 rounded border border-gray-300 text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50 transition-colors"
        >
          上一页
        </button>
        {#each Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
          let start = Math.max(1, currentPage - 2);
          if (start + 4 > totalPages) start = Math.max(1, totalPages - 4);
          return start + i;
        }) as page}
          {#if page <= totalPages}
            <button
              on:click={() => goToPage(page)}
              class="px-3 py-1 rounded text-sm transition-colors {currentPage === page
                ? 'bg-primary-600 text-white'
                : 'border border-gray-300 hover:bg-gray-50'}"
            >
              {page}
            </button>
          {/if}
        {/each}
        <button
          on:click={nextPage}
          disabled={currentPage === totalPages}
          class="px-3 py-1 rounded border border-gray-300 text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50 transition-colors"
        >
          下一页
        </button>
      </div>
    </div>
  {/if}
</div>
