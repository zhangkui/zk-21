<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import type { ChartData, ChartOptions, Chart as ChartJSType } from 'chart.js';

  export let type: 'line' | 'bar' | 'pie' | 'doughnut' = 'line';
  export let data: ChartData;
  export let options: ChartOptions = {};
  export let height = '300px';

  let canvas: HTMLCanvasElement;
  let chart: ChartJSType | null = null;
  let ChartJS: any = null;
  let isBrowser = false;

  async function createChart() {
    if (!canvas || !ChartJS) return;
    
    if (chart) {
      chart.destroy();
    }
    
    chart = new ChartJS(canvas, {
      type,
      data,
      options: {
        responsive: true,
        maintainAspectRatio: false,
        ...options
      }
    });
  }

  $: if (isBrowser && chart && data) {
    chart.data = data;
    chart.update();
  }

  onMount(async () => {
    isBrowser = true;
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
    
    createChart();
  });

  onDestroy(() => {
    if (chart) {
      chart.destroy();
      chart = null;
    }
  });
</script>

<div style="height: {height};">
  <canvas bind:this={canvas}></canvas>
</div>
