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
        elCumplimiento.textContent = `${promedio.toFixed(1)}%`;
    } catch {
        elCumplimiento.textContent = '—';
    }

    try {
        const evaluaciones = await api.evaluaciones.list({ limit: 1000 });
        const procesadas = evaluaciones.filter((e) => (e.detalles_resultado || []).length > 0);
        elEvaluaciones.textContent = procesadas.length;
    } catch {
        elEvaluaciones.textContent = '—';
    }
}

async function cargarUltimasEvaluaciones() {
    const body = document.getElementById('recent-evaluations-body');
    try {
        const evaluaciones = await api.evaluaciones.list({ limit: 1000 });
        if (!evaluaciones.length) {
            body.innerHTML = emptyRow(5, 'Todavía no se han creado evaluaciones.');
            return;
        }

        const ultimas = [...evaluaciones]
            .sort((a, b) => new Date(b.fecha_evaluacion) - new Date(a.fecha_evaluacion))
            .slice(0, 6);

        body.innerHTML = ultimas.map((ev) => {
            const recomendado = (ev.detalles_resultado || []).find((d) => d.recomendado);
            const recomendadoHTML = recomendado
                ? `<span class="recommended-cell">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 6L9 17l-5-5"></path></svg>
                        ${escapeHtml(recomendado.proveedor ? recomendado.proveedor.razon_social : `Proveedor #${recomendado.proveedor_id}`)}
                   </span>`
                : `<span class="text-muted">Pendiente de procesar</span>`;

            const estado = (ev.detalles_resultado || []).length > 0 ? 'Procesada' : (ev.estado || 'Pendiente');

            return `
                <tr>
                    <td>
                        <div class="eval-title-cell">
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
