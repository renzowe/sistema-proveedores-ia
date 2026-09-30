/* ============================================================
   Componente: Topbar
   ============================================================ */

function renderNavbar() {
    const container = document.getElementById('navbar-container');
    if (!container) return;

    container.innerHTML = `
        <header class="topbar">
            <div class="topbar-left">
                <button class="topbar-menu-btn" id="sidebar-toggle-btn" aria-label="Abrir menú de navegación" aria-expanded="false">
                    ${icon('menu', { size: 18 })}
                </button>
                <span class="topbar-title">${currentSectionLabel()}</span>
            </div>
            <div class="topbar-right">
                <span class="status-pill checking" id="backend-status-pill" role="status">
                    <span class="status-dot"></span>
                    <span id="backend-status-text">Verificando backend…</span>
                </span>
                <div class="org-chip">
                    <span class="org-chip-avatar">${icon('building', { size: 14 })}</span>
                    <span class="org-chip-text">
                        <strong>Área de Compras</strong>
                        <span>Procurement</span>
                    </span>
                </div>
            </div>
        </header>
    `;

    const toggleBtn = document.getElementById('sidebar-toggle-btn');
    if (toggleBtn) {
        toggleBtn.addEventListener('click', () => {
            toggleSidebar();
            const expanded = document.getElementById('app-sidebar')?.classList.contains('open');
            toggleBtn.setAttribute('aria-expanded', expanded ? 'true' : 'false');
        });
    }

    checkBackendStatus();
}

async function checkBackendStatus() {
    const pill = document.getElementById('backend-status-pill');
    const text = document.getElementById('backend-status-text');
    if (!pill || !text) return;
    try {
        await api.health();
        pill.className = 'status-pill online';
        text.textContent = 'Backend conectado';
    } catch {
        pill.className = 'status-pill offline';
        text.textContent = 'Backend no disponible';
    }
}

document.addEventListener('DOMContentLoaded', renderNavbar);
