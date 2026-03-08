/**
 * Logic for reports_list.html
 */

document.addEventListener('DOMContentLoaded', () => {
    const tableBody = document.getElementById('table-body');
    const loading = document.getElementById('loading');
    const emptyState = document.getElementById('empty-state');
    
    // Filters
    const filterName = document.getElementById('filter-name');
    const filterPurpose = document.getElementById('filter-purpose');
    const filterStatus = document.getElementById('filter-status');
    const filterSection = document.getElementById('filter-section');
    const filterCourse = document.getElementById('filter-course');
    const filterPeriod = document.getElementById('filter-period');

    let allReports = [];

    async function fetchReports() {
        loading.classList.remove('hidden');
        tableBody.innerHTML = '';
        try {
            const res = await fetch('/api/reports');
            allReports = await res.json();
            renderTable(allReports);
        } catch (e) {
            console.error(e);
        } finally {
            loading.classList.add('hidden');
        }
    }

    function getGradeName(course) {
        if (!course) return '---';
        const c = course.toString().toUpperCase();
        if (c.startsWith('TR')) return 'Transición';
        // handle 3-digit vs 4-digit codes
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

    function renderTable(reports) {
        const tableBody = document.getElementById('table-body');
        const emptyState = document.getElementById('empty-state');
        
        if (reports.length === 0) {
            emptyState.classList.remove('hidden');
            tableBody.innerHTML = '';
            return;
        }
        emptyState.classList.add('hidden');
        
        tableBody.innerHTML = reports.map(r => `
            <tr class="hover:bg-gray-50 transition-colors group cursor-pointer" onclick="openStudentModal('${r.student?.code}')">
                <td class="px-4 py-3 border-r border-gray-100 text-center" onclick="event.stopPropagation()">
                    <input type="checkbox" class="rounded border-gray-300 text-inst-blue w-3.5 h-3.5 cursor-pointer shadow-sm">
                </td>
                <td class="px-4 py-3 border-r border-gray-100">
                    <div class="flex items-center gap-3">
                        <div class="w-8 h-8 rounded-full bg-slate-100 flex items-center justify-center border border-slate-200 overflow-hidden shrink-0 relative shadow-sm">
                            <img src="/archivos/img_pruebas/${encodeURIComponent((r.student?.full_name || '').toUpperCase())}.jpg" class="w-full h-full object-cover absolute inset-0 z-10" onerror="this.style.display='none'">
                            <span class="text-slate-400 font-bold text-[10px]">${(r.student?.full_name || 'U').split(' ').map(n=>n[0]).join('').substring(0,2).toUpperCase()}</span>
                        </div>
                        <div class="flex flex-col">
                            <span class="font-bold text-[11px] text-slate-800">${r.student?.full_name || '---'}</span>
                            <span class="text-[9px] text-slate-400 font-medium">ID: ${r.student?.code || '---'}</span>
                        </div>
                    </div>
                </td>
                <td class="px-4 py-3 border-r border-gray-100 font-bold text-slate-700">${r.student?.course || '---'}</td>
                <td class="px-4 py-3 border-r border-gray-100 text-slate-600 font-medium">${getGradeName(r.student?.course)}</td>
                <td class="px-4 py-3 border-r border-gray-100 text-[10px] font-bold text-slate-400 uppercase tracking-tighter">${r.student?.section || '---'}</td>
                <td class="px-4 py-3 border-r border-gray-100 text-slate-600 font-medium">${r.created_by?.full_name || '---'}</td>
                <td class="px-4 py-3 border-r border-gray-100 text-slate-600 font-medium">${r.assigned_to?.full_name || '---'}</td>
                <td class="px-4 py-3 border-r border-gray-100">
                    <span class="px-2 py-0.5 rounded text-[9px] font-black uppercase tracking-tighter shadow-sm
                        ${r.status === 'PROGRAMADO' ? 'bg-amber-100 text-amber-700 border border-amber-200' : 
                          r.status === 'SEGUIMIENTO' ? 'bg-blue-100 text-blue-700 border border-blue-200' : 
                          'bg-emerald-100 text-emerald-700 border border-emerald-200'}">
                        ${r.status}
                    </span>
                </td>
                <td class="px-4 py-3 border-r border-gray-100">
                    <span class="px-2 py-0.5 rounded text-[9px] font-black uppercase tracking-tighter shadow-sm border
                        ${r.purpose === 'Psicoafectivo' ? 'bg-rose-50 text-rose-700 border-rose-200' : 
                          r.purpose === 'Espiritual' ? 'bg-purple-50 text-purple-700 border-purple-200' : 
                          r.purpose === 'Académico' ? 'bg-blue-50 text-blue-700 border-blue-200' : 
                          'bg-emerald-50 text-emerald-700 border-emerald-200'}">
                        ${r.purpose}
                    </span>
                </td>
                <td class="px-4 py-3 border-r border-gray-100 text-gray-400 font-medium">${r.academic_period || '-'}</td>
                <td class="px-4 py-3 text-center" onclick="event.stopPropagation()">
                    <button onclick="openStudentModal('${r.student?.code}')" class="text-inst-blue hover:underline font-bold text-[10px] uppercase tracking-wider">Ver detalle</button>
                </td>
            </tr>
        `).join('');
    }

    window.openStudentModal = function(studentCode) {
        const studentReports = allReports.filter(r => r.student?.code === studentCode);
        if (studentReports.length === 0) return;

        const student = studentReports[0].student;
        const modal = document.getElementById('student-modal');
        const infoArea = document.getElementById('modal-student-info');
        const selectorArea = document.getElementById('modal-report-selector');
        
        // Force uppercase for image matching
        const studentPhotoUrl = `/archivos/img_pruebas/${encodeURIComponent(student.full_name.toUpperCase())}.jpg`;

        // Populate Student Info in Sidebar
        infoArea.innerHTML = `
            <div class="flex items-center gap-4 mb-4">
                <div class="w-14 h-14 rounded-full bg-slate-100 flex items-center justify-center border-2 border-slate-200 overflow-hidden shrink-0 relative shadow-sm">
                    <img src="${studentPhotoUrl}" class="w-full h-full object-cover absolute inset-0 z-10" onerror="this.style.display='none'">
                    <span class="text-slate-400 font-bold text-lg">${(student.full_name || 'U').split(' ').map(n=>n[0]).join('').substring(0,2).toUpperCase()}</span>
                </div>
                <div>
                    <h3 class="text-[13px] font-black text-slate-800 leading-tight">${student.full_name}</h3>
                    <p class="text-[10px] text-inst-blue font-bold uppercase mt-1 tracking-wider">${student.course}</p>
                </div>
            </div>
            <div class="space-y-3 pt-2">
                <div class="flex flex-col">
                    <span class="text-[9px] font-bold text-slate-500 uppercase tracking-widest">Código Institucional</span>
                    <span class="text-[11px] font-black text-slate-700">${student.code}</span>
                </div>
                <div class="flex flex-col">
                    <span class="text-[9px] font-bold text-slate-500 uppercase tracking-widest">Grado / Sección</span>
                    <span class="text-[11px] font-black text-slate-700 font-bold">${getGradeName(student.course)} - ${student.section || 'N/A'}</span>
                </div>
            </div>
        `;

        // Function to render report details in the content area
        window.renderModalReportContent = function(reportId) {
            const report = allReports.find(r => r.id == reportId);
            const contentArea = document.getElementById('modal-content-area');
            if (!report) return;

            // Define color themes for each purpose
            const themes = {
                'Convivencia': { bg: 'bg-emerald-50', text: 'text-emerald-700', border: 'border-emerald-200', highlight: 'border-l-emerald-500', headerBg: 'bg-emerald-100/50', indicator: 'bg-emerald-500' },
                'Académico': { bg: 'bg-blue-50', text: 'text-blue-700', border: 'border-blue-200', highlight: 'border-l-blue-500', headerBg: 'bg-blue-100/50', indicator: 'bg-blue-500' },
                'Psicoafectivo': { bg: 'bg-rose-50', text: 'text-rose-700', border: 'border-rose-200', highlight: 'border-l-rose-500', headerBg: 'bg-rose-100/50', indicator: 'bg-rose-500' },
                'Espiritual': { bg: 'bg-purple-50', text: 'text-purple-700', border: 'border-purple-200', highlight: 'border-l-purple-500', headerBg: 'bg-purple-100/50', indicator: 'bg-purple-500' }
            };
            const theme = themes[report.purpose] || themes['Convivencia'];

            // Update selector buttons styling
            document.querySelectorAll('.report-selector-btn').forEach(btn => {
                const isSelected = btn.dataset.id == reportId;
                const btnPurpose = btn.dataset.purpose;
                const btnTheme = themes[btnPurpose] || themes['Convivencia'];
                
                btn.classList.toggle('bg-white', isSelected);
                btn.classList.toggle('shadow-md', isSelected);
                btn.classList.toggle('border-slate-200', isSelected);
                btn.classList.toggle('scale-[1.02]', isSelected);
                
                const indicator = btn.querySelector('.indicator');
                if (indicator) {
                    indicator.className = `indicator w-1 h-8 rounded-full transition-colors ${isSelected ? btnTheme.indicator : 'bg-slate-200'}`;
                }
            });
            
            // Dispatch event to update Alpine state for tabs color
            window.dispatchEvent(new CustomEvent('update-theme', { detail: { 
                purpose: report.purpose,
                indicator: theme.indicator,
                text: theme.text
            }}));

            contentArea.innerHTML = `
                <!-- Objetivo Tab Content -->
                <div x-show="activeTab === 'objective'" class="space-y-6">
                    <div class="bg-white rounded-xl border border-slate-200 ${theme.highlight} shadow-sm overflow-hidden border-l-4">
                        <div class="${theme.headerBg} px-5 py-3 border-b border-slate-100 flex justify-between items-center text-slate-800">
                            <h4 class="text-[11px] font-black uppercase tracking-widest">OBJETIVO PRINCIPAL DEL ACOMPAÑAMIENTO</h4>
                        </div>
                        <div class="p-5">
                            <p class="text-[15px] font-medium text-slate-800 leading-relaxed italic">"${report.objective || 'Sin objetivo definido'}"</p>
                        </div>
                    </div>
                </div>

                <!-- Observations Tab Content -->
                <div x-show="activeTab === 'observations'" class="space-y-4" x-cloak>
                    <h4 class="text-[11px] font-black text-slate-400 uppercase tracking-widest mb-2 px-1">Línea de tiempo de Seguimiento</h4>
                    <div class="space-y-4">
                        ${report.observations?.length > 0 ? report.observations.map(obs => `
                            <div class="bg-white p-4 rounded-xl border border-slate-200 shadow-sm border-l-4 border-l-inst-blue">
                                <div class="flex justify-between items-center mb-2">
                                    <span class="text-[10px] font-black text-inst-blue uppercase">OBSERVACIÓN REGISTRADA</span>
                                    <span class="text-[11px] font-bold text-slate-600">${new Date(obs.date_log).toLocaleDateString()}</span>
                                </div>
                                <p class="text-[13px] text-slate-700 leading-relaxed font-semibold">${obs.content}</p>
                                <div class="mt-3 pt-2 border-t border-slate-100 text-[10px] font-black text-slate-500 text-right">
                                    REGISTRADO POR: ${obs.created_by?.full_name || 'Desconocido'}
                                </div>
                            </div>
                        `).join('') : `
                            <div class="bg-white p-10 rounded-xl border border-dashed border-slate-200 text-center">
                                <p class="text-xs text-slate-400 font-bold">No hay observaciones registradas en este proceso.</p>
                            </div>
                        `}
                    </div>
                </div>

                <!-- Recommendations Tab Content -->
                <div x-show="activeTab === 'recommendations'" class="space-y-4" x-cloak>
                    <h4 class="text-[11px] font-black text-slate-400 uppercase tracking-widest mb-2 px-1">Plan de Actividades / Sugerencias</h4>
                    <div class="space-y-4">
                        ${report.recommendations?.length > 0 ? report.recommendations.map(rec => `
                            <div class="bg-white p-4 rounded-xl border border-slate-200 shadow-sm border-l-4 border-l-emerald-500">
                                <div class="flex justify-between items-center mb-2">
                                    <span class="text-[10px] font-black text-emerald-600 uppercase">RECOMENDACIÓN TÉCNICA</span>
                                    <span class="text-[11px] font-bold text-slate-600">${new Date(rec.date_log).toLocaleDateString()}</span>
                                </div>
                                <p class="text-[13px] text-slate-700 leading-relaxed font-semibold">${rec.content}</p>
                                <div class="mt-3 pt-2 border-t border-slate-100 text-[10px] font-black text-slate-500 text-right">
                                    REGISTRADO POR: ${rec.created_by?.full_name || 'Desconocido'}
                                </div>
                            </div>
                        `).join('') : `
                            <div class="bg-white p-10 rounded-xl border border-dashed border-slate-200 text-center">
                                <p class="text-xs text-slate-400 font-bold">Aún no se han registrado recomendaciones específicas.</p>
                            </div>
                        `}
                    </div>
                </div>
            `;
        };

        // Populate Report Selector in Sidebar
        selectorArea.innerHTML = studentReports.map(r => `
            <button onclick="window.renderModalReportContent(${r.id})" 
                data-id="${r.id}"
                data-purpose="${r.purpose}"
                class="report-selector-btn w-full flex items-center gap-3 p-3 rounded-xl border border-transparent hover:bg-white hover:shadow-sm transition-all text-left">
                <div class="indicator w-1 h-8 rounded-full bg-slate-200 transition-colors"></div>
                <div class="flex-1">
                    <span class="block text-[11px] font-black text-slate-700 uppercase leading-none mb-1">${r.purpose}</span>
                    <span class="block text-[9px] text-slate-400 font-bold uppercase tracking-tighter">${r.status}</span>
                </div>
                <i class="bi bi-chevron-right text-slate-300"></i>
            </button>
        `).join('');

        modal.classList.remove('hidden');
        
        // Initial render of the first report
        const firstReportId = studentReports[0].id;
        window.dispatchEvent(new CustomEvent('open-modal', { detail: { firstId: firstReportId } }));
        window.renderModalReportContent(firstReportId);
    };

    function applyFilters() {
        const nameVal = filterName.value.toLowerCase();
        const purposeVal = filterPurpose.value;
        const statusVal = filterStatus.value;
        const sectionVal = filterSection.value;
        const courseVal = filterCourse.value;
        const periodVal = filterPeriod.value;

        const filtered = allReports.filter(r => {
            const matchesName = !nameVal || r.student?.full_name.toLowerCase().includes(nameVal);
            const matchesPurpose = !purposeVal || r.purpose === purposeVal;
            const matchesStatus = !statusVal || r.status === statusVal;
            const matchesSection = !sectionVal || r.student?.section === sectionVal;
            const matchesCourse = !courseVal || r.student?.course === courseVal;
            const matchesPeriod = !periodVal || r.academic_period === periodVal;
            return matchesName && matchesPurpose && matchesStatus && matchesSection && matchesCourse && matchesPeriod;
        });
        renderTable(filtered);
    }

    [filterName, filterPurpose, filterStatus, filterSection, filterCourse, filterPeriod].forEach(el => {
        if (el) el.addEventListener('input', applyFilters);
    });

    fetchReports();
});
