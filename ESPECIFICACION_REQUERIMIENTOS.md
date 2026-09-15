# Especificacion de Requerimientos de Negocio y Reglas Operativas
## Proyecto: Asistente Virtual para Licitaciones (Mercado Publico)
### Programa de Vinculacion con el Medio (VcM) DUOC UC - Hotel Plaza San Francisco

---

## 1. Introduccion y Diagnostico del Problema

### 1.1. Contexto General
El presente documento consolida los requerimientos funcionales, reglas de negocio y restricciones operativas para el desarrollo de un Asistente Virtual de prospeccion comercial en Mercado Publico, desarrollado en conjunto por DUOC UC y el Hotel Plaza San Francisco.

El objetivo central es automatizar la prospeccion reactiva, reduciendo el trabajo manual del equipo comercial y de eventos para asegurar la deteccion oportuna de oportunidades de negocio estatal.

### 1.2. Diagnostico Operativo y Fricciones Criticas
El flujo manual previo evidencio los siguientes problemas operativos:
* **Ineficiencia Semantica y Dispersion de Rubros:** Mercado Publico carece de filtrado semantico preciso. Se pierden licitaciones por variaciones de vocabulario (por ejemplo, "hospedaje" frente a "alojamiento").
* **Alto Costo Comercial por Revision Manual:** El equipo de eventos gasta entre 1 y 2 horas diarias revisando hasta 10 paginas de resultados de forma manual. Esta demora permite que competidores bloqueen disponibilidad o ingresen propuestas antes de que el hotel detecte la oportunidad.
* **Inconsistencia de Datos ("Efecto ID"):** Las vistas resumidas de Mercado Publico presentan con frecuencia IDs de licitacion inexistentes, desactualizados o no coincidentes con los adjuntos reales, derivando en busquedas infructuosas.
* **Barreras de Autenticacion:** Procesos de ingreso via Clave Unica y verificaciones por correo ralentizan la rutina comercial diaria.

---

## 2. Requerimientos Funcionales y Reglas de Negocio

### 2.1. Matriz de Palabras Clave Obligatorias y Segmentacion
El motor de busqueda debera filtrar con procesamiento de lenguaje natural (NLP) considerando intencion de compra en dos categorias principales:

| Categoria | Palabras Clave Obligatorias | Contexto de Negocio |
| :--- | :--- | :--- |
| Alojamiento | Hospedaje, Alojamiento, Habitaciones | Delegaciones, pernoctacion corporativa y reservas de estadia. |
| Eventos / Catering | Eventos, Catering, Centro de Eventos, Salones | Servicios de alimentacion, coffee breaks, salones de conferencias y reuniones. |

### 2.2. Filtro de Geolocalizacion
* Prioridad estricta y filtrado primario para la **Region Metropolitana** (con enfasis central en la comuna de Santiago y radio urbano relevante para el hotel).

### 2.3. Modalidad Compra Agil
* El sistema debe identificar, priorizar y generar alertas inmediatas para procesos de **Compra Agil**.
* Debe ajustarse al umbral normativo vigente de hasta **6.900.000 CLP** (actualizado respecto al limite anterior de 1.900.000 CLP).

### 2.4. Validacion Robusta de ID y Existencia Real
* **Regla estricta:** El asistente virtual no debe limitarse a leer el ID visible en la ficha resumen del portal.
* **Procedimiento obligatorio:** Debe acceder a la ficha detallada de la licitacion y realizar un cotejo cruzado del ID contra los documentos y archivos adjuntos publicados. Solo se catalogara y reportara la licitacion como oportunidad valida si este cruce resulta exitoso.

### 2.5. Analisis de Terminos de Referencia (TDR) y Admisibilidad
Tras la deteccion de una oportunidad valida, el motor ejecutara un analisis documental de alta densidad:
* **Capacidad de lectura:** Procesamiento de bases y TDRs de hasta 50 paginas por licitacion.
* **Extraccion clave:**
  * Descripcion de servicios requeridos.
  * Cronograma y fechas criticas (visitas a terreno, consultas, cierre de recepcion de ofertas).
  * Presupuesto maximo disponible asignado por la entidad compradora.
* **Verificacion Administrativa de Bases (Causales de Inadmisibilidad):**
  El sistema debe auditar la presencia de requisitos documentales obligatorios y alertar al equipo. Debe buscar expresamente:
  * Anexo 4 (Pactos de Integridad).
  * Escrituras publicas.
  * Poderes de representacion legal.
  * Certificados de vigencia.
* **Control Presupuestario Preventivo:**
  El sistema debe cruzar el costo operativo base del Hotel Plaza San Francisco contra el presupuesto maximo publicado por el mandante. Si el presupuesto oficial no cubre los costos bases o los margenes minimos, el sistema generara una alerta de inviabilidad economica preventiva para evitar desgastes administrativos.

---

## 3. Restricciones Operativas y Requerimientos No Funcionales

### 3.1. Arquitectura de Ejecucion 100% Web (Python)
* **Prohibicion Explicita:** Queda terminantemente prohibida la creacion o ejecucion de scripts locales o ejecutables de escritorio en los puestos de trabajo del personal del hotel.
* **Justificacion Tecnica e Historica:** En fases preliminares (Fase 1), las politicas de seguridad perimetral, firewalls corporativos y suites de antivirus del hotel bloquearon la ejecucion de scripts locales y procesos en segundo plano.
* **Mandato de Implementacion:** Toda la solucion debe estar desarrollada en Python y servirse exclusivamente a traves de una plataforma web (backend API y frontend web accesible desde el navegador institucional).

### 3.2. Diseno y Experiencia de Usuario (UX)
* La interfaz de usuario debe estar orientada a personal comercial y de eventos sin conocimientos tecnicos de programacion ni configuraciones de red.
* Gestion visual y clara de parametros: creacion de filtros, ejecucion de busquedas y visualizacion de resultados en pocos clics.

### 3.3. Configuracion de Tolerancia y Umbrales
* La interfaz debe permitir a los administradores comerciales definir y ajustar margenes de tolerancia presupuestaria (porcentajes o montos fijos tanto en pesos chilenos CLP como en dolares USD).

### 3.4. Restriccion de Estilo: Supresion Total de Emojis
* **Regla estricta de interfaz y reportes:** Se elimina por completo el uso de emojis o iconografia informal en la interfaz de usuario, logs de auditoria, notificaciones por correo o mensajeria, reportes generados y documentacion tecnica del proyecto. Todo mensaje, estado o alerta debe ser comunicado mediante texto profesional, nomenclaturas formales e indicadores visuales estandar de diseno corporativo (etiquetas de texto, codigos de estado o badges de severidad).

---

## 4. Tablero de Control (Dashboard) y Gestion Comercial

### 4.1. Embudo de Conversion de Licitaciones
La herramienta debe estructurar la visualizacion del rendimiento comercial en cuatro etapas:
1. **Total Identificadas:** Licitaciones captadas por el motor semantico segun rubro y geolocalizacion.
2. **Calificadas:** Oportunidades que pasaron con exito los filtros de presupuesto, fechas y admisibilidad documental.
3. **Participadas:** Licitaciones en las cuales el equipo comercial ingreso formalmente una oferta.
4. **Adjudicadas:** Procesos adjudicados al hotel (calculo de tasa de cierre y conversion de ingresos).

### 4.2. Reportabilidad Ejecutiva
* Generacion de informes consolidados de periodicidad semanal y mensual.
* Destinatarios directos: Gerencia General y Direccion de Finanzas.
* Proposito: Evaluar la demanda estatal y habilitar el ajuste dinamico de politicas de precios.
