/* ============================================================
   Componente: Asistente conversacional (Claude, vía API de Anthropic)
   Compartido entre evaluaciones.js (modo 'borrador') y
   evaluacion-detalle.js (modo 'explicacion').

   El panel se pinta de inmediato y nunca espera al backend: el estado del
   LLM (real / demostración) y cualquier error de conexión se muestran
   después, dentro del propio panel.
   ============================================================ */

function esEntornoDesarrollo() {
    return (typeof isLocalHost !== 'undefined' && isLocalHost) || window.location.search.includes('debug=1');
}

function initAsistente({
    modo,                               // 'borrador' | 'explicacion'
    contenedorId,
    evaluacionId = null,
    contextoLabel = '',
    obtenerBorrador = () => ({ productos: [] }),
    aplicarBorrador = () => {},
}) {
    const contenedor = document.getElementById(contenedorId);
    if (!contenedor) {
        console.error(`initAsistente: no existe el contenedor #${contenedorId}`);
        return null;
    }

    const mensajes = [];
    let enviando = false;
    let estadoLLM = 'comprobando'; // 'comprobando' | 'demostracion' | 'real' | 'sin-conexion'
    let modeloLLM = null;
    let errorConexion = null;
    let ultimoDebug = null; // { payload, respuesta } del último turno — solo para el panel de desarrollo

    function textoBienvenida() {
        if (modo === 'explicacion' && !evaluacionId) {
            return 'Elige una evaluación para que pueda explicarte su resultado.';
        }
        if (modo === 'explicacion') {
            return 'Hola. Puedo explicarte el resultado de esta evaluación: por qué se recomendó un proveedor o qué significan los puntajes. Solo uso los datos ya calculados por el motor de decisión.';
        }
        return 'Hola. Cuéntame qué necesitas evaluar (productos, cantidades, plazo de entrega y prioridad) y voy completando el formulario contigo. No se crea ninguna evaluación hasta que pulses "Confirmar y evaluar".';
    }

    function badgeEstadoHTML() {
        if (estadoLLM === 'real') {
            return `<span class="badge badge-ai">Claude${modeloLLM ? ` · ${escapeHtml(modeloLLM)}` : ''}</span>`;
        }
        if (estadoLLM === 'demostracion') {
            return '<span class="badge badge-warning">Modo demostración</span>';
        }
        if (estadoLLM === 'sin-conexion') {
            return '<span class="badge badge-danger">Sin conexión</span>';
        }
        return '<span class="badge badge-neutral">Comprobando…</span>';
    }

    function avisoHTML() {
        if (estadoLLM === 'sin-conexion') {
            return `<div class="chat-aviso">${renderAlert({
                type: 'danger',
                title: 'No se pudo conectar con el backend',
                body: `${escapeHtml(errorConexion || '')} El chat no podrá responder hasta que el servidor esté disponible (${escapeHtml(API_BASE_URL)}). El formulario sigue disponible.`,
            })}</div>`;
        }
        if (estadoLLM === 'demostracion') {
            return `<div class="chat-aviso">${renderAlert({
                type: 'warning',
                title: 'Modo demostración',
                body: 'No hay una API Key de Anthropic configurada: las respuestas se generan con reglas simples, sin IA real. Los puntajes siempre los calcula el motor determinístico.',
            })}</div>`;
        }
        return '';
    }

    function burbujaHTML(m) {
        const esUsuario = m.rol === 'usuario';
        const badgeModo = (!esUsuario && m.modo === 'demostracion')
            ? '<span class="badge badge-warning chat-burbuja-badge">Modo demostración</span>'
            : '';
        return `
            <div class="chat-burbuja ${esUsuario ? 'usuario' : 'asistente'} ${m.esError ? 'error' : ''}">
                ${badgeModo}
                <div class="chat-burbuja-texto">${escapeHtml(m.contenido)}</div>
            </div>
        `;
    }

    function render() {
        const textareaPrevio = document.getElementById(`${contenedorId}-input`);
        const borradorTexto = textareaPrevio ? textareaPrevio.value : '';
        const inputDeshabilitado = enviando || (modo === 'explicacion' && !evaluacionId);

        contenedor.innerHTML = `
            <div class="card asistente-panel">
                <div class="card-header">
                    <div>
                        <h2>${icon('sparkles', { size: 16 })} Asistente conversacional</h2>
                        ${contextoLabel ? `<div class="card-subtitle chat-contexto-chip">${escapeHtml(contextoLabel)}</div>` : ''}
                    </div>
                    ${badgeEstadoHTML()}
                </div>
                ${avisoHTML()}
                <div class="chat-mensajes" id="${contenedorId}-mensajes">
                    <div class="chat-burbuja asistente bienvenida">
                        <div class="chat-burbuja-texto">${escapeHtml(textoBienvenida())}</div>
                    </div>
                    ${mensajes.map(burbujaHTML).join('')}
                    ${enviando ? '<div class="loading-state chat-loading"><div class="spinner"></div><span>Pensando…</span></div>' : ''}
                </div>
                <form class="chat-entrada" id="${contenedorId}-form">
                    <textarea id="${contenedorId}-input" rows="2" placeholder="Escribe tu mensaje…" aria-label="Mensaje para el asistente"
                        ${inputDeshabilitado ? 'disabled' : ''}>${escapeHtml(borradorTexto)}</textarea>
                    <button type="submit" class="btn btn-primary btn-sm" ${inputDeshabilitado ? 'disabled' : ''}>Enviar</button>
                </form>
                ${esEntornoDesarrollo() && ultimoDebug ? `
                    <details class="chat-debug-panel">
                        <summary>JSON de depuración (solo desarrollo)</summary>
                        <pre>${escapeHtml(JSON.stringify(ultimoDebug, null, 2))}</pre>
                    </details>
                ` : ''}
            </div>
        `;
        renderIcons(contenedor);

        const panelMensajes = document.getElementById(`${contenedorId}-mensajes`);
        panelMensajes.scrollTop = panelMensajes.scrollHeight;

        const form = document.getElementById(`${contenedorId}-form`);
        const textarea = document.getElementById(`${contenedorId}-input`);
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            const texto = textarea.value;
            textarea.value = '';
            enviarMensaje(texto);
        });
        textarea.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                form.requestSubmit();
            }
        });
    }

    async function consultarEstado() {
        try {
            const data = await api.evaluaciones.asistenteEstado();
            estadoLLM = data.modo === 'real' ? 'real' : 'demostracion';
            modeloLLM = data.modelo || null;
            errorConexion = null;
        } catch (err) {
            estadoLLM = 'sin-conexion';
            errorConexion = err.message;
        }
        render();
    }

    async function enviarMensaje(texto) {
        if (!texto || !texto.trim() || enviando) return;
        mensajes.push({ rol: 'usuario', contenido: texto.trim() });
        enviando = true;
        render();

        const payload = {
            mensajes: mensajes.filter((m) => !m.esError).map((m) => ({ rol: m.rol, contenido: m.contenido })),
            borrador: modo === 'borrador' ? obtenerBorrador() : { productos: [] },
        };
        if (modo === 'explicacion' && evaluacionId) {
            payload.evaluacion_id = evaluacionId;
        }

        try {
            const data = await api.evaluaciones.asistenteMensaje(payload);
            mensajes.push({ rol: 'asistente', contenido: data.respuesta, modo: data.modo });
            ultimoDebug = { payload, respuesta: data };
            if (estadoLLM === 'sin-conexion' || estadoLLM === 'comprobando') {
                estadoLLM = data.modo === 'real' ? 'real' : 'demostracion';
            }
            if (modo === 'borrador') {
                aplicarBorrador(data.borrador, data.campos_actualizados, data.listo_para_confirmar);
            }
        } catch (err) {
            mensajes.push({ rol: 'asistente', contenido: `No se pudo contactar al asistente: ${err.message}`, esError: true });
        } finally {
            enviando = false;
            render();
        }
    }

    render();
    consultarEstado();

    return {
        setContexto(nuevoContextoLabel) {
            contextoLabel = nuevoContextoLabel || '';
            render();
        },
        reiniciar(nuevoEvaluacionId, nuevoContextoLabel) {
            evaluacionId = nuevoEvaluacionId;
            contextoLabel = nuevoContextoLabel || '';
            mensajes.length = 0;
            render();
        },
    };
}
