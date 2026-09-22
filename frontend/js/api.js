/* ============================================================
   Cliente API — capa de acceso al backend FastAPI
   ============================================================ */

// En local (localhost/127.0.0.1) apunta al backend local; en producción usa
// la URL pública del backend desplegado en Render.
const PRODUCTION_API_URL = 'https://sistema-proveedores-ia.onrender.com';
const isLocalHost = ['localhost', '127.0.0.1'].includes(window.location.hostname);
const API_ROOT_URL = isLocalHost ? 'http://localhost:8000' : PRODUCTION_API_URL;
const API_BASE_URL = `${API_ROOT_URL}/api/v1`;

async function apiFetch(endpoint, options = {}) {
    let response;
    try {
        response = await fetch(`${API_BASE_URL}${endpoint}`, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers,
            },
            ...options,
        });
    } catch (networkError) {
        throw new Error('No se pudo conectar con el servidor. Verifica que el backend esté en ejecución.');
    }

    if (response.status === 204) {
        return null;
    }

    let data = null;
    try {
        data = await response.json();
    } catch (parseError) {
        data = null;
    }

    if (!response.ok) {
        const detail = (data && data.detail) ? data.detail : `Error HTTP ${response.status}`;
        throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail));
    }

    return data;
}

function buildQuery(params = {}) {
    const usable = Object.entries(params).filter(([, v]) => v !== undefined && v !== null && v !== '');
    if (usable.length === 0) return '';
    const search = new URLSearchParams();
    usable.forEach(([k, v]) => search.append(k, v));
    return `?${search.toString()}`;
}

const api = {
    async health() {
        const res = await fetch(`${API_ROOT_URL}/health`);
        if (!res.ok) throw new Error('Backend no disponible');
        return res.json();
    },

    proveedores: {
        list: (params) => apiFetch(`/proveedores/${buildQuery(params)}`),
        get: (id) => apiFetch(`/proveedores/${id}`),
        create: (data) => apiFetch('/proveedores/', { method: 'POST', body: JSON.stringify(data) }),
        update: (id, data) => apiFetch(`/proveedores/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
        remove: (id) => apiFetch(`/proveedores/${id}`, { method: 'DELETE' }),
    },

    productos: {
        list: (params) => apiFetch(`/productos/${buildQuery(params)}`),
        get: (id) => apiFetch(`/productos/${id}`),
        create: (data) => apiFetch('/productos/', { method: 'POST', body: JSON.stringify(data) }),
        update: (id, data) => apiFetch(`/productos/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
        remove: (id) => apiFetch(`/productos/${id}`, { method: 'DELETE' }),
    },

    proveedorProductos: {
        list: (params) => apiFetch(`/proveedor-productos/${buildQuery(params)}`),
        get: (id) => apiFetch(`/proveedor-productos/${id}`),
        create: (data) => apiFetch('/proveedor-productos/', { method: 'POST', body: JSON.stringify(data) }),
        update: (id, data) => apiFetch(`/proveedor-productos/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
        remove: (id) => apiFetch(`/proveedor-productos/${id}`, { method: 'DELETE' }),
    },

    historial: {
        list: (params) => apiFetch(`/historial-desempeno/${buildQuery(params)}`),
        get: (id) => apiFetch(`/historial-desempeno/${id}`),
        metricasProveedor: (proveedorId) => apiFetch(`/historial-desempeno/proveedor/${proveedorId}/metricas`),
        porProducto: (productoId, params) => apiFetch(`/historial-desempeno/producto/${productoId}${buildQuery(params)}`),
        create: (data) => apiFetch('/historial-desempeno/', { method: 'POST', body: JSON.stringify(data) }),
        remove: (id) => apiFetch(`/historial-desempeno/${id}`, { method: 'DELETE' }),
    },

    evaluaciones: {
        list: (params) => apiFetch(`/evaluaciones/${buildQuery(params)}`),
        get: (id) => apiFetch(`/evaluaciones/${id}`),
        compatibles: (id) => apiFetch(`/evaluaciones/${id}/proveedores-compatibles`),
        procesar: (id) => apiFetch(`/evaluaciones/${id}/procesar`, { method: 'POST' }),
        resultados: (id) => apiFetch(`/evaluaciones/${id}/resultados`),
        informeAgentes: (id) => apiFetch(`/evaluaciones/${id}/informe-agentes`),
        create: (data) => apiFetch('/evaluaciones/', { method: 'POST', body: JSON.stringify(data) }),
        remove: (id) => apiFetch(`/evaluaciones/${id}`, { method: 'DELETE' }),
    },
};

/* ============================== Helpers de UI compartidos ============================== */

function escapeHtml(value) {
    if (value === null || value === undefined) return '';
    return String(value)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

function formatCurrency(value) {
    const num = Number(value);
    if (Number.isNaN(num)) return 'S/ 0.00';
    return `S/ ${num.toLocaleString('es-PE', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function formatDate(value) {
    if (!value) return '—';
    try {
        const d = new Date(value);
        return d.toLocaleDateString('es-PE', { year: 'numeric', month: 'short', day: '2-digit' });
    } catch {
        return value;
    }
}

function formatDateTime(value) {
    if (!value) return '—';
    try {
        const d = new Date(value);
        return d.toLocaleString('es-PE', { year: 'numeric', month: 'short', day: '2-digit', hour: '2-digit', minute: '2-digit' });
    } catch {
        return value;
    }
}

function showToast(message, type = 'info') {
    let root = document.getElementById('toast-root');
    if (!root) {
        root = document.createElement('div');
        root.id = 'toast-root';
        document.body.appendChild(root);
    }
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    root.appendChild(toast);
    setTimeout(() => toast.remove(), 4200);
}

function loadingRow(colspan, text = 'Cargando datos...') {
    return `<tr><td colspan="${colspan}"><div class="loading-state"><div class="spinner"></div><span>${escapeHtml(text)}</span></div></td></tr>`;
}

function errorRow(colspan, message) {
    return `<tr><td colspan="${colspan}"><div class="error-state">⚠ ${escapeHtml(message)}</div></td></tr>`;
}

function emptyRow(colspan, text = 'No hay registros todavía.') {
    return `<tr><td colspan="${colspan}"><div class="empty-state">${escapeHtml(text)}</div></td></tr>`;
}

function estadoBadge(estado) {
    const value = (estado || '').toLowerCase();
    const map = {
        activo: 'badge-success',
        inactivo: 'badge-danger',
        pendiente: 'badge-warning',
        procesada: 'badge-success',
        procesado: 'badge-success',
        'en proceso': 'badge-info',
        cancelada: 'badge-danger',
    };
    const cls = map[value] || 'badge-neutral';
    return `<span class="badge ${cls}">${escapeHtml(estado || 'Sin estado')}</span>`;
}
