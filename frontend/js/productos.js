/* ============================================================
   Página: Gestión de Productos
   ============================================================ */

let productosCache = [];
const productosTable = createTableController(8);

document.addEventListener('DOMContentLoaded', () => {
    cargarProductos();
    document.getElementById('btn-nuevo-producto').addEventListener('click', () => abrirModalProducto());

    document.getElementById('search-productos').addEventListener('input', (e) => {
        productosTable.setSearch(e.target.value);
        renderProductosTable();
    });
    document.getElementById('filtro-estado-producto').addEventListener('change', () => {
        aplicarFiltroEstadoProducto();
        renderProductosTable();
    });
});

function aplicarFiltroEstadoProducto() {
    const estado = document.getElementById('filtro-estado-producto').value;
    const items = estado ? productosCache.filter((p) => p.estado === estado) : productosCache;
    productosTable.setItems(items, ['nombre', 'codigo', 'descripcion']);
}

async function cargarProductos() {
    const body = document.getElementById('productos-body');
    try {
        productosCache = await api.productos.list({ limit: 1000 });
        aplicarFiltroEstadoProducto();
        renderProductosTable();
    } catch (err) {
        body.innerHTML = errorRow(5, err.message);
    }
}

function renderProductosTable() {
    const body = document.getElementById('productos-body');
    const paginationEl = document.getElementById('productos-pagination');
    const resultCount = document.getElementById('result-count');
    const view = productosTable.getView();

    resultCount.textContent = `${view.totalCount} producto(s)`;

    if (!view.totalCount) {
        body.innerHTML = emptyRow(5, 'Ajusta la búsqueda o el filtro, o registra un nuevo producto.', { title: 'Sin productos', icon: 'products' });
        paginationEl.innerHTML = '';
        return;
    }

    body.innerHTML = view.items.map((p) => `
        <tr>
            <td class="cell-muted">${escapeHtml(p.codigo || '—')}</td>
            <td><strong>${escapeHtml(p.nombre)}</strong></td>
            <td class="cell-muted">${escapeHtml(p.descripcion || '—')}</td>
            <td>${estadoBadge(p.estado)}</td>
            <td>
                <div class="actions-cell" style="justify-content:flex-end;">
                    <button class="btn btn-ghost btn-sm" data-action="proveedores" data-id="${p.id}">Proveedores</button>
                    <button class="btn btn-secondary btn-sm" data-action="editar" data-id="${p.id}" data-tooltip="Editar" aria-label="Editar ${escapeHtml(p.nombre)}">${icon('edit', { size: 14 })}</button>
                    <button class="btn btn-danger btn-sm" data-action="eliminar" data-id="${p.id}" data-tooltip="Eliminar" aria-label="Eliminar ${escapeHtml(p.nombre)}">${icon('trash', { size: 14 })}</button>
                </div>
            </td>
        </tr>
    `).join('');

    paginationEl.innerHTML = paginationHTML(view);
    wirePagination(paginationEl, productosTable, renderProductosTable);

    body.querySelectorAll('[data-action="editar"]').forEach((btn) =>
        btn.addEventListener('click', () => abrirModalProducto(productosCache.find((p) => p.id === Number(btn.dataset.id))))
    );
    body.querySelectorAll('[data-action="proveedores"]').forEach((btn) =>
        btn.addEventListener('click', () => abrirModalProveedoresDeProducto(productosCache.find((p) => p.id === Number(btn.dataset.id))))
    );
    body.querySelectorAll('[data-action="eliminar"]').forEach((btn) =>
        btn.addEventListener('click', () => eliminarProducto(Number(btn.dataset.id)))
    );
}

