# Diccionario de Datos

**Base de datos:** SQLite 3, archivo `licitaciones.db` (una unica base por
instalacion). **Total: 6 tablas.**

Convenciones de tipos:

| Tipo SQLite | Tipo logico | Uso |
| :--- | :--- | :--- |
| `TEXT` | Cadena | Texto libre, fechas `AAAA-MM-DD`, marcas `AAAA-MM-DD HH:MM` (hora de Chile) |
| `INTEGER` | Entero | Montos en CLP, contadores, banderas `0/1` |
| `REAL` | Decimal | Puntajes de adjudicacion |

Todas las fechas se guardan como texto ISO-8601 para ordenarlas
lexicograficamente. Los montos son enteros en pesos chilenos (sin decimales).

---

## 1. `ajustes` — Parametros de negocio

Almacena los valores configurables desde la interfaz. Una fila por
parametro (esquema clave-valor).

| Columna | Tipo | Clave | Nulo | Descripcion |
| :--- | :--- | :---: | :---: | :--- |
| `clave` | TEXT | PK | No | Nombre del parametro |
| `valor` | INTEGER | — | No | Valor entero del parametro |

Claves conocidas:

| `clave` | Significado |
| :--- | :--- |
| `seed_demo` | `1` = datos de demostracion ya cargados (evita recargarlos) |
| `utm_valor` | Valor de la UTM vigente, usado para el tope de Compra Agil |
| `tope_compra_agil` | Tope en pesos para clasificar una compra agil |
| `margen_tolerancia_modo` | `0` = porcentaje, `1` = monto en CLP |
| `margen_tolerancia_valor` | Valor del margen minimo exigido para priorizar |

---

## 2. `salones` — Catalogo oficial de espacios del hotel

17 filas: los 16 salones del catalogo oficial ("SALONES HPSF.pdf") mas el
Salon Tam (unico provisional, aforos deducidos).

| Columna | Tipo | Clave | Nulo | Descripcion |
| :--- | :--- | :---: | :---: | :--- |
| `id_salon` | TEXT | PK | No | Identificador unico, formato `SALON-<NOMBRE>` |
| `nombre` | TEXT | — | No | Nombre visible ("Salon Danubio") |
| `tipo` | TEXT | — | No | Clase por aforo: Mesa ejecutiva / Sala de reuniones / Salon de eventos / Salon de gran capacidad |
| `capacidad_maxima` | INTEGER | — | No | Mejor aforo que admite (mejor montaje) |
| `horario_disponible` | TEXT | — | No | Horario operativo ("Por confirmar con el hotel" si no esta publicado) |
| `tarifa_referencial` | INTEGER | — | No | Tarifa de referencia; `0` = por confirmar |
| `ubicacion` | TEXT | — | No | Piso y superficie ("Piso 2 - 108 m2") |
| `equipamiento` | TEXT | — | No | Equipamiento del salon |
| `descripcion` | TEXT | — | No | Descripcion libre |
| `propiedad` | TEXT | — | No | Hotel al que pertenece (default `Plaza San Francisco`) |
| `montajes` | TEXT | — | No | Lista de montajes admitidos, separados por coma |
| `es_provisional` | INTEGER | — | No | `1` = aforos deducidos, pendientes de confirmacion (solo Salon Tam) |

---

## 3. `reservas_salones` — Agenda de ocupacion (bookings)

Una fila por evento reservado. El control de colisiones de fechas se ejecuta
dentro de la transaccion de escritura (`BEGIN IMMEDIATE`).

| Columna | Tipo | Clave | Nulo | Descripcion |
| :--- | :--- | :---: | :---: | :--- |
| `id_reserva` | INTEGER PK | PK (auto) | No | Correlativo de la reserva |
| `id_salon` | TEXT | FK | No | Salon reservado → `salones.id_salon` (FK explicita) |
| `cliente_evento` | TEXT | — | No | Nombre del evento o cliente |
| `organismo_o_empresa` | TEXT | — | No | Organismo contratante o empresa |
| `tipo_evento` | TEXT | — | No | Tipo de evento |
| `montaje` | TEXT | — | No | Montaje elegido (U, Auditorio, Mesa imperial, Escuela, Mesas redondas, Coctel de pie) |
| `fecha_inicio` | TEXT | — | No | Inicio `AAAA-MM-DD` |
| `fecha_fin` | TEXT | — | No | Fin `AAAA-MM-DD` (igual a inicio para eventos de un dia) |
| `horario` | TEXT | — | No | Franja horaria ("08:30 a 18:30 hrs") |
| `asistentes_estimados` | INTEGER | — | No | Numero de asistentes previstos |
| `estado_reserva` | TEXT | — | No | `Confirmada` / `Tentativa` / `Bloqueo Interno` |
| `id_licitacion` | TEXT | — | No | Licitacion que origino la reserva (referencia sin FK) |
| `contacto_responsable` | TEXT | — | No | Contacto del responsable del evento |
| `observaciones` | TEXT | — | No | Observaciones libres |

---

## 4. `licitaciones` — Oportunidades de Mercado Publico

Tabla principal (embudo comercial). Una fila por licitacion identificada.

