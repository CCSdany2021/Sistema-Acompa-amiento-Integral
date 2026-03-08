let currentCourseId = null;

document.addEventListener('DOMContentLoaded', () => {
    // Load Stats & Recent Reports
    loadDashboardData();

    // Load Users for Assignment
    loadUsers();
});

async function loadUsers() {
    try {
        const response = await fetch('/api/users');
        const users = await response.json();
        const select = document.getElementById('assigned_to');
        
        // Clear existing except default
        while (select && select.options.length > 1) {
            select.remove(1);
        }

        users.forEach(user => {
            const option = document.createElement('option');
            option.value = user.id;
            option.textContent = user.full_name;
            if(select) select.appendChild(option);
        });
    } catch (error) {
        console.error("Error loading users:", error);
    }
}

function getGradeName(course) {
    if (!course) return '---';
    const c = course.toString().toUpperCase();
    if (c.startsWith('TR')) return 'Transición';
    if (c.length === 3) {
        const grade = c[0];
        const grades = { '1': 'Primero', '2': 'Segundo', '3': 'Tercero', '4': 'Cuarto', '5': 'Quinto', '6': 'Sexto', '7': 'Séptimo', '8': 'Octavo', '9': 'Noveno' };
        return grades[grade] || course;
    }
    if (c.length === 4) {
        const grade = c.substring(0, 2);
        if (grade === '10') return 'Décimo';
        if (grade === '11') return 'Undécimo';
    }
    return course;
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
        // Update Stats using specific IDs
        const statTotal = document.getElementById('stat-total');
        const statActive = document.getElementById('stat-active');
        const statPending = document.getElementById('stat-pending');

        if (statTotal) statTotal.textContent = reports.length;
        if (statActive) statActive.textContent = reports.filter(r => r.status === 'SEGUIMIENTO').length;
        if (statPending) statPending.textContent = reports.filter(r => r.status === 'PROGRAMADO').length;

        if (recentArea && reports.length > 0) {
            let html = `
            <table class="w-full text-left border-collapse">
                <thead>
                    <tr class="bg-slate-50 border-b border-slate-100 text-[10px] text-slate-400 font-semibold">
                        <th class="px-8 py-4">Estudiante</th>
                        <th class="px-8 py-4">Curso</th>
                        <th class="px-8 py-4">Fin Educativo / Estado</th>
                        <th class="px-8 py-4 text-right">Acción</th>
                    </tr>
                </thead>
                <tbody class="text-sm font-medium text-gray-700 divide-y divide-gray-50 bg-white">`;
        
            reports.forEach(r => {
                const studentName = r.student ? r.student.full_name : 'Desconocido';
                const studentId = r.student ? r.student.code : '---';
                const rawCourse = r.student ? r.student.course : '---';
                const courseName = getGradeName(rawCourse);
                
                let purposeColor = 'bg-slate-50 text-slate-700';
                if (r.purpose === 'Convivencia') purposeColor = 'bg-emerald-50 text-emerald-700 border-emerald-200';
                else if (r.purpose === 'Académico') purposeColor = 'bg-blue-50 text-blue-700 border-blue-200';
                else if (r.purpose === 'Psicoafectivo') purposeColor = 'bg-rose-50 text-rose-700 border-red-200';
                else if (r.purpose === 'Espiritual') purposeColor = 'bg-purple-50 text-purple-700 border-purple-200';

                let statusBadge = '';
                if (r.status === 'PROGRAMADO') {
                    statusBadge = `<span class="flex items-center gap-1.5 text-[10px] font-bold text-amber-700 bg-amber-100 px-2.5 py-1.5 rounded shadow-sm border border-amber-200 uppercase">PROGRAMADO</span>`;
                } else if (r.status === 'SEGUIMIENTO') {
                    statusBadge = `<span class="flex items-center gap-1.5 text-[10px] font-bold text-blue-700 bg-blue-100 px-2.5 py-1.5 rounded shadow-sm border border-blue-200 uppercase">SEGUIMIENTO</span>`;
                } else if (r.status === 'ATENDIDO') {
                    statusBadge = `<span class="flex items-center gap-1.5 text-[10px] font-bold text-emerald-700 bg-emerald-100 px-2.5 py-1.5 rounded shadow-sm border border-emerald-200 uppercase">ATENDIDO</span>`;
                }

                html += `
                <tr class="hover:bg-slate-50 transition-colors">
                    <td class="px-8 py-5">
                        <div class="font-bold text-slate-800 text-[11px]">${studentName}</div>
                        <div class="text-[9px] text-slate-400 font-bold uppercase tracking-tight">Id: ${studentId}</div>
                    </td>
                    <td class="px-8 py-5">
                        <span class="text-slate-600 font-bold px-2 py-1 text-[10px] border border-slate-200 bg-slate-50 rounded italic">${courseName}</span>
                    </td>
                    <td class="px-8 py-5">
                        <div class="flex items-center gap-3">
                            <span class="px-3 py-1.5 text-[10px] font-black border uppercase ${purposeColor}">
                                ${r.purpose}
                            </span>
                            ${statusBadge}
                        </div>
                    </td>
                    <td class="px-8 py-5 text-right">
                        <a href="/reports/${r.id}" class="inline-flex items-center justify-center w-8 h-8 bg-inst-blue text-white rounded-full hover:bg-inst-navy transition-all shadow-sm">
                            <i class="bi bi-eye-fill"></i>
                        </a>
                    </td>
                </tr>`;
            });

            html += '</tbody></table>';
            recentArea.innerHTML = html;
        } 

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
    currentCourseId = courseId;
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
        courseSubtitle.textContent = `${students.length} Estudiantes - ${getGradeName(students[0].course)}`;
    }

    if (students.length === 0) {
        contentArea.innerHTML = `
            <div class="flex flex-col items-center justify-center h-64 text-slate-400">
                <i class="fa-solid fa-users-slash text-5xl mb-4 opacity-20"></i>
                <p class="font-bold text-xs">No hay estudiantes en este curso.</p>
            </div>`;
        return;
    }

    let html = `
    <div class="overflow-x-auto bg-white border border-slate-200 rounded-xl shadow-sm">
        <table class="w-full text-left text-sm whitespace-nowrap">
            <thead>
                <tr class="bg-slate-50 text-slate-600 border-b border-slate-200">
                    <th class="px-4 py-3 w-10 border-b border-slate-200">
                        <input type="checkbox" class="rounded border-slate-300 text-inst-blue focus:ring-inst-blue w-4 h-4 cursor-pointer" disabled title="Selección global">
                    </th>
                    <th class="sticky top-0 bg-slate-50 z-10 px-4 py-3 text-[11px] font-semibold text-slate-600 border-b border-slate-200">Estudiante</th>
                    <th class="sticky top-0 bg-slate-50 z-10 px-4 py-3 text-[11px] font-semibold text-slate-600 border-b border-slate-200">Código</th>
                    <th class="sticky top-0 bg-slate-50 z-10 px-4 py-3 text-[11px] font-semibold text-slate-600 border-b border-slate-200">Curso</th>
                    <th class="sticky top-0 bg-slate-50 z-10 px-4 py-3 text-[11px] font-semibold text-slate-600 border-b border-slate-200">Grado</th>
                    <th class="sticky top-0 bg-slate-50 z-10 px-4 py-3 text-[11px] font-semibold text-slate-600 border-b border-slate-200">Trazabilidad por Fines Educativos</th>
                    <th class="sticky top-0 bg-slate-50 z-10 px-4 py-3 text-[11px] font-semibold text-slate-600 border-b border-slate-200 text-right">Gestión</th>
                </tr>
            </thead>
            <tbody class="divide-y divide-slate-100 bg-white">`;
        
    students.forEach(student => {
        const hasPending = student.active_reports.some(r => r.status === 'PROGRAMADO');
        const statusBadge = hasPending ? 
            `<span class="ml-2 px-1.5 py-0.5 bg-red-50 text-red-600 border border-red-200 text-[10px] font-medium rounded-sm">
                Pendiente Atencion
            </span>` : '';

        html += `
        <tr class="hover:bg-slate-50 transition-colors group">
            <td class="px-4 py-3">
                <input type="checkbox" class="rounded border-slate-300 text-inst-blue focus:ring-inst-blue w-4 h-4 cursor-pointer" disabled>
            </td>
            <td class="px-4 py-3">
                <div class="flex items-center gap-3">
                    <div class="w-8 h-8 rounded-full bg-slate-100 flex items-center justify-center text-slate-500 font-bold text-[10px] border border-slate-200 group-hover:bg-inst-blue/5 group-hover:text-inst-blue transition-colors relative overflow-hidden shrink-0">
                        <img src="/archivos/img_pruebas/ARIAS%20URQUIJO%20SERGIO%20ALEJANDRO.jpg" class="w-full h-full object-cover absolute inset-0 z-10" onerror="this.style.display='none'">
                        <span class="relative z-0">${getInitials(student.full_name)}</span>
                    </div>
                    <div class="flex items-center">
                        <button class="open-report-btn text-sm font-semibold text-inst-blue hover:text-inst-dark hover:underline focus:outline-none"
                            data-id="${student.id}" 
                            data-name="${student.full_name.replace(/"/g, '&quot;')}" 
                            data-code="${student.code}"
                            data-course="${student.course || '---'}">
                            ${student.full_name}
                        </button>
                        ${statusBadge}
                    </div>
                </div>
            </td>
            <td class="px-4 py-3 text-slate-600 font-medium text-xs">
                ${student.code || '--'}
            </td>
            <td class="px-4 py-3 text-slate-700 font-bold text-xs">
                ${student.course || '--'}
            </td>
            <td class="px-4 py-3 text-slate-600 font-medium text-xs">
                ${getGradeName(student.course)}
            </td>
            <td class="px-4 py-3">
                <div class="flex flex-row gap-2 items-center">
                    ${renderBadges(student.active_reports)}
                </div>
            </td>
            <td class="px-4 py-3 text-right">
                <button class="open-report-btn px-4 py-1.5 bg-white border border-slate-300 text-slate-700 hover:bg-slate-50 hover:border-slate-400 transition-colors rounded text-xs font-semibold shadow-sm focus:outline-none"
                    data-id="${student.id}" 
                    data-name="${student.full_name.replace(/"/g, '&quot;')}" 
                    data-code="${student.code}"
                    data-course="${student.course || '---'}">
                    Generar Reporte <span class="text-slate-400 font-normal ml-1">&rarr;</span>
                </button>
            </td>
        </tr>
        `;
    });
    html += '</tbody></table></div>';
    contentArea.innerHTML = html;

    // Add Listeners
    document.querySelectorAll('.open-report-btn').forEach(btn => {
        btn.addEventListener('click', () => {
             openReportModal(btn.dataset.id, btn.dataset.name, btn.dataset.code, btn.dataset.course);
        });
    });
}


