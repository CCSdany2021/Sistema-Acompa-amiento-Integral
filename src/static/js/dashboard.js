document.addEventListener('DOMContentLoaded', () => {
    // Load Courses into Sidebar
    loadCourses();

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

async function loadCourses() {
    // Ideally we filter by section if the user is a teacher/coordinator
    // But for now verify what the dashboard template provides or just fetch all
    try {
        const response = await fetch('/api/courses');
        const courses = await response.json();
        
        const sidebar = document.querySelector('aside nav'); // Assuming structure from base.html
        // If sidebar not found by tag, we might need a specific ID.
        // Let's print to console to debug if we don't find it.
        if (!sidebar) { 
            console.error("Sidebar nav not found"); 
            return;
        }

        // Clear existing mock links if any (except dashboard home)
        // For simplicity, let's append a "Cursos" section
        
        let html = '<div class="mt-4 px-4"><h3 class="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2 px-2">Cursos</h3><div class="space-y-1">';
        
        courses.forEach(course => {
            html += `
            <a href="#" data-course="${course}" class="course-link flex items-center px-4 py-2 text-slate-300 hover:bg-white/10 hover:text-white rounded-lg transition-colors group">
                <i class="fa-solid fa-graduation-cap text-slate-400 group-hover:text-brand-gold mr-3 transition-colors"></i>
                <span class="font-medium">${course}</span>
            </a>`;
        });
        html += '</div></div>';
        
        sidebar.insertAdjacentHTML('beforeend', html);

        // Add Event Listeners
        document.querySelectorAll('.course-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                // Handle click on icon or text
                const target = e.target.closest('.course-link');
                const courseId = target.dataset.course;
                
                // Highlight active
                document.querySelectorAll('.course-link').forEach(l => {
                    l.classList.remove('bg-white/10', 'text-brand-gold', 'border-r-2', 'border-brand-gold');
                    l.classList.add('text-slate-300');
                    // Reset icon color
                    const icon = l.querySelector('i');
                    if(icon) icon.classList.remove('text-brand-gold');
                });
                
                target.classList.remove('text-slate-300');
                target.classList.add('bg-white/10', 'text-brand-gold');
                
                // Highlight icon
                const icon = target.querySelector('i');
                if(icon) icon.classList.add('text-brand-gold');
                
                loadStudents(courseId);
            });
        });

    } catch (error) {
        console.error("Error loading courses:", error);
    }
}

async function loadStudents(courseId) {
    const contentArea = document.querySelector('#content-area'); // Need to ID this in HTML
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
                <th class="sticky top-0 bg-slate-50 z-10 px-6 py-3 text-xs font-bold text-slate-500 uppercase border-b border-slate-200">Estudiante</th>
                <th class="sticky top-0 bg-slate-50 z-10 px-6 py-3 text-xs font-bold text-slate-500 uppercase border-b border-slate-200">Código</th>
                <th class="sticky top-0 bg-slate-50 z-10 px-6 py-3 text-xs font-bold text-slate-500 uppercase border-b border-slate-200 text-right">Acción</th>
            </tr>
        </thead>
        <tbody class="divide-y divide-slate-100">`;
        
    students.forEach(student => {
        const initials = getInitials(student.full_name);
        html += `
        <tr class="hover:bg-blue-50/50 transition-colors group">
            <td class="px-6 py-3">
                <div class="flex items-center">
                    <div class="relative w-10 h-10 mr-3">
                         <!-- Profile Photo: Try .jpg first (common). Valid for local files if named by code. -->
                         <img src="/static/img/students/${student.code}.jpg" 
                              class="w-full h-full rounded-full object-cover shadow-sm absolute inset-0 z-10"
                              onerror="this.style.display='none'; this.nextElementSibling.style.display='flex'"
                              alt="${student.full_name}">
                         <!-- Fallback Initials -->
                         <div class="hidden w-full h-full rounded-full bg-slate-100 text-slate-600 flex items-center justify-center text-xs font-bold border border-slate-200 absolute inset-0 z-0">
                            ${initials}
                         </div>
                    </div>
                    <div>
                        <p class="text-sm font-semibold text-slate-700">${student.full_name}</p>
                        <p class="text-xs text-slate-400 md:hidden">${student.code}</p>
                    </div>
                </div>
            </td>
            <td class="px-6 py-3 text-sm text-slate-500 font-mono">
                ${student.code}
            </td>
            <td class="px-6 py-3 text-right">
                <button class="open-report-btn text-slate-400 hover:text-blue-600 hover:bg-blue-100 p-2 rounded-lg transition-all transform hover:scale-105 active:scale-95" 
                    data-id="${student.id}" 
                    data-name="${student.full_name.replace(/"/g, '&quot;')}" 
                    title="Crear Reporte">
                    <span class="text-xs font-medium mr-2 hidden group-hover:inline-block">Reportar</span>
                    <i class="fa-solid fa-file-pen text-lg pointer-events-none"></i>
                </button>
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
}

function getInitials(name) {
    return name.split(' ').map(n => n[0]).join('').substring(0,2).toUpperCase();
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
            alert('Error: ' + (error.detail || 'No se pudo crear el reporte'));
        }
    } catch (error) {
        alert('Error de conexión: ' + error);
    }
});

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
