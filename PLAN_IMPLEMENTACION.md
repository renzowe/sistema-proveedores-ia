# Plan de implementación del sistema inteligente agéntico para la evaluación y selección de proveedores

## 1. Objetivo general

Desarrollar una versión MVP local y funcional del sistema con las tecnologías requeridas: Python + FastAPI + SQLAlchemy + PostgreSQL para el backend, HTML + CSS + JavaScript para el frontend, manteniendo una arquitectura preparada para agentes especializados y futura integración con un LLM. El sistema debe operar sin depender de Docker, Render, Supabase ni APIs externas durante la fase inicial.

## 2. Alcance del MVP

El MVP deberá permitir:

- Registrar proveedores.
- Registrar productos.
- Registrar la relación entre proveedores y productos.
- Registrar historial de desempeño por proveedor y producto.
- Crear evaluaciones con uno o varios productos.
- Buscar proveedores compatibles para una necesidad.
- Evaluar proveedores mediante criterios determinísticos.
- Calcular puntajes y recomendaciones.
- Mostrar resultados y explicación al usuario.
- Mantener el sistema funcional aunque el LLM esté desactivado.

No se incluirán, en esta etapa, usuarios, compras, inventario, ventas, categorías ni cualquier módulo no solicitado dentro del alcance.

---

## Fase 1 — Preparación y estructura del proyecto

### Objetivo
Preparar la base del proyecto, definir la estructura de carpetas y las herramientas necesarias para iniciar el desarrollo local y reproducible.

### Tareas
- Crear la estructura de carpetas indicada por el proyecto.
- Crear archivos iniciales de configuración y documentación.
- Definir la organización de backend, frontend y archivos de configuración.
- Instalar dependencias iniciales: FastAPI, SQLAlchemy, pydantic, psycopg2 o asyncpg según la configuración final, uvicorn, pytest y python-dotenv.
- Crear archivo .env y .env.example con variables de entorno locales.
- Definir la configuración base del proyecto para PostgreSQL local.
- Crear README inicial con instrucciones de ejecución.

### Archivos que se crearán o modificarán
- backend/requirements.txt
- backend/.env
- backend/.env.example
- backend/README.md
- backend/app/__init__.py
- backend/app/main.py
- backend/app/config.py
- backend/app/database.py
- .gitignore
- README.md
- Estructura de carpetas del frontend y backend según el esquema solicitado

### Dependencias
Ninguna previa. Esta fase inicia el proyecto.

### Criterio de terminación
- La estructura del repositorio queda creada exactamente conforme al esquema requerido.
- Las dependencias principales están instaladas.
- La conexión a PostgreSQL local está documentada y lista para configurarse.

---

## Fase 2 — Modelo de datos

### Objetivo
Diseñar y crear la base de datos del MVP con las 8 tablas requeridas y sus relaciones, claves primarias y foráneas.

### Tareas
- Definir cada una de las 8 tablas:
  - proveedores
  - productos
  - proveedor_productos
  - historial_desempeno
  - historial_desempeno_detalle
  - evaluaciones
  - evaluacion_productos
  - evaluacion_detalle
- Definir claves primarias, tipos de datos, índices y relaciones.
- Definir restricciones y validaciones básicas.
- Definir modelos SQLAlchemy en la carpeta backend/app/models.
- Crear las relaciones necesarias entre proveedores, productos, evaluaciones y desempeño.
- Validar integridad referencial.
- Crear la base de datos local en PostgreSQL.
- Ejecutar migración inicial o creación de tablas con SQLAlchemy.

### Archivos que se crearán o modificarán
- backend/app/models/__init__.py
- backend/app/models/proveedor.py
- backend/app/models/producto.py
- backend/app/models/proveedor_producto.py
- backend/app/models/historial_desempeno.py
- backend/app/models/historial_desempeno_detalle.py
- backend/app/models/evaluacion.py
- backend/app/models/evaluacion_producto.py
- backend/app/models/evaluacion_detalle.py
- backend/app/database.py