function getInitials(name) {
    return name.split(' ').map(n => n[0]).join('').substring(0,2).toUpperCase();
}

function renderBadges(reports) {
    if (!reports || reports.length === 0) return '<span class="text-[9px] font-bold text-slate-300 italic">Sin procesos activos</span>';
    
    return reports.map(r => {
        let colorTheme = 'bg-slate-50 text-slate-600 border-slate-200';
        let icon = 'fa-circle-dot';
        let statusTag = '';
        
        // Normalizar el texto para la comparación
        const purpose = (r.purpose || '').toString().trim();
        const pLower = purpose.toLowerCase();

        // Purpose Colors - Prioridad total al fin educativo
        if (pLower.includes('espiritual')) { 
            colorTheme = 'bg-purple-100 text-purple-800 border-purple-200'; 
            icon = 'fa-dove'; 
        } else if (pLower.includes('acad') || pLower.includes('academico')) { 
            colorTheme = 'bg-blue-100 text-blue-800 border-blue-200'; 
            icon = 'fa-book-open'; 
        } else if (pLower.includes('convivencia')) { 
            colorTheme = 'bg-emerald-100 text-emerald-800 border-emerald-200'; 
            icon = 'fa-handshake'; 
        } else if (pLower.includes('psicoafectivo')) { 
            colorTheme = 'bg-rose-100 text-rose-800 border-red-200'; 
            icon = 'fa-heart'; 
        }
        
        // Status Indicators - Etiquetas pequeñas
        if (r.status === 'PROGRAMADO') {
            statusTag = `<span class="ml-1.5 px-2 py-0.5 bg-red-600 text-white rounded-full text-[8px] font-black uppercase tracking-tighter">PROGRAMADO</span>`;
        } else if (r.status === 'SEGUIMIENTO') {
            statusTag = `<span class="ml-1.5 px-2 py-0.5 bg-amber-500 text-white rounded-full text-[8px] font-black uppercase tracking-tighter">SEGUIMIENTO</span>`;
        } else if (r.status === 'ATENDIDO') {
            statusTag = `<span class="ml-1.5 px-2 py-0.5 bg-emerald-600 text-white rounded-full text-[8px] font-black uppercase tracking-tighter">CERRADO</span>`;
        }

        return `
        <a href="/reports/${r.id}" class="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg border-2 ${colorTheme} transition-all hover:scale-105 hover:shadow-lg no-underline group/badge">
            <i class="fa-solid ${icon} text-[11px] ${r.status === 'PROGRAMADO' ? 'text-red-600 animate-pulse' : 'opacity-90'}"></i>
            <span class="font-black text-[10px] uppercase tracking-wide italic">${purpose}</span>
            ${statusTag}
        </a>`;
    }).join('');
}


