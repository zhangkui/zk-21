<script lang="ts">
  export let title: string;
  export let value: number | string;
  export let icon: string;
  export let trend: number | undefined = undefined;
  export let color: 'blue' | 'green' | 'yellow' | 'red' = 'blue';

  const colorClasses: Record<string, { bg: string; text: string; iconBg: string }> = {
    blue: { bg: 'bg-blue-50', text: 'text-blue-600', iconBg: 'bg-blue-100' },
    green: { bg: 'bg-green-50', text: 'text-green-600', iconBg: 'bg-green-100' },
    yellow: { bg: 'bg-yellow-50', text: 'text-yellow-600', iconBg: 'bg-yellow-100' },
    red: { bg: 'bg-red-50', text: 'text-red-600', iconBg: 'bg-red-100' }
  };

  $: classes = colorClasses[color];
</script>

<div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
  <div class="flex items-center justify-between">
    <div>
      <p class="text-sm font-medium text-gray-500">{title}</p>
      <p class="text-3xl font-bold text-gray-900 mt-2">{value}</p>
      {#if trend !== undefined}
        <p class="text-sm mt-2 {trend >= 0 ? 'text-green-600' : 'text-red-600'}">
          {trend >= 0 ? '↑' : '↓'} {Math.abs(trend)}% 较上月
        </p>
      {/if}
    </div>
    <div class="w-14 h-14 {classes.iconBg} rounded-xl flex items-center justify-center">
      <span class="text-3xl">{icon}</span>
    </div>
  </div>
</div>
