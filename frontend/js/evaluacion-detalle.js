/* ============================================================
   Página: Detalle de Evaluación y Recomendación Agéntica
   ============================================================ */

const CRITERIOS_LABELS = {
    precio: 'Precio',
    calidad: 'Calidad',
    logistica: 'Logística',
    historial: 'Historial',
    riesgo: 'Riesgo',
    final: 'Puntaje Final',
};

const AGENTES_TABS = [
    { key: 'financiero', label: 'Agente Financiero' },
    { key: 'calidad', label: 'Agente de Calidad' },
    { key: 'logistico', label: 'Agente Logístico' },
    { key: 'riesgo', label: 'Agente de Riesgo' },
    { key: 'decisor', label: 'Agente Decisor' },
];

let evaluacionActual = null;
let informeAgentesActual = null;
let proveedorSeleccionadoId = null;

function obtenerEvaluacionId() {
    const params = new URLSearchParams(window.location.search);
    return params.get('id');
}

document.addEventListener('DOMContentLoaded', () => {
    const id = obtenerEvaluacionId();
    if (!id) {
        document.getElementById('detalle-content').innerHTML = `<div class="error-state">⚠ No se especificó una evaluación válida.</div>`;
        return;
    }
    document.getElementById('btn-ver-compatibles').addEventListener('click', () => abrirModalCompatibles(id));
    cargarEvaluacion(id);
});

async function abrirModalCompatibles(id) {
    Modal.open({
        title: 'Proveedores compatibles con esta evaluación',
        size: 'lg',
        bodyHTML: `<div id="compatibles-contenido"><div class="loading-state"><div class="spinner"></div><span>Consultando cobertura de catálogo...</span></div></div>`,
        footerHTML: `<button class="btn btn-primary" id="btn-cerrar-compatibles">Cerrar</button>`,
    });
    document.getElementById('btn-cerrar-compatibles').addEventListener('click', () => Modal.close());

    const contenedor = document.getElementById('compatibles-contenido');
    try {
        const data = await api.evaluaciones.compatibles(id);
        const proveedores = data.proveedores_compatibles || [];

        if (!proveedores.length) {
            contenedor.innerHTML = `<div class="empty-state">Ningún proveedor activo ofrece los productos solicitados en esta evaluación.</div>`;
            return;
        }

        contenedor.innerHTML = `
            <p class="text-muted" style="margin-top:0;">
                ${data.total_proveedores_compatibles} proveedor(es) con al menos un producto de los ${data.total_productos_solicitados} solicitados.
            </p>
            <div class="table-wrapper">
                <table class="data-table">
                    <thead>
                        <tr><th>Proveedor</th><th>Cobertura</th><th>Costo total</th><th>Entrega máx.</th><th>Cumple plazo</th><th>Faltantes</th></tr>
                    </thead>
                    <tbody>
                        ${proveedores.map((p) => `
                            <tr>
                                <td><strong>${escapeHtml(p.razon_social)}</strong><br><span class="cell-muted">${escapeHtml(p.ciudad || '—')}</span></td>
                                <td>${p.es_cobertura_total ? '<span class="badge badge-success">100%</span>' : `<span class="badge badge-warning">${p.cobertura_porcentaje}%</span>`}</td>
                                <td>${formatCurrency(p.costo_total)}</td>
                                <td class="cell-muted">${p.tiempo_entrega_max_dias} día(s)</td>
                                <td>${p.cumple_plazo_maximo ? '<span class="badge badge-success">Sí</span>' : '<span class="badge badge-danger">No</span>'}</td>
                                <td class="cell-muted">${(p.productos_faltantes || []).length ? escapeHtml(p.productos_faltantes.map((f) => f.nombre_producto).join(', ')) : '—'}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
    } catch (err) {
        contenedor.innerHTML = `<div class="error-state">⚠ ${escapeHtml(err.message)}</div>`;
    }
}

async function cargarEvaluacion(id) {
    const contenido = document.getElementById('detalle-content');
    try {
        evaluacionActual = await api.evaluaciones.get(id);
        document.getElementById('detalle-titulo').textContent = evaluacionActual.titulo;
        document.getElementById('detalle-subtitulo').textContent =
            evaluacionActual.descripcion_necesidad || `${(evaluacionActual.productos_solicitados || []).length} producto(s) solicitado(s)`;

        const procesada = (evaluacionActual.detalles_resultado || []).length > 0;
        if (!procesada) {
            renderSinProcesar(id);
        } else {
            await renderProcesada(id);
        }
    } catch (err) {
        contenido.innerHTML = `<div class="error-state">⚠ ${escapeHtml(err.message)}</div>`;
    }
}

