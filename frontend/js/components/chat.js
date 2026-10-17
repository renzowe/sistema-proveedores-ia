/* ============================================================
   Componente: acceso directo al asistente conversacional
   El asistente vive en la pestaña Evaluaciones; este botón flotante
   lleva allí desde el resto de páginas, con la vista "Solo chat".
   ============================================================ */

function renderAccesoAsistente() {
    const container = document.getElementById('chat-container');
    if (!container) return;

    const enCarpetaPages = window.location.pathname.includes('/pages/');
    const href = `${enCarpetaPages ? '' : 'pages/'}evaluaciones.html?vista=chat`;

    container.innerHTML = `
        <a class="chat-fab" href="${href}" aria-label="Abrir el asistente conversacional" title="Asistente conversacional">
            ${icon('sparkles', { size: 21 })}
        </a>
    `;
}

document.addEventListener('DOMContentLoaded', renderAccesoAsistente);
