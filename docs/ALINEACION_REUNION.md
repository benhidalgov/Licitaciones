# Alineacion del sistema con la reunion de levantamiento

Documento de trabajo. Contrasta lo acordado en la reunion con el estado real del
repositorio y define que cambiar, en que orden y con que criterio de aceptacion.

---

## 1. Resumen ejecutivo

El sistema ya cubre el nucleo de prospeccion (API Mercado Publico, filtro semantico,
embudo, control presupuestario, admisibilidad y agenda de salones). La reunion no
invalida esa base, pero si corrige cuatro supuestos:

1. **El alcance es mas amplio y mas acotado a la vez.** Mas servicios (salones,
   alojamiento y A&B intramuros) y dos propiedades (Plaza San Francisco e Ismael),
   con una exclusion dura: nada de banqueteria fuera del hotel.
2. **El presupuesto manda.** Si no cubre el costo minimo, se descarta de inmediato.
   Hoy el sistema solo lo advierte y, ademas, estima el costo como 75% del
   presupuesto, por lo que una oportunidad importada desde la API nunca resulta
   inviable.
3. **La comuna no descarta.** Se evalua margen; Las Condes o Vitacura no se filtran
   automaticamente.
4. **La operacion es colaborativa.** Tres usuarias, estados compartidos, notas y
   motivos de descarte. Hoy existe un unico usuario demo.

Estado de la suite al momento de este analisis: **121 pruebas, 0 fallos**
(`python verify.py`).

---

## 2. Matriz de brechas

| # | Tema | Reunion | Estado actual | Brecha | Accion | Prioridad |
|:-:|:--|:--|:--|:--|:--|:--:|
| 1 | Servicios | Salones, alojamiento y A&B solo intramuros | Categorias `Alojamiento` y `Eventos / Catering` (`mercado_publico.py:26-34`) | No habia regla de intramuros ni exclusion de servicios externos | Mantener A&B dentro de `Eventos / Catering` y excluir servicios fuera del hotel | P0 |
| 2 | Propiedades | Plaza San Francisco (todo) e Ismael (solo hospedaje) | Una sola propiedad implicita; `salones` no tiene campo de hotel (`database.py:39-51`) | No se puede modelar Ismael ni restringirlo | Campo `propiedad` en salones y licitaciones; regla Ismael = solo alojamiento | P0 |
| 3 | Salones | 17 salones con distintos montajes | 5 salones (`database.py:67-123`) | Faltan 12 espacios y el catalogo de montajes | Cargar catalogo real del hotel; campo `montajes` | P0 (dato pendiente) |
| 4 | Presupuesto | Criterio mandatorio: si no cubre costo minimo, se descarta | Se muestra alerta, no se descarta (`app.py:196-216`; badge en `dashboard.html:322-339`) | No hay descarte automatico ni motivo | Calcular costo minimo real y marcar `Descartada / Precio` | P0 |
| 5 | Costo base | Costo minimo del hotel | `costo_base_hotel = 75% del presupuesto` (`mercado_publico.py:217`) | El costo depende del presupuesto, no de la operacion | Modelo de costo: salones + alimentacion por persona + habitaciones + margen | P0 |
| 6 | Capacidad | Proponer match por capacidad; hotel valida disponibilidad en PMS | `get_salones_aptos` existe (`database.py:545`) pero solo se listan alternativas ante sobrecupo (`detail.html:387-436`) | No hay propuesta de match permanente ni aviso PMS | Mostrar siempre salones compatibles y etiqueta "Disponibilidad a validar en PMS" | P0 |
| 7 | Geografia | No descartar por comuna si el margen es atractivo | La especificacion exige prioridad estricta RM (`ESPECIFICACION_REQUERIMIENTOS.md:33-34`), aunque el codigo no filtra | Regla escrita contradice la reunion | Quitar filtro estricto; region solo informativa; evaluar margen | P0 |
| 8 | Sellos | Sello Mujer, 40 horas, Sernatur, inclusion laboral | Checklist solo con 4 documentos administrativos (`detail.html:517-636`) | No se evaluan exigencias complementarias | Checklist de sellos y criterios tecnicos | P1 |
| 9 | Home | Vista priorizada de oportunidades del dia con match viable | Listado completo por fecha de cierre (`database.py:799`) | No hay priorizacion diaria | Bloque "Oportunidades priorizadas de hoy" | P0 |
| 10 | ID y enlace | ID destacado y enlace directo a Mercado Publico | Existe en la ficha (`detail.html:6, 21`), no en la fila del listado | Falta acceso directo desde el home | Agregar enlace MP en la tabla | P1 |
| 11 | Ficha IA | Resumen: fechas, personas, salones/habitaciones, A&B y ponderaciones | **Implementado** en `resumen.py` + panel en `detail.html` | Sin IA configurada usa reglas deterministicas; `RESUMEN_IA_API_KEY` la habilita | Reglas por defecto, IA opcional, desglose de ponderacion que suma 100 | P1 |
| 12 | Estados | Revisada/Vista, Participamos, No participamos + motivo | 5 etapas de embudo (`app.py:25-31`) | No hay marca de revision ni motivo de descarte | Campo `revisada`, `motivo_descarte` (precio/disponibilidad) y notas | P0 |
| 13 | Exportacion | Exportar resumenes e indicadores a Excel | Solo ficha Markdown (`app.py:308-318`) | No hay exportacion tabular | Exportacion CSV compatible con Excel (stdlib `csv`, BOM UTF-8) | P0 |
| 14 | Usuarios | 3 perfiles con estados y notas compartidas | Un usuario `admin` (`app.py:22-23`) | No hay perfiles ni autoria | 3 usuarios, sesion compartida, autor en notas | P0 |
| 15 | Clientes clave | Mineduc, Minsal, U. de Chile, Usach, productoras | **Implementado**: lista `CLIENTES_CLAVE` (`database.py`), filtro y etiqueta en el tablero | Sin monitoreo | Filtrar por `organismo` con alias; etiqueta "Cliente: ..." en la ficha y el listado | P2 |
| 16 | Benchmarking | Adjudicatario, puntajes, precio final | **Implementado**: columnas `adjudicatario`, `puntaje_adjudicacion`, `precio_final` + pagina Analitica | La API publica no expone puntajes, solo la ficha | Carga manual desde la ficha; calcula desviacion vs. presupuesto y margen vs. costo | P2 |
| 17 | Historial OC | Excel entregado por el hotel | **Implementado**: tabla `historial_oc` e importador `.xlsx`/`.csv` | No habia importacion | Encabezados tolerantes (Organismo/Objeto/Fecha/Monto) y cruce de experiencia por organismo | P2 (columnas por confirmar) |
| 18 | Tolerancia a tipeo | Filtro semantico que no pierda `catring` por `catering` | **Implementado** en `contar_terminos_fuzzy` (`mercado_publico.py`) | Solo regex estricto, el tipeo descartaba licitaciones | Levenshtein con tope 1 palabra corta / 2 larga; solo rescata, nunca inventa | P1 |

