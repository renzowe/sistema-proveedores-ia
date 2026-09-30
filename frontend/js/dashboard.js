/* ============================================================
   Página: Dashboard
   ============================================================ */

document.addEventListener('DOMContentLoaded', () => {
    cargarKPIs();
    cargarUltimasEvaluaciones();
});

async function cargarKPIs() {
    const elProveedores = document.getElementById('kpi-proveedores');
    const elProductos = document.getElementById('kpi-productos');
    const elCumplimiento = document.getElementById('kpi-cumplimiento');
    const elEvaluaciones = document.getElementById('kpi-evaluaciones');

    try {
        const proveedores = await api.proveedores.list({ limit: 1000 });
        const activos = proveedores.filter((p) => (p.estado || '').toLowerCase() === 'activo');
        elProveedores.textContent = activos.length;
    } catch {
        elProveedores.textContent = '—';
    }

    try {
        const productos = await api.productos.list({ limit: 1000 });
        elProductos.textContent = productos.length;
    } catch {
        elProductos.textContent = '—';
    }

    try {
        const historial = await api.historial.list({ limit: 1000 });
        const valores = historial
            .map((h) => Number(h.cumplimiento_porcentaje))
            .filter((v) => !Number.isNaN(v));
        const promedio = valores.length ? valores.reduce((a, b) => a + b, 0) / valores.length : 0;
        elCumplimiento.textContent = valores.length ? `${promedio.toFixed(1)}%` : 'Sin datos';
    } catch {
        elCumplimiento.textContent = '—';
    }

    try {
        const evaluaciones = await api.evaluaciones.list({ limit: 1000 });
        const procesadas = evaluaciones.filter((e) => (e.detalles_resultado || []).length > 0);
        const pendientes = evaluaciones.filter((e) => (e.detalles_resultado || []).length === 0);
        elEvaluaciones.textContent = procesadas.length;
        renderPendientes(pendientes);
    } catch {
        elEvaluaciones.textContent = '—';
    }
}

function renderPendientes(pendientes) {
    const card = document.getElementById('pending-card');
    const body = document.getElementById('pending-card-body');
    if (!pendientes.length) {
        card.hidden = true;
        return;
    }
    card.hidden = false;
    body.innerHTML = renderAlert({
        type: 'warning',
        title: `${pendientes.length} evaluación(es) sin procesar`,
        body: `Hay solicitudes creadas que todavía no pasaron por el motor de decisión. <a href="evaluaciones.html">Ir a Evaluaciones →</a>`,
    });
    renderIcons(body);
}

async function cargarUltimasEvaluaciones() {
    const body = document.getElementById('recent-evaluations-body');
    try {
        const evaluaciones = await api.evaluaciones.list({ limit: 1000 });
        if (!evaluaciones.length) {
            body.innerHTML = emptyRow(5, 'Crea tu primera evaluación para ver resultados aquí.', { title: 'Todavía no hay evaluaciones', icon: 'evaluations' });
            return;
        }

        const ultimas = [...evaluaciones]
            .sort((a, b) => new Date(b.fecha_evaluacion) - new Date(a.fecha_evaluacion))
            .slice(0, 6);

        body.innerHTML = ultimas.map((ev) => {
            const recomendado = (ev.detalles_resultado || []).find((d) => d.recomendado);
            const recomendadoHTML = recomendado
                ? `<span class="recommended-cell">${icon('checkCircle', { size: 14 })}${escapeHtml(recomendado.proveedor ? recomendado.proveedor.razon_social : `Proveedor #${recomendado.proveedor_id}`)}</span>`
                : `<span class="text-muted">Pendiente de procesar</span>`;

            const estado = (ev.detalles_resultado || []).length > 0 ? 'Procesada' : (ev.estado || 'Pendiente');

            return `
                <tr>
                    <td>
                        <div class="cell-primary">
                            <strong>${escapeHtml(ev.titulo)}</strong>
                            <span>${(ev.productos_solicitados || []).length} producto(s)</span>
                        </div>
                    </td>
                    <td class="cell-muted">${formatDate(ev.fecha_evaluacion)}</td>
                    <td>${estadoBadge(estado)}</td>
                    <td>${recomendadoHTML}</td>
                    <td class="text-right">
                        <a class="btn btn-ghost btn-sm" href="evaluacion-detalle.html?id=${ev.id}">Ver detalle</a>
                    </td>
                </tr>
            `;
        }).join('');
    } catch (err) {
        body.innerHTML = errorRow(5, err.message);
    }
}