### Dependencias
- Fase 1 completada.

### Criterio de terminación
- Las 8 tablas existen en PostgreSQL local.
- Todas las claves foráneas y relaciones están funcionando.
- Las restricciones principales están implementadas.
- La estructura es consistente con la lógica del negocio del MVP.

---

## Fase 3 — Schemas y API base

### Objetivo
Establecer la capa de validación y de entrada/salida de la API con Pydantic y preparar los endpoints base.

### Tareas
- Crear los schemas Pydantic para cada modelo.
- Crear schemas de lectura y escritura según sea necesario.
- Configurar FastAPI con los routers principales.
- Definir rutas base y prefijos de API.
- Implementar endpoints CRUD básicos por entidad.
- Validar respuestas JSON y códigos HTTP estándar.
- Probar los endpoints más básicos con Swagger UI y/o requests.

### Archivos que se crearán o modificarán
- backend/app/schemas/__init__.py
- backend/app/schemas/proveedor.py
- backend/app/schemas/producto.py
- backend/app/schemas/proveedor_producto.py
- backend/app/schemas/historial_desempeno.py
- backend/app/schemas/historial_desempeno_detalle.py
- backend/app/schemas/evaluacion.py
- backend/app/schemas/evaluacion_producto.py
- backend/app/schemas/evaluacion_detalle.py
- backend/app/main.py
- backend/app/routers/__init__.py

### Dependencias
- Fase 2 completada.

### Criterio de terminación
- Los schemas están definidos correctamente.
- Los routers base están creados.
- Se puede crear, leer, actualizar y eliminar registros de prueba en la API.
- La documentación interactiva de FastAPI funciona correctamente.

---

## Fase 4 — Gestión de proveedores y productos

### Objetivo
Implementar la gestión funcional de proveedores, productos y la relación proveedor-producto.

### Tareas
- Crear services de proveedor y producto.
- Implementar endpoints CRUD para proveedores.
- Implementar endpoints CRUD para productos.
- Implementar relación proveedor-producto con precio, tiempo de entrega, condiciones y disponibilidad.
- Añadir validaciones para RUC, correo, teléfono y estado.
- Crear datos de prueba mínimos para probar flujo real.

### Archivos que se crearán o modificarán
- backend/app/services/proveedor_service.py
- backend/app/services/producto_service.py
- backend/app/services/proveedor_producto_service.py
- backend/app/routers/proveedores.py
- backend/app/routers/productos.py
- backend/app/routers/proveedor_productos.py
- backend/tests/test_proveedores.py
- backend/tests/test_productos.py

### Dependencias
- Fase 3 completada.

### Criterio de terminación
- Se pueden registrar proveedores y productos.
- Se puede vincular un producto a varios proveedores y viceversa.
- Los precios y tiempos de entrega por proveedor se gestionan correctamente.
- La capa de servicios está separada de los routers.

---

## Fase 5 — Historial de desempeño

### Objetivo
Registrar experiencias históricas de rendimiento de proveedores y permitir comparación por proveedor y por producto.

### Tareas
- Crear el servicio y router de historial de desempeño.
- Permitir registrar una experiencia histórica con varios productos al mismo tiempo.
- Crear registros en historial_desempeno y historial_desempeno_detalle.
- Definir indicadores reales que se puedan consultar: cumplimiento, entregas, defectos, demora, servicio y comportamiento general.
- Implementar consultas por proveedor y por producto.
- Crear datos de prueba de historial.

### Archivos que se crearán o modificararán
- backend/app/models/historial_desempeno.py
- backend/app/models/historial_desempeno_detalle.py
- backend/app/services/historial_service.py
- backend/app/routers/historial_desempeno.py
- backend/tests/test_historial_desempeno.py (si se requiere un archivo adicional)

### Dependencias
- Fase 4 completada.

