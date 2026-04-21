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
            <tr class="hover:bg-gray-50 transition-colors group cursor-pointer" onclick="openReportDetail('${r.student?.code}')">
                <td class="px-4 py-3 border-r border-gray-100 text-center" onclick="event.stopPropagation()">
                    <input type="checkbox" class="rounded border-gray-300 text-inst-blue w-3.5 h-3.5 cursor-pointer shadow-sm">
                </td>
                <td class="px-4 py-3 border-r border-gray-100">
                    <div class="flex items-center gap-3">
                        <div class="w-8 h-8 rounded-full bg-slate-100 flex items-center justify-center border border-slate-200 overflow-hidden shrink-0 relative shadow-sm">
                            <img src="/archivos/img_pruebas/${encodeURIComponent((r.student?.full_name || '').trim().toUpperCase())}.jpg" class="w-full h-full object-cover absolute inset-0 z-10" onerror="this.style.display='none'">
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
                    <button onclick="openReportDetail('${r.student?.code}')" class="text-inst-blue hover:underline font-bold text-[10px] uppercase tracking-wider">Ver detalle</button>
                </td>
            </tr>
        `).join('');
    }

    window.openReportDetail = function(studentCode) {
        console.log("Iniciando apertura de detalle para:", studentCode);
        const studentReports = allReports.filter(r => r.student?.code === studentCode);
        
        if (studentReports.length === 0) {
            console.warn("No se encontraron reportes para el código:", studentCode);
            return;
        }

        const student = studentReports[0].student;
        const infoArea = document.getElementById('modal-student-info');
        const selectorArea = document.getElementById('modal-report-selector');
        
        // CORRECCIÓN: Usar backticks para template literals y trim para evitar espacios en blanco
        const studentPhotoUrl = `/archivos/img_pruebas/${encodeURIComponent((student.full_name || '').trim().toUpperCase())}.jpg`;

        console.log("Cargando información del estudiante:", student.full_name);

        // Update Student Info Card with refined radius
        infoArea.innerHTML = `
            <div class="bg-white rounded-xl border border-slate-100 shadow-lg shadow-slate-200/40 mb-8 overflow-hidden group transition-all">
                <div class="relative h-20 bg-slate-50 border-b border-slate-100 flex items-center px-6">
                    <div class="w-14 h-14 rounded-xl bg-white p-1 shadow-md transform transition-transform group-hover:scale-105 border border-slate-100">
                        <div class="w-full h-full rounded-lg bg-slate-50 flex items-center justify-center overflow-hidden relative">
                            <img src="${studentPhotoUrl}" class="w-full h-full object-cover absolute inset-0 z-10" onerror="this.style.display='none'">
                            <span class="text-slate-300 font-black text-lg uppercase">${(student.full_name || 'U').split(' ').map(n=>n[0]).join('').substring(0,2)}</span>
                        </div>
                    </div>
                    <div class="ml-4">
                        <h3 class="text-[13px] font-black text-slate-800 uppercase leading-none">${student.full_name}</h3>
                        <span class="text-[9px] font-black text-slate-400 uppercase tracking-[2px]">${student.code}</span>
                    </div>
                </div>
            </div>
            <div class="bg-slate-50 border-2 border-slate-100 p-6 rounded-none space-y-4">
                <div class="flex items-center gap-4">
                    <div class="w-16 h-16 bg-[#2F4DAA] text-white flex items-center justify-center font-black text-2xl rounded-none shadow-lg">
                        ${student.full_name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase()}
                    </div>
                    <div>
                        <h3 class="text-sm font-black text-slate-950 leading-tight uppercase tracking-tighter">${student.full_name}</h3>
                        <span class="inline-block mt-1 px-2 py-0.5 bg-slate-200 text-slate-600 text-[9px] font-black uppercase tracking-widest">${student.course}</span>
                    </div>
                </div>
                <div class="pt-4 border-t border-slate-100 space-y-2">
                    <div class="flex justify-between items-center bg-white p-3 border border-slate-100">
                        <span class="text-[9px] font-black text-slate-400 uppercase tracking-widest">Código</span>
                        <span class="text-xs font-black text-slate-950">${student.code}</span>
                    </div>
                </div>
            </div>
        `;

        window.renderDetailReportContent = function(reportId) {
            const report = allReports.find(r => r.id == reportId);
            const contentArea = document.getElementById('modal-content-area');
            if (!report || !contentArea) return;

            const themes = {
                'Convivencia': { bg: 'bg-emerald-50', border: 'border-emerald-100', text: 'text-emerald-800', accent: 'bg-emerald-400', highlight: 'border-l-emerald-400' },
                'Académico': { bg: 'bg-blue-50', border: 'border-blue-100', text: 'text-blue-800', accent: 'bg-blue-400', highlight: 'border-l-blue-400' },
                'Psicoafectivo': { bg: 'bg-rose-50', border: 'border-rose-100', text: 'text-rose-800', accent: 'bg-rose-400', highlight: 'border-l-rose-400' },
                'Espiritual': { bg: 'bg-purple-50', border: 'border-purple-100', text: 'text-purple-800', accent: 'bg-purple-400', highlight: 'border-l-purple-400' }
            };

            document.querySelectorAll('.report-selector-btn').forEach(btn => {
                const isSelected = btn.dataset.id == reportId;
                const btnPurpose = btn.dataset.purpose;
                const btnTheme = themes[btnPurpose] || themes['Convivencia'];
                
                btn.className = "report-selector-btn w-full flex items-center gap-4 p-4 rounded-xl border transition-all text-left mb-3 group " + 
                                (isSelected ? `${btnTheme.bg} ${btnTheme.border} shadow-sm scale-[1.01]` : "bg-white border-slate-100 font-bold hover:bg-slate-50 text-slate-700 shadow-none");
                
                const title = btn.querySelector('.title');
                const subtitle = btn.querySelector('.subtitle');
                const dot = btn.querySelector('.status-dot');

                if (isSelected) {
                    title.className = `title block text-[11px] font-black uppercase leading-none mb-1.5 ${btnTheme.text}`;
                    subtitle.className = `subtitle block text-[9px] font-bold uppercase tracking-tighter ${btnTheme.text} opacity-70`;
                    if (dot) dot.className = `status-dot w-2 h-8 rounded-full ${btnTheme.accent} transition-all`;
                } else {
                    title.className = "title block text-[11px] font-black uppercase leading-none mb-1.5 text-slate-700";
                    subtitle.className = "subtitle block text-[9px] font-bold uppercase tracking-tighter text-slate-400";
                    if (dot) {
                        const statusColor = btn.dataset.status === 'ATENDIDO' ? 'bg-emerald-400' : 'bg-amber-400';
                        dot.className = `status-dot w-1.5 h-1.5 rounded-full ${statusColor} transition-all`;
                    }
                }
            });

            contentArea.innerHTML = `
                <div class="space-y-12 w-full">
                    <div x-show="activeTab === 'objective'" x-transition class="animate-in fade-in slide-in-from-bottom-4 duration-300">
                        <div class="bg-white border-l-[12px] border-[#2F4DAA] shadow-2xl p-12 rounded-none">
                            <div class="flex items-center gap-3 mb-8">
                                <i class="bi bi-info-circle-fill text-[#2F4DAA] opacity-40"></i>
                                <span class="text-[11px] font-black text-[#2F4DAA] uppercase tracking-[0.4em]">Propósito Fundamental</span>
                            </div>
                            <p class="text-[36px] font-black text-slate-950 leading-[1.1] tracking-tighter italic ring-0 outline-none">"${report.objective || 'Sin contenido'}"</p>
                            <div class="mt-12 pt-8 border-t border-slate-100 flex justify-between items-end">
                                <div class="flex items-center gap-4">
                                    <div class="w-12 h-12 bg-[#2F4DAA] text-white flex items-center justify-center font-black text-xs rounded-none shadow-lg">${report.created_by?.full_name[0] || 'A'}</div>
                                    <div>
                                        <span class="text-[9px] font-black text-slate-400 uppercase block tracking-widest">Referente del Caso</span>
                                        <span class="text-sm font-black text-slate-950">${report.created_by?.full_name || 'Admin Global'}</span>
                                    </div>
                                </div>
                                <div class="text-right">
                                    <span class="text-[9px] font-black text-slate-400 uppercase block tracking-widest">Apertura Oficial</span>
                                    <span class="text-sm font-black text-slate-950">${new Date(report.created_at).toLocaleDateString('es-ES', { day: '2-digit', month: 'long', year: 'numeric' })}</span>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div x-show="activeTab === 'observations'" x-transition class="space-y-6">
                        ${report.observations?.length > 0 ? report.observations.map(obs => `
                            <div class="bg-white border-l-8 border-blue-600 shadow-xl p-10 rounded-none transform transition-all">
                                <div class="flex justify-between items-center mb-6">
                                    <span class="px-5 py-2 bg-blue-600 text-white text-[10px] font-black uppercase tracking-[0.2em] rounded-none">Entrada de Seguimiento</span>
                                    <span class="text-[10px] font-black text-slate-400 uppercase">${new Date(obs.date_log).toLocaleDateString('es-ES', {day:'2-digit', month:'short', year:'numeric'})}</span>
                                </div>
                                <p class="text-[17px] font-bold text-slate-950 leading-relaxed">${obs.content}</p>
                                <div class="mt-8 pt-6 border-t border-slate-50 flex items-center justify-between">
                                    <span class="text-[10px] font-black text-slate-400 uppercase tracking-widest">Autor: ${obs.created_by?.full_name || 'Especialista'}</span>
                                    <i class="bi bi-pencil-square text-blue-600 opacity-20 text-2xl"></i>
                                </div>
                            </div>
                        `).join('') : `
                            <div class="bg-blue-50 border-2 border-dashed border-blue-100 p-20 text-center rounded-none">
                                <i class="bi bi-journal-x text-5xl text-blue-200 mb-4 block"></i>
                                <p class="text-blue-400 font-bold uppercase text-xs tracking-widest">Sin carpetas de observaciones registradas</p>
                            </div>
                        `}
                    </div>

                    <div x-show="activeTab === 'recommendations'" x-transition class="space-y-6">
                        ${report.recommendations?.length > 0 ? report.recommendations.map(rec => `
                            <div class="bg-white border-l-8 border-emerald-600 shadow-xl p-10 rounded-none relative">
                                <div class="flex items-center gap-4 mb-6">
                                    <div class="w-10 h-10 bg-emerald-600 text-white flex items-center justify-center rounded-none shadow-lg">
                                        <i class="bi bi-shield-check text-xl"></i>
                                    </div>
                                    <div>
                                        <h4 class="text-[11px] font-black text-emerald-700 uppercase tracking-widest">Plan de Acción Sugerido</h4>
                                        <span class="text-[10px] font-black text-slate-400 uppercase">${new Date(rec.date_log).toLocaleDateString()}</span>
                                    </div>
                                </div>
                                <p class="text-lg font-bold text-slate-950 leading-relaxed italic border-l-4 border-emerald-50 pl-8">${rec.content}</p>
                                <div class="mt-8 pt-6 border-t border-slate-50 text-right">
                                    <span class="text-[10px] font-black text-emerald-600 uppercase tracking-widest leading-none flex items-center justify-end gap-2">
                                        <i class="bi bi-award-fill"></i> Oficializado por: ${rec.created_by?.full_name || 'Coordinación'}
                                    </span>
                                </div>
                            </div>
                        `).join('') : `
                            <div class="bg-emerald-50 border-2 border-dashed border-emerald-100 p-20 text-center rounded-none">
                                <i class="bi bi-bookmark-check text-5xl text-emerald-200 mb-4 block"></i>
                                <p class="text-emerald-400 font-bold uppercase text-xs tracking-widest">No se han emitido recomendaciones aún</p>
                            </div>
                        `}
                    </div>
                </div>
            `;
        };

        selectorArea.innerHTML = studentReports.map(r => `
            <button onclick="window.renderDetailReportContent(${r.id})" 
                data-id="${r.id}"
                data-purpose="${r.purpose}"
                data-status="${r.status}"
                class="report-selector-btn w-full flex items-center gap-4 p-4 rounded-xl border transition-all text-left mb-3 group bg-white border-slate-100 hover:bg-slate-50">
                <div class="flex-1">
                    <span class="title block text-[11px] font-black text-slate-700 uppercase leading-none mb-1.5">${r.purpose}</span>
                    <div class="flex items-center gap-2">
                        <span class="status-dot w-1.5 h-1.5 rounded-full ${r.status === 'ATENDIDO' ? 'bg-emerald-400' : 'bg-amber-400'}"></span>
                        <span class="subtitle block text-[9px] text-slate-400 font-bold uppercase tracking-tighter">${r.status}</span>
                    </div>
                </div>
                <i class="bi bi-chevron-right text-slate-300 text-xs transition-transform group-hover:translate-x-1"></i>
            </button>
        `).join('');
        
        const firstReportId = studentReports[0].id;
        console.log("Enviando evento open-detail...");
        window.dispatchEvent(new CustomEvent('open-detail', { detail: { firstId: firstReportId } }));
        window.renderDetailReportContent(firstReportId);
        console.log("Carga de detalle finalizada.");
    };

    // Alias de compatibilidad para evitar errores si el navegador tiene caché antigua
    window.openStudentModal = window.openReportDetail;

    function applyFilters() {
        if (!allReports) return;
        
        const nameVal = filterName ? filterName.value.toLowerCase() : '';
        const purposeVal = filterPurpose ? filterPurpose.value : '';
        const statusVal = filterStatus ? filterStatus.value : '';
        const sectionVal = filterSection ? filterSection.value : '';
        const courseVal = filterCourse ? filterCourse.value : '';
        const periodVal = filterPeriod ? filterPeriod.value : '';

        const filtered = allReports.filter(r => {
            const matchesName = !nameVal || (r.student?.full_name || '').toLowerCase().includes(nameVal);
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
