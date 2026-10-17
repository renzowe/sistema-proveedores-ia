/* ============================================================
   Página: Evaluaciones de Necesidades
   ============================================================ */

let productosCacheEval = [];
let evaluacionesCache = [];
const evaluacionesTable = createTableController(8);

// Borrador compartido entre el formulario y el asistente conversacional.
// Ambos lo leen y lo escriben; nunca se crea ninguna evaluación hasta que
// el usuario confirma explícitamente con "Confirmar y evaluar".
const borrador = {
    titulo: '',
    descripcion_necesidad: '',
    entrega_maxima_dias: null,
    prioridad: 'balanceado',
    productos: [], // { nombre_detectado, cantidad, especificaciones, producto_id, producto_nombre_catalogo, sin_coincidencia }
};

// Campos que el usuario tocó a mano DESDE el último mensaje enviado al
// asistente — se usa para no pisar una edición manual reciente con una
// respuesta del chat que ya estaba "en vuelo" cuando el usuario editó.
const camposEditadosManualmente = new Set();

let resultadoActual = null;
let resultadoDesactualizado = false;
let evaluandoConfirmacion = false;
// Firma (JSON del payload) de la última versión del borrador evaluada con
// éxito: confirmar otra vez la misma versión crearía un duplicado.
let firmaUltimaEvaluada = null;
const TEXTO_BTN_CONFIRMAR = 'Confirmar y evaluar';
const TEXTO_BTN_EVALUADO = 'Evaluado — modifica el borrador para reevaluar';

const ETIQUETAS_CAMPO = {
    titulo: 'título',
    descripcion_necesidad: 'descripción',
    entrega_maxima_dias: 'plazo de entrega',
    prioridad: 'prioridad',
    productos: 'productos',
};

document.addEventListener('DOMContentLoaded', async () => {
    // El chat se crea antes de cualquier llamada al backend: si el servidor
    // tarda (p. ej. arranque en frío de Render) o no responde, el panel
    // igual aparece y muestra el aviso de conexión en vez de quedar vacío.
    initAsistente({
        modo: 'borrador',
        contenedorId: 'asistente-chat-container',
        obtenerBorrador: obtenerBorradorParaAsistente,
        aplicarBorrador: aplicarBorradorDesdeAsistente,
    });

    document.getElementById('btn-agregar-linea-eval').addEventListener('click', agregarLineaManual);
    document.getElementById('form-evaluacion').addEventListener('submit', confirmarYEvaluar);
    document.getElementById('search-evaluaciones').addEventListener('input', (e) => {
        evaluacionesTable.setSearch(e.target.value);
        renderEvaluacionesTable();
    });
    document.getElementById('filtro-estado-eval').addEventListener('change', () => {
        aplicarFiltroEstadoEval();
        renderEvaluacionesTable();
    });

    wireCamposFormulario();
    wireSelectorVista();

    sincronizarFormularioDesdeBorrador();
    cargarEvaluaciones();
    await cargarProductosParaEvaluacion();
    sincronizarFormularioDesdeBorrador();
});

async function cargarProductosParaEvaluacion() {
    try {
        productosCacheEval = await api.productos.list({ limit: 1000 });
    } catch (err) {
        showToast('No se pudieron cargar los productos: ' + err.message, 'error');
    }
}

/* ---------------- Selector de vista (Ambos / Solo chat / Solo formulario) --------------- */

const VISTAS_EVALUACION = ['ambos', 'chat', 'formulario'];

function seleccionarVista(vista) {
    document.querySelectorAll('#selector-vista-evaluacion .tab-btn').forEach((b) => b.classList.toggle('active', b.dataset.vista === vista));

    const layout = document.getElementById('asistente-layout');
    layout.classList.remove(...VISTAS_EVALUACION.map((v) => `vista-${v}`));
    layout.classList.add(`vista-${vista}`);
}