Prioridad: **P0** = sin esto la reunion no esta reflejada; **P1** = visible para el
usuario final; **P2** = bonus track.

---

## 3. Lo que ya esta alineado y no se debe tocar

- Tope de Compra Agil en **$6.900.000 CLP** configurable (`database.py:916-939`).
- Embudo comercial y metricas de conversion (`database.py:889-913`).
- Cruce documental y "Efecto ID" (campo `validacion_adjuntos`).
- Checklist de admisibilidad de 4 antecedentes.
- Agenda de salones con deteccion de colisiones.
- Arquitectura 100% web y politica de cero emojis.
- Uso de la API oficial con ticket en `.env`.

---

## 4. Contradicciones documentales a corregir

| Documento | Dice hoy | Debe decir |
|:--|:--|:--|
| `README.md:30` | Revision manual de hasta 10 paginas | 12 a mas de 20 paginas por manana |
| `README.md:52-57` | 5 salones | 17 salones, con montajes y dos propiedades |
| `ESPECIFICACION_REQUERIMIENTOS.md:17` | Hasta 10 paginas | 12 a mas de 20 paginas |
| `ESPECIFICACION_REQUERIMIENTOS.md:33-34` | Filtrado primario estricto RM | Region informativa; no descartar por comuna sin evaluar margen |
| `ESPECIFICACION_REQUERIMIENTOS.md:46` | Bases de hasta 50 paginas | Bases de 40 a 100 paginas + 5 a 7 anexos |
| `ESPECIFICACION_REQUERIMIENTOS.md:25-31` | Dos categorias | Tres lineas: Salones, Alojamiento, A&B |
| `README.md:40` | Embudo de 5 etapas | Embudo + estados operativos Revisada / Participamos / No participamos |

---

## 5. Plan de implementacion

### Fase 0 - Decisiones y datos (bloquea P0)

1. Catalogo real de los **17 salones**: nombre, propiedad, capacidad por montaje,
   tarifa y equipamiento.
2. **Modelo de costos minimos**: tarifa de salon, valor por persona de alimentacion,
   tarifa de habitacion y margen/tolerancia.
3. **Usuarios**: nombres, credenciales y si tendran roles distintos o solo autoria.
4. **Resumen IA**: confirmar proveedor o aceptar una version basada en reglas.
5. **Excel de OC**: columnas disponibles y frecuencia de actualizacion.
6. **Benchmarking**: fuente de adjudicaciones (API, scraping o carga manual).

### Fase 1 - Alineacion operativa (P0)

1. Modelo de datos: `propiedad`, `tipo_servicio`, `montajes`, `revisada`,
   `motivo_descarte`, `notas`, checklist de sellos.
