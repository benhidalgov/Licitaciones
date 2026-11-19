# Entregables — Copilot de Licitaciones y Operaciones Hoteleras

Hotel Plaza San Francisco | Programa VcM DUOC UC

Mapeo entre la lista de entrega y los archivos de esta carpeta.

## Aplicacion

| Item de la entrega | Estado | Archivo |
| :--- | :--- | :--- |
| APK sistema | **No aplica** (ver nota al final) | — |
| Codigo sistema | Disponible | Repositorio: https://github.com/benhidalgov/Licitaciones |
| PDF Implementacion ambiente de desarrollo | Generado en Markdown (convertir a PDF antes de subir) | `ambiente_de_desarrollo.md` |
| txt Repositorio GitHub del proyecto documentado | No incluido en esta corrida | — |

## Base de datos

| Item de la entrega | Estado | Archivo |
| :--- | :--- | :--- |
| Script sistema (poblar tablas) | Generado (CREATE TABLE + INSERTs oficiales) | `script_poblar_tablas.sql` |
| Diccionario de datos | Generado (6 tablas) | `diccionario_de_datos.md` |
| Modelo logico | Generado (entidades y relaciones) | `modelo_logico.md` |
| Modelo relacional | Generado (esquema con claves y restricciones) | `modelo_relacional.md` |
| NO SQL descripciones de las colecciones | Generado (justificacion de no aplica + colecciones JSON externas) | `no_sql_colecciones.md` |

## Otros documentos

| Documento | Contenido |
| :--- | :--- |
| `manual_de_instalacion.md` | Requisitos, instalacion local paso a paso, despliegue en Render, actualizacion, desinstalacion y solucion de problemas |
| `plan_de_pruebas.md` | Estrategia, tipos y distribucion de las 230 pruebas, 18 casos representativos, criterios de aceptacion y limites |

## Nota: por que el APK no aplica

El sistema es una aplicacion web (Flask + SQLite) que se sirve y se usa
enteramente desde el navegador, incluido en telefonos via la URL del sitio.
No es una aplicacion nativa Android, por lo que el entregable "APK sistema"
no corresponde a este proyecto.

## Como usar el script SQL

```bash
sqlite3 licitaciones.db < script_poblar_tablas.sql
```

Crea las 6 tablas y las puebla con los datos semilla oficiales. En el uso
normal del sistema no hace falta: `database.py` hace este trabajo solo en el
primer arranque.