### Criterio de terminación
- Se puede crear un historial de desempeño con múltiples productos.
- El detalle del historial mantiene relación con la experiencia principal.
- Se pueden consultar datos históricos por proveedor y producto.
- Los indicadores del historial están listos para alimentarse al motor de evaluación.

---

## Fase 6 — Sistema de evaluaciones

### Objetivo
Crear el flujo de evaluación de necesidades, permitiendo seleccionar productos, cantidades y condiciones.

### Tareas
- Crear el modelo y schema de evaluaciones.
- Crear el modelo y schema de evaluacion_productos.
- Permitir una evaluación con múltiples productos.
- Incluir campos para cantidad, prioridad, entrega máxima y condiciones generales.
- Implementar búsqueda de proveedores compatibles por producto.
- Definir cómo se comparan proveedores en una evaluación.
- Crear endpoint para iniciar evaluación y guardar la información base.

### Archivos que se crearán o modificarán
- backend/app/models/evaluacion.py
- backend/app/models/evaluacion_producto.py
- backend/app/schemas/evaluacion.py
- backend/app/schemas/evaluacion_producto.py
- backend/app/services/evaluacion_service.py
- backend/app/routers/evaluaciones.py
- backend/tests/test_evaluaciones.py

### Dependencias
- Fase 5 completada.

### Criterio de terminación
- Se puede crear una evaluación con varios productos.
- Cada producto dentro de la evaluación tiene cantidad y condiciones.
- El sistema puede identificar proveedores que ofrecen los productos solicitados.
- La evaluación queda guardada y está lista para ser analizada por el motor.

---

## Fase 7 — Motor de evaluación

### Objetivo
Implementar el cálculo determinístico de puntajes de proveedores para cada evaluación y cada producto.

### Tareas
- Definir criterios de evaluación: precio, calidad, entrega/logística, historial, riesgo y puntaje final.
- Crear utilidades de normalización de valores.
- Definir ponderaciones por criterio.
- Implementar lógica para calcular puntajes y recomendaciones.
- Crear modelo de detalle de evaluación para guardar resultados por proveedor.
- Generar explicaciones básicas basadas en los valores calculados.
- Guardar puntajes finales por proveedor en evaluacion_detalle.
- Mantener el cálculo en Python, sin depender del LLM.

### Archivos que se crearán o modificarán
- backend/app/models/evaluacion_detalle.py
- backend/app/schemas/evaluacion_detalle.py
- backend/app/utils/calculos.py
- backend/app/utils/validaciones.py
- backend/app/services/evaluacion_service.py
- backend/app/agents/orquestador.py
- backend/app/agents/decisor.py

### Dependencias
- Fases 4, 5 y 6 completadas.

### Criterio de terminación
- Una evaluación produce puntajes por proveedor.
- El algoritmo es determinístico y reproducible.
- Se guarda un resultado detallado por criterio y puntaje final.
- El sistema puede recomendar un proveedor con base en evidencia calculada.

---

## Fase 8 — Arquitectura de agentes

### Objetivo
Construir la arquitectura de agentes especializados para descomponer la evaluación por dominio sin depender obligatoriamente de un LLM.

### Tareas
- Implementar agente financiero.
- Implementar agente de calidad.
- Implementar agente logístico.
- Implementar agente de riesgo.
- Implementar agente decisor.
- Implementar orquestador que coordine el flujo.
- Definir contratos entre agentes y resultados.
- Integrar los resultados de los agentes con el motor de evaluación.
- Mantener la lógica ejecutable sin LLM.

### Archivos que se crearán o modificarán
- backend/app/agents/__init__.py
- backend/app/agents/orquestador.py
- backend/app/agents/financiero.py
- backend/app/agents/calidad.py
- backend/app/agents/logistico.py
- backend/app/agents/riesgo.py
- backend/app/agents/decisor.py

### Dependencias
- Fase 7 completada.

