document.addEventListener('DOMContentLoaded', () => {
    const fileInput = document.getElementById('excel-upload-admin');
    
    if(fileInput) {
        fileInput.addEventListener('change', async (e) => {
            const file = e.target.files[0];
            if(!file) return;
            
            if(!confirm(`¿Seguro que deseas importar el archivo "${file.name}"? Esto agregará o actualizará estudiantes.`)) {
                fileInput.value = '';
                return;
            }

            const formData = new FormData();
            formData.append('file', file);

            try {
                // Show loading
                const btn = document.getElementById('btn-import-students');
                const originalText = btn.innerHTML;
                btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin mr-2"></i> Subiendo...';
                btn.disabled = true;

                const response = await fetch('/api/import/students', {
                    method: 'POST',
                    body: formData
                });

                const result = await response.json();
                
                if(response.ok) {
                    alert(`Importación exitosa!\nProcesados: ${result.success || 'N/A'}`);
                    // Optional: reload or update UI
                } else {
                    alert('Error en la importación: ' + (result.detail || JSON.stringify(result)));
                }
            } catch (error) {
                alert('Error de red: ' + error);
            } finally {
                // Reset
                const btn = document.getElementById('btn-import-students');
                if(btn) {
                    btn.innerHTML = originalText;
                    btn.disabled = false;
                }
                fileInput.value = '';
            }
        });
    }
});