function wireSelectorVista() {
    document.getElementById('selector-vista-evaluacion').addEventListener('click', (e) => {
        const btn = e.target.closest('[data-vista]');
        if (btn) seleccionarVista(btn.dataset.vista);
    });

    // ?vista=chat llega desde el acceso directo flotante de las demás páginas.
    const vistaInicial = new URLSearchParams(window.location.search).get('vista');
    if (VISTAS_EVALUACION.includes(vistaInicial)) {
        seleccionarVista(vistaInicial);
        if (vistaInicial === 'chat') {
            document.getElementById('asistente-chat-container-input')?.focus();
        }
    }
}

/* ---------------- Enlace entre el formulario y el borrador compartido ------------------- */

function wireCamposFormulario() {
    const form = document.getElementById('form-evaluacion');

    form.querySelector('[name="titulo"]').addEventListener('input', (e) => {
        borrador.titulo = e.target.value;
        marcarCampoEditado('titulo');
    });
    form.querySelector('[name="descripcion_necesidad"]').addEventListener('input', (e) => {
        borrador.descripcion_necesidad = e.target.value || null;
        marcarCampoEditado('descripcion_necesidad');
    });
    form.querySelector('[name="entrega_maxima_dias"]').addEventListener('input', (e) => {
        borrador.entrega_maxima_dias = e.target.value ? Number(e.target.value) : null;
        marcarCampoEditado('entrega_maxima_dias');
    });
    form.querySelectorAll('[name="prioridad"]').forEach((radio) => {
        radio.addEventListener('change', (e) => {
            if (e.target.checked) {
                borrador.prioridad = e.target.value;
                marcarCampoEditado('prioridad');
            }
        });
    });
}

function marcarCampoEditado(campo) {
    camposEditadosManualmente.add(campo);
    marcarResultadoDesactualizado();
}

function marcarResultadoDesactualizado() {
    if (resultadoActual && !resultadoDesactualizado) {
        resultadoDesactualizado = true;
        renderResultado();
        const btn = document.getElementById('btn-confirmar-evaluar');
        btn.disabled = false;
        btn.textContent = TEXTO_BTN_CONFIRMAR;
    }
}

function sincronizarFormularioDesdeBorrador() {
    const form = document.getElementById('form-evaluacion');
    form.querySelector('[name="titulo"]').value = borrador.titulo || '';
    form.querySelector('[name="descripcion_necesidad"]').value = borrador.descripcion_necesidad || '';
    form.querySelector('[name="entrega_maxima_dias"]').value = borrador.entrega_maxima_dias || '';
    const radioPrioridad = form.querySelector(`[name="prioridad"][value="${borrador.prioridad}"]`);
    if (radioPrioridad) radioPrioridad.checked = true;
    renderLineasProductos();
}

/* ---------------- Líneas de producto (ligadas a borrador.productos) --------------------- */

function renderLineasProductos() {
    const tbody = document.getElementById('eval-lineas-body');
    tbody.innerHTML = '';
    borrador.productos.forEach((_, index) => tbody.appendChild(crearFilaProducto(index)));
}

