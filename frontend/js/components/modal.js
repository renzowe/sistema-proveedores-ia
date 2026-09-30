/* ============================================================
   Componente: Modal / Dialog — sistema reutilizable
   ============================================================ */

const Modal = {
    _getRoot() {
        let root = document.getElementById('modal-root');
        if (!root) {
            root = document.createElement('div');
            root.id = 'modal-root';
            document.body.appendChild(root);
        }
        return root;
    },

    open({ title = '', bodyHTML = '', footerHTML = '', size = 'md', danger = false, onClose = null }) {
        const root = this._getRoot();
        this._onClose = onClose;
        this._lastFocused = document.activeElement;

        root.innerHTML = `
            <div class="modal-overlay" id="modal-overlay">
                <div class="modal ${size === 'lg' ? 'modal-lg' : ''}" role="dialog" aria-modal="true" aria-labelledby="modal-title-text">
                    <div class="modal-header">
                        <h3 id="modal-title-text">${title}</h3>
                        <button class="modal-close" id="modal-close-btn" aria-label="Cerrar">${icon('close', { size: 17 })}</button>
                    </div>
                    <div class="modal-body">${bodyHTML}</div>
                    ${footerHTML ? `<div class="modal-footer ${danger ? 'danger-context' : ''}">${footerHTML}</div>` : ''}
                </div>
            </div>
        `;

        const overlay = document.getElementById('modal-overlay');
        const closeBtn = document.getElementById('modal-close-btn');

        overlay.addEventListener('mousedown', (e) => {
            if (e.target === overlay) Modal.close();
        });
        closeBtn.addEventListener('click', () => Modal.close());

        document.addEventListener('keydown', Modal._escHandler);

        const firstField = root.querySelector('.modal-body input, .modal-body select, .modal-body textarea');
        if (firstField) {
            setTimeout(() => firstField.focus(), 30);
        } else {
            closeBtn.focus();
        }
    },

    close() {
        const root = document.getElementById('modal-root');
        if (root) root.innerHTML = '';
        document.removeEventListener('keydown', Modal._escHandler);
        if (this._lastFocused && typeof this._lastFocused.focus === 'function') {
            this._lastFocused.focus();
        }
        if (typeof this._onClose === 'function') {
            const cb = this._onClose;
            this._onClose = null;
            cb();
        }
    },

    _escHandler(e) {
        if (e.key === 'Escape') Modal.close();
    },

    confirm({ title = 'Confirmar acción', message = '¿Estás seguro?', confirmLabel = 'Confirmar', danger = true }) {
        return new Promise((resolve) => {
            Modal.open({
                title,
                danger,
                bodyHTML: `
                    <div class="alert ${danger ? 'alert-danger' : 'alert-info'}">
                        ${icon(danger ? 'alertTriangle' : 'info', { size: 18 })}
                        <div class="alert-body">${message}</div>
                    </div>
                `,
                footerHTML: `
                    <button class="btn btn-ghost" id="modal-cancel-btn">Cancelar</button>
                    <button class="btn ${danger ? 'btn-danger' : 'btn-primary'}" id="modal-confirm-btn">${confirmLabel}</button>
                `,
                onClose: () => resolve(false),
            });

            document.getElementById('modal-cancel-btn').addEventListener('click', () => Modal.close());
            document.getElementById('modal-confirm-btn').addEventListener('click', () => {
                this._onClose = null;
                Modal.close();
                resolve(true);
            });
        });
    },
};

document.addEventListener('DOMContentLoaded', () => {
    Modal._getRoot();
});
