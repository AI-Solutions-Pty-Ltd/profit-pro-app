document.addEventListener('DOMContentLoaded', function () {
    fetchFinancialData();
});

async function fetchFinancialData() {
    try {
        const queryParams = window.location.search;
        const response = await fetch('data/' + queryParams);
        const data = await response.json();

        initCharts(data);
    } catch (error) {
        console.error('Error fetching financial data:', error);
    }
}

const commonOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: {
            position: 'top',
            align: 'end',
            labels: {
                boxWidth: 8,
                usePointStyle: true,
                pointStyle: 'circle',
                font: { size: 10, weight: '600' },
                padding: 15
            }
        },
        tooltip: {
            backgroundColor: 'rgba(15, 23, 42, 0.9)',
            padding: 12,
            cornerRadius: 8,
            titleFont: { size: 11, weight: '700' },
            bodyFont: { size: 11 },
            footerFont: { size: 10 },
            callbacks: {
                label: function (context) {
                    let label = context.dataset.label || '';
                    if (label) {
                        label += ': ';
                    }
                    if (context.parsed.y !== null) {
                        label += new Intl.NumberFormat('en-ZA', { style: 'currency', currency: 'ZAR' }).format(context.parsed.y);
                    }
                    return label;
                }
            }
        }
    },
    scales: {
        x: {
            grid: { display: false },
            ticks: {
                font: { size: 9, weight: '500' },
                color: '#94a3b8',
                maxRotation: 0
            }
        },
        y: {
            grid: { color: 'rgba(241, 245, 249, 1)', drawBorder: false },
            ticks: {
                font: { size: 9, weight: '500' },
                color: '#94a3b8',
                padding: 8,
                callback: function (value) {
                    return 'R' + (value / 1000).toFixed(0) + 'k';
                }
            }
        }
    },
    elements: {
        point: { radius: 0, hoverRadius: 5 },
        line: { tension: 0.3 }
    }
};