2. Regla de exclusion: banqueteria o eventos fuera del hotel; Ismael solo alojamiento.
3. Costo minimo real y descarte automatico por presupuesto con motivo.
4. Propuesta de salones compatibles permanente + aviso de validacion en PMS.
5. Eliminar el filtro estricto por comuna; dejar region como dato informativo.
6. Home priorizado: oportunidades abiertas, viables y con match de capacidad.
7. Estados Revisada / Participamos / No participamos con motivo y notas compartidas.
8. Tres usuarios con datos compartidos.
9. Exportacion CSV/Excel de oportunidades e indicadores.
10. Correccion de README y especificacion.

### Fase 2 - Analitica y bonus (P1-P2)

1. ~~Ficha resumen estructurada: fechas, personas, salones/habitaciones, A&B y
   ponderacion de criterios.~~ **Hecho**: `resumen.py`, reglas por defecto y
   IA opcional via `RESUMEN_IA_API_KEY`.
2. Enlace directo a Mercado Publico en el listado.
3. ~~Monitoreo de clientes clave.~~ **Hecho**: `CLIENTES_CLAVE`, filtro y etiqueta.
4. ~~Benchmarking de adjudicaciones.~~ **Hecho**: bloque en la ficha + pagina
   `/analitica`.
5. ~~Importacion del historial de OC.~~ **Hecho**: `/analitica` acepta `.xlsx`
   y `.csv`; cruce de experiencia en la ficha.

### Fase 3 - Reporting

1. Informes semanales y mensuales para Gerencia y Finanzas.
2. Alertas y seguimiento post-mortem.

---

## 6. Criterios de aceptacion de Fase 1

- Una licitacion cuyo costo minimo supere el presupuesto queda en `Descartada`
  con motivo `Precio` y no aparece en la vista priorizada.
- Una licitacion de Ismael solo puede clasificarse como `Alojamiento`.
- Una licitacion con servicios fuera del hotel se descarta en la importacion.
- El detalle muestra al menos un salon compatible o indica explicitamente que no
  existe capacidad, junto al aviso de validacion en PMS.
- Dos usuarios distintos ven el mismo estado y las mismas notas.
- El listado se exporta a un archivo que Excel abre sin pasos adicionales.
- La suite completa sigue en verde (`python verify.py`).

---

## 7. Estado de implementacion (Fase 1)

Implementado en el repositorio:

- [x] Campo `propiedad` en licitaciones y salones; regla Ismael solo alojamiento.
- [x] Catalogo de 17 salones (5 confirmados + 12 provisionales marcados).
- [x] Explicitud de A&B dentro de `Eventos / Catering` y exclusion de servicios fuera del hotel.
- [x] Costo minimo por tarifa de salon + consumo por persona y descarte automatico con motivo `Precio`.
- [x] Costeo provisional identificado; no se descarta hasta que el equipo lo valide.
- [x] Propuesta de salones por capacidad y aviso de validacion en PMS.
- [x] Region informativa; sin descarte automatico por comuna.
- [x] Vista priorizada del dia con enlace a Mercado Publico.
- [x] Estados Revisada / Participamos / No participamos con motivo y notas compartidas.
- [x] Tres perfiles operativos: Daniela, Francisca y Mari Carmen.
- [x] Exportacion CSV compatible con Excel.
- [x] Sellos: Sello Mujer, jornada de 40 horas, Sello Sernatur e inclusion laboral.
- [x] README y especificacion corregidos.
- [x] Ficha resumen con fechas, personas, espacio, alimentacion y desglose de
      ponderacion; IA opcional, reglas como base.
- [x] Filtro semantico tolerante a tipeos (`catring`, `hospedagh`) sin inventar
      clasificaciones.
- [x] Monitoreo de clientes clave (Mineduc, Minsal, U. de Chile, Usach,
      productoras) con filtro y etiqueta en el tablero.
- [x] Benchmarking de adjudicaciones: adjudicatario, puntaje y precio final,
      con desviacion sobre el presupuesto y margen sobre el costo del hotel.
- [x] Importador de historial de OC (`.xlsx` / `.csv`) y cruce de experiencia
      por organismo en la ficha.

Pendiente de datos o de Fase 2:

- [ ] Validar los 12 salones provisionales con el hotel.
- [ ] Confirmar tarifas de alimentacion y habitacion usadas por el modelo de costos.
- [ ] Confirmar las columnas exactas del Excel de OC con el hotel (el importador
      ya tolera variantes, pero conviene fijarlas).
- [ ] Definir proveedor de IA para la ficha resumen (hoy solo reglas, salvo
      `RESUMEN_IA_API_KEY`).

---

## 8. Riesgos

- **Datos faltantes**: cargar 17 salones con aforos inventados produce matches
  falsos. Es preferible dejar el catalogo incompleto y marcarlo.
- **Costo minimo**: sin tarifas reales el descarte por presupuesto sera tan
  arbitrario como el 75% actual.
- **PMS**: no hay integracion; la validacion final siempre es humana. El sistema
  no debe prometer disponibilidad confirmada.
- **IA**: si no hay proveedor definido, el resumen debe generarse con reglas y
  marcarse como tal. Ya funciona asi por defecto; el texto de IA es un
  enriquecimiento opcional que nunca reemplaza las reglas si falla.
