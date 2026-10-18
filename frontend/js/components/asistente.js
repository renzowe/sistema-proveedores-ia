/* ============================================================
   Componente: Asistente conversacional (Claude, vía API de Anthropic)
   Compartido entre evaluaciones.js (modo 'borrador') y
   evaluacion-detalle.js (modo 'explicacion').

   El panel se pinta de inmediato y nunca espera al backend: el estado del
   LLM (real / demostración) y cualquier error de conexión se muestran
   después, dentro del propio panel.
   ============================================================ */

// Deben ser ≤ que los topes del backend (app/schemas/asistente.py): el chat
// solo reenvía los últimos mensajes y cada mensaje tiene longitud máxima.
const ASISTENTE_MAX_MENSAJES_ENVIADOS = 20;
const ASISTENTE_MAX_CARACTERES_MENSAJE = 2000;

// El código de acceso dura lo que la pestaña (sessionStorage): sirve en todas
// las páginas mientras esté abierta y se olvida al cerrarla.
const CLAVE_CODIGO_ASISTENTE = 'asistenteCodigoAcceso';

function leerCodigoAsistente() {
    try {
        return sessionStorage.getItem(CLAVE_CODIGO_ASISTENTE) || '';
    } catch {
        return '';
    }
}

function guardarCodigoAsistente(codigo) {
    try {
        if (codigo) sessionStorage.setItem(CLAVE_CODIGO_ASISTENTE, codigo);
        else sessionStorage.removeItem(CLAVE_CODIGO_ASISTENTE);
    } catch {
        // Sin almacenamiento disponible: el código solo dura en esta página.
    }
}

function esEntornoDesarrollo() {
    return (typeof isLocalHost !== 'undefined' && isLocalHost) || window.location.search.includes('debug=1');
}