| Columna | Tipo | Clave | Nulo | Descripcion |
| :--- | :--- | :---: | :---: | :--- |
| `id_licitacion` | TEXT | PK | No | Codigo externo de la licitacion (ej. `1058-12-COT26`) |
| `titulo` | TEXT | — | No | Titulo del servicio |
| `organismo` | TEXT | — | No | Organismo mandante |
| `categoria` | TEXT | — | No | Categoria (Alojamiento, Eventos / Catering, etc.) |
| `modalidad` | TEXT | — | No | `Compra Agil` o `Licitacion Publica` |
| `region` | TEXT | — | No | Region del organismo |
| `presupuesto_mandante` | INTEGER | — | No | Presupuesto del mandante en CLP |
| `costo_base_hotel` | INTEGER | — | No | Costo minimo estimado del hotel en CLP (provisional o validado) |
| `estado_embudo` | TEXT | — | No | `Identificada` / `Calificada` / `Participada` / `Cerrada` / `Adjudicada` / `Descartada` |
| `validacion_adjuntos` | TEXT | — | No | `Valida` / `Error ID / Discrepancia` / `Sin verificar` |
| `tiene_anexo4` | INTEGER | — | No | `1` = Anexo 4 presentado |
| `tiene_escrituras` | INTEGER | — | No | `1` = escrituras sociales presentadas |
| `tiene_poderes` | INTEGER | — | No | `1` = poderes de representacion presentados |
| `tiene_vigencias` | INTEGER | — | No | `1` = certificados de vigencia presentados |
| `fecha_publicacion` | TEXT | — | No | Publicacion `AAAA-MM-DD` |
| `fecha_cierre` | TEXT | — | No | Cierre de recepcion `AAAA-MM-DD` |
| `descripcion_tdr` | TEXT | — | Si | Texto de los terminos de referencia |
| `cantidad_asistentes` | INTEGER | — | No | Asistentes estimados del evento |
| `tipo_jornada` | TEXT | — | No | Jornada solicitada (completa, media, etc.) |
| `horario_evento` | TEXT | — | No | Horario solicitado |
| `id_salon_asignado` | TEXT | — | No | Salon propuesto (referencia a `salones` sin FK) |
| `propiedad` | TEXT | — | No | Hotel (default `Plaza San Francisco`; Ismael solo alojamiento) |
| `revisada` | INTEGER | — | No | `1` = revisada por el equipo |
| `motivo_descarte` | TEXT | — | No | `Precio` / `Disponibilidad` / `Fuera de alcance` / `Otro` |
| `descripcion_descarte` | TEXT | — | No | Detalle del motivo de descarte |
| `notas` | TEXT | — | No | Notas compartidas del equipo (una por linea con marca de tiempo) |
| `costeo_validado` | INTEGER | — | No | `1` = el costo base fue validado por el equipo |
| `sello_mujer` | INTEGER | — | No | `1` = aplica el Sello de la Mujer |
| `jornada_40h` | INTEGER | — | No | `1` = aplica jornada de 40 horas |
| `sello_sernatur` | INTEGER | — | No | `1` = aplica Sello Sernatur |
| `inclusion_laboral` | INTEGER | — | No | `1` = aplica inclusion laboral |
| `adjudicatario` | TEXT | — | No | Empresa adjudicada si se conoce |
| `puntaje_adjudicacion` | REAL | — | No | Puntaje de la adjudicacion |
| `precio_final` | INTEGER | — | No | Precio final adjudicado en CLP |
| `actualizado_en` | TEXT | — | No | Ultima modificacion `AAAA-MM-DD HH:MM` (hora de Chile) |

---

## 5. `historial_oc` — Historial de ordenes de compra del hotel

Se carga desde el Excel/CSV que entrega el hotel (importador de OC).

| Columna | Tipo | Clave | Nulo | Descripcion |
| :--- | :--- | :---: | :---: | :--- |
| `id_oc` | INTEGER PK | PK (auto) | No | Correlativo del registro |
| `fecha` | TEXT | — | No | Fecha de la OC |
| `organismo` | TEXT | — | No | Organismo que adjudico |
| `objeto` | TEXT | — | No | Objeto de la compra |
| `monto` | INTEGER | — | No | Monto en CLP |
| `modalidad` | TEXT | — | No | Modalidad de la compra |
| `archivo` | TEXT | — | No | Archivo de origen (nombre + huella), para no duplicar cargas |
| `cargado_en` | TEXT | — | No | Momento de la carga `AAAA-MM-DD` |

---

## 6. `historial_licitacion` — Bitacora de actividad por licitacion

Eventos del sistema (notas, decisiones, revisiones) vinculados a una
licitacion. La referencia `id_licitacion` es logica: no hay FK declarada, y
al eliminar una licitacion sus eventos se borran en la misma transaccion.

| Columna | Tipo | Clave | Nulo | Descripcion |
| :--- | :--- | :---: | :---: | :--- |
| `id_evento` | INTEGER PK | PK (auto) | No | Correlativo del evento |
| `id_licitacion` | TEXT | — | No | Licitacion afectada → `licitaciones.id_licitacion` (referencia sin FK) |
| `fecha` | TEXT | — | No | Marca de tiempo `AAAA-MM-DD HH:MM` (hora de Chile) |
| `usuario` | TEXT | — | No | Usuario que ejecuto la accion |
| `tipo` | TEXT | — | No | Tipo de evento (`Nota`, `Decision`, `Revision`, etc.) |
| `detalle` | TEXT | — | No | Descripcion del evento (maximo 200 caracteres en la interfaz) |
