# 🏢 Estructura del Proyecto (SAI)

Esta es la nueva organización de los archivos para mantener el proyecto limpio y profesional.

## 📂 Directorios Principales

- **`src/`**: Contiene el código fuente principal de la aplicación (FastAPI).
  - `/routers`: Lógica de rutas de API y UI.
  - `/static`: Archivos estáticos (JS, CSS, Imágenes).
  - `/templates`: Plantillas HTML (Jinja2).
- **`docs/`**: Documentación técnica y especificaciones.
  - `/ui`: Guías de diseño y componentes de interfaz.
  - `/prompts`: Guías de instucciones para la IA.
- **`scripts/`**: Automatización y utilidades.
  - `/management`: Scripts de base (sincronización, importación, navegación).
  - `/tests`: Scripts de validación, depuración y verificación.
  - `/maintenance`: Scripts de mantenimiento visual (tipografía, bordes).
- **`data/`**: Datos locales persistentes.
  - `/db`: Base de datos SQLite (`acompanamiento.db`).
  - `/samples`: Archivos de ejemplo (.json).
- **`logs/`**: Registros de actividad y errores.
  - `/temp`: Archivos temporales de log.
- **`archivos/`**: Recursos media y archivos externos (Excel).

## 🚀 Archivos en Raíz (Root)

Se mantienen únicamente los archivos esenciales de configuración y ejecución:
- `.env`: Configuración de variables de entorno (Base de Datos, Secretos).
- `requirements.txt`: Dependencias del proyecto.
- `start_servers.bat` / `run_app.ps1`: Atajos para iniciar la aplicación.