function crearFilaProducto(index) {
    const entry = borrador.productos[index];
    const opciones = productosCacheEval.map((p) =>
        `<option value="${p.id}" ${entry.producto_id === p.id ? 'selected' : ''}>${escapeHtml(p.nombre)}</option>`
    ).join('');

    const row = document.createElement('tr');
    row.dataset.index = index;
    if (entry.sin_coincidencia) row.classList.add('linea-sin-coincidencia');
    row.innerHTML = `
        <td>
            <select name="producto_id" required>
                <option value="">${entry.sin_coincidencia ? `Sin coincidencia: "${escapeHtml(entry.nombre_detectado)}"` : 'Selecciona un producto'}</option>
                ${opciones}
            </select>
            ${entry.sin_coincidencia ? `<div class="hint" style="color:var(--warning);margin-top:0.25rem;">El asistente detectó "${escapeHtml(entry.nombre_detectado)}" — selecciona el producto correcto del catálogo</div>` : ''}
        </td>
        <td><input type="number" min="1" name="cantidad" required value="${entry.cantidad || 1}"></td>
        <td><input type="text" name="especificaciones" maxlength="500" placeholder="Opcional" value="${escapeHtml(entry.especificaciones || '')}"></td>
        <td><button type="button" class="remove-line-btn" aria-label="Quitar producto de la lista">${icon('close', { size: 14 })}</button></td>
    `;

    row.querySelector('[name="producto_id"]').addEventListener('change', (e) => {
        const productoId = Number(e.target.value) || null;
        const producto = productosCacheEval.find((p) => p.id === productoId);
        borrador.productos[index].producto_id = productoId;
        borrador.productos[index].producto_nombre_catalogo = producto ? producto.nombre : null;
        borrador.productos[index].sin_coincidencia = !productoId;
        if (producto) borrador.productos[index].nombre_detectado = producto.nombre;
        marcarCampoEditado('productos');
        renderLineasProductos();
    });
    row.querySelector('[name="cantidad"]').addEventListener('input', (e) => {
        borrador.productos[index].cantidad = Number(e.target.value) || 1;
        marcarCampoEditado('productos');
    });
    row.querySelector('[name="especificaciones"]').addEventListener('input', (e) => {
        borrador.productos[index].especificaciones = e.target.value || null;
        marcarCampoEditado('productos');
    });
    row.querySelector('.remove-line-btn').addEventListener('click', () => {
        borrador.productos.splice(index, 1);
        marcarCampoEditado('productos');
        renderLineasProductos();
    });

    return row;
}

function agregarLineaManual() {
    const primerProducto = productosCacheEval[0] || null;
    borrador.productos.push({
        nombre_detectado: primerProducto ? primerProducto.nombre : '',
        cantidad: 1,
        especificaciones: null,
        producto_id: primerProducto ? primerProducto.id : null,
        producto_nombre_catalogo: primerProducto ? primerProducto.nombre : null,
        sin_coincidencia: !primerProducto,
    });
    marcarCampoEditado('productos');
    renderLineasProductos();
}

/* ---------------- Puente con el asistente conversacional -------------------------------- */

function obtenerBorradorParaAsistente() {
    // Punto de "envío": lo que el usuario ya haya editado a mano viaja en
    // este snapshot, así que a partir de aquí cualquier edición nueva se
    // considera posterior a este mensaje (ver aplicarBorradorDesdeAsistente).
    camposEditadosManualmente.clear();
    return JSON.parse(JSON.stringify(borrador));
}

function aplicarBorradorDesdeAsistente(nuevoBorrador, camposActualizados) {
    const aplicados = [];
    const omitidos = [];
    const camposEscalares = ['titulo', 'descripcion_necesidad', 'entrega_maxima_dias', 'prioridad'];

    (camposActualizados || []).forEach((campo) => {
        if (camposEditadosManualmente.has(campo)) {
            omitidos.push(campo);
            return;
        }
        if (campo === 'productos') {
            borrador.productos = nuevoBorrador.productos || [];
        } else if (camposEscalares.includes(campo)) {
            borrador[campo] = nuevoBorrador[campo];
        } else {
            return;
        }
        aplicados.push(campo);
    });

    sincronizarFormularioDesdeBorrador();

    if (aplicados.length) {
        marcarResultadoDesactualizado();
        showToast(`El asistente actualizó: ${aplicados.map((c) => ETIQUETAS_CAMPO[c] || c).join(', ')}.`, 'info');
    }
    if (omitidos.length) {
        showToast(`No se aplicaron cambios en ${omitidos.map((c) => ETIQUETAS_CAMPO[c] || c).join(', ')} porque los editaste manualmente.`, 'warning');
    }
}

