/* ============================================================
   Componente: Sidebar — navegación empresarial agrupada
   ============================================================ */

const SIDEBAR_GROUPS = [
    {
        label: 'Panel',
        links: [
            { page: 'dashboard.html', label: 'Dashboard', icon: 'dashboard' },
        ],
    },
    {
        label: 'Procurement',
        links: [
            { page: 'proveedores.html', label: 'Proveedores', icon: 'providers' },
            { page: 'productos.html', label: 'Productos', icon: 'products' },
            { page: 'desempeno.html', label: 'Desempeño', icon: 'performance' },
        ],
    },
    {
        label: 'Decisiones',
        links: [
            { page: 'evaluaciones.html', label: 'Evaluaciones', icon: 'evaluations' },
        ],
    },
];

const SECTION_LABEL_OVERRIDES = {
    'evaluacion-detalle.html': 'Detalle de evaluación',
};

function currentSectionLabel() {
    const currentFile = location.pathname.split('/').pop();
    if (SECTION_LABEL_OVERRIDES[currentFile]) return SECTION_LABEL_OVERRIDES[currentFile];
    for (const group of SIDEBAR_GROUPS) {
        const match = group.links.find((l) => l.page === currentFile);
        if (match) return match.label;
    }
    return 'Sistema de Proveedores';
}

function renderSidebar() {
    const container = document.getElementById('sidebar-container');
    if (!container) return;

    const inPages = location.pathname.includes('/pages/');
    const base = inPages ? '' : 'pages/';
    const homeHref = inPages ? '../index.html' : 'index.html';
    const currentFile = location.pathname.split('/').pop();

    const groupsHTML = SIDEBAR_GROUPS.map((group) => `
        <div class="sidebar-group-label">${group.label}</div>
        ${group.links.map((link) => {
            const isActive = currentFile === link.page;
            return `
                <a class="sidebar-link ${isActive ? 'active' : ''}" href="${base}${link.page}" ${isActive ? 'aria-current="page"' : ''}>
                    ${icon(link.icon, { size: 17 })}
                    <span>${link.label}</span>
                </a>
            `;
        }).join('')}
    `).join('');

    container.innerHTML = `
        <nav class="sidebar" id="app-sidebar" aria-label="Navegación principal">
            <a class="sidebar-brand" href="${homeHref}">
                <span class="sidebar-brand-mark">${icon('logo', { size: 18 })}</span>
                <span class="sidebar-brand-text">
                    <strong>Proveedores IA</strong>
                    <span>Evaluación multicriterio</span>
                </span>
            </a>
            <div class="sidebar-nav">
                ${groupsHTML}
            </div>
            <div class="sidebar-footer">
                <div class="sidebar-footer-note">
                    ${icon('info', { size: 14 })}
                    <span>Motor determinístico activo. Asistente conversacional disponible en una fase posterior.</span>
                </div>
            </div>
        </nav>
        <div class="sidebar-backdrop" id="sidebar-backdrop"></div>
    `;

    const backdrop = document.getElementById('sidebar-backdrop');
    backdrop.addEventListener('click', () => closeSidebar());
}

function closeSidebar() {
    const sidebar = document.getElementById('app-sidebar');
    const backdrop = document.getElementById('sidebar-backdrop');
    if (sidebar) sidebar.classList.remove('open');
    if (backdrop) backdrop.classList.remove('open');
}

function toggleSidebar() {
    const sidebar = document.getElementById('app-sidebar');
    const backdrop = document.getElementById('sidebar-backdrop');
    if (sidebar) sidebar.classList.toggle('open');
    if (backdrop) backdrop.classList.toggle('open');
}

document.addEventListener('DOMContentLoaded', renderSidebar);
