document.addEventListener('DOMContentLoaded', () => {
    loadAnalyticsData();
});

let charts = {}; // Store chart instances to destroy before re-rendering

async function loadAnalyticsData() {
    try {
        const response = await fetch('/api/stats/analytics');
        if (!response.ok) throw new Error("Failed to fetch analytics");
        const data = await response.json();

        // 1. Update KPIs
        document.getElementById('kpi-total-reports').textContent = data.total_reports;
        document.getElementById('kpi-total-students').textContent = data.total_students;

        // 2. Render Charts
        renderStatusChart(data.by_status);
        renderPurposeChart(data.by_purpose);
        renderCoursesChart(data.by_course);
        renderStatusPieChart(data.by_status);

        // 3. Render Table
        renderRankingTable(data.student_ranking);

    } catch (error) {
        console.error("Error loading analytics:", error);
    }
}

function renderStatusChart(statusData) {
    const ctx = document.getElementById('chartStatus').getContext('2d');
    const labels = Object.keys(statusData);
    const values = Object.values(statusData);

    if (charts['status']) charts['status'].destroy();

    charts['status'] = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Reportes',
                data: values,
                backgroundColor: ['#fbbf24', '#10b981', '#ef4444'], // Gold, Emerald, Red (approx)
                borderRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: { y: { beginAtZero: true } }
        }
    });
}

function renderPurposeChart(purposeData) {
    const ctx = document.getElementById('chartPurpose').getContext('2d');
    const labels = Object.keys(purposeData);
    const values = Object.values(purposeData);

    if (charts['purpose']) charts['purpose'].destroy();

    charts['purpose'] = new Chart(ctx, {
        type: 'bar', // Horizontal bar is type: 'bar' with indexAxis: 'y' in Chart.js v3+
        data: {
            labels: labels,
            datasets: [{
                label: 'Reportes',
                data: values,
                backgroundColor: '#1e3a8a', // Dark Blue
                borderRadius: 4
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: { x: { beginAtZero: true } }
        }
    });
}

function renderCoursesChart(courseData) {
    const ctx = document.getElementById('chartCourses').getContext('2d');
    // Sort by count descending
    const sorted = Object.entries(courseData).sort((a,b) => b[1] - a[1]);
    const labels = sorted.map(k => k[0]);
    const values = sorted.map(v => v[1]);

    if (charts['courses']) charts['courses'].destroy();

    charts['courses'] = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Reportes',
                data: values,
                backgroundColor: '#f59e0b', // Amber/Gold
                borderRadius: 4
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: { x: { beginAtZero: true } }
        }
    });
}

function renderStatusPieChart(statusData) {
    const ctx = document.getElementById('chartStatusPie').getContext('2d');
    const labels = Object.keys(statusData);
    const values = Object.values(statusData);

    if (charts['statusPie']) charts['statusPie'].destroy();

    charts['statusPie'] = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: values,
                backgroundColor: ['#fbbf24', '#10b981', '#ef4444'],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { 
                legend: { position: 'right' } 
            }
        }
    });
}

function renderRankingTable(students) {
    const tbody = document.getElementById('ranking-table-body');
    tbody.innerHTML = '';

    students.forEach((s, index) => {
        const tr = document.createElement('tr');
        tr.className = index % 2 === 0 ? 'bg-white' : 'bg-slate-50';
        tr.innerHTML = `
            <td class="px-4 py-2 border-b border-slate-100 font-medium text-slate-700 truncate max-w-[150px]" title="${s.name}">${s.name}</td>
            <td class="px-4 py-2 border-b border-slate-100 text-slate-500">${s.course}</td>
            <td class="px-4 py-2 border-b border-slate-100 text-right font-bold text-blue-600">${s.count}</td>
        `;
        tbody.appendChild(tr);
    });
}
