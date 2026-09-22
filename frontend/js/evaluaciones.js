/* ============================================================
   Página: Evaluaciones de Necesidades
   ============================================================ */

let productosCacheEval = [];
let evaluacionesCache = [];
let contadorLineasEval = 0;

document.addEventListener('DOMContentLoaded', async () => {
    document.getElementById('btn-agregar-linea-eval').addEventListener('click', () => agregarLineaEvaluacion());
    document.getElementById('form-evaluacion').addEventListener('submit', crearEvaluacion);

    await cargarProductosParaEvaluacion();
    agregarLineaEvaluacion();
    cargarEvaluaciones();
});

async function cargarProductosParaEvaluacion() {
    try {
        productosCacheEval = await api.productos.list({ limit: 1000 });
    } catch (err) {
        showToast('No se pudieron cargar los productos: ' + err.message, 'error');
    }
}

function agregarLineaEvaluacion() {
    const tbody = document.getElementById('eval-lineas-body');
    const lineaId = contadorLineasEval++;
    const opciones = productosCacheEval.map((p) => `<option value="${p.id}">${escapeHtml(p.nombre)}</option>`).join('');

    const row = document.createElement('tr');
    row.dataset.linea = lineaId;
    row.innerHTML = `
        <td><select name="producto_id" required>${opciones || '<option value="">Sin productos</option>'}</select></td>
        <td><input type="number" min="1" name="cantidad" required value="1"></td>
        <td><input type="text" name="especificaciones" placeholder="Opcional"></td>
        <td><button type="button" class="remove-line-btn" title="Quitar">&times;</button></td>
    `;
    tbody.appendChild(row);

    row.querySelector('.remove-line-btn').addEventListener('click', () => {
        if (tbody.children.length > 1) {
            row.remove();
        } else {
            showToast('La evaluación debe incluir al menos un producto.', 'error');
        }
    });
}

async function crearEvaluacion(event) {
    event.preventDefault();
    const form = document.getElementById('form-evaluacion');
    if (!form.reportValidity()) return;

    const formData = new FormData(form);
    const filas = document.querySelectorAll('#eval-lineas-body tr');

    const productos = Array.from(filas).map((fila) => ({
        producto_id: Number(fila.querySelector('[name="producto_id"]').value),
        cantidad: Number(fila.querySelector('[name="cantidad"]').value),
        especificaciones: fila.querySelector('[name="especificaciones"]').value || null,
    }));

    if (!productos.length) {
        showToast('Agrega al menos un producto a la evaluación.', 'error');
        return;
    }

    const payload = {
        titulo: formData.get('titulo'),
        descripcion_necesidad: formData.get('descripcion_necesidad') || null,
        entrega_maxima_dias: formData.get('entrega_maxima_dias') ? Number(formData.get('entrega_maxima_dias')) : null,
        prioridad: formData.get('prioridad') || 'balanceado',
        productos,
    };

    const btn = document.getElementById('btn-crear-evaluacion');
    btn.disabled = true;
    btn.textContent = 'Creando...';

    try {
        await api.evaluaciones.create(payload);
        showToast('Evaluación creada correctamente.', 'success');
        form.reset();
        document.getElementById('eval-lineas-body').innerHTML = '';
        agregarLineaEvaluacion();
        cargarEvaluaciones();
    } catch (err) {
        showToast(err.message, 'error');
    } finally {
        btn.disabled = false;
        btn.textContent = 'Crear evaluación';
    }
}

async function cargarEvaluaciones() {
    const body = document.getElementById('evaluaciones-body');
    body.innerHTML = loadingRow(5);
    try {
        evaluacionesCache = await api.evaluaciones.list({ limit: 1000 });
        renderEvaluacionesTable();
    } catch (err) {
        body.innerHTML = errorRow(5, err.message);
    }
}

function renderEvaluacionesTable() {
    const body = document.getElementById('evaluaciones-body');
    if (!evaluacionesCache.length) {
        body.innerHTML = emptyRow(5, 'Todavía no se han creado evaluaciones.');
        return;
    }

    const ordenadas = [...evaluacionesCache].sort((a, b) => new Date(b.fecha_evaluacion) - new Date(a.fecha_evaluacion));

    body.innerHTML = ordenadas.map((ev) => {
        const procesada = (ev.detalles_resultado || []).length > 0;
        return `
            <tr>
                <td>
                    <div class="eval-title-cell">
                        <strong>${escapeHtml(ev.titulo)}</strong>
                        <span>${(ev.productos_solicitados || []).length} producto(s) · máx. ${ev.entrega_maxima_dias || '—'} días</span>
                    </div>
                </td>
                <td><span class="badge badge-info">${escapeHtml(ev.prioridad || 'balanceado')}</span></td>
                <td class="cell-muted">${formatDate(ev.fecha_evaluacion)}</td>
                <td>${estadoBadge(procesada ? 'Procesada' : 'Pendiente')}</td>
                <td>
                    <div class="actions-cell" style="justify-content:flex-end;">
                        ${!procesada ? `<button class="btn btn-secondary btn-sm" data-procesar="${ev.id}">Procesar</button>` : ''}
                        <a class="btn btn-ghost btn-sm" href="evaluacion-detalle.html?id=${ev.id}">Ver detalle</a>
                        <button class="btn btn-danger btn-sm" data-eliminar="${ev.id}">Eliminar</button>
                    </div>
                </td>
            </tr>
        `;
    }).join('');

    body.querySelectorAll('[data-procesar]').forEach((btn) =>
        btn.addEventListener('click', () => procesarEvaluacion(Number(btn.dataset.procesar), btn))
    );
    body.querySelectorAll('[data-eliminar]').forEach((btn) =>
        btn.addEventListener('click', () => eliminarEvaluacion(Number(btn.dataset.eliminar)))
    );
}

async function procesarEvaluacion(id, btn) {
    btn.disabled = true;
    btn.textContent = 'Procesando...';
    try {
        await api.evaluaciones.procesar(id);
        showToast('Evaluación procesada. Redirigiendo al detalle...', 'success');
        window.location.href = `evaluacion-detalle.html?id=${id}`;
    } catch (err) {
        showToast(err.message, 'error');
        btn.disabled = false;
        btn.textContent = 'Procesar';
    }
}

async function eliminarEvaluacion(id) {
    const ev = evaluacionesCache.find((e) => e.id === id);
    const confirmado = await Modal.confirm({
        title: 'Eliminar evaluación',
        message: `¿Deseas eliminar la evaluación <strong>${escapeHtml(ev?.titulo || '')}</strong>?`,
        confirmLabel: 'Eliminar',
    });
    if (!confirmado) return;

    try {
        await api.evaluaciones.remove(id);
        showToast('Evaluación eliminada.', 'success');
        cargarEvaluaciones();
    } catch (err) {
        showToast(err.message, 'error');
    }
}