/* ---------------- Confirmar y evaluar ---------------------------------------------------- */

async function confirmarYEvaluar(event) {
    event.preventDefault();
    if (evaluandoConfirmacion) return;

    if (!borrador.titulo || !borrador.titulo.trim()) {
        showToast('Agrega un título para la evaluación.', 'error');
        return;
    }
    if (!borrador.productos.length) {
        showToast('Agrega al menos un producto a la evaluación.', 'error');
        return;
    }
    if (borrador.productos.some((p) => !p.producto_id)) {
        showToast('Hay productos sin coincidencia en el catálogo: selecciónalos manualmente antes de confirmar.', 'error');
        return;
    }

    const payload = {
        titulo: borrador.titulo.trim(),
        descripcion_necesidad: borrador.descripcion_necesidad || null,
        entrega_maxima_dias: borrador.entrega_maxima_dias || null,
        prioridad: borrador.prioridad || 'balanceado',
        productos: borrador.productos.map((p) => ({
            producto_id: p.producto_id,
            cantidad: p.cantidad,
            especificaciones: p.especificaciones || null,
        })),
    };

    const firma = JSON.stringify(payload);
    if (firma === firmaUltimaEvaluada) {
        showToast('Esta versión del borrador ya fue evaluada. Modifica algún dato para volver a evaluar.', 'warning');
        return;
    }

    evaluandoConfirmacion = true;
    const btn = document.getElementById('btn-confirmar-evaluar');
    btn.disabled = true;
    btn.textContent = 'Evaluando…';
    let exito = false;

    try {
        const nuevaEvaluacion = await api.evaluaciones.create(payload);
        const resultado = await api.evaluaciones.procesar(nuevaEvaluacion.id);
        resultadoActual = resultado;
        resultadoDesactualizado = false;
        firmaUltimaEvaluada = firma;
        exito = true;
        renderResultado();
        showToast('Evaluación creada y procesada correctamente.', 'success');
        cargarEvaluaciones();
    } catch (err) {
        showToast(err.message, 'error');
    } finally {
        evaluandoConfirmacion = false;
        btn.disabled = exito;
        btn.textContent = exito ? TEXTO_BTN_EVALUADO : TEXTO_BTN_CONFIRMAR;
    }
}

