/* ============================================================
   Página: Historial de Desempeño
   ============================================================ */

let proveedoresCacheDesempeno = [];
let productosCacheDesempeno = [];
let historialCache = [];
let contadorLineasHistorial = 0;
const historialTable = createTableController(8);

document.addEventListener('DOMContentLoaded', async () => {
    document.getElementById('btn-nueva-experiencia').addEventListener('click', abrirModalExperiencia);
    document.getElementById('btn-consultar-metricas').addEventListener('click', consultarMetricasProveedor);
    document.getElementById('search-historial').addEventListener('input', (e) => {
        historialTable.setSearch(e.target.value);
        renderHistorialTable();
    });

    await cargarProveedoresParaSelect();
    cargarHistorial();
});

async function cargarProveedoresParaSelect() {
    const select = document.getElementById('select-metrica-proveedor');
    try {
        proveedoresCacheDesempeno = await api.proveedores.list({ limit: 1000 });
        select.innerHTML = '<option value="">Selecciona un proveedor…</option>' +
            proveedoresCacheDesempeno.map((p) => `<option value="${p.id}">${escapeHtml(p.razon_social)}</option>`).join('');
    } catch (err) {
        select.innerHTML = '<option value="">Error al cargar proveedores</option>';
    }
}

async function consultarMetricasProveedor() {
    const select = document.getElementById('select-metrica-proveedor');
    const resultado = document.getElementById('metricas-proveedor-resultado');
    const id = select.value;

    if (!id) {
        resultado.innerHTML = `<p class="text-muted mt-1">Selecciona un proveedor para ver sus métricas.</p>`;
        return;
    }

    resultado.innerHTML = `<div class="loading-state"><div class="spinner"></div><span>Calculando métricas…</span></div>`;

    try {
        const m = await api.historial.metricasProveedor(id);
        if (!m.total_operaciones) {
            resultado.innerHTML = renderAlert({
                type: 'info',
                title: 'Sin historial registrado',
                body: 'Este proveedor todavía no tiene experiencias registradas. Sus métricas parten de un valor neutro en el motor de decisión.',
            });
            renderIcons(resultado);
            return;
        }
        resultado.innerHTML = `
            <div class="metrics-grid">
                <div class="metric-tile"><div class="label">Operaciones registradas</div><div class="value">${m.total_operaciones}</div></div>
                <div class="metric-tile"><div class="label">Cumplimiento promedio</div><div class="value">${m.cumplimiento_promedio}%</div></div>
                <div class="metric-tile"><div class="label">Entrega promedio</div><div class="value">${m.tiempo_entrega_promedio_dias} días</div></div>
                <div class="metric-tile"><div class="label">Tasa de defectos</div><div class="value">${m.tasa_defectos_promedio}%</div></div>
                <div class="metric-tile"><div class="label">Efectividad de entrega</div><div class="value">${m.tasa_efectividad_entrega}%</div></div>
                <div class="metric-tile"><div class="label">Unidades solicitadas / entregadas</div><div class="value">${m.total_solicitado} / ${m.total_entregado}</div></div>
            </div>
        `;
    } catch (err) {
        resultado.innerHTML = renderAlert({ type: 'danger', title: 'No se pudo consultar', body: escapeHtml(err.message) });
        renderIcons(resultado);
    }
}

async function cargarHistorial() {
    const body = document.getElementById('historial-body');
    try {
        historialCache = await api.historial.list({ limit: 1000 });
        historialTable.setItems(historialCache.map((h) => ({ ...h, _proveedorNombre: h.proveedor ? h.proveedor.razon_social : '' })), ['_proveedorNombre']);
        renderHistorialTable();
    } catch (err) {
        body.innerHTML = errorRow(6, err.message);
    }
}

