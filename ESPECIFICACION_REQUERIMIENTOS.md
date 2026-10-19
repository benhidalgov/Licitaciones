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
* **Alto Costo Comercial por Revision Manual:** El equipo de eventos gasta entre 1 y 2 horas diarias revisando entre 12 y mas de 20 paginas de resultados de forma manual. Esta demora permite que competidores bloqueen disponibilidad o ingresen propuestas antes de que el hotel detecte la oportunidad.
* **Inconsistencia de Datos ("Efecto ID"):** Las vistas resumidas de Mercado Publico presentan con frecuencia IDs de licitacion inexistentes, desactualizados o no coincidentes con los adjuntos reales, derivando en busquedas infructuosas.
* **Barreras de Autenticacion:** Procesos de ingreso via Clave Unica y verificaciones por correo ralentizan la rutina comercial diaria.

---

## 2. Requerimientos Funcionales y Reglas de Negocio

### 2.1. Matriz de Palabras Clave Obligatorias y Segmentacion
El motor de busqueda debera filtrar con procesamiento de lenguaje natural (NLP) considerando intencion de compra en dos categorias principales:

| Categoria | Palabras Clave Obligatorias | Contexto de Negocio |
| :--- | :--- | :--- |
| Alojamiento | Hospedaje, Alojamiento, Habitaciones | Delegaciones, pernoctacion corporativa y reservas de estadia. |
| Eventos / Catering | Eventos, Catering, Centro de Eventos, Salones, Coffee Break, Coctel | Arriendo de salones y servicios de alimentacion intramuros. |

La categoria **Eventos / Catering** agrupa las lineas de salones y de alimentos y bebidas. Todo servicio debe ejecutarse dentro de las instalaciones del hotel.

* El filtrado debe tolerar errores de tipeo propios de los textos de compra publica (`catring` por `catering`, `hospedagh` por `hospedaje`). Se aplica **solo cuando la coincidencia exacta no arroja resultado**, de modo que nunca convierta una licitacion no relevante en relevante.
* La tolerancia se resuelve con distancia de edicion: una palabra corta admite un error y una palabra larga dos. No se requiere un proveedor externo de NLP.

### 2.2. Filtro de Geolocalizacion
* La region y comuna son **datos informativos**, no criterios de descarte automatico.
* Una oportunidad fuera de la comuna de Santiago (por ejemplo Las Condes o Vitacura) se evalua igualmente si el presupuesto deja margen. El equipo decide caso a caso; en la practica el hotel ha ganado procesos por descarte de competidores.
* No se debe descartar una licitacion solo por su ubicacion geografica.

### 2.3. Modalidad Compra Agil
* El sistema debe identificar, priorizar y generar alertas inmediatas para procesos de **Compra Agil**.
* Debe ajustarse al umbral normativo vigente de hasta **6.900.000 CLP** (actualizado respecto al limite anterior de 1.900.000 CLP).

### 2.4. Validacion Robusta de ID y Existencia Real
* **Regla estricta:** El asistente virtual no debe limitarse a leer el ID visible en la ficha resumen del portal.
* **Procedimiento obligatorio:** Debe acceder a la ficha detallada de la licitacion y realizar un cotejo cruzado del ID contra los documentos y archivos adjuntos publicados. Solo se catalogara y reportara la licitacion como oportunidad valida si este cruce resulta exitoso.

### 2.5. Analisis de Terminos de Referencia (TDR) y Admisibilidad
Tras la deteccion de una oportunidad valida, el motor ejecutara un analisis documental de alta densidad:
* **Capacidad de lectura:** Procesamiento de bases y TDRs de entre 40 y 100 paginas, mas 5 a 7 anexos por proceso.
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
### 2.6. Alcance por Propiedad y Servicios
* **Hotel Plaza San Francisco:** salones, eventos, alimentos y bebidas, y habitaciones.
* **Hotel Ismael:** unicamente hospedaje y alojamiento. No se postulan salones ni eventos en esta propiedad.
* **Restriccion estricta:** no se postula banqueteria, catering ni eventos fuera de las instalaciones del hotel, incluidos servicios a domicilio o en espacios publicos.
* El hotel cuenta con **17 salones** con distintos tipos de montaje. El catalogo debe permitir marcar como provisionales los espacios cuyos aforos y tarifas aun no estan validados.
* El sistema propone matches por capacidad requerida versus capacidad maxima del salon. La disponibilidad final la valida el equipo en el PMS del hotel; no existe sincronizacion automatica con Mercado Publico por razones de seguridad y API.

