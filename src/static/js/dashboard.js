document.addEventListener('DOMContentLoaded', () => {
    // Load Stats & Recent Reports
    loadDashboardData();

    // Load Users for Assignment
    loadUsers();
    
    // Import Excel Listener removed (moved to admin_import.js)
});

async function loadUsers() {
    try {
        const response = await fetch('/api/users');
        const users = await response.json();
        const select = document.getElementById('assigned_to');
        
        users.forEach(user => {
            const option = document.createElement('option');
            option.value = user.id;
            // Format: "Name (Role - Section)" or just Name
            let label = user.full_name;
            if (user.role && user.role !== 'Docente') {
                label += ` (${user.role})`;
            }
            option.textContent = label;
            select.appendChild(option);
        });
    } catch (error) {
        console.error("Error loading users:", error);
    }
}

async function loadDashboardData() {
    try {
        const response = await fetch('/api/reports?limit=10');
        if (!response.ok) {
            let errorMsg = `API Error: ${response.status}`;
            try {
                const errData = await response.json();
                if (errData.detail) errorMsg += ` - ${errData.detail}`;
            } catch (e) { /* ignore json parse error */ }
            throw new Error(errorMsg);
        }
        
        const reports = await response.json();
        
        if (!Array.isArray(reports)) {
            console.error("Expected array, got:", reports);
            throw new Error("Invalid data format received");
        }
        
        // Render Recent Reports List Side Panel
        const recentArea = document.querySelector('#recent-reports-area');
        if (recentArea) {
             if (reports.length === 0) {
                recentArea.innerHTML = '<div class="p-6 text-center text-slate-400 text-sm">No hay actividad reciente.</div>';
            } else {
                // Clear loading message before loop
                recentArea.innerHTML = ''; 
            }
        }
        
        // Update Stats
        const statElements = document.querySelectorAll('h3.text-3xl.font-bold');
        if (statElements.length >= 4) {
             const activeReports = reports.filter(r => r.status === 'PROGRAMADO' || r.status === 'SEGUIMIENTO');
             const attendedReports = reports.filter(r => r.status === 'ATENDIDO');
             
             statElements[0].textContent = reports.length;
             statElements[1].textContent = activeReports.length;
             statElements[2].textContent = attendedReports.length;
             statElements[3].textContent = reports.filter(r => r.status === 'PROGRAMADO').length; 
        }

        if (recentArea && reports.length > 0) {
            let html = '<div class="divide-y divide-slate-50">';
        
        reports.forEach(r => {
            const studentName = r.student ? r.student.full_name : 'Desconocido';
            const assignedName = r.assigned_to ? r.assigned_to.full_name.split(' ')[0] : 'Sin asignar'; // Short name
            const date = new Date(r.created_at).toLocaleDateString();
            
            // Status Badge Color
            let statusColor = 'bg-slate-100 text-slate-600';
            if (r.status === 'PROGRAMADO') statusColor = 'bg-emerald-100 text-emerald-700';
            if (r.status === 'SEGUIMIENTO') statusColor = 'bg-blue-100 text-blue-700';
            if (r.status === 'ATENDIDO') statusColor = 'bg-slate-200 text-slate-700';

            // Generate HTML for Report Item
            const tempDiv = document.createElement('div');
            tempDiv.innerHTML = `
            <div onclick="window.location.href='/reports/${r.id}'" class="p-4 hover:bg-slate-50 transition-colors cursor-pointer group border-b border-slate-50">
                <div class="flex justify-between items-start mb-1">
                    <h4 class="text-sm font-semibold text-slate-800 line-clamp-1 group-hover:text-blue-600 transition-colors">${studentName}</h4>
                    <span class="text-[10px] uppercase font-bold px-1.5 py-0.5 rounded ${statusColor}">${r.status}</span>
                </div>
                <p class="text-xs text-slate-500 mb-2 line-clamp-2">${r.objective}</p>
                <div class="flex items-center justify-between text-xs text-slate-400">
                    <div class="flex items-center" title="Encargado">
                        <i class="fa-solid fa-user-circle mr-1.5"></i>
                        <span>${assignedName}</span>
                    </div>
                    <span>${date}</span>
                </div>
            </div>`;
            html += tempDiv.innerHTML;
        });

        html += '</div>';
        recentArea.innerHTML = html;
        } // Close if (recentArea && reports.length > 0)

    } catch (error) {
        console.error("Error loading dashboard data:", error);
        const recentArea = document.querySelector('#recent-reports-area');
        if (recentArea) {
            recentArea.innerHTML = `<div class="p-4 bg-red-50 text-red-600 text-xs rounded-lg border border-red-100">
                <p class="font-bold">Error cargando datos:</p>
                <p>${error.message}</p>
            </div>`;
        }
    }
}

// End of loadDashboardData


