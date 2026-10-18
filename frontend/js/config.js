/* ============================================================
   Configuración del frontend en tiempo de ejecución.

   Sin apiRootUrl, api.js elige el backend automáticamente (local o Render).
   La imagen Docker reemplaza este archivo con apiRootUrl: '' para llamar al
   mismo origen, donde nginx reenvía /api al contenedor del backend.
   ============================================================ */

window.APP_CONFIG = window.APP_CONFIG || {};