function renderProductosSolicitadosHTML() {
    const productos = evaluacionActual.productos_solicitados || [];
    if (!productos.length) return '<p class="text-muted">Sin productos registrados.</p>';
    return `
        <div class="table-wrapper">
            <table class="data-table">
                <thead><tr><th>Producto</th><th>Cantidad</th><th>Especificaciones</th></tr></thead>
                <tbody>
                    ${productos.map((p) => `
                        <tr>
                            <td>${escapeHtml(p.producto ? p.producto.nombre : `Producto #${p.producto_id}`)}</td>
                            <td>${p.cantidad}</td>
                            <td class="cell-muted">${escapeHtml(p.especificaciones || '—')}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;
}

function renderSinProcesar(id) {
    const contenido = document.getElementById('detalle-content');
    contenido.innerHTML = `
        <div class="card mb-1">
            <div class="card-header"><h2>Productos solicitados</h2></div>
            <div class="card-body">${renderProductosSolicitadosHTML()}</div>
        </div>
        <div class="card">
            <div class="card-body">
                <div class="empty-state">
                    <p style="margin:0;">Esta evaluación todavía no ha sido procesada por el motor de agentes.</p>
                    <button class="btn btn-primary mt-1" id="btn-procesar-detalle">Procesar evaluación ahora</button>
                </div>
            </div>
        </div>
    `;

    document.getElementById('btn-procesar-detalle').addEventListener('click', async (e) => {
        const btn = e.target;
        btn.disabled = true;
        btn.textContent = 'Procesando...';
        try {
            await api.evaluaciones.procesar(id);
            showToast('Evaluación procesada correctamente.', 'success');
            cargarEvaluacion(id);
        } catch (err) {
            showToast(err.message, 'error');
            btn.disabled = false;
            btn.textContent = 'Procesar evaluación ahora';
        }
    });
}