function initCharts(data) {
    const labels = data.labels;
    const ds = data.datasets;

    // 1. Revenue vs Cost Trend
    const revCtx = document.getElementById('revenueCostChart').getContext('2d');
    new Chart(revCtx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Actual Revenue',
                    data: ds.revenue_actual,
                    backgroundColor: 'rgba(79, 70, 229, 0.8)',
                    borderRadius: 4,
                },
                {
                    label: 'Actual Cost',
                    data: ds.cost_actual,
                    backgroundColor: 'rgba(244, 63, 94, 0.8)',
                    borderRadius: 4,
                },
                {
                    label: 'Gross Profit',
                    data: ds.profit_actual,
                    type: 'line',
                    borderColor: '#10b981',
                    borderWidth: 3,
                    fill: false,
                    pointRadius: 2,
                    pointBackgroundColor: '#fff'
                }
            ]
        },
        options: {
            ...commonOptions,
            plugins: {
                ...commonOptions.plugins,
                tooltip: {
                    ...commonOptions.plugins.tooltip,
                    mode: 'index',
                    intersect: false
                }
            }
        }
    });

    // 2. Profitability Trend (Multi-series)
    const profitCtx = document.getElementById('netProfitChart').getContext('2d');
    new Chart(profitCtx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Gross Profit',
                    data: ds.gross_profit_actual,
                    backgroundColor: 'rgba(59, 130, 246, 0.7)',
                    borderRadius: 4,
                },
                {
                    label: 'Operating Expense',
                    data: ds.opex_actual,
                    backgroundColor: 'rgba(244, 63, 94, 0.7)',
                    borderRadius: 4,
                },
                {
                    label: 'Net Profit',
                    data: ds.profit_actual,
                    type: 'line',
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    fill: true,
                    borderWidth: 3,
                    pointRadius: 3,
                    pointBackgroundColor: '#fff',
                    pointBorderWidth: 2,
                    tension: 0.4
                }
            ]
        },
        options: {
            ...commonOptions,
            plugins: {
                ...commonOptions.plugins,
                tooltip: {
                    ...commonOptions.plugins.tooltip,
                    mode: 'index',
                    intersect: false
                }
            }
        }
    });

    // 3. Cost Composition (Donut)
    const compositionCtx = document.getElementById('costCompositionChart').getContext('2d');
    const compositionTotal = ds.cost_breakdown.reduce((a, b) => a + b, 0);

    new Chart(compositionCtx, {
        type: 'doughnut',
        data: {
            labels: ['Materials', 'Labour', 'Subcon', 'Plant', 'Overheads'],
            datasets: [{
                data: ds.cost_breakdown,
                backgroundColor: ['#6366f1', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'],
                borderWidth: 0,
                cutout: '75%'
            }]
        },
        options: {
            ...commonOptions,
            scales: { x: { display: false }, y: { display: false } },
            plugins: {
                ...commonOptions.plugins,
                legend: {
                    position: 'bottom',
                    align: 'center',
                    labels: {
                        ...commonOptions.plugins.legend.labels,
                        generateLabels: function (chart) {
                            const data = chart.data;
                            if (data.labels.length && data.datasets.length) {
                                return data.labels.map((label, i) => {
                                    const value = data.datasets[0].data[i];
                                    const percentage = compositionTotal > 0 ? ((value / compositionTotal) * 100).toFixed(0) : 0;
                                    return {
                                        text: `${label} (${percentage}%)`,
                                        fillStyle: data.datasets[0].backgroundColor[i],
                                        strokeStyle: data.datasets[0].backgroundColor[i],
                                        lineWidth: 0,
                                        hidden: isNaN(data.datasets[0].data[i]) || chart.getDatasetMeta(0).data[i].hidden,
                                        index: i
                                    };
                                });
                            }
                            return [];
                        }
                    }
                },
                tooltip: {
                    ...commonOptions.plugins.tooltip,
                    callbacks: {
                        label: function (context) {
                            const value = context.parsed;
                            const percentage = compositionTotal > 0 ? ((value / compositionTotal) * 100).toFixed(1) : 0;
                            return `${context.label}: R${value.toLocaleString()} (${percentage}%)`;
                        }
                    }
                }
            }
        },
        plugins: [{
            id: 'centerText',
            beforeDraw: function (chart) {
                const width = chart.width,
                    height = chart.height,
                    ctx = chart.ctx;

                ctx.restore();
                const fontSize = (height / 220).toFixed(2); // Reduced from 150
                ctx.font = `600 ${fontSize}em Inter, sans-serif`;
                ctx.textBaseline = "middle";
                ctx.fillStyle = "#64748b"; // Softer color

                const text = "Total Cost",
                    textX = Math.round((width - ctx.measureText(text).width) / 2),
                    textY = (height / 2) - 12;

                ctx.fillText(text, textX, textY);

                const value = "R" + compositionTotal.toLocaleString(),
                    valX = Math.round((width - ctx.measureText(value).width) / 2),
                    valY = (height / 2) + 12;

                ctx.font = `bold ${(height / 180).toFixed(2)}em Inter, sans-serif`; // Reduced from 120
                ctx.fillStyle = "#1e293b";
                ctx.fillText(value, valX, valY);
                ctx.save();
            }
        }]
    });

    // 4. OpEx Breakdown (Pie)
    const opexCtx = document.getElementById('opexBreakdownChart').getContext('2d');
    new Chart(opexCtx, {
        type: 'pie',
        data: {
            labels: ['Overheads', 'Journal Entries'],
            datasets: [{
                data: ds.opex_breakdown,
                backgroundColor: ['#6366f1', '#818cf8'],
                borderWidth: 0
            }]
        },
        options: {
            ...commonOptions,
            scales: { x: { display: false }, y: { display: false } },
            plugins: {
                ...commonOptions.plugins,
                legend: { position: 'right', align: 'center' }
            }
        }
    });
}
