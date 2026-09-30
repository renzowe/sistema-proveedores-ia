/* ============================================================
   Componente: Asistente conversacional — panel visual (Fase 12)
   ============================================================ */

function renderChatWidget() {
    const container = document.getElementById('chat-container');
    if (!container) return;

    container.innerHTML = `
        <div class="chat-panel" id="chat-panel">
            <div class="chat-panel-header">
                <span class="chat-panel-header-title">
                    ${icon('sparkles', { size: 16 })}
                    Asistente conversacional
                </span>
                <span class="badge badge-neutral">Próximamente</span>
            </div>
            <div class="chat-panel-body">
                <span class="icon-tile ai">${icon('sparkles', { size: 17 })}</span>
                <p style="margin:0;font-size:0.82rem;">
                    Un asistente conversacional (Claude, vía API de Anthropic) está planificado para una
                    fase posterior. No reemplazará el motor de decisión determinístico: solo ayudará a
                    interpretar solicitudes y explicar resultados ya calculados por el sistema.
                </p>
            </div>
            <div class="chat-panel-footer">
                <input type="text" placeholder="Disponible próximamente…" disabled aria-disabled="true">
            </div>
        </div>
        <button class="chat-fab" id="chat-fab-btn" aria-label="Abrir asistente conversacional" aria-haspopup="dialog">
            ${icon('sparkles', { size: 21 })}
        </button>
    `;

    const fab = document.getElementById('chat-fab-btn');
    const panel = document.getElementById('chat-panel');
    fab.addEventListener('click', () => panel.classList.toggle('open'));
}

document.addEventListener('DOMContentLoaded', renderChatWidget);
