/* ============================================================
   Componentes UI compartidos: StatCard, Alert, búsqueda + paginación
   ============================================================ */

// Cualquier elemento estático con data-icon="nombre" se hidrata automáticamente.
// Para HTML inyectado dinámicamente (después del primer render), llamar renderIcons().
function renderIcons(root = document) {
    root.querySelectorAll('[data-icon]').forEach((el) => {
        el.innerHTML = icon(el.dataset.icon, { size: Number(el.dataset.iconSize) || 18 });
    });
}

document.addEventListener('DOMContentLoaded', () => renderIcons());

function renderStatCard({ iconName, label, value, tone = '' }) {
    return `
        <div class="stat-card">
            <div class="stat-card-top">
                <span class="stat-card-label">${escapeHtml(label)}</span>
                <span class="icon-tile ${tone}">${icon(iconName, { size: 17 })}</span>
            </div>
            <div class="stat-card-value">${value}</div>
        </div>
    `;
}

function renderAlert({ type = 'info', iconName, title, body }) {
    const iconMap = { info: 'info', success: 'checkCircle', warning: 'alertTriangle', danger: 'alertCircle', ai: 'sparkles' };
    return `
        <div class="alert alert-${type}">
            ${icon(iconName || iconMap[type] || 'info', { size: 18 })}
            <div>
                ${title ? `<div class="alert-title">${escapeHtml(title)}</div>` : ''}
                <div class="alert-body">${body}</div>
            </div>
        </div>
    `;
}

function searchInputHTML(id, placeholder) {
    return `
        <div class="search-input">
            ${icon('search', { size: 16 })}
            <input type="search" id="${id}" placeholder="${escapeHtml(placeholder)}" aria-label="${escapeHtml(placeholder)}">
        </div>
    `;
}

/* ---------- Controlador de tabla: búsqueda + paginación en cliente ---------- */

function createTableController(pageSize = 8) {
    let allItems = [];
    let filtered = [];
    let searchFields = [];
    let searchTerm = '';
    let currentPage = 1;

    function applyFilter() {
        if (!searchTerm) {
            filtered = allItems;
        } else {
            filtered = allItems.filter((item) =>
                searchFields.some((f) => String(item[f] ?? '').toLowerCase().includes(searchTerm))
            );
        }
        currentPage = 1;
    }

    return {
        setItems(items, fields) {
            allItems = items;
            searchFields = fields;
            applyFilter();
        },
        setSearch(term) {
            searchTerm = (term || '').trim().toLowerCase();
            applyFilter();
        },
        goToPage(p) {
            currentPage = p;
        },
        getView() {
            const totalCount = filtered.length;
            const totalPages = Math.max(1, Math.ceil(totalCount / pageSize));
            currentPage = Math.min(Math.max(1, currentPage), totalPages);
            const start = (currentPage - 1) * pageSize;
            return {
                items: filtered.slice(start, start + pageSize),
                currentPage,
                totalPages,
                totalCount,
                pageSize,
            };
        },
    };
}

function paginationHTML(view) {
    if (view.totalCount === 0) return '';
    if (view.totalPages <= 1) {
        return `<div class="pagination"><span class="pagination-info">${view.totalCount} resultado(s)</span></div>`;
    }
    const start = (view.currentPage - 1) * view.pageSize + 1;
    const end = Math.min(view.currentPage * view.pageSize, view.totalCount);
    return `
        <div class="pagination">
            <span class="pagination-info">Mostrando ${start}–${end} de ${view.totalCount}</span>
            <div class="pagination-controls">
                <button type="button" data-page-action="prev" ${view.currentPage <= 1 ? 'disabled' : ''} aria-label="Página anterior">${icon('chevronLeft', { size: 14 })}</button>
                <span class="current-page">${view.currentPage} / ${view.totalPages}</span>
                <button type="button" data-page-action="next" ${view.currentPage >= view.totalPages ? 'disabled' : ''} aria-label="Página siguiente">${icon('chevronRight', { size: 14 })}</button>
            </div>
        </div>
    `;
}

function wirePagination(container, controller, onChange) {
    container.querySelectorAll('[data-page-action]').forEach((btn) => {
        btn.addEventListener('click', () => {
            const view = controller.getView();
            const next = btn.dataset.pageAction === 'next' ? view.currentPage + 1 : view.currentPage - 1;
            controller.goToPage(next);
            onChange();
        });
    });
}