// Claude puede devolver **negritas** aunque se le pida texto plano: se
// muestran como negrita en vez de asteriscos. El texto se escapa antes de
// sustituir, así que no puede inyectarse HTML.
function formatearRespuestaAsistente(texto) {
    return escapeHtml(texto).replace(/\*\*([^*\n]+)\*\*/g, '<strong>$1</strong>');
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
    let reenfocarTrasEnvio = false;

    // Código de acceso (solo si el backend define ASISTENTE_CODIGO_ACCESO).
    let codigoAcceso = leerCodigoAsistente();
    let requiereCodigo = false;
    let formCodigoAbierto = false;
    let enfocarCodigo = false;
    let validandoCodigo = false;
    let errorCodigo = null;

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

    function accionesCabeceraHTML() {
        let botones = '';
        if (requiereCodigo && estadoLLM === 'demostracion' && !formCodigoAbierto) {
            botones = '<button type="button" class="btn btn-secondary btn-sm" data-accion="abrir-codigo">Usar Claude</button>';
        } else if (requiereCodigo && estadoLLM === 'real') {
            botones = '<button type="button" class="btn btn-ghost btn-sm" data-accion="salir-codigo" title="Olvidar el código en este navegador">Salir</button>';
        }
        return `<div class="chat-cabecera-acciones">${badgeEstadoHTML()}${botones}</div>`;
    }

    function formCodigoHTML(valorPrevio) {
        if (!formCodigoAbierto) return '';
        return `
            <form class="chat-codigo" id="${contenedorId}-codigo-form">
                <label for="${contenedorId}-codigo">Código de acceso para usar Claude</label>
                <div class="chat-codigo-fila">
                    <input type="password" id="${contenedorId}-codigo" autocomplete="off" maxlength="200"
                        value="${escapeHtml(valorPrevio)}" ${validandoCodigo ? 'disabled' : ''}>
                    <button type="submit" class="btn btn-primary btn-sm" ${validandoCodigo ? 'disabled' : ''}>${validandoCodigo ? 'Comprobando…' : 'Entrar'}</button>
                    <button type="button" class="btn btn-ghost btn-sm" data-accion="cancelar-codigo">Cancelar</button>
                </div>
                ${errorCodigo ? `<div class="chat-codigo-error" role="alert">${escapeHtml(errorCodigo)}</div>` : ''}
            </form>
        `;
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
            const motivo = requiereCodigo
                ? 'El asistente con IA real requiere un código de acceso (botón "Usar Claude"). Mientras tanto, las respuestas se generan con reglas simples, sin IA real.'
                : 'No hay una API Key de Anthropic configurada: las respuestas se generan con reglas simples, sin IA real.';
            return `<div class="chat-aviso">${renderAlert({
                type: 'warning',
                title: 'Modo demostración',
                body: `${motivo} Los puntajes siempre los calcula el motor determinístico.`,
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
                <div class="chat-burbuja-texto">${esUsuario ? escapeHtml(m.contenido) : formatearRespuestaAsistente(m.contenido)}</div>
            </div>
        `;
    }

    function render() {
        const textareaPrevio = document.getElementById(`${contenedorId}-input`);
        const borradorTexto = textareaPrevio ? textareaPrevio.value : '';
        const teniaFoco = Boolean(textareaPrevio) && document.activeElement === textareaPrevio;
        const codigoPrevio = document.getElementById(`${contenedorId}-codigo`)?.value || '';
        const inputDeshabilitado = enviando || (modo === 'explicacion' && !evaluacionId);

        contenedor.innerHTML = `
            <div class="card asistente-panel">
                <div class="card-header">
                    <div>
                        <h2>${icon('sparkles', { size: 16 })} Asistente conversacional</h2>
                        ${contextoLabel ? `<div class="card-subtitle chat-contexto-chip">${escapeHtml(contextoLabel)}</div>` : ''}
                    </div>
                    ${accionesCabeceraHTML()}
                </div>
                ${formCodigoHTML(codigoPrevio)}
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
                        maxlength="${ASISTENTE_MAX_CARACTERES_MENSAJE}"
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
        if ((teniaFoco || reenfocarTrasEnvio) && !textarea.disabled) {
            reenfocarTrasEnvio = false;
            textarea.focus();
            textarea.setSelectionRange(textarea.value.length, textarea.value.length);
        }

        contenedor.querySelector('[data-accion="abrir-codigo"]')?.addEventListener('click', () => {
            formCodigoAbierto = true;
            enfocarCodigo = true;
            errorCodigo = null;
            render();
        });
        contenedor.querySelector('[data-accion="cancelar-codigo"]')?.addEventListener('click', () => {
            formCodigoAbierto = false;
            errorCodigo = null;
            render();
        });
        contenedor.querySelector('[data-accion="salir-codigo"]')?.addEventListener('click', () => {
            codigoAcceso = '';
            guardarCodigoAsistente('');
            consultarEstado();
        });
        const formCodigo = document.getElementById(`${contenedorId}-codigo-form`);
        if (formCodigo) {
            const inputCodigo = document.getElementById(`${contenedorId}-codigo`);
            formCodigo.addEventListener('submit', (e) => {
                e.preventDefault();
                validarCodigo(inputCodigo.value.trim());
            });
            if (enfocarCodigo && !inputCodigo.disabled) {
                enfocarCodigo = false;
                inputCodigo.focus();
            }
        }
    }

    function aplicarEstado(data) {
        requiereCodigo = Boolean(data.requiere_codigo);
        estadoLLM = data.modo === 'real' ? 'real' : 'demostracion';
        modeloLLM = data.modelo || null;
        errorConexion = null;
    }

    async function consultarEstado() {
        try {
            const data = await api.evaluaciones.asistenteEstado(codigoAcceso);
            if (data.codigo_valido === false) {
                // El código guardado ya no sirve (p. ej. se cambió en el servidor).
                codigoAcceso = '';
                guardarCodigoAsistente('');
                formCodigoAbierto = true;
                errorCodigo = 'El código guardado ya no es válido. Introdúcelo de nuevo.';
            }
            aplicarEstado(data);
        } catch (err) {
            estadoLLM = 'sin-conexion';
            errorConexion = err.message;
        }
        render();
    }

    async function validarCodigo(codigo) {
        if (!codigo) {
            errorCodigo = 'Escribe el código de acceso.';
            enfocarCodigo = true;
            render();
            return;
        }
        validandoCodigo = true;
        errorCodigo = null;
        render();
        try {
            const data = await api.evaluaciones.asistenteEstado(codigo);
            if (data.codigo_valido) {
                codigoAcceso = codigo;
                guardarCodigoAsistente(codigo);
                formCodigoAbierto = false;
                reenfocarTrasEnvio = true;
                aplicarEstado(data);
            } else {
                errorCodigo = 'Código incorrecto.';
                enfocarCodigo = true;
            }
        } catch (err) {
            errorCodigo = err.message;
        } finally {
            validandoCodigo = false;
            render();
        }
    }

    async function enviarMensaje(texto) {
        if (!texto || !texto.trim() || enviando) return;
        mensajes.push({ rol: 'usuario', contenido: texto.trim() });
        enviando = true;
        render();

        const payload = {
            mensajes: mensajes
                .filter((m) => !m.esError)
                .slice(-ASISTENTE_MAX_MENSAJES_ENVIADOS)
                .map((m) => ({ rol: m.rol, contenido: m.contenido })),
            borrador: modo === 'borrador' ? obtenerBorrador() : { productos: [] },
        };
        if (modo === 'explicacion' && evaluacionId) {
            payload.evaluacion_id = evaluacionId;
        }

        try {
            const data = await api.evaluaciones.asistenteMensaje(payload, codigoAcceso);
            mensajes.push({ rol: 'asistente', contenido: data.respuesta, modo: data.modo });
            ultimoDebug = { payload, respuesta: data };
            if (requiereCodigo && estadoLLM === 'real' && data.modo === 'demostracion') {
                consultarEstado(); // el código pudo cambiar en el servidor
            }
            if (estadoLLM === 'sin-conexion' || estadoLLM === 'comprobando') {
                estadoLLM = data.modo === 'real' ? 'real' : 'demostracion';
            }
            if (modo === 'borrador') {
                aplicarBorrador(data.borrador, data.campos_actualizados, data.listo_para_confirmar);
            }
        } catch (err) {
            mensajes.push({ rol: 'asistente', contenido: err.message, esError: true });
        } finally {
            enviando = false;
            reenfocarTrasEnvio = true;
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
