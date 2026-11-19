# Modelo Relacional

Esquema relacional completo en notacion convencional. Claves primarias en
**negrita**, claves foraneas como `FK`. Coherente con el script
`script_poblar_tablas.sql`.

## Esquema

```text
AJUSTES (
    clave       TEXT PK,
    valor       INTEGER NN
)

SALONES (
    id_salon            TEXT PK,
    nombre              TEXT NN,
    tipo                TEXT NN,
    capacidad_maxima    INTEGER NN,
    horario_disponible  TEXT NN,
    tarifa_referencial  INTEGER NN DEFAULT 0,
    ubicacion           TEXT NN DEFAULT '',
    equipamiento        TEXT NN DEFAULT '',
    descripcion         TEXT NN DEFAULT '',
    propiedad           TEXT NN DEFAULT 'Plaza San Francisco',
    montajes            TEXT NN DEFAULT '',
    es_provisional      INTEGER NN DEFAULT 0
)

RESERVAS_SALONES (
    id_reserva           INTEGER PK AUTOINCREMENT,
    id_salon             TEXT NN  FK -> SALONES(id_salon),
    cliente_evento       TEXT NN,
    organismo_o_empresa  TEXT NN,
    tipo_evento          TEXT NN,
    montaje              TEXT NN DEFAULT '',
    fecha_inicio         TEXT NN,
    fecha_fin            TEXT NN,
    horario              TEXT NN,
    asistentes_estimados INTEGER NN DEFAULT 0,
    estado_reserva       TEXT NN DEFAULT 'Confirmada',
    id_licitacion        TEXT NN DEFAULT '',   -- FK logica -> LICITACIONES
    contacto_responsable TEXT NN DEFAULT '',
    observaciones        TEXT NN DEFAULT ''
)

LICITACIONES (
    id_licitacion        TEXT PK,
    titulo               TEXT NN,
    organismo            TEXT NN,
    categoria            TEXT NN,
    modalidad            TEXT NN,
    region               TEXT NN,
    presupuesto_mandante INTEGER NN,
    costo_base_hotel     INTEGER NN,
    estado_embudo        TEXT NN,
    validacion_adjuntos  TEXT NN,
    tiene_anexo4         INTEGER NN DEFAULT 1,
    tiene_escrituras     INTEGER NN DEFAULT 1,
    tiene_poderes        INTEGER NN DEFAULT 1,
    tiene_vigencias      INTEGER NN DEFAULT 1,
    fecha_publicacion    TEXT NN,
    fecha_cierre         TEXT NN,
    descripcion_tdr      TEXT,
    cantidad_asistentes  INTEGER NN DEFAULT 0,
    tipo_jornada         TEXT NN DEFAULT '',
    horario_evento       TEXT NN DEFAULT '',
    id_salon_asignado    TEXT NN DEFAULT '',   -- FK logica -> SALONES
    propiedad            TEXT NN DEFAULT 'Plaza San Francisco',
    revisada             INTEGER NN DEFAULT 0,
    motivo_descarte      TEXT NN DEFAULT '',
    descripcion_descarte TEXT NN DEFAULT '',
    notas                TEXT NN DEFAULT '',
    costeo_validado      INTEGER NN DEFAULT 0,
    sello_mujer          INTEGER NN DEFAULT 0,
    jornada_40h          INTEGER NN DEFAULT 0,
    sello_sernatur       INTEGER NN DEFAULT 0,
    inclusion_laboral    INTEGER NN DEFAULT 0,
    adjudicatario        TEXT NN DEFAULT '',
    puntaje_adjudicacion REAL    NN DEFAULT 0,
    precio_final         INTEGER NN DEFAULT 0,
    actualizado_en       TEXT NN DEFAULT ''
)

HISTORIAL_OC (
    id_oc       INTEGER PK AUTOINCREMENT,
    fecha       TEXT NN DEFAULT '',
    organismo   TEXT NN DEFAULT '',
    objeto      TEXT NN DEFAULT '',
    monto       INTEGER NN DEFAULT 0,
    modalidad   TEXT NN DEFAULT '',
    archivo     TEXT NN DEFAULT '',
    cargado_en  TEXT NN DEFAULT ''
)

HISTORIAL_LICITACION (
    id_evento     INTEGER PK AUTOINCREMENT,
    id_licitacion TEXT NN,                     -- FK logica -> LICITACIONES
    fecha         TEXT NN DEFAULT '',
    usuario       TEXT NN DEFAULT '',
    tipo          TEXT NN DEFAULT '',
    detalle       TEXT NN DEFAULT ''
)
```

## Restricciones e integridad

| Tipo | Donde | Comportamiento |
| :--- | :--- | :--- |
| Primaria | Todas las tablas | SQLite crea el indice unico automatico |
| Foranea explicita | `RESERVAS_SALONES.id_salon` → `SALONES.id_salon` | `PRAGMA foreign_keys = ON` en cada conexion; no se puede borrar un salon con reservas |
| Unicidad logica | `LICITACIONES.id_licitacion` | PK: el codigo de Mercado Publico identifica una unica licitacion |
| Sin duplicados de OC | `HISTORIAL_OC.archivo` | La reimportacion del mismo archivo reemplaza sus filas en una transaccion |

**Referencias sin FK (garantizadas por la aplicacion):**
`RESERVAS_SALONES.id_licitacion` e `HISTORIAL_LICITACION.id_licitacion`
apuntan a `LICITACIONES.id_licitacion` sin restriccion declarada; la app
mantiene la consistencia (al eliminar una licitacion, su historial se borra
y sus reservas se desvinculan en la misma transaccion), y
`LICITACIONES.id_salon_asignado` guarda el salon propuesto aunque el salon
aun no exista en el catalogo.

## Normalizacion

* Forma normal de Boyce-Codd: cada tabla tiene una sola entidad; los
  atributos dependen unicamente de la clave primaria.
* Sin redundancia estructural: el catalogo de salones esta separado de las
  reservas (no se repiten aforos ni nombres por reserva).
* Los valores repetidos en columnas (`estado_embudo`, `motivo_descarte`,
  `estado_reserva`) son catalogs de aplicacion validados en las rutas, no
  tablas aparte: su volumen es fijo y se actualiza con el codigo.
* Fechas y montos en tipos atomicos (texto ISO y enteros), sin listas
  embebidas en una celda salvo `montajes`/`notas`, donde la lista es
  presentacional y no participa en joins.
