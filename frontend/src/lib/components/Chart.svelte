<script lang="ts">
  import { onMount, onDestroy, tick } from 'svelte';
  import type { ChartData, ChartOptions, Chart as ChartJSType } from 'chart.js';

  export let type: 'line' | 'bar' | 'pie' | 'doughnut' = 'line';
  export let data: ChartData;
  export let options: ChartOptions = {};
  export let height = '300px';

  let canvas: HTMLCanvasElement;
  let ChartJS: any = null;
  let isBrowser = false;

  let _loadPromise: Promise<any> | null = null;
  let _queue: Promise<void> = Promise.resolve();
  let _pendingKey: string | null = null;
  let _chartRef: { instance: ChartJSType | null; lastType: string | null; lastSig: string } = {
    instance: null,
    lastType: null,
    lastSig: ''
  };
  let _destroyed = false;

  $: hasData = !!(
    data &&
    (data.labels?.length ||
      (data.datasets && data.datasets.some((d) => d.data && d.data.length > 0)))
  );

  function dataSignature(d: ChartData | undefined | null): string {
    if (!d) return 'null';
    try {
      return JSON.stringify({
        labels: d.labels,
        datasets: (d.datasets || []).map((ds: any) => ({
          data: ds.data,
          label: ds.label
        }))
      });
    } catch {
      return 'err';
    }
  }

  function renderKey(): string {
    return `${type}|${dataSignature(data)}`;
  }

  async function ensureChartJS(): Promise<any> {
    if (ChartJS) return ChartJS;
    if (_loadPromise) return _loadPromise;
    _loadPromise = (async () => {
      try {
        const chartModule = await import('chart.js');
        const Ctor = chartModule.Chart;

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

        Ctor.register(
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
        ChartJS = Ctor;
        return Ctor;
      } catch (err) {
        console.error('Failed to load Chart.js:', err);
        _loadPromise = null;
        throw err;
      }
    })();
    return _loadPromise;
  }

  function _destroyCurrentChart(Ctor: any) {
    try {
      if (Ctor && canvas) {
        const attached = Ctor.getChart(canvas);
        if (attached) attached.destroy();
      }
    } catch {}
    try {
      if (_chartRef.instance) {
        _chartRef.instance.destroy();
      }
    } catch {}
    _chartRef.instance = null;
  }

  async function _doRender() {
    if (_destroyed || !isBrowser || !canvas || !hasData) {
      return;
    }

    const key = renderKey();
    const [sigType, sigData] = [type, dataSignature(data)];

    const Ctor = await ensureChartJS();
    if (_destroyed || !canvas) return;

    const typeChanged = _chartRef.lastType !== sigType;
    const sigChanged = _chartRef.lastSig !== sigData;
    const needsWork = !_chartRef.instance || typeChanged || sigChanged;

    if (!needsWork) return;

    _destroyCurrentChart(Ctor);

    try {
      const instance = new Ctor(canvas, {
        type: sigType,
        data: data || { labels: [], datasets: [] },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          ...options
        }
      });
      _chartRef.instance = instance;
      _chartRef.lastType = sigType;
      _chartRef.lastSig = sigData;
    } catch (err) {
      console.error('Failed to create chart:', err);
      _chartRef.instance = null;
      _chartRef.lastType = null;
      _chartRef.lastSig = '';
    }
  }

  function scheduleRender() {
    if (_destroyed) return;
    const key = renderKey();
    _queue = _queue.then(async () => {
      if (_destroyed) return;
      _pendingKey = null;
      await _doRender();
    }).catch((err) => {
      console.error('Chart render error:', err);
    });
    void key;
  }

  $: if (isBrowser) {
    scheduleRender();
  }

  onMount(async () => {
    isBrowser = true;
    _destroyed = false;
    await tick();
    scheduleRender();
  });

  onDestroy(() => {
    _destroyed = true;
    _queue.then(() => {
      try {
        if (ChartJS && canvas) {
          const attached = ChartJS.getChart(canvas);
          if (attached) attached.destroy();
        }
      } catch {}
      try {
        if (_chartRef.instance) _chartRef.instance.destroy();
      } catch {}
      _chartRef.instance = null;
      ChartJS = null;
      _loadPromise = null;
    });
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