async function loadStudents(courseId) {
    const emptyState = document.getElementById('empty-state');
    const mainContent = document.getElementById('main-content');
    const contentArea = document.querySelector('#content-area'); 

    // Switch view
    if(emptyState) emptyState.classList.add('hidden');
    if(mainContent) {
        mainContent.classList.remove('hidden');
        mainContent.classList.add('flex');
    }

    contentArea.innerHTML = '<div class="text-center p-10"><i class="fa-solid fa-spinner fa-spin text-4xl text-blue-500"></i><p class="mt-4 text-slate-500">Cargando estudiantes...</p></div>';
    
    try {
        const response = await fetch(`/api/students?course=${courseId}`);
        const students = await response.json();
        
        renderStudentGrid(students);
    } catch (error) {
        contentArea.innerHTML = `<div class="text-center p-10 text-red-500">Error al cargar datos: ${error}</div>`;
    }
}

function renderStudentGrid(students) {
    const contentArea = document.querySelector('#content-area');
    const courseTitle = document.querySelector('#course-title');
    const courseSubtitle = document.querySelector('#course-subtitle');

    if (students.length > 0) {
        courseTitle.textContent = `Curso ${students[0].course}`;
        courseSubtitle.textContent = `${students.length} Estudiantes registrados`;
    }

    if (students.length === 0) {
        contentArea.innerHTML = `
            <div class="flex flex-col items-center justify-center h-64 text-slate-400">
                <p>No hay estudiantes en este curso.</p>
            </div>`;
        return;
    }

    let html = `
    <table class="w-full text-left border-collapse">
        <thead>
            <tr>
                <th class="sticky top-0 bg-slate-100 z-10 px-6 py-3 text-xs font-extra-bold text-slate-700 uppercase border-b border-slate-300 shadow-sm">Estudiante</th>
                <th class="sticky top-0 bg-slate-100 z-10 px-6 py-3 text-xs font-extra-bold text-slate-700 uppercase border-b border-slate-300 shadow-sm">Fines Reportados</th> <!-- New Column -->
                <th class="sticky top-0 bg-slate-100 z-10 px-6 py-3 text-xs font-extra-bold text-slate-700 uppercase border-b border-slate-300 shadow-sm text-right">Acción</th>
            </tr>
        </thead>
        <tbody class="divide-y divide-slate-100">`;
        
    students.forEach(student => {
        const initials = getInitials(student.full_name);
        html += `
        <tr class="hover:bg-blue-50 transition-colors group border-b border-slate-100">
            <td class="px-6 py-3">
                <div class="flex items-center">
                    <div class="relative w-10 h-10 mr-3 flex-shrink-0">
                         <div class="w-full h-full rounded-full bg-slate-100 text-slate-600 flex items-center justify-center text-xs font-bold border border-slate-200">
                            ${initials}
                         </div>
                    </div>
                    <div>
                        <p class="text-sm font-bold text-slate-800">${student.full_name}</p>
                    </div>
                </div>
            </td>
            <td class="px-6 py-3">
                <div class="flex flex-wrap gap-2">
                    ${renderBadges(student.active_reports)}
                </div>
            </td>
            <td class="px-6 py-3">
                <div class="flex items-center justify-end gap-2">
                <!-- Nuevo Reporte Button -->
                <button class="open-report-btn bg-brand-blue text-white hover:bg-blue-700 px-4 py-2 rounded-lg text-xs font-bold transition-all shadow-md hover:shadow-lg flex items-center"
                    data-id="${student.id}" 
                    data-name="${student.full_name.replace(/"/g, '&quot;')}" 
                    title="Crear Nuevo Reporte">
                    <i class="fa-solid fa-plus mr-2"></i> Nuevo reporte
                </button>
                
                <!-- Editar Reporte Button (Only enabled if active reports exist) -->
                ${student.active_reports.length > 0 ? 
                `<button class="edit-report-btn bg-brand-gold text-brand-navy hover:bg-yellow-400 px-4 py-2 rounded-lg text-xs font-bold transition-all shadow-md hover:shadow-lg flex items-center"
                    data-id="${student.id}" 
                    data-report-id="${student.active_reports[0].id}" 
                    title="Editar Reporte Existente">
                    <i class="fa-solid fa-pen mr-2"></i> Editar reporte
                </button>` : 
                 `<button class="opacity-40 cursor-not-allowed bg-slate-200 text-slate-400 px-4 py-2 rounded-lg text-xs font-bold flex items-center" disabled>
                    <i class="fa-solid fa-pen mr-2"></i> Editar reporte
                 </button>`
                }
                </div>
            </td>
        </tr>
        `;
    });
    html += '</tbody></table>';
    contentArea.innerHTML = html;

    // Add Listeners
    document.querySelectorAll('.open-report-btn').forEach(btn => {
        btn.addEventListener('click', () => {
             openReportModal(btn.dataset.id, btn.dataset.name);
        });
    });

    document.querySelectorAll('.edit-report-btn').forEach(btn => {
        btn.addEventListener('click', () => {
             window.location.href = `/reports/${btn.dataset.reportId}`;
        });
    });
}