### 2.7. Regla Mandatoria de Presupuesto
* Si el costo minimo operativo supera el presupuesto publicado por el mandante, la oportunidad se descarta de inmediato con motivo **Precio**.
* El costo minimo se compone de la tarifa del salon mas el consumo de alimentacion por persona, o la tarifa de habitacion por persona en alojamiento.
* Mientras el costo sea provisional (importado desde la API), la oportunidad debe identificarse como no validada y no se descarta automaticamente.

### 2.8. Criterios Complementarios y Sellos
El sistema debe registrar y evaluar exigencias complementarias de las bases, entre ellas:
* Sello Mujer.
* Jornada laboral de 40 horas.
* Sello Sernatur.
* Inclusion laboral.

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
1. **Total Identificadas:** Licitaciones captadas por el motor semantico segun rubro.
2. **Calificadas:** Oportunidades que pasaron con exito los filtros de presupuesto, fechas y admisibilidad documental.
3. **Participadas:** Licitaciones en las cuales el equipo comercial ingreso formalmente una oferta.
4. **Adjudicadas:** Procesos adjudicados al hotel (calculo de tasa de cierre y conversion de ingresos).

### 4.2. Vista Priorizada y Ficha Resumen
* La pantalla principal debe priorizar las compras y licitaciones del dia que hacen match viable, destacando el ID y el enlace directo a Mercado Publico.
* Cada oportunidad debe contar con una ficha resumen con fechas del evento, cantidad de personas, requerimientos de salones o habitaciones, servicios de alimentacion y desglose de ponderacion de criterios de evaluacion.
* La ficha resumen puede generarse con IA o con reglas; si no hay proveedor de IA definido, debe indicarse que el resumen es automatico no generativo.

### 4.3. Estados Operativos Compartidos
* **Revisada:** la oportunidad fue vista y analizada por el equipo.
* **Participamos:** el equipo decide postular.
* **No participamos:** el equipo descarta la oportunidad indicando motivo: precio, disponibilidad, fuera de alcance u otro.
* Los estados y las notas son compartidos entre los tres perfiles operativos: Daniela, Francisca y Mari Carmen.

### 4.4. Exportabilidad
* El sistema debe permitir exportar el listado filtrado e indicadores a una planilla compatible con Excel.
* La exportacion debe incluir ID, organismo, propiedad, presupuesto, costo, margen, estado, motivo, aforo y notas.

### 4.5. Reportabilidad Ejecutiva
* Generacion de informes consolidados de periodicidad semanal y mensual.
* Destinatarios directos: Gerencia General y Direccion de Finanzas.
* Proposito: Evaluar la demanda estatal y habilitar el ajuste dinamico de politicas de precios.

### 4.6. Monitoreo de Clientes Clave
* Se debe mantener una lista configurable de clientes prioritarios: **Mineduc, Minsal, Universidad de Chile, Usach y productoras**.
* El tablero debe permitir filtrar el listado por cliente clave y etiquetar cada fila que corresponda.
* El reconocimiento se realiza sobre el organismo y el titulo, tolerando acentos y mayusculas, sin exigir coincidencia literal completa.
* Los clientes fuera de la lista no deben devolver resultados en vez de devolver todos.

### 4.7. Benchmarking de Adjudicaciones
* Por cada licitacion se deben registrar **adjudicatario, puntaje de adjudicacion (0 a 100) y precio final**.
* La API publica de Mercado Publico no expone puntajes: la fuente es la ficha publicada y la carga la realiza el equipo.
* El sistema debe calcular la desviacion del precio final respecto del presupuesto mandante y el margen respecto del costo minimo del hotel.
* La pagina de analitica debe consolidar las adjudicaciones ordenadas por precio final descendente e informar el precio promedio observado.

### 4.8. Historial de Ordenes de Compra
* El sistema debe importar el historial de OC que entrega el hotel en formato `.xlsx` o `.csv`.
* Los encabezados se aceptan con variantes de acento, mayusculas y puntuacion; las columnas ausentes quedan vacias en vez de abortar la carga.
* Se deben normalizar fechas (`15/03/2026` a `2026-03-15`) y montos en formato chileno (`$1.234.567`).
* La ficha de cada licitacion debe mostrar la experiencia previa con el mismo organismo: cantidad de OC y monto acumulado.
