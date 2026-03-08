# Especificaciones Técnicas: Modales de Seguimiento (Observaciones y Recomendaciones)

Este documento detalla la estructura, estilo y lógica de los modales de visualización empleados en el **Sistema de Acompañamiento Integral (SAI)**. El objetivo es permitir la replicación exacta de estos componentes en otras aplicaciones.

## 1. Concepto de Diseño (Aesthetics)
El diseño sigue una estética inspirada en interfaces profesionales (tipo ESET/Admin dashboards):
- **Tipografía:** [Outfit](https://fonts.google.com/specimen/Outfit) (Sans-serif).
- **Iconografía:** FontAwesome 6.4.0.
- **Paleta de Colores:** 
  - Cabecera: Azul Marino Oscuro (`#1e293b / slate-800`).
  - Fondo de Contenedor: Gris muy claro (`#f8fafc / slate-50`).
  - Bordes: Gris suave (`#e2e8f0 / slate-200`).
  - Acentos: Azul Brillante (`#0091d3`) para observaciones y Esmeralda (`#10b981`) para recomendaciones.

---

## 2. Estructura HTML (Modales de Visualización)

### A. Modal: Ver Historial de Observaciones
Este modal presenta una lista cronológica inversa de entradas de seguimiento.

```html
<!-- ID: view-observations-modal -->
<div id="view-observations-modal" class="fixed inset-0 z-[60] hidden bg-gray-900/40 backdrop-blur-sm flex justify-center items-center p-4">
    <div class="bg-white rounded shadow-xl w-full max-w-5xl flex flex-col max-h-[90vh] overflow-hidden">
        
        <!-- Header: Dark Blue Bar -->
        <div class="bg-[#1e293b] px-6 py-4 flex justify-between items-center rounded-t">
            <h3 class="text-sm font-bold text-white uppercase tracking-wider">
                OBSERVACIONES FIN EDUCATIVO: <span class="text-blue-300">[[NOMBRE_FIN]]</span>
            </h3>
            <button onclick="closeViewObsModal()" class="text-slate-400 hover:text-white transition-colors">
                <i class="fa-solid fa-times text-xl"></i>
            </button>
        </div>

        <!-- Content Area: Clean Rows -->
        <div class="p-6 overflow-y-auto bg-slate-50 flex-1">
            <div class="space-y-3">
                <!-- Iteración por cada observación -->
                <div class="bg-white border border-slate-200 rounded p-4 flex gap-4 hover:shadow-sm transition-shadow">
                    <!-- Icono Ojo -->
                    <div class="shrink-0 flex items-center justify-center w-10 border-r border-slate-100">
                        <i class="fa-regular fa-eye text-slate-400"></i>
                    </div>

                    <!-- Columna de Fecha -->
                    <div class="shrink-0 w-32 flex flex-col justify-center">
                        <span class="text-xs font-bold text-slate-700">[[FECHA_DD_MM_AAAA]]</span>
                        <span class="text-[10px] text-slate-400 uppercase">Fecha Registro</span>
                    </div>

                    <!-- Columna de Contenido -->
                    <div class="flex-1 border-l border-slate-100 pl-4 py-1">
                        <p class="text-sm text-slate-700 leading-relaxed">[[CONTENIDO_DE_LA_OBSERVACION]]</p>
                        <div class="mt-2 text-[10px] text-slate-400 uppercase font-bold text-right">
                            Registrado por: [[NOMBRE_USUARIO]]
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Footer -->
        <div class="px-6 py-3 bg-gray-100 border-t border-slate-200 flex justify-end">
            <button type="button" onclick="closeViewObsModal()" class="px-5 py-2 bg-[#1e293b] hover:bg-slate-800 text-white text-xs font-bold uppercase rounded">
                Cerrar
            </button>
        </div>
    </div>
</div>
```

### B. Modal: Ver Historial de Recomendaciones
Idéntico al anterior, pero con acentos en color verde/esmeralda para diferenciar visualmente el tipo de dato.

---

## 3. Lógica JavaScript (Controladores)

Para abrir y cerrar los modales sin recargar la página:

```javascript
/* Control de Visibilidad */
function openViewObsModal() {
    document.getElementById('view-observations-modal').classList.remove('hidden');
}

function closeViewObsModal() {
    document.getElementById('view-observations-modal').classList.add('hidden');
}

/* Nota: Se aplica la misma lógica para Recommendations cambiando los IDs */
```

---

## 4. Contrato de Datos (Contexto Backend)

Para renderizar las filas, el componente espera un objeto de reporte que contenga un array de observaciones.

### Ejemplo de JSON esperado:
```json
{
  "id": 123,
  "purpose": "Académico",
  "observations": [
    {
      "id": 1,
      "date_log": "2023-10-27T10:00:00Z",
      "content": "El estudiante muestra mejora en la participación...",
      "created_by": {
        "full_name": "Juan Pérez"
      }
    }
  ]
}
```

### Comportamiento Requerido:
1. **Ordenamiento:** Las observaciones deben presentarse de la más reciente a la más antigua (`sort reverse by date_log`).
2. **Scroll:** El cuerpo del modal (`modal-content`) debe tener scroll independiente si la lista es larga, manteniendo el **Header** y **Footer** fijos.
3. **Responsive:** En pantallas pequeñas, el modal ocupa el 100% del ancho con márgenes mínimos.

---

## 5. Dependencias Necesarias
- **Tailwind CSS:** Para el sistema de utilidad (flex, shadow, text-sm, etc.).
- **FontAwesome 6.4:** Iconos `fa-eye`, `fa-times`, `fa-list`.
- **Google Fonts (Outfit):** Para mantener la legibilidad premium.
