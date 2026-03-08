let charts = {
    status: null,
    purpose: null,
    courses: null
};

const elegantPalette = [
    'rgba(15, 23, 42, 0.85)',   // Slate 900
    'rgba(245, 158, 11, 0.85)',  // Amber 500
    'rgba(16, 185, 129, 0.85)',  // Emerald 500
    'rgba(99, 102, 241, 0.85)',  // Indigo 500
    'rgba(244, 63, 94, 0.85)',   // Rose 500
    'rgba(6, 182, 212, 0.85)'    // Cyan 500
];

function getGradient(ctx, color) {
    const gradient = ctx.createLinearGradient(0, 0, 400, 0);
    gradient.addColorStop(0, color.replace('0.85', '0.6'));
    gradient.addColorStop(1, color);
    return gradient;
}

function renderCharts(data) {
    const ctxStatus = document.getElementById('chart-status').getContext('2d');
    const ctxPurpose = document.getElementById('chart-purpose').getContext('2d');
    const ctxCourses = document.getElementById('chart-courses').getContext('2d');

    // 1. Chart: Status
    if (charts.status) charts.status.destroy();
    
    const statusGradients = [
        getGradient(ctxStatus, 'rgba(245, 158, 11, 0.85)'), // Amber
        getGradient(ctxStatus, 'rgba(99, 102, 241, 0.85)'), // Indigo
        getGradient(ctxStatus, 'rgba(16, 185, 129, 0.85)')  // Emerald
    ];

    charts.status = new Chart(ctxStatus, {
        type: 'bar',
        plugins: [ChartDataLabels],
        data: {
            labels: Object.keys(data.by_status),
            datasets: [{
                data: Object.values(data.by_status),
                backgroundColor: statusGradients,
                borderRadius: 8,
                barThickness: 50
            }]
        },
        options: {
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                datalabels: {
                    anchor: 'end',
                    align: 'top',
                    color: '#475569',
                    font: { weight: '800', size: 12 },
                    formatter: (value, context) => {
                        const total = context.dataset.data.reduce((a, b) => a + b, 0);
                        return `${value} (${((value/total)*100).toFixed(1)}%)`;
                    }
                }
            },
            layout: { padding: { top: 35 } },
            scales: {
                y: { display: false, beginAtZero: true },
                x: { grid: { display: false }, ticks: { color: '#64748b', font: { weight: 'bold', size: 11 } } }
            }
        }
    });

    // 2. Chart: Purpose
    if (charts.purpose) charts.purpose.destroy();
    const sortedPurpose = Object.entries(data.by_purpose).sort((a, b) => b[1] - a[1]);
    const totalReports = data.total_reports || 1;

    const purposeColorsMap = {
        'Convivencia': 'rgba(16, 185, 129, 0.85)',
        'Académico': 'rgba(99, 102, 241, 0.85)',
        'Psicoafectivo': 'rgba(244, 63, 94, 0.85)',
        'Espiritual': 'rgba(168, 85, 247, 0.85)'
    };

    charts.purpose = new Chart(ctxPurpose, {
        type: 'bar',
        plugins: [ChartDataLabels],
        data: {
            labels: sortedPurpose.map(x => x[0]),
            datasets: [{
                data: sortedPurpose.map(x => x[1]),
                backgroundColor: sortedPurpose.map(x => purposeColorsMap[x[0]] || 'rgba(148, 163, 184, 0.85)'),
                borderRadius: 4,
                barThickness: 30
            }]
        },
        options: {
            indexAxis: 'y',
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                datalabels: {
                    anchor: 'center',
                    align: 'center',
                    color: '#fff',
                    font: { weight: 'bold', size: 11 },
                    formatter: (value) => {
                        const pct = ((value / totalReports) * 100).toFixed(1);
                        return `${value} (${pct}%)`;
                    }
                }
            },
            scales: {
                x: { display: false, beginAtZero: true },
                y: { grid: { display: false }, ticks: { color: '#475569', font: { weight: '700' } } }
            },
            layout: { padding: { left: 10, right: 10, top: 10 } }
        }
    });

    // 3. Chart: Courses
    if (charts.courses) charts.courses.destroy();
    
    // Create special gradient for rankings
    const rankingGradient = ctxCourses.createLinearGradient(0, 0, 800, 0);
    rankingGradient.addColorStop(0, 'rgba(15, 23, 42, 0.05)');
    rankingGradient.addColorStop(1, 'rgba(15, 23, 42, 0.4)');

    charts.courses = new Chart(ctxCourses, {
        type: 'bar',
        plugins: [ChartDataLabels],
        data: {
            labels: Object.keys(data.by_course),
            datasets: [{
                data: Object.values(data.by_course),
                backgroundColor: rankingGradient,
                hoverBackgroundColor: 'rgba(15, 23, 42, 0.8)',
                borderRadius: 6,
                barThickness: 25
            }]
        },
        options: {
            indexAxis: 'y',
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                datalabels: {
                    anchor: 'end',
                    align: 'right',
                    color: '#0f172a',
                    font: { weight: '900', size: 13 },
                    formatter: (value) => value
                }
            },
            layout: { padding: { right: 50 } },
            scales: {
                x: { display: false, beginAtZero: true },
                y: { 
                    type: 'category',
                    grid: { display: false },
                    ticks: { color: '#334155', font: { weight: '800', size: 12 } }
                }
            }
        }
    });
}

// Function to handle filter logic in cascade (Section -> Course)
document.addEventListener('alpine:init', () => {
    // This is handled by Alpine x-model and updateData() in the template itself
});
