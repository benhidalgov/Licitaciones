# Modelo Logico

Vista de entidades y relaciones del sistema (diagrama entidad-relacion).
Fuente de verdad: el esquema real de `database.py`.

## Diagrama

```mermaid
erDiagram
    SALONES ||--o{ RESERVAS_SALONES : "ocupa"
    LICITACIONES ||--o{ RESERVAS_SALONES : "origina"
    LICITACIONES ||--o{ HISTORIAL_LICITACION : "registra"

    SALONES {
        text id_salon PK
        text nombre
        int capacidad_maxima
        int es_provisional
    }
    RESERVAS_SALONES {
        int id_reserva PK
        text id_salon FK
        text fecha_inicio
        text fecha_fin
        text estado_reserva
    }
    LICITACIONES {
        text id_licitacion PK
        text titulo
        text estado_embudo
        int presupuesto_mandante
        int costo_base_hotel
    }
    HISTORIAL_LICITACION {
        int id_evento PK
        text id_licitacion FK
        text fecha
        text usuario
        text tipo
    }
```

## Entidades independientes

| Entidad | Descripcion |
| :--- | :--- |
| `AJUSTES` | Parametros de negocio en esquema clave-valor (UTM, tope de Compra Agil, margen de tolerancia). No relaciona con otras entidades. |
| `HISTORIAL_OC` | Ordenes de compra historicas del hotel, cargadas desde un archivo Excel. Se usa solo para reportes por cliente clave; no referencia ni es referenciada. |

## Descripcion de las relaciones

| Relacion | Cardinalidad | Tipo | Naturaleza |
| :--- | :--- | :---: | :--- |
| `SALONES` → `RESERVAS_SALONES` | 1 a N | Fuerte (FK explicita) | Un salon tiene muchas reservas; cada reserva apunta a un salon existente. |
| `LICITACIONES` → `RESERVAS_SALONES` | 1 a N | Debil (sin FK) | Una licitacion puede generar varias reservas; la reserva guarda el codigo en `id_licitacion`. |
| `LICITACIONES` → `HISTORIAL_LICITACION` | 1 a N | Debil (sin FK) | Una licitacion acumula muchos eventos de bitacora. |

## Reglas de negocio asociadas

* **Colisiones de agenda:** dos reservas `Confirmada` del mismo salon no
  pueden solaparse en fechas. La validacion corre dos veces: en el formulario
  y dentro de la transaccion de escritura (`BEGIN IMMEDIATE`).
* **Embudo:** `estado_embudo` avanza Identificada → Calificada →
  Participada → Adjudicada; `Descartada` y `Cerrada` son estados de salida.
* **Eliminacion en cascada (a nivel de aplicacion):** borrar una licitacion
  borra su `HISTORIAL_LICITACION` y desvincula sus reservas en una sola
  transaccion SQLite.
* **Cierre automatico:** al entrar al tablero, las licitaciones con
  `fecha_cierre` pasada pasan de abiertas a `Cerrada`.
