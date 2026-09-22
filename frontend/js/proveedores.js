/* ============================================================
   Página: Gestión de Proveedores
   ============================================================ */

let proveedoresCache = [];

document.addEventListener('DOMContentLoaded', () => {
    cargarProveedores();
    document.getElementById('btn-nuevo-proveedor').addEventListener('click', () => abrirModalProveedor());
});

async function cargarProveedores() {
    const body = document.getElementById('proveedores-body');
    body.innerHTML = loadingRow(6);
    try {
        proveedoresCache = await api.proveedores.list({ limit: 1000 });
        renderProveedoresTable();
    } catch (err) {
        body.innerHTML = errorRow(6, err.message);
    }
}

function renderProveedoresTable() {
    const body = document.getElementById('proveedores-body');
    if (!proveedoresCache.length) {
        body.innerHTML = emptyRow(6, 'Aún no hay proveedores registrados.');
        return;
    }

    body.innerHTML = proveedoresCache.map((p) => `
        <tr>
            <td><strong>${escapeHtml(p.razon_social)}</strong>${p.nombre_comercial ? `<br><span class="cell-muted">${escapeHtml(p.nombre_comercial)}</span>` : ''}</td>
            <td>${escapeHtml(p.ruc)}</td>
            <td class="cell-muted">${escapeHtml(p.ciudad || '—')}</td>
            <td class="cell-muted">${escapeHtml(p.contacto || '—')}</td>
            <td>${estadoBadge(p.estado)}</td>
            <td>
                <div class="actions-cell" style="justify-content:flex-end;">
                    <button class="btn btn-ghost btn-sm" data-action="catalogo" data-id="${p.id}">Catálogo</button>
                    <button class="btn btn-secondary btn-sm" data-action="editar" data-id="${p.id}">Editar</button>
                    <button class="btn btn-danger btn-sm" data-action="eliminar" data-id="${p.id}">Eliminar</button>
                </div>
            </td>
        </tr>
    `).join('');

    body.querySelectorAll('[data-action="editar"]').forEach((btn) =>
        btn.addEventListener('click', () => abrirModalProveedor(proveedoresCache.find((p) => p.id === Number(btn.dataset.id))))
    );
    body.querySelectorAll('[data-action="catalogo"]').forEach((btn) =>
        btn.addEventListener('click', () => abrirModalCatalogo(proveedoresCache.find((p) => p.id === Number(btn.dataset.id))))
    );
    body.querySelectorAll('[data-action="eliminar"]').forEach((btn) =>
        btn.addEventListener('click', () => eliminarProveedor(Number(btn.dataset.id)))
    );
}

function abrirModalProveedor(proveedor = null) {
    const esEdicion = Boolean(proveedor);

    Modal.open({
        title: esEdicion ? 'Editar proveedor' : 'Nuevo proveedor',
        size: 'lg',
        bodyHTML: `
            <form id="form-proveedor">
                <div class="form-grid">
                    <div class="form-group full">
                        <label>Razón social *</label>
                        <input type="text" name="razon_social" required value="${escapeHtml(proveedor?.razon_social || '')}">
                    </div>
                    <div class="form-group">
                        <label>RUC *</label>
                        <input type="text" name="ruc" required maxlength="20" value="${escapeHtml(proveedor?.ruc || '')}">
                    </div>
                    <div class="form-group">
                        <label>Nombre comercial</label>
                        <input type="text" name="nombre_comercial" value="${escapeHtml(proveedor?.nombre_comercial || '')}">
                    </div>
                    <div class="form-group">
                        <label>País</label>
                        <input type="text" name="pais" value="${escapeHtml(proveedor?.pais || 'Perú')}">
                    </div>
                    <div class="form-group">
                        <label>Ciudad</label>
                        <input type="text" name="ciudad" value="${escapeHtml(proveedor?.ciudad || '')}">
                    </div>
                    <div class="form-group">
                        <label>Contacto</label>
                        <input type="text" name="contacto" value="${escapeHtml(proveedor?.contacto || '')}">
                    </div>
                    <div class="form-group">
                        <label>Teléfono</label>
                        <input type="text" name="telefono" value="${escapeHtml(proveedor?.telefono || '')}">
                    </div>
                    <div class="form-group">
                        <label>Correo</label>
                        <input type="email" name="correo" value="${escapeHtml(proveedor?.correo || '')}">
                    </div>
                    <div class="form-group">
                        <label>Estado</label>
                        <select name="estado">
                            <option value="Activo" ${proveedor?.estado !== 'Inactivo' ? 'selected' : ''}>Activo</option>
                            <option value="Inactivo" ${proveedor?.estado === 'Inactivo' ? 'selected' : ''}>Inactivo</option>
                        </select>
                    </div>
                    <div class="form-group full">
                        <label>Dirección</label>
                        <textarea name="direccion">${escapeHtml(proveedor?.direccion || '')}</textarea>
                    </div>
                </div>
            </form>
        `,
        footerHTML: `
            <button class="btn btn-ghost" id="btn-cancelar-proveedor">Cancelar</button>
            <button class="btn btn-primary" id="btn-guardar-proveedor">${esEdicion ? 'Guardar cambios' : 'Registrar proveedor'}</button>
        `,
    });

    document.getElementById('btn-cancelar-proveedor').addEventListener('click', () => Modal.close());
    document.getElementById('btn-guardar-proveedor').addEventListener('click', async () => {
        const form = document.getElementById('form-proveedor');
        if (!form.reportValidity()) return;

        const formData = new FormData(form);
        const payload = Object.fromEntries(formData.entries());

        const btn = document.getElementById('btn-guardar-proveedor');
        btn.disabled = true;
        btn.textContent = 'Guardando...';

        try {
            if (esEdicion) {
                await api.proveedores.update(proveedor.id, payload);
                showToast('Proveedor actualizado correctamente.', 'success');
            } else {
                await api.proveedores.create(payload);
                showToast('Proveedor registrado correctamente.', 'success');
            }
            Modal.close();
            cargarProveedores();
        } catch (err) {
            showToast(err.message, 'error');
            btn.disabled = false;
            btn.textContent = esEdicion ? 'Guardar cambios' : 'Registrar proveedor';
        }
    });
}