### Criterio de terminación
- Los agentes ejecutan una evaluación por dominios específicos.
- El orquestador integra los resultados.
- El decisor produce una recomendación final basada en los criterios.
- El sistema funciona sin API de LLM.

---

## Fase 9 — Frontend

### Objetivo
Construir la interfaz de usuario del sistema con las vistas principales del MVP.

### Tareas
- Crear dashboard principal.
- Crear vista de proveedores.
- Crear vista de productos.
- Crear vista de historial de desempeño.
- Crear vista de evaluaciones.
- Crear vista de detalle de evaluación.
- Crear formulario para crear evaluaciones con múltiples productos.
- Añadir panel de asistente IA visual, pero desactivado inicialmente.
- Diseñar estilos CSS y componentes reutilizables.

### Archivos que se crearán o modificarán
- frontend/index.html
- frontend/pages/dashboard.html
- frontend/pages/proveedores.html
- frontend/pages/productos.html
- frontend/pages/desempeno.html
- frontend/pages/evaluaciones.html
- frontend/pages/evaluacion-detalle.html
- frontend/css/styles.css
- frontend/css/dashboard.css
- frontend/css/formularios.css
- frontend/css/evaluaciones.css
- frontend/js/api.js
- frontend/js/dashboard.js
- frontend/js/proveedores.js
- frontend/js/productos.js
- frontend/js/desempeno.js
- frontend/js/evaluaciones.js
- frontend/js/components/navbar.js
- frontend/js/components/sidebar.js
- frontend/js/components/modal.js
- frontend/js/components/chat.js

### Dependencias
- Fases 1 a 8 completadas.

### Criterio de terminación
- El frontend tiene las pantallas principales del MVP.
- La navegación entre vistas funciona.
- El formulario de evaluación permite múltiples productos y condiciones.
- El panel de IA está presente visualmente, pero deshabilitado sin romper el flujo principal.

---

## Fase 10 — Integración frontend-backend

### Objetivo
Conectar la capa de frontend con la API REST de FastAPI y permitir el flujo completo del sistema.

### Tareas
- Implementar consumo de endpoints del backend desde JavaScript.
- Manejar errores HTTP y respuestas vacías.
- Crear funciones reutilizables para fetch y manejo de errores.
- Conectar proveedores, productos, historial y evaluaciones con el frontend.
- Mostrar resultados en tablas y formularios.
- Verificar flujo completo desde la pantalla de evaluación hasta la recomendación.

