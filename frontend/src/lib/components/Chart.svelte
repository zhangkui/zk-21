<script lang="ts">
  import { onMount, onDestroy, tick, beforeUpdate } from 'svelte';
  import type { ChartData, ChartOptions, Chart as ChartJSType } from 'chart.js';

  export let type: 'line' | 'bar' | 'pie' | 'doughnut' = 'line';
  export let data: ChartData;
  export let options: ChartOptions = {};
  export let height = '300px';

  let canvas: HTMLCanvasElement;
  let chart: ChartJSType | null = null;
  let ChartJS: any = null;
  let isBrowser = false;
  let lastType: string | null = null;
  let lastDataSig = '';
  let _busy = false;
  let _pending = false;

  $: hasData = !!(
    data &&
    (data.labels?.length ||
      (data.datasets && data.datasets.some((d) => d.data && d.data.length > 0)))
  );

  function dataSignature(d: ChartData | undefined | null): string {
    if (!d) return '';
    try {
      return JSON.stringify({
        labels: d.labels,
        datasets: (d.datasets || []).map((ds: any) => ({
          data: ds.data,
          label: ds.label
        }))
      });
    } catch {
      return '';
    }
  }

  async function ensureChartJS() {
    if (ChartJS) return true;
    if (_busy && !ChartJS) return false;
    _busy = true;
    try {
      const chartModule = await import('chart.js');
      ChartJS = chartModule.Chart;

      const {
        CategoryScale,
        LinearScale,
        PointElement,
        LineElement,
        BarElement,
        Title,
        Tooltip,
        Legend,
        ArcElement
      } = chartModule;

      ChartJS.register(
        CategoryScale,
        LinearScale,
        PointElement,
        LineElement,
        BarElement,
        Title,
        Tooltip,
        Legend,
        ArcElement
      );
      return true;
    } catch (err) {
      console.error('Failed to load Chart.js:', err);
      return false;
    } finally {
      _busy = false;
    }
  }

  async function createOrUpdateChart() {
    if (!isBrowser || !canvas) {
      _pending = true;
      return;
    }
    if (_busy) {
      _pending = true;
      return;
    }
    const ready = await ensureChartJS();
    if (!ready) {
      _pending = true;
      return;
    }
    if (!canvas) return;

    const sig = dataSignature(data);
    const typeChanged = lastType !== type;
    const dataChanged = sig !== lastDataSig;

    if (!typeChanged && !dataChanged && chart) return;

    const needCreate = !chart || typeChanged;
    if (needCreate) {
      if (chart) {
        try {
          chart.destroy();
        } catch {}
        chart = null;
      }
      try {
        chart = new ChartJS(canvas, {
          type,
          data: data || { labels: [], datasets: [] },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            ...options
          }
        });
        lastType = type;
        lastDataSig = sig;
      } catch (err) {
        console.error('Failed to create chart:', err);
      }
    } else if (chart && data) {
      try {
        chart.data.labels = data.labels || [];
        chart.data.datasets = (data.datasets || []).map((ds) => ({ ...ds }));
        chart.options = {
          responsive: true,
          maintainAspectRatio: false,
          ...options
        };
        chart.update();
        lastDataSig = sig;
      } catch (err) {
        console.error('Failed to update chart:', err);
      }
    }

    if (_pending) {
      _pending = false;
      createOrUpdateChart();
    }
  }

  $: if (isBrowser && hasData) {
    createOrUpdateChart();
  }

  $: if (isBrowser && type && lastType !== type) {
    createOrUpdateChart();
  }

  onMount(async () => {
    isBrowser = true;
    await tick();
    await createOrUpdateChart();
  });

  beforeUpdate(async () => {
    if (isBrowser && !chart && canvas && hasData) {
      await createOrUpdateChart();
    }
  });

  onDestroy(() => {
    if (chart) {
      try {
        chart.destroy();
      } catch {}
      chart = null;
    }
    ChartJS = null;
  });
</script>

<div style="height: {height};" class="w-full relative">
  <canvas bind:this={canvas}></canvas>
  {#if !hasData}
    <div class="absolute inset-0 flex items-center justify-center bg-white/70 text-sm text-gray-500">
      暂无数据
    </div>
  {/if}
</div>
