<script>
  import { onMount } from 'svelte';
  import { Chart, registerables } from 'chart.js';
  
  Chart.register(...registerables);
  
  export let chartData;
  let canvas;
  let chartInstance;
  
  onMount(() => {
    if (!canvas || !chartData) return;
    
    const labels = chartData.data.map(d => d.label);
    const dataValues = chartData.data.map(d => d.value);
    
    // Default to Elfaria gold colors
    const bgColor = 'rgba(201, 168, 76, 0.6)';
    const borderColor = 'rgba(201, 168, 76, 1)';
    
    // Rich color palette for pie charts
    const pieColors = [
      '#c9a84c', '#8ab5b0', '#c8b8c8', '#b8bcc0', '#5a4f47',
      '#e8d5a0', '#8aabb8', '#ddd0dd', '#d5d8dc', '#2a241e'
    ];
    
    const config = {
      type: chartData.chart_type || 'bar',
      data: {
        labels: labels,
        datasets: [{
          label: chartData.y_label || 'Value',
          data: dataValues,
          backgroundColor: chartData.chart_type === 'pie' ? pieColors : bgColor,
          borderColor: chartData.chart_type === 'pie' ? '#fcf9f5' : borderColor,
          borderWidth: 1
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          title: {
            display: !!chartData.title,
            text: chartData.title,
            color: '#2a241e',
            font: { family: 'Quicksand', size: 16 }
          },
          legend: {
            display: chartData.chart_type === 'pie'
          }
        },
        scales: chartData.chart_type !== 'pie' ? {
          x: {
            title: { display: !!chartData.x_label, text: chartData.x_label }
          },
          y: {
            title: { display: !!chartData.y_label, text: chartData.y_label },
            beginAtZero: true
          }
        } : {}
      }
    };
    
    chartInstance = new Chart(canvas, config);
    
    return () => {
      if (chartInstance) chartInstance.destroy();
    };
  });
</script>

<div class="chart-container">
  <canvas bind:this={canvas}></canvas>
</div>

<style>
  .chart-container {
    width: 100%;
    height: 300px;
    margin: 16px 0;
    padding: 16px;
    background: var(--elf-cream, #ede6dc);
    border: 1px solid var(--elf-border, #ddd0c4);
    border-radius: 16px;
  }
</style>