async function eliminarProveedor(id) {
    const proveedor = proveedoresCache.find((p) => p.id === id);
    const confirmado = await Modal.confirm({
        title: 'Eliminar proveedor',
        message: `¿Deseas eliminar a <strong>${escapeHtml(proveedor?.razon_social || '')}</strong>? Esta acción no se puede deshacer.`,
        confirmLabel: 'Eliminar',
    });
    if (!confirmado) return;

    try {
        await api.proveedores.remove(id);
        showToast('Proveedor eliminado.', 'success');
        cargarProveedores();
    } catch (err) {
        showToast(err.message, 'error');
    }
}

/* ============================== Catálogo comercial del proveedor ============================== */

async function abrirModalCatalogo(proveedor) {
    Modal.open({
        title: `Catálogo de ${proveedor.razon_social}`,
        size: 'lg',
        bodyHTML: `
            <div id="catalogo-lista"><div class="loading-state"><div class="spinner"></div><span>Cargando catálogo...</span></div></div>
            <hr style="border-color:var(--border-soft); margin:1.2rem 0;">
            <h4>Agregar producto al catálogo</h4>
            <form id="form-catalogo">
                <div class="form-grid">
                    <div class="form-group full">
                        <label>Producto *</label>
                        <select name="producto_id" id="select-producto-catalogo" required>
                            <option value="">Cargando productos...</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Precio (S/) *</label>
                        <input type="number" step="0.01" min="0" name="precio" required>
                    </div>
                    <div class="form-group">
                        <label>Tiempo de entrega (días) *</label>
                        <input type="number" min="0" name="tiempo_entrega_dias" required>
                    </div>
                    <div class="form-group full">
                        <label>Condiciones</label>
                        <input type="text" name="condiciones" placeholder="Ej: pago a 30 días, envío incluido">
                    </div>
                    <div class="form-group checkbox-row full">
                        <input type="checkbox" name="disponible" id="chk-disponible" checked>
                        <label for="chk-disponible">Disponible actualmente</label>
                    </div>
                </div>
            </form>
        `,
        footerHTML: `
            <button class="btn btn-ghost" id="btn-cerrar-catalogo">Cerrar</button>
            <button class="btn btn-primary" id="btn-agregar-catalogo">Agregar al catálogo</button>
        `,
    });

    document.getElementById('btn-cerrar-catalogo').addEventListener('click', () => Modal.close());
    document.getElementById('btn-agregar-catalogo').addEventListener('click', () => agregarProductoCatalogo(proveedor.id));

    cargarSelectProductos();
    cargarCatalogoProveedor(proveedor.id);
}

async function cargarSelectProductos() {
    const select = document.getElementById('select-producto-catalogo');
    try {
        const productos = await api.productos.list({ limit: 1000 });
        if (!select) return;
        select.innerHTML = productos.length
            ? productos.map((p) => `<option value="${p.id}">${escapeHtml(p.nombre)}${p.codigo ? ` (${escapeHtml(p.codigo)})` : ''}</option>`).join('')
            : '<option value="">No hay productos registrados</option>';
    } catch (err) {
        if (select) select.innerHTML = `<option value="">Error al cargar productos</option>`;
    }
}

