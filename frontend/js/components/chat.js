/* ============================================================
   Componente: Chat IA — panel visual del Asistente (Fase 12)
   ============================================================ */

function renderChatWidget() {
    const container = document.getElementById('chat-container');
    if (!container) return;

    container.innerHTML = `
        <div class="chat-panel" id="chat-panel">
            <div class="chat-panel-header">
                <strong>Asistente IA</strong>
                <span class="badge badge-warning">Próximamente</span>
            </div>
            <div class="chat-panel-body">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                </svg>
                <p style="margin:0;font-size:0.85rem;">
                    El Asistente conversacional impulsado por Claude estará disponible en la Fase 12,
                    cuando se active la integración con el LLM.
                </p>
            </div>
            <div class="chat-panel-footer">
                <input type="text" placeholder="Disponible en Fase 12…" disabled>
            </div>
        </div>
        <button class="chat-fab" id="chat-fab-btn" aria-label="Abrir asistente IA">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
            </svg>
        </button>
    `;

    const fab = document.getElementById('chat-fab-btn');
    const panel = document.getElementById('chat-panel');
    fab.addEventListener('click', () => panel.classList.toggle('open'));
}

document.addEventListener('DOMContentLoaded', renderChatWidget);