function getInitials(name) {
    return name.split(' ').map(n => n[0]).join('').substring(0,2).toUpperCase();
}

function renderBadges(reports) {
    if (!reports || reports.length === 0) return '<span class="text-xs text-slate-300 italic">Sin reportes</span>';
    
    return reports.map(r => {
        let colorClass = 'bg-slate-100 text-slate-700 border-slate-300 hover:bg-slate-200';
        if (r.purpose === 'Espiritual') colorClass = 'bg-purple-100 text-purple-800 border-purple-300 hover:bg-purple-200';
        if (r.purpose === 'Académico') colorClass = 'bg-blue-100 text-blue-800 border-blue-300 hover:bg-blue-200';
        if (r.purpose === 'Convivencia') colorClass = 'bg-orange-100 text-orange-800 border-orange-300 hover:bg-orange-200';
        if (r.purpose === 'Psicoafectivo') colorClass = 'bg-rose-100 text-rose-800 border-rose-300 hover:bg-rose-200';
        
        return `<a href="/reports/${r.id}" class="px-2.5 py-1 rounded-md text-[11px] font-bold border ${colorClass} uppercase tracking-wide shadow-sm transition-colors text-center block mb-1 no-underline" title="Ir a reporte ${r.purpose}">
            ${r.purpose} - ${r.status}
        </a>`;
    }).join('');
}

// Modal Logic
const modal = document.getElementById('report-modal');
const modalContent = modal.querySelector('.modal-content');
const reportForm = document.getElementById('report-form');

function openReportModal(studentId, studentName) {
    document.getElementById('student_id').value = studentId;
    document.getElementById('student_name_display').value = studentName;
    
    modal.classList.remove('hidden');
    modal.classList.add('flex');
    setTimeout(() => {
        modalContent.classList.remove('scale-95', 'opacity-0');
        modalContent.classList.add('scale-100', 'opacity-100');
    }, 10);
}

function closeReportModal() {
    modalContent.classList.remove('scale-100', 'opacity-100');
    modalContent.classList.add('scale-95', 'opacity-0');
    setTimeout(() => {
        modal.classList.add('hidden');
        modal.classList.remove('flex');
        reportForm.reset();
    }, 300);
}

// Form Submission
reportForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    console.log("Submitting report...");
    
    const formData = {
        student_id: parseInt(document.getElementById('student_id').value),
        purpose: document.getElementById('purpose').value,
        assigned_to_id: document.getElementById('assigned_to').value ? parseInt(document.getElementById('assigned_to').value) : null,
        academic_period: document.getElementById('academic_period').value,
        objective: document.getElementById('objective').value
    };

    try {
        const response = await fetch('/api/reports', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        });

        if (response.ok) {
            alert('Reporte creado exitosamente');
            closeReportModal();
            loadDashboardData(); // Refresh data immediately
        } else {
            const error = await response.json();
            
            // Check for Duplicate Report (409)
            if (response.status === 409) {
                closeReportModal(); // Close the create modal
                showDuplicateModal(error.detail); // Show the warning modal
            } else {
                alert('Error: ' + (error.detail || 'No se pudo crear el reporte'));
            }
        }
    } catch (error) {
        alert('Error de conexión: ' + error);
    }
});

// Duplicate Modal Logic
function showDuplicateModal(details) {
    const modal = document.getElementById('duplicate-report-modal');
    // Populate details
    document.getElementById('dup-message').textContent = details.message || "Este estudiante ya posee un proceso activo.";
    document.getElementById('dup-creator').textContent = details.created_by || "Desconocido";
    
    // Format date
    let dateStr = details.created_at || "--";
    try {
        const dateObj = new Date(details.created_at);
        dateStr = dateObj.toLocaleDateString() + ' ' + dateObj.toLocaleTimeString();
    } catch(e) {}
    document.getElementById('dup-date').textContent = dateStr;

    // Setup View Button
    const viewBtn = document.getElementById('dup-view-btn');
    viewBtn.onclick = () => window.location.href = `/reports/${details.report_id}`;

    // Show Modal
    modal.classList.remove('hidden');
}

function closeDuplicateModal() {
    document.getElementById('duplicate-report-modal').classList.add('hidden');
}

async function loadUsers() {
    try {
        const response = await fetch('/api/users');
        const users = await response.json();
        const select = document.getElementById('assigned_to');
        
        // Clear existing except default
        while (select.options.length > 1) {
            select.remove(1);
        }

        users.forEach(user => {
            const option = document.createElement('option');
            option.value = user.id;
            // Format: "Name (Role - Section)" or just Name
            let label = user.full_name;
            if (user.role && user.role !== 'Docente') {
                label += ` (${user.role})`;
            }
            option.textContent = label;
            select.appendChild(option);
        });
    } catch (error) {
        console.error("Error loading users:", error);
    }
}