async function renderProcesada(id) {
    const contenido = document.getElementById('detalle-content');
    const detalles = [...evaluacionActual.detalles_resultado].sort((a, b) => b.puntaje_final - a.puntaje_final);
    const ganador = detalles.find((d) => d.recomendado) || detalles[0];
    proveedorSeleccionadoId = ganador.proveedor_id;

    contenido.innerHTML = `
        <div class="recommended-banner">
            <div class="icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2l2.9 6.26L21 9.27l-4.5 4.38L17.8 20 12 16.9 6.2 20l1.3-6.35L3 9.27l6.1-1.01L12 2z"></path></svg>
            </div>
            <div>
                <div class="label">Proveedor recomendado</div>
                <div class="name">${escapeHtml(ganador.proveedor ? ganador.proveedor.razon_social : `Proveedor #${ganador.proveedor_id}`)}</div>
            </div>
            <div class="score">
                <div class="label">Puntaje final</div>
                <div class="value">${Number(ganador.puntaje_final).toFixed(1)}/100</div>
            </div>
        </div>

        <div class="score-grid">
            ${['precio', 'calidad', 'logistica', 'historial', 'riesgo', 'final'].map((crit) => {
                const valor = Number(ganador[`puntaje_${crit}`]);
                return `
                    <div class="score-card ${crit === 'final' ? 'final' : ''}">
                        <div class="label">${CRITERIOS_LABELS[crit]}</div>
                        <div class="value">${valor.toFixed(1)}</div>
                        <div class="score-bar-track"><div class="score-bar-fill" style="width:${Math.min(valor, 100)}%"></div></div>
                    </div>
                `;
            }).join('')}
        </div>

        <div class="card mb-1">
            <div class="card-header"><h2>Ranking de proveedores evaluados</h2></div>
            <div class="table-wrapper">
                <table class="data-table ranking-table">
                    <thead>
                        <tr><th>#</th><th>Proveedor</th><th>Precio</th><th>Calidad</th><th>Logística</th><th>Historial</th><th>Riesgo</th><th>Final</th><th></th></tr>
                    </thead>
                    <tbody>
                        ${detalles.map((d, idx) => `
                            <tr>
                                <td class="cell-muted">${idx + 1}</td>
                                <td class="${d.recomendado ? 'is-recommended' : ''}">${escapeHtml(d.proveedor ? d.proveedor.razon_social : `Proveedor #${d.proveedor_id}`)}${d.recomendado ? ' ★' : ''}</td>
                                <td>${Number(d.puntaje_precio).toFixed(1)}</td>
                                <td>${Number(d.puntaje_calidad).toFixed(1)}</td>
                                <td>${Number(d.puntaje_logistica).toFixed(1)}</td>
                                <td>${Number(d.puntaje_historial).toFixed(1)}</td>
                                <td>${Number(d.puntaje_riesgo).toFixed(1)}</td>
                                <td><strong>${Number(d.puntaje_final).toFixed(1)}</strong></td>
                                <td class="text-right"><button class="btn btn-ghost btn-sm" data-ver-agentes="${d.proveedor_id}">Ver dictámenes</button></td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        </div>

        <div class="card mb-1">
            <div class="card-header"><h2>Productos solicitados</h2></div>
            <div class="card-body">${renderProductosSolicitadosHTML()}</div>
        </div>

        <div class="card" id="card-dictamenes-agentes">
            <div class="card-header"><h2>Dictámenes de Agentes IA</h2></div>
            <div class="card-body">
                <div class="loading-state"><div class="spinner"></div><span>Consultando informe agéntico...</span></div>
            </div>
        </div>
    `;

    contenido.querySelectorAll('[data-ver-agentes]').forEach((btn) =>
        btn.addEventListener('click', () => {
            proveedorSeleccionadoId = Number(btn.dataset.verAgentes);
            renderDictamenesAgentes();
            document.getElementById('card-dictamenes-agentes').scrollIntoView({ behavior: 'smooth', block: 'start' });
        })
    );

    await cargarInformeAgentes(id);
}

async function cargarInformeAgentes(id) {
    try {
        informeAgentesActual = await api.evaluaciones.informeAgentes(id);
        renderDictamenesAgentes();
    } catch (err) {
        const body = document.querySelector('#card-dictamenes-agentes .card-body');
        if (body) body.innerHTML = `<div class="error-state">⚠ No se pudo obtener el informe agéntico: ${escapeHtml(err.message)}</div>`;
    }
}

function renderDictamenesAgentes() {
    const body = document.querySelector('#card-dictamenes-agentes .card-body');
    if (!body || !informeAgentesActual) return;

    const ranking = informeAgentesActual.ranking || [];
    if (!ranking.length) {
        body.innerHTML = `<div class="empty-state">No hay dictámenes disponibles.</div>`;
        return;
    }

    if (!ranking.some((r) => r.proveedor_id === proveedorSeleccionadoId)) {
        proveedorSeleccionadoId = ranking[0].proveedor_id;
    }

    const chips = ranking.map((r) => `
        <button class="provider-tab-chip ${r.proveedor_id === proveedorSeleccionadoId ? 'active' : ''}" data-chip="${r.proveedor_id}">
            ${escapeHtml(r.razon_social)}${r.recomendado ? ' ★' : ''}
        </button>
    `).join('');

    body.innerHTML = `
        <div class="agent-dictamen mb-1">
            <strong>Conclusión ejecutiva del Agente Decisor:</strong><br>
            ${escapeHtml(informeAgentesActual.conclusion_ejecutiva || '—')}
        </div>
        <div class="provider-tabs-nav">${chips}</div>
        <div class="tabs" id="agentes-tabs-nav"></div>
        <div id="agentes-tab-panels"></div>
    `;

    body.querySelectorAll('[data-chip]').forEach((chip) =>
        chip.addEventListener('click', () => {
            proveedorSeleccionadoId = Number(chip.dataset.chip);
            renderDictamenesAgentes();
        })
    );

    const seleccionado = ranking.find((r) => r.proveedor_id === proveedorSeleccionadoId);
    const tabsNav = document.getElementById('agentes-tabs-nav');
    const tabPanels = document.getElementById('agentes-tab-panels');

    tabsNav.innerHTML = AGENTES_TABS.map((tab, idx) => `
        <button class="tab-btn ${idx === 0 ? 'active' : ''}" data-tab="${tab.key}">${tab.label}</button>
    `).join('');

    tabPanels.innerHTML = AGENTES_TABS.map((tab, idx) => {
        let texto;
        if (tab.key === 'decisor') {
            const detalle = (evaluacionActual.detalles_resultado || []).find((d) => d.proveedor_id === proveedorSeleccionadoId);
            texto = detalle?.explicacion || 'Sin explicación disponible para este proveedor.';
        } else {
            texto = seleccionado?.dictamenes?.[tab.key] || 'Sin dictamen disponible.';
        }
        return `
            <div class="tab-panel ${idx === 0 ? 'active' : ''}" data-tab-panel="${tab.key}">
                <div class="agent-dictamen">${escapeHtml(texto)}</div>
            </div>
        `;
    }).join('');

    tabsNav.querySelectorAll('.tab-btn').forEach((btn) => {
        btn.addEventListener('click', () => {
            tabsNav.querySelectorAll('.tab-btn').forEach((b) => b.classList.remove('active'));
            tabPanels.querySelectorAll('.tab-panel').forEach((p) => p.classList.remove('active'));
            btn.classList.add('active');
            tabPanels.querySelector(`[data-tab-panel="${btn.dataset.tab}"]`).classList.add('active');
        });
    });
}
