/* ============================================================
   Página: Detalle de Evaluación y Recomendación
   ============================================================ */

const CRITERIOS_LABELS = {
    precio: 'Precio',
    calidad: 'Calidad',
    logistica: 'Logística',
    historial: 'Historial',
    riesgo: 'Riesgo',
    final: 'Puntaje Final',
};

const CRITERIOS_ICONS = {
    precio: 'dollar',
    calidad: 'award',
    logistica: 'truck',
    historial: 'clock',
    riesgo: 'shield',
    final: 'star',
};

const AGENTES_TABS = [
    { key: 'financiero', label: 'Financiero', icon: 'dollar' },
    { key: 'calidad', label: 'Calidad', icon: 'award' },
    { key: 'logistico', label: 'Logístico', icon: 'truck' },
    { key: 'riesgo', label: 'Riesgo', icon: 'shield' },
    { key: 'decisor', label: 'Decisor', icon: 'checkCircle' },
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
        document.getElementById('detalle-content').innerHTML = renderAlert({ type: 'danger', title: 'Evaluación no especificada', body: 'No se indicó un identificador de evaluación válido en la URL.' });
        renderIcons(document.getElementById('detalle-content'));
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
            contenedor.innerHTML = `<div class="empty-state"><span class="icon-tile neutral">${icon('providers', { size: 18 })}</span><div class="empty-state-title">Sin coincidencias</div><div class="empty-state-desc">Ningún proveedor activo ofrece los productos solicitados en esta evaluación.</div></div>`;
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
        contenedor.innerHTML = `<div class="error-state">${icon('alertTriangle', { size: 18 })}<div class="empty-state-desc">${escapeHtml(err.message)}</div></div>`;
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
        contenido.innerHTML = renderAlert({ type: 'danger', title: 'No se pudo cargar la evaluación', body: escapeHtml(err.message) });
        renderIcons(contenido);
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
                    <span class="icon-tile">${icon('evaluations', { size: 20 })}</span>
                    <div class="empty-state-title">Evaluación pendiente de procesar</div>
                    <div class="empty-state-desc">El motor de decisión todavía no calculó puntajes ni recomendación para esta solicitud.</div>
                    <button class="btn btn-primary mt-1" id="btn-procesar-detalle">Procesar evaluación ahora</button>
                </div>
            </div>
        </div>
    `;

    document.getElementById('btn-procesar-detalle').addEventListener('click', async (e) => {
        const btn = e.target.closest('button');
        btn.disabled = true;
        btn.textContent = 'Procesando…';
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
            <span class="icon-tile">${icon('star', { size: 22 })}</span>
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

        <div class="card mb-1" id="card-metodologia"></div>

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
            <div class="card-header">
                <div>
                    <h2>Dictámenes del motor de agentes</h2>
                    <div class="card-subtitle">Financiero · Calidad · Logístico · Riesgo · Decisor</div>
                </div>
            </div>
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
        renderMetodologia();
        renderDictamenesAgentes();
    } catch (err) {
        const body = document.querySelector('#card-dictamenes-agentes .card-body');
        if (body) body.innerHTML = renderAlert({ type: 'danger', title: 'No se pudo obtener el informe agéntico', body: escapeHtml(err.message) });
        renderIcons(body);
        const metCard = document.getElementById('card-metodologia');
        if (metCard) metCard.remove();
    }
}

const CRITERIOS_ORDEN = ['precio', 'calidad', 'logistica', 'historial', 'riesgo'];

function renderMetodologia() {
    const card = document.getElementById('card-metodologia');
    if (!card || !informeAgentesActual) return;

    const ponderaciones = informeAgentesActual.ponderaciones || {};
    const prioridad = informeAgentesActual.prioridad || evaluacionActual.prioridad || 'balanceado';

    card.innerHTML = `
        <div class="card-header"><h2>Metodología aplicada</h2></div>
        <div class="card-body">
            ${renderAlert({
                type: 'info',
                iconName: 'info',
                title: 'Cálculo 100% determinístico',
                body: `Prioridad seleccionada: <strong>${escapeHtml(prioridad)}</strong>. El puntaje final de cada proveedor es la suma ponderada de 5 criterios, calculada con reglas de negocio fijas — no interviene ningún modelo de lenguaje en esta cifra.`,
            })}
            <div class="flex" style="gap:0.6rem; flex-wrap:wrap; margin-top:0.9rem;">
                ${CRITERIOS_ORDEN.map((c) => `
                    <span class="badge badge-neutral" style="padding:0.4rem 0.7rem;">
                        ${icon(CRITERIOS_ICONS[c], { size: 13 })} ${CRITERIOS_LABELS[c]}: ${Math.round((ponderaciones[c] || 0) * 100)}%
                    </span>
                `).join('')}
            </div>
        </div>
    `;
    renderIcons(card);
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
        <div class="ai-provenance-alert">
            ${renderAlert({
                type: 'ai',
                iconName: 'sparkles',
                title: 'Motor de agentes especializados (reglas determinísticas)',
                body: 'Cada dictamen es generado por un agente de dominio (Financiero, Calidad, Logístico, Riesgo, Decisor) usando fórmulas y umbrales fijos sobre datos reales del sistema. No es texto generado por un modelo de lenguaje — esa capacidad está prevista para una fase posterior.',
            })}
        </div>
        <div class="agent-dictamen mb-1">
            <strong>Conclusión ejecutiva del Agente Decisor:</strong><br>
            ${escapeHtml(informeAgentesActual.conclusion_ejecutiva || '—')}
        </div>
        <div class="provider-tabs-nav">${chips}</div>
        <div class="tabs" id="agentes-tabs-nav"></div>
        <div id="agentes-tab-panels"></div>
    `;
    renderIcons(body);

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
        <button class="tab-btn ${idx === 0 ? 'active' : ''}" data-tab="${tab.key}">
            <span class="agent-tab-icon">${icon(tab.icon, { size: 14 })}</span>${tab.label}
        </button>
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