function renderResultado() {
    const container = document.getElementById('resultado-evaluacion-container');
    if (!resultadoActual) {
        container.innerHTML = '';
        return;
    }

    const ranking = resultadoActual.ranking || [];
    const ganador = resultadoActual.proveedor_recomendado;

    container.innerHTML = `
        <div class="card">
            <div class="card-header">
                <div>
                    <h2>Resultado de la evaluación</h2>
                    <div class="card-subtitle">${escapeHtml(resultadoActual.titulo || '')}</div>
                </div>
                ${resultadoDesactualizado ? '<span class="badge badge-warning">Desactualizado — vuelve a confirmar</span>' : ''}
            </div>
            <div class="card-body">
                ${ganador ? `
                    <div class="resultado-ganador">
                        <strong>${escapeHtml(ganador.razon_social || '')}</strong>
                        <span>Puntaje final: ${Number(ganador.puntajes?.final ?? 0).toFixed(1)}/100</span>
                    </div>
                ` : ''}
                <div class="table-wrapper mt-1">
                    <table class="data-table">
                        <thead><tr><th>Proveedor</th><th>Puntaje final</th><th></th></tr></thead>
                        <tbody>
                            ${ranking.map((p) => `
                                <tr>
                                    <td>${escapeHtml(p.razon_social || '')}</td>
                                    <td>${Number(p.puntajes?.final ?? 0).toFixed(1)}</td>
                                    <td>${p.recomendado ? '<span class="badge badge-success">Recomendado</span>' : ''}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
                <p class="mt-1">${escapeHtml(resultadoActual.conclusion_ejecutiva || '')}</p>
                <a class="btn btn-ghost btn-sm" href="evaluacion-detalle.html?id=${resultadoActual.evaluacion_id}">Ver detalle completo</a>
            </div>
        </div>
    `;
    renderIcons(container);
}

/* ---------------- Listado de evaluaciones existentes ------------------------------------- */

function aplicarFiltroEstadoEval() {
    const filtro = document.getElementById('filtro-estado-eval').value;
    const enriquecidas = evaluacionesCache.map((ev) => ({
        ...ev,
        _estadoCalculado: (ev.detalles_resultado || []).length > 0 ? 'procesada' : 'pendiente',
    }));
    const items = filtro ? enriquecidas.filter((ev) => ev._estadoCalculado === filtro) : enriquecidas;
    evaluacionesTable.setItems(items, ['titulo']);
}

async function cargarEvaluaciones() {
    const body = document.getElementById('evaluaciones-body');
    try {
        evaluacionesCache = await api.evaluaciones.list({ limit: 1000 });
        aplicarFiltroEstadoEval();
        renderEvaluacionesTable();
    } catch (err) {
        body.innerHTML = errorRow(5, err.message);
    }
}

function renderEvaluacionesTable() {
    const body = document.getElementById('evaluaciones-body');
    const paginationEl = document.getElementById('evaluaciones-pagination');
    const resultCount = document.getElementById('result-count');
    const view = evaluacionesTable.getView();

    resultCount.textContent = `${view.totalCount} evaluación(es)`;

    if (!view.totalCount) {
        body.innerHTML = emptyRow(5, 'Crea una evaluación con el formulario o el asistente de arriba.', { title: 'Sin evaluaciones', icon: 'evaluations' });
        paginationEl.innerHTML = '';
        return;
    }

    const ordenadas = [...view.items].sort((a, b) => new Date(b.fecha_evaluacion) - new Date(a.fecha_evaluacion));

    body.innerHTML = ordenadas.map((ev) => {
        const procesada = ev._estadoCalculado === 'procesada';
        return `
            <tr>
                <td>
                    <div class="cell-primary">
                        <strong>${escapeHtml(ev.titulo)}</strong>
                        <span>${(ev.productos_solicitados || []).length} producto(s) · máx. ${ev.entrega_maxima_dias || '—'} días</span>
                    </div>
                </td>
                <td><span class="badge badge-neutral">${escapeHtml(ev.prioridad || 'balanceado')}</span></td>
                <td class="cell-muted">${formatDate(ev.fecha_evaluacion)}</td>
                <td>${estadoBadge(procesada ? 'Procesada' : 'Pendiente')}</td>
                <td>
                    <div class="actions-cell" style="justify-content:flex-end;">
                        ${!procesada ? `<button class="btn btn-secondary btn-sm" data-procesar="${ev.id}">Procesar</button>` : ''}
                        <a class="btn btn-ghost btn-sm" href="evaluacion-detalle.html?id=${ev.id}">Ver detalle</a>
                        <button class="btn btn-danger btn-sm" data-eliminar="${ev.id}" data-tooltip="Eliminar" aria-label="Eliminar ${escapeHtml(ev.titulo)}">${icon('trash', { size: 14 })}</button>
                    </div>
                </td>
            </tr>
        `;
    }).join('');

    paginationEl.innerHTML = paginationHTML(view);
    wirePagination(paginationEl, evaluacionesTable, renderEvaluacionesTable);

    body.querySelectorAll('[data-procesar]').forEach((btn) =>
        btn.addEventListener('click', () => procesarEvaluacion(Number(btn.dataset.procesar), btn))
    );
    body.querySelectorAll('[data-eliminar]').forEach((btn) =>
        btn.addEventListener('click', () => eliminarEvaluacion(Number(btn.dataset.eliminar)))
    );
}

async function procesarEvaluacion(id, btn) {
    btn.disabled = true;
    btn.textContent = 'Procesando…';
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
