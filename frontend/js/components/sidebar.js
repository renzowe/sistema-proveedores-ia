/* ============================================================
   Componente: Sidebar
   ============================================================ */

const SIDEBAR_LINKS = [
    {
        page: 'dashboard.html',
        label: 'Dashboard',
        icon: '<rect x="3" y="3" width="7" height="9" rx="1.5"></rect><rect x="14" y="3" width="7" height="5" rx="1.5"></rect><rect x="14" y="12" width="7" height="9" rx="1.5"></rect><rect x="3" y="16" width="7" height="5" rx="1.5"></rect>',
    },
    {
        page: 'proveedores.html',
        label: 'Proveedores',
        icon: '<path d="M3 21h18"></path><path d="M5 21V7l7-4 7 4v14"></path><path d="M9 21v-6h6v6"></path>',
    },
    {
        page: 'productos.html',
        label: 'Productos',
        icon: '<path d="M21 8l-9-5-9 5 9 5 9-5z"></path><path d="M3 8v8l9 5 9-5V8"></path><path d="M12 13v8"></path>',
    },
    {
        page: 'desempeno.html',
        label: 'Desempeño',
        icon: '<path d="M3 3v18h18"></path><path d="M7 15l4-5 3 3 5-7"></path>',
    },
    {
        page: 'evaluaciones.html',
        label: 'Evaluaciones',
        icon: '<path d="M9 11l3 3L22 4"></path><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"></path>',
    },
];

function renderSidebar() {
    const container = document.getElementById('sidebar-container');
    if (!container) return;

    const inPages = location.pathname.includes('/pages/');
    const base = inPages ? '' : 'pages/';
    const currentFile = location.pathname.split('/').pop();

    const links = SIDEBAR_LINKS.map((link) => {
        const isActive = currentFile === link.page;
        return `
            <a class="sidebar-link ${isActive ? 'active' : ''}" href="${base}${link.page}">
                <svg viewBox="0 0 24 24" fill="none" stroke-linecap="round" stroke-linejoin="round">${link.icon}</svg>
                <span>${link.label}</span>
            </a>
        `;
    }).join('');

    container.innerHTML = `
        <nav class="sidebar">
            <div class="sidebar-section-label">Navegación</div>
            ${links}
        </nav>
    `;
}

document.addEventListener('DOMContentLoaded', renderSidebar);