### Archivos que se crearán o modificarán
- frontend/js/api.js
- frontend/js/proveedores.js
- frontend/js/productos.js
- frontend/js/desempeno.js
- frontend/js/evaluaciones.js
- frontend/pages/*.html

### Dependencias
- Fase 9 completada.

### Criterio de terminación
- El frontend puede crear y listar proveedores, productos y evaluaciones.
- La evaluación puede enviarse al backend.
- Los resultados de puntuación y recomendación se muestran en la interfaz.
- El flujo end-to-end funciona sin errores básicos.

---

## Fase 11 — Preparación de inteligencia artificial

### Objetivo
Preparar la arquitectura para la futura integración con Claude mediante la API de Anthropic, sin afectar el funcionamiento del MVP determinístico.

Esta fase no requiere disponer todavía de una API Key activa ni de una suscripción de pago. El objetivo es dejar preparada la estructura de código, configuración, prompts y contratos necesarios para que la integración real con Claude pueda habilitarse posteriormente.

### Tareas
- Crear la estructura de la carpeta ai.
- Crear llm_client.py con una interfaz preparada para comunicarse con la API de Anthropic.
- Mantener la configuración de Claude separada de la lógica principal del sistema.
- Crear parser_solicitud.py para transformar solicitudes expresadas en lenguaje natural en una estructura de datos utilizable por el sistema.
- Definir prompts base para los agentes financiero, calidad, logístico, riesgo y decisor.
- Añadir variables de entorno para activar o desactivar la integración con Claude.
- Añadir variables de entorno para configurar la API Key, modelo y parámetros necesarios de Claude.
- Definir contratos claros de entrada y salida para las interacciones con Claude.
- Garantizar que el sistema pueda funcionar completamente con el LLM desactivado.
- Evitar que la ausencia de una API Key o de acceso a Claude impida ejecutar el MVP.
- Mantener el motor determinístico y los agentes actuales como base funcional del sistema

### Archivos que se crearán o modificarán
- backend/app/ai/__init__.py
- backend/app/ai/llm_client.py
- backend/app/ai/parser_solicitud.py
- backend/app/ai/prompts/financiero.txt
- backend/app/ai/prompts/calidad.txt
- backend/app/ai/prompts/logistico.txt
- backend/app/ai/prompts/riesgo.txt
- backend/app/ai/prompts/decisor.txt
- backend/app/config.py
- backend/.env
- backend/.env.examplE
### Configuración prevista

La integración con Claude deberá utilizar variables de entorno para evitar almacenar credenciales directamente en el código fuente.

Ejemplo conceptual:

LLM_ENABLED=false
ANTHROPIC_API_KEY=
CLAUDE_MODEL=

La API Key deberá permanecer únicamente en el archivo .env local y nunca deberá incluirse en el repositorio.

### Dependencias
- Fase 10 completada.

### Criterio de terminación
- La arquitectura para integrar Claude está preparada pero desactivada por defecto.
- Existe una estructura clara para configurar posteriormente la API de Anthropic.
- Existen contratos de entrada y salida para las interacciones con Claude.
- Los prompts base de los agentes están definidos.
- El flujo principal del MVP no depende de Claude.
- El sistema funciona correctamente sin disponer de una API Key.
- La ausencia o indisponibilidad de Claude no impide ejecutar el sistema determinístico

---

## Fase 12 — Integración del LLM

### Objetivo
Integrar Claude mediante la API de Anthropic cuando exista acceso real a las credenciales, manteniendo el motor determinístico como fuente principal de cálculo y decisión.

Claude será utilizado como componente de inteligencia de lenguaje para interpretar solicitudes en lenguaje natural y generar explicaciones de los resultados obtenidos por el sistema.

### Tareas
- Definir cuándo y cómo se activa la integración con Claude.
- Configurar la API Key de Anthropic mediante variables de entorno.
- Configurar el modelo Claude seleccionado.
- Implementar la comunicación entre llm_client.py y la API de Anthropic.
- Implementar la interpretación de solicitudes expresadas en lenguaje natural.
- Convertir las solicitudes interpretadas por Claude en parámetros estructurados de evaluación.
- Integrar Claude para generar explicaciones de los resultados obtenidos.
- Proporcionar a Claude únicamente la información necesaria obtenida desde el backend y PostgreSQL.
- Asegurar que Claude no invente proveedores, productos, precios, métricas, puntajes ni resultados que no existan en el sistema.
- Mantener PostgreSQL y el backend como fuente de verdad de los datos.
- Mantener el motor determinístico como responsable del cálculo de puntajes y la recomendación principal.
- Evitar que Claude modifique directamente los resultados calculados por el motor determinístico.
- Manejar errores de conexión, credenciales inválidas, límites de API o indisponibilidad de Claude.
- Permitir desactivar Claude y continuar utilizando el sistema en modo determinístico.

### Archivos que se crearán o modificarán
- backend/app/ai/llm_client.py
- backend/app/ai/parser_solicitud.py
- backend/app/services/evaluacion_service.py
- backend/app/agents/orquestador.py
- backend/app/config.py

### Dependencias
- Fase 11 completada.
- Disponibilidad real de credenciales o API del proveedor LLM.
- Acceso al modelo Claude seleccionado.

### Criterio de terminación
- Claude puede interpretar una solicitud expresada en lenguaje natural y transformarla en una estructura útil para el sistema.
- Claude puede generar explicaciones utilizando datos reales obtenidos desde el backend.
- Claude no inventa información sobre proveedores, productos, precios, métricas o resultados.
- El motor determinístico continúa siendo responsable del cálculo de puntajes y de la recomendación principal.
- Las credenciales de Anthropic se gestionan mediante variables de entorno.
- Claude puede ser activado o desactivado mediante configuración.
- El sistema continúa funcionando en modo determinístico cuando Claude está desactivado o no disponible.
- La integración con Claude está aislada en la capa ai y no altera innecesariamente la arquitectura principal del sistema.

---

## Fase 13 — Pruebas y cierre del MVP

### Objetivo
Validar que el MVP cumple con el flujo funcional completo y está listo para uso local.

### Tareas
- Probar CRUD de proveedores.
- Probar CRUD de productos.
- Probar relación proveedor-producto.
- Probar historial por proveedor y por producto.
- Probar creación de evaluaciones con un producto y varios productos.
- Probar búsqueda de proveedores compatibles.
- Probar cálculo de puntajes y recomendaciones.
- Probar agentes especializados.
- Probar disponibilidad y resultado de la API REST.
- Probar flujo completo frontend → backend → PostgreSQL.
- Corregir errores y ajustar validaciones.
- Verificar que el sistema funciona sin LLM.

### Archivos que se crearán o modificarán
- backend/tests/test_proveedores.py
- backend/tests/test_productos.py
- backend/tests/test_evaluaciones.py
- backend/tests/test_historial_desempeno.py (si aplica)
- backend/app/
- frontend/js/
- README.md


### Dependencias
- Fases 1 a 11 completadas.
- La Fase 12 es opcional para el cierre del MVP
  y se realizará cuando exista acceso a una API de LLM

### Criterio de terminación
- El flujo completo puede ejecutarse localmente.
- La evaluación y recomendación del proveedor funcionan correctamente.
- El sistema cumple con los objetivos del MVP definidos en este documento.
- La documentación del proyecto describe la ejecución local de manera clara.

---

## Definición del MVP terminado

El MVP se considerará terminado cuando el sistema pueda realizar correctamente este flujo:

1. El usuario registra proveedores.
2. El usuario registra productos.
3. El usuario registra qué productos ofrece cada proveedor.
4. El usuario registra historial de desempeño.
5. El usuario crea una evaluación.
6. El usuario selecciona uno o varios productos.
7. El usuario indica cantidades y condiciones.
8. El sistema busca proveedores compatibles.
9. El motor de evaluación analiza los proveedores.
10. Los agentes procesan los distintos criterios.
11. El sistema calcula puntajes.
12. El sistema genera una recomendación.
13. El sistema presenta la explicación.

Esto debe ocurrir de forma local, sin Docker, sin Supabase, sin Render y sin LLM de pago.

---

## Estado del proyecto

- [x] Documento de planificación inicial creado.
- [x] Fase 1 — Preparación y estructura del proyecto
- [x] Fase 2 — Modelo de datos
- [x] Fase 3 — Schemas y API base
- [x] Fase 4 — Gestión de proveedores y productos
- [x] Fase 5 — Historial de desempeño
- [x] Fase 6 — Sistema de evaluaciones
- [x] Fase 7 — Motor de evaluación
- [x] Fase 8 — Arquitectura de agentes
- [x] Fase 9 — Frontend
- [x] Fase 10 — Integración frontend-backend
- [x] Fase 11 — Preparación de inteligencia artificial
- [ ] Fase 12 — Integración del LLM (pendiente: requiere API Key real de Anthropic)
- [x] Fase 13 — Pruebas y cierre del MVP

> Este documento sirve como hoja de ruta principal para el desarrollo posterior. No se debe avanzar a una fase posterior si una dependencia fundamental de la fase anterior no está correctamente implementada.
