# NO SQL — Descripcion de las colecciones

## Estado: no aplica al almacenamiento del sistema

El sistema es **100% SQLite (relacional)**: toda la informacion persiste en
un unico archivo `licitaciones.db` con 6 tablas (ver
`diccionario_de_datos.md`). No se usa ninguna base de datos NoSQL
(documentos, clave-valor, grafos o columnas) ni se instala un motor de ese
tipo.

Lo unico con forma de "coleccion" en el proyecto son los **documentos JSON
que llegan desde la API externa de Mercado Publico**, que se procesan en
memoria y se guardan como filas de la tabla `licitaciones`. Se describen a
continuacion por completitud.

## Coleccion externa: listado de licitaciones

**Origen:** `GET https://api.mercadopublico.cl/servicios/v1/publico/licitaciones.json?fecha=DDMMAAAA`
**Formato:** objeto JSON con una lista bajo la clave `Listado`.

```json
{
  "Listado": [
    {
      "CodigoExterno": "1058-12-COT26",
      "Nombre": "Servicio de Banqueteria y Salones ...",
      "Descripcion": "Texto de los terminos de referencia ...",
      "MontoEstimado": 5800000,
      "Moneda": "CLP",
      "FechaCreacion": "2026-09-12",
      "FechaCierre": "2026-09-20",
      "Fechas": { "MontoEstimado": 5800000, "FechaCierre": "...", "FechaCreacion": "..." },
      "Comprador": { "NombreOrganismo": "Subsecretaria de Turismo", "RegionUnidad": "Region Metropolitana (Santiago)" }
    }
  ]
}
```

| Campo del documento | Destino en la base |
| :--- | :--- |
| `CodigoExterno` | `licitaciones.id_licitacion` (PK) |
| `Nombre` | `licitaciones.titulo` |
| `Descripcion` | `licitaciones.descripcion_tdr` |
| `MontoEstimado` | `licitaciones.presupuesto_mandante` (solo si la moneda es CLP) |
| `FechaCreacion` / `Fechas.FechaCreacion` | `licitaciones.fecha_publicacion` |
| `FechaCierre` / `Fechas.FechaCierre` | `licitaciones.fecha_cierre` |
| `Comprador.NombreOrganismo` | `licitaciones.organismo` |
| `Comprador.RegionUnidad` | `licitaciones.region` |

Reglas aplicadas al recibir un documento:

* Moneda distinta de `CLP` → el documento se descarta (montos no
  comparables).
* Fecha de cierre ya pasada → se descarta como oportunidad.
* Texto sin pertinencia hotelera → se descarta (filtro semantico).
* El documento se fusiona con la ficha detalle (mismo formato, mas campos)
  antes de guardarse.

## Coleccion externa: ficha detalle de una licitacion

**Origen:** mismo endpoint consultado por `CodigoExterno`.
Devuelve un documento con la misma forma que un item del listado, con los
datos completos (presupuesto, fechas y comprador reales). La aplicacion lo
usa para enriquecer la fila ya guardada; si `CodigoExterno` no coincide con
el codigo pedido, la ficha se ignora.