function renderHistorialTable() {
    const body = document.getElementById('historial-body');
    const paginationEl = document.getElementById('historial-pagination');
    const resultCount = document.getElementById('result-count');
    const view = historialTable.getView();

    resultCount.textContent = `${view.totalCount} registro(s)`;

    if (!view.totalCount) {
        body.innerHTML = emptyRow(6, 'Registra la primera experiencia de desempeño de un proveedor.', { title: 'Sin historial', icon: 'performance' });
        paginationEl.innerHTML = '';
        return;
    }

    body.innerHTML = view.items.map((h) => `
        <tr>
            <td><strong>${escapeHtml(h.proveedor ? h.proveedor.razon_social : `Proveedor #${h.proveedor_id}`)}</strong></td>
            <td class="cell-muted">${formatDate(h.fecha_operacion)}</td>
            <td>${h.cumplimiento_porcentaje !== null && h.cumplimiento_porcentaje !== undefined ? `${h.cumplimiento_porcentaje}%` : '—'}</td>
            <td class="cell-muted">${h.tiempo_entrega_promedio_dias !== null ? `${h.tiempo_entrega_promedio_dias} días` : '—'}</td>
            <td class="cell-muted">${(h.detalles || []).length} producto(s)</td>
            <td class="text-right">
                <button class="btn btn-ghost btn-sm" data-detalle="${h.id}">Ver detalle</button>
            </td>
        </tr>
    `).join('');

    paginationEl.innerHTML = paginationHTML(view);
    wirePagination(paginationEl, historialTable, renderHistorialTable);

    body.querySelectorAll('[data-detalle]').forEach((btn) =>
        btn.addEventListener('click', () => verDetalleHistorial(Number(btn.dataset.detalle)))
    );
}

function verDetalleHistorial(id) {
    const h = historialCache.find((item) => item.id === id);
    if (!h) return;

    Modal.open({
        title: `Detalle de experiencia — ${h.proveedor ? h.proveedor.razon_social : `Proveedor #${h.proveedor_id}`}`,
        size: 'lg',
        bodyHTML: `
            <p class="text-muted" style="margin-top:0;">Fecha de operación: ${formatDate(h.fecha_operacion)} · Observaciones generales: ${escapeHtml(h.observaciones || 'Ninguna')}</p>
            <div class="table-wrapper">
                <table class="data-table">
                    <thead>
                        <tr><th>Producto</th><th>Solicitado</th><th>Entregado</th><th>% Defectos</th><th>Observaciones</th></tr>
                    </thead>
                    <tbody>
                        ${(h.detalles || []).map((d) => `
                            <tr>
                                <td>${escapeHtml(d.producto ? d.producto.nombre : `Producto #${d.producto_id}`)}</td>
                                <td>${d.cantidad_solicitada}</td>
                                <td>${d.cantidad_entregada}</td>
                                <td>${d.porcentaje_defectos}%</td>
                                <td class="cell-muted">${escapeHtml(d.observaciones || '—')}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `,
        footerHTML: `<button class="btn btn-primary" id="btn-cerrar-detalle-historial">Cerrar</button>`,
    });

    document.getElementById('btn-cerrar-detalle-historial').addEventListener('click', () => Modal.close());
}

/* ============================== Registrar nueva experiencia ============================== */

async function abrirModalExperiencia() {
    contadorLineasHistorial = 0;

    Modal.open({
        title: 'Registrar experiencia de desempeño',
        size: 'lg',
        bodyHTML: `
            <form id="form-experiencia">
                <div class="form-grid">
                    <div class="form-group">
                        <label>Proveedor<span class="required">*</span></label>
                        <select name="proveedor_id" id="select-proveedor-experiencia" required>
                            <option value="">Cargando proveedores…</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Fecha de operación<span class="required">*</span></label>
                        <input type="date" name="fecha_operacion" required>
                    </div>
                    <div class="form-group">
                        <label>Tiempo de entrega promedio (días)</label>
                        <input type="number" min="0" name="tiempo_entrega_promedio_dias">
                    </div>
                    <div class="form-group">
                        <label>Cumplimiento (%)</label>
                        <input type="number" min="0" max="100" step="0.1" name="cumplimiento_porcentaje">
                    </div>
                    <div class="form-group full">
                        <label>Observaciones generales</label>
                        <textarea name="observaciones"></textarea>
                    </div>
                </div>

                <h4 style="margin-top:0.3rem;">Productos de la experiencia</h4>
                <div class="table-wrapper">
                    <table class="product-line-table">
                        <thead>
                            <tr>
                                <th style="width:26%">Producto</th>
                                <th>Cant. solicitada</th>
                                <th>Cant. entregada</th>
                                <th>% Defectos</th>
                                <th>Observaciones</th>
                                <th></th>
                            </tr>
                        </thead>
                        <tbody id="historial-lineas-body"></tbody>
                    </table>
                </div>
                <button type="button" class="btn btn-secondary btn-sm add-line-btn" id="btn-agregar-linea-historial">+ Agregar producto</button>
            </form>
        `,
        footerHTML: `
            <button class="btn btn-ghost" id="btn-cancelar-experiencia">Cancelar</button>
            <button class="btn btn-primary" id="btn-guardar-experiencia">Registrar experiencia</button>
        `,
    });

    document.getElementById('btn-cancelar-experiencia').addEventListener('click', () => Modal.close());
    document.getElementById('btn-agregar-linea-historial').addEventListener('click', () => agregarLineaHistorial());
    document.getElementById('btn-guardar-experiencia').addEventListener('click', guardarExperiencia);

    try {
        const [proveedores, productos] = await Promise.all([
            api.proveedores.list({ limit: 1000 }),
            api.productos.list({ limit: 1000 }),
        ]);
        proveedoresCacheDesempeno = proveedores;
        productosCacheDesempeno = productos;

        const selectProveedor = document.getElementById('select-proveedor-experiencia');
        if (selectProveedor) {
            selectProveedor.innerHTML = '<option value="">Selecciona un proveedor…</option>' +
                proveedores.map((p) => `<option value="${p.id}">${escapeHtml(p.razon_social)}</option>`).join('');
        }
        agregarLineaHistorial();
    } catch (err) {
        showToast('No se pudieron cargar proveedores/productos: ' + err.message, 'error');
    }
}

function agregarLineaHistorial() {
    const tbody = document.getElementById('historial-lineas-body');
    if (!tbody) return;
    const lineaId = contadorLineasHistorial++;

    const opciones = productosCacheDesempeno.map((p) => `<option value="${p.id}">${escapeHtml(p.nombre)}</option>`).join('');

    const row = document.createElement('tr');
    row.dataset.linea = lineaId;
    row.innerHTML = `
        <td><select name="producto_id" required>${opciones || '<option value="">Sin productos</option>'}</select></td>
        <td><input type="number" min="1" name="cantidad_solicitada" required></td>
        <td><input type="number" min="0" name="cantidad_entregada" required></td>
        <td><input type="number" min="0" max="100" step="0.1" name="porcentaje_defectos" value="0"></td>
        <td><input type="text" name="observaciones"></td>
        <td><button type="button" class="remove-line-btn" aria-label="Quitar producto de la lista">${icon('close', { size: 14 })}</button></td>
    `;
    tbody.appendChild(row);

    row.querySelector('.remove-line-btn').addEventListener('click', () => {
        if (tbody.children.length > 1) {
            row.remove();
        } else {
            showToast('La experiencia debe incluir al menos un producto.', 'error');
        }
    });
}

async function guardarExperiencia() {
    const form = document.getElementById('form-experiencia');
    if (!form.reportValidity()) return;

    const formData = new FormData(form);
    const filas = document.querySelectorAll('#historial-lineas-body tr');

    const detalles = Array.from(filas).map((fila) => ({
        producto_id: Number(fila.querySelector('[name="producto_id"]').value),
        cantidad_solicitada: Number(fila.querySelector('[name="cantidad_solicitada"]').value),
        cantidad_entregada: Number(fila.querySelector('[name="cantidad_entregada"]').value),
        porcentaje_defectos: Number(fila.querySelector('[name="porcentaje_defectos"]').value || 0),
        observaciones: fila.querySelector('[name="observaciones"]').value || null,
    }));

    if (!detalles.length) {
        showToast('Agrega al menos un producto a la experiencia.', 'error');
        return;
    }

    const payload = {
        proveedor_id: Number(formData.get('proveedor_id')),
        fecha_operacion: formData.get('fecha_operacion'),
        tiempo_entrega_promedio_dias: formData.get('tiempo_entrega_promedio_dias') ? Number(formData.get('tiempo_entrega_promedio_dias')) : null,
        cumplimiento_porcentaje: formData.get('cumplimiento_porcentaje') ? Number(formData.get('cumplimiento_porcentaje')) : null,
        observaciones: formData.get('observaciones') || null,
        detalles,
    };

    const btn = document.getElementById('btn-guardar-experiencia');
    btn.disabled = true;
    btn.textContent = 'Guardando…';

    try {
        await api.historial.create(payload);
        showToast('Experiencia de desempeño registrada.', 'success');
        Modal.close();
        cargarHistorial();
    } catch (err) {
        showToast(err.message, 'error');
        btn.disabled = false;
        btn.textContent = 'Registrar experiencia';
    }
}