function abrirModalProducto(producto = null) {
    const esEdicion = Boolean(producto);

    Modal.open({
        title: esEdicion ? 'Editar producto' : 'Nuevo producto',
        bodyHTML: `
            <form id="form-producto">
                <div class="form-grid single">
                    <div class="form-group">
                        <label>Nombre<span class="required">*</span></label>
                        <input type="text" name="nombre" required value="${escapeHtml(producto?.nombre || '')}">
                    </div>
                    <div class="form-group">
                        <label>Código</label>
                        <input type="text" name="codigo" value="${escapeHtml(producto?.codigo || '')}">
                    </div>
                    <div class="form-group">
                        <label>Descripción</label>
                        <textarea name="descripcion">${escapeHtml(producto?.descripcion || '')}</textarea>
                    </div>
                    <div class="form-group">
                        <label>Estado</label>
                        <select name="estado">
                            <option value="Activo" ${producto?.estado !== 'Inactivo' ? 'selected' : ''}>Activo</option>
                            <option value="Inactivo" ${producto?.estado === 'Inactivo' ? 'selected' : ''}>Inactivo</option>
                        </select>
                    </div>
                </div>
            </form>
        `,
        footerHTML: `
            <button class="btn btn-ghost" id="btn-cancelar-producto">Cancelar</button>
            <button class="btn btn-primary" id="btn-guardar-producto">${esEdicion ? 'Guardar cambios' : 'Registrar producto'}</button>
        `,
    });

    document.getElementById('btn-cancelar-producto').addEventListener('click', () => Modal.close());
    document.getElementById('btn-guardar-producto').addEventListener('click', async () => {
        const form = document.getElementById('form-producto');
        if (!form.reportValidity()) return;

        const payload = Object.fromEntries(new FormData(form).entries());
        const btn = document.getElementById('btn-guardar-producto');
        btn.disabled = true;
        btn.textContent = 'Guardando…';

        try {
            if (esEdicion) {
                await api.productos.update(producto.id, payload);
                showToast('Producto actualizado correctamente.', 'success');
            } else {
                await api.productos.create(payload);
                showToast('Producto registrado correctamente.', 'success');
            }
            Modal.close();
            cargarProductos();
        } catch (err) {
            showToast(err.message, 'error');
            btn.disabled = false;
            btn.textContent = esEdicion ? 'Guardar cambios' : 'Registrar producto';
        }
    });
}

async function eliminarProducto(id) {
    const producto = productosCache.find((p) => p.id === id);
    const confirmado = await Modal.confirm({
        title: 'Eliminar producto',
        message: `¿Deseas eliminar <strong>${escapeHtml(producto?.nombre || '')}</strong>? Esta acción no se puede deshacer.`,
        confirmLabel: 'Eliminar',
    });
    if (!confirmado) return;

    try {
        await api.productos.remove(id);
        showToast('Producto eliminado.', 'success');
        cargarProductos();
    } catch (err) {
        showToast(err.message, 'error');
    }
}

async function abrirModalProveedoresDeProducto(producto) {
    Modal.open({
        title: `Proveedores que ofrecen "${producto.nombre}"`,
        size: 'lg',
        bodyHTML: `<div id="proveedores-producto-lista"><div class="loading-state"><div class="spinner"></div><span>Cargando proveedores…</span></div></div>`,
        footerHTML: `<button class="btn btn-ghost" id="btn-cerrar-proveedores-producto">Cerrar</button>`,
    });

    document.getElementById('btn-cerrar-proveedores-producto').addEventListener('click', () => Modal.close());

    const contenedor = document.getElementById('proveedores-producto-lista');
    try {
        const relaciones = await api.proveedorProductos.list({ producto_id: producto.id });
        if (!relaciones.length) {
            contenedor.innerHTML = `<div class="empty-state"><span class="icon-tile neutral">${icon('providers', { size: 18 })}</span><div class="empty-state-title">Sin proveedores</div><div class="empty-state-desc">Ningún proveedor ofrece este producto todavía.</div></div>`;
            return;
        }
        contenedor.innerHTML = `
            <div class="table-wrapper">
                <table class="data-table">
                    <thead>
                        <tr><th>Proveedor</th><th>Precio</th><th>Entrega</th><th>Estado</th></tr>
                    </thead>
                    <tbody>
                        ${relaciones.map((r) => `
                            <tr>
                                <td>${escapeHtml(r.proveedor ? r.proveedor.razon_social : `Proveedor #${r.proveedor_id}`)}</td>
                                <td>${formatCurrency(r.precio)}</td>
                                <td class="cell-muted">${r.tiempo_entrega_dias} día(s)</td>
                                <td>${r.disponible ? '<span class="badge badge-success">Disponible</span>' : '<span class="badge badge-neutral">No disponible</span>'}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
    } catch (err) {
        contenedor.innerHTML = `<div class="error-state">${icon('alertTriangle', { size: 18 })}<div class="empty-state-desc">${escapeHtml(err.message)}</div></div>`;
    }
}
