/* ============================================================
   Componente: Navbar
   ============================================================ */

function renderNavbar() {
    const container = document.getElementById('navbar-container');
    if (!container) return;

    const inPages = location.pathname.includes('/pages/');
    const homeHref = inPages ? '../index.html' : 'index.html';

    container.innerHTML = `
        <header class="navbar">
            <div class="flex" style="align-items:center; gap:0.75rem;">
                <button class="navbar-toggle" id="sidebar-toggle-btn" aria-label="Abrir menú">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <line x1="3" y1="6" x2="21" y2="6"></line>
                        <line x1="3" y1="12" x2="21" y2="12"></line>
                        <line x1="3" y1="18" x2="21" y2="18"></line>
                    </svg>
                </button>
                <a class="navbar-brand" href="${homeHref}">
                    <span class="navbar-logo">SP</span>
                    <span class="navbar-title">
                        <strong>Sistema de Proveedores IA</strong>
                        <span>Evaluación multicriterio agéntica</span>
                    </span>
                </a>
            </div>
            <div class="navbar-right">
                <span class="status-pill checking" id="backend-status-pill">
                    <span class="status-dot"></span>
                    <span id="backend-status-text">Verificando backend…</span>
                </span>
            </div>
        </header>
    `;

    const toggleBtn = document.getElementById('sidebar-toggle-btn');
    if (toggleBtn) {
        toggleBtn.addEventListener('click', () => {
            const sidebar = document.querySelector('.sidebar');
            if (sidebar) sidebar.classList.toggle('open');
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