// Modal Logic
const reportModal = document.getElementById('report-modal');
const reportModalContent = reportModal ? reportModal.querySelector('.modal-content') : null;
const reportForm = document.getElementById('report-form');

function openReportModal(studentId, studentName, studentCode, studentCourse) {
    if(!reportModal) return;
    
    // Debug logging
    console.log("Opening Modal for Student:", { id: studentId, name: studentName, code: studentCode, course: studentCourse });

    document.getElementById('student_id').value = studentId || '';
    document.getElementById('student_name_display').value = studentName || '';
    document.getElementById('student_code_display').value = studentCode || 'N/A';
    document.getElementById('student_course_display').value = studentCourse || 'N/A';
    
    reportModal.classList.remove('hidden');
    reportModal.classList.add('flex');
    setTimeout(() => {
        if(reportModalContent) {
            reportModalContent.classList.remove('scale-95', 'opacity-0');
            reportModalContent.classList.add('scale-100', 'opacity-100');
        }
    }, 10);
}

function closeReportModal() {
    if(!reportModal || !reportModalContent) return;
    reportModalContent.classList.remove('scale-100', 'opacity-100');
    reportModalContent.classList.add('scale-95', 'opacity-0');
    setTimeout(() => {
        reportModal.classList.add('hidden');
        reportModal.classList.remove('flex');
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
            loadDashboardData(); // Refresh sidebar stats
            if (currentCourseId) {
                loadStudents(currentCourseId); // Refresh student grid to show new badge
            }
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
    const dupModal = document.getElementById('duplicate-report-modal');
    if(!dupModal) return;

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
    if(viewBtn) viewBtn.onclick = () => window.location.href = `/reports/${details.report_id}`;

    // Show Modal
    dupModal.classList.remove('hidden');
}

function closeDuplicateModal() {
    const dupModal = document.getElementById('duplicate-report-modal');
    if(dupModal) dupModal.classList.add('hidden');
}

// Global Refresh Helper
function refreshCurrentData() {
    loadDashboardData();
    if (currentCourseId) {
        loadStudents(currentCourseId);
    }
}


