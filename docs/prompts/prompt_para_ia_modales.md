# Prompt de Implementación para IA: Modales de Seguimiento Premium

Copia y pega el siguiente prompt en tu chat con la IA (Claude, GPT, etc.) para que te genere los modales exactamente como los necesitas:

---

## PROMPT PARA LA IA

"Necesito que implementes dos modales de visualización para un sistema de reportes utilizando **HTML y Tailwind CSS**. El diseño debe ser premium, limpio y profesional, siguiendo estas directrices:

### 1. Requerimientos de Estilo:
- **Tipografía:** Usar la fuente 'Outfit' de Google Fonts.
- **Iconografía:** Usar FontAwesome 6 per iconas.
- **Colores:** Header en azul pizarra oscuro (`bg-[#1e293b]`), textos en `slate-700` y acentos en azul (`#0091d3`) para una versión y verde esmeralda (`#10b981`) para la otra.
- **Efectos:** El fondo debe tener un desenfoque (`backdrop-blur-sm`) y una opacidad gris oscura (`bg-gray-900/40`).

### 2. Estructura del Modal (ID: view-observations-modal):
- **Header:** Fondo oscuro, título en mayúsculas blancas. Debe mostrar el nombre del fin educativo analizado. Botón de cierre (X) que cambie a blanco al pasar el mouse.
- **Contenido (Listado):** 
  - Las observaciones deben venir de un array de objetos.
  - Cada fila debe ser un card blanco con borde suave, con un icono de ojo (`fa-eye`) a la izquierda.
  - Debe mostrar la fecha formateada de manera prominente a la izquierda.
  - El contenido de la observación debe tener un interlineado relajado (`leading-relaxed`).
  - Al final de cada fila, a la derecha, debe decir 'Registrado por: [Nombre]' en tamaño pequeño y negrita.
- **Footer:** Fondo gris claro, botón 'Cerrar' centrado a la derecha con el mismo color oscuro del header.

### 3. Lógica JavaScript:
- Crear funciones `openModal` y `closeModal` que manipulen la clase `hidden`.
- Asegurar que el cuerpo del modal tenga scroll independiente (`overflow-y-auto`) pero el header y footer permanezcan fijos.

### 4. Modelo de Datos Esperado:
Genera el código asumiendo que recibes un objeto llamado 'report' que tiene una lista de 'observations', cada una con los campos: `date_log`, `content` y `created_by.full_name`."

---

## CÓDIGO DE REFERENCIA (Para inspección manual)

Si prefieres darle el código fuente directamente, aquí tienes el bloque exacto del modal de observaciones:

```html
<!-- Modal: Ver Historial Observaciones -->
<div id="view-observations-modal" class="fixed inset-0 z-[60] hidden bg-gray-900/40 backdrop-blur-sm flex justify-center items-center p-4">
    <div class="bg-white rounded shadow-xl w-full max-w-5xl transform flex flex-col max-h-[90vh] overflow-hidden">
        <!-- Header -->
        <div class="bg-[#1e293b] px-6 py-4 flex justify-between items-center rounded-t">
            <h3 class="text-sm font-bold text-white uppercase tracking-wider">
                OBSERVACIONES FIN EDUCATIVO: <span class="text-blue-300">{{ report.purpose.value }}</span>
            </h3>
            <button onclick="closeViewObsModal()" class="text-slate-400 hover:text-white">
                <i class="fa-solid fa-times text-xl"></i>
            </button>
        </div>
        <!-- Content -->
        <div class="p-6 overflow-y-auto bg-slate-50 flex-1">
            <div class="space-y-3">
                {% if report.observations %}
                {% for obs in report.observations|sort(attribute='date_log', reverse=True) %}
                <div class="bg-white border border-slate-200 rounded p-4 flex gap-4 hover:shadow-sm">
                    <div class="shrink-0 flex items-center justify-center w-10 border-r border-slate-100">
                        <i class="fa-regular fa-eye text-slate-400"></i>
                    </div>
                    <div class="shrink-0 w-32 flex flex-col justify-center">
                        <span class="text-xs font-bold text-slate-700">{{ obs.date_log.strftime('%d %B %Y') }}</span>
                        <span class="text-[10px] text-slate-400 uppercase">Fecha Registro</span>
                    </div>
                    <div class="flex-1 border-l border-slate-100 pl-4 py-1">
                        <p class="text-sm text-slate-700 leading-relaxed">{{ obs.content }}</p>
                        <div class="mt-2 text-[10px] text-slate-400 uppercase font-bold text-right">
                            Registrado por: {{ obs.created_by.full_name }}
                        </div>
                    </div>
                </div>
                {% endfor %}
                {% endif %}
            </div>
        </div>
        <!-- Footer -->
        <div class="px-6 py-3 bg-gray-100 border-t border-slate-200 flex justify-end">
            <button onclick="closeViewObsModal()" class="px-5 py-2 bg-[#1e293b] text-white text-xs font-bold uppercase rounded">Cerrar</button>
        </div>
    </div>
</div>
```