async function cargarCatalogoProveedor(proveedorId) {
    const contenedor = document.getElementById('catalogo-lista');
    try {
        const relaciones = await api.proveedorProductos.list({ proveedor_id: proveedorId });
        if (!relaciones.length) {
            contenedor.innerHTML = `<div class="empty-state">Este proveedor todavía no tiene productos asignados.</div>`;
            return;
        }

        contenedor.innerHTML = `
            <div class="table-wrapper">
                <table class="data-table">
                    <thead>
                        <tr><th>Producto</th><th>Precio</th><th>Entrega</th><th>Estado</th><th></th></tr>
                    </thead>
                    <tbody>
                        ${relaciones.map((r) => `
                            <tr data-rel-row="${r.id}">
                                <td>${escapeHtml(r.producto ? r.producto.nombre : `Producto #${r.producto_id}`)}</td>
                                <td data-cell="precio">${formatCurrency(r.precio)}</td>
                                <td class="cell-muted" data-cell="tiempo">${r.tiempo_entrega_dias} día(s)</td>
                                <td data-cell="estado">${r.disponible ? '<span class="badge badge-success">Disponible</span>' : '<span class="badge badge-neutral">No disponible</span>'}</td>
                                <td class="text-right">
                                    <div class="actions-cell" style="justify-content:flex-end;">
                                        <button class="btn btn-secondary btn-sm" data-edit-rel="${r.id}">Editar</button>
                                        <button class="btn btn-danger btn-sm" data-remove-rel="${r.id}">Quitar</button>
                                    </div>
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;

        contenedor.querySelectorAll('[data-remove-rel]').forEach((btn) => {
            btn.addEventListener('click', async () => {
                try {
                    await api.proveedorProductos.remove(Number(btn.dataset.removeRel));
                    showToast('Producto retirado del catálogo.', 'success');
                    cargarCatalogoProveedor(proveedorId);
                } catch (err) {
                    showToast(err.message, 'error');
                }
            });
        });

        contenedor.querySelectorAll('[data-edit-rel]').forEach((btn) => {
            btn.addEventListener('click', () => {
                const relId = Number(btn.dataset.editRel);
                const relacion = relaciones.find((r) => r.id === relId);
                if (relacion) activarEdicionInlineCatalogo(relacion, proveedorId);
            });
        });
    } catch (err) {
        contenedor.innerHTML = `<div class="error-state">⚠ ${escapeHtml(err.message)}</div>`;
    }
}

function activarEdicionInlineCatalogo(relacion, proveedorId) {
    const fila = document.querySelector(`tr[data-rel-row="${relacion.id}"]`);
    if (!fila) return;

    fila.querySelector('[data-cell="precio"]').innerHTML =
        `<input type="number" step="0.01" min="0" class="edit-precio" value="${relacion.precio}" style="width:100px;">`;
    fila.querySelector('[data-cell="tiempo"]').innerHTML =
        `<input type="number" min="0" class="edit-tiempo" value="${relacion.tiempo_entrega_dias}" style="width:80px;">`;
    fila.querySelector('[data-cell="estado"]').innerHTML =
        `<select class="edit-disponible">
            <option value="true" ${relacion.disponible ? 'selected' : ''}>Disponible</option>
            <option value="false" ${!relacion.disponible ? 'selected' : ''}>No disponible</option>
        </select>`;

    const celdaAcciones = fila.querySelector('td:last-child');
    celdaAcciones.innerHTML = `
        <div class="actions-cell" style="justify-content:flex-end;">
            <button class="btn btn-primary btn-sm" data-guardar-rel="${relacion.id}">Guardar</button>
            <button class="btn btn-ghost btn-sm" data-cancelar-rel="${relacion.id}">Cancelar</button>
        </div>
    `;

    celdaAcciones.querySelector('[data-cancelar-rel]').addEventListener('click', () => cargarCatalogoProveedor(proveedorId));
    celdaAcciones.querySelector('[data-guardar-rel]').addEventListener('click', async () => {
        const precio = Number(fila.querySelector('.edit-precio').value);
        const tiempo = Number(fila.querySelector('.edit-tiempo').value);
        const disponible = fila.querySelector('.edit-disponible').value === 'true';

        if (Number.isNaN(precio) || precio < 0 || Number.isNaN(tiempo) || tiempo < 0) {
            showToast('Ingresa un precio y tiempo de entrega válidos.', 'error');
            return;
        }

        try {
            await api.proveedorProductos.update(relacion.id, {
                precio,
                tiempo_entrega_dias: tiempo,
                disponible,
            });
            showToast('Catálogo actualizado correctamente.', 'success');
            cargarCatalogoProveedor(proveedorId);
        } catch (err) {
            showToast(err.message, 'error');
        }
    });
}

async function agregarProductoCatalogo(proveedorId) {
    const form = document.getElementById('form-catalogo');
    if (!form.reportValidity()) return;

    const formData = new FormData(form);
    const payload = {
        proveedor_id: proveedorId,
        producto_id: Number(formData.get('producto_id')),
        precio: Number(formData.get('precio')),
        tiempo_entrega_dias: Number(formData.get('tiempo_entrega_dias')),
        condiciones: formData.get('condiciones') || null,
        disponible: formData.get('disponible') === 'on',
    };

    const btn = document.getElementById('btn-agregar-catalogo');
    btn.disabled = true;

    try {
        await api.proveedorProductos.create(payload);
        showToast('Producto agregado al catálogo.', 'success');
        form.reset();
        document.getElementById('chk-disponible').checked = true;
        cargarCatalogoProveedor(proveedorId);
    } catch (err) {
        showToast(err.message, 'error');
    } finally {
        btn.disabled = false;
    }
}
