# Task 1: Configuracion del Entorno y Modulo de Base de Datos (SQLite)

## Files:
- Create: `database.py`
- Test: `tests/test_database.py`

## Interfaces:
- Produces:
  - `init_db()`: inicializa el esquema en `licitaciones.db` si no existe y carga licitaciones de prueba iniciales.
  - `get_db_connection()`: retorna una conexion sqlite3 con `row_factory = sqlite3.Row`.
  - `get_all_licitaciones(categoria=None, modalidad=None, estado=None, q=None)` -> List[dict]
  - `get_licitacion_by_id(id_licitacion)` -> Optional[dict]
  - `create_licitacion(data)` -> str (id_licitacion)
  - `update_licitacion(id_licitacion, data)` -> bool
  - `delete_licitacion(id_licitacion)` -> bool
  - `get_funnel_metrics()` -> dict con conteos por estado (Identificada, Calificada, Participada, Adjudicada, Descartada, Compra Agil, Total)

## Global Constraints:
- Sin emojis en ningun mensaje, comentario, log o dato.
- Base de datos SQLite local (`licitaciones.db`).
- Soporte para parametrizar `DB_NAME` en tests (`test_licitaciones.db`).
- Minimo 8 registros iniciales de prueba (seed data) que reflejen:
  - Alojamiento y Eventos/Catering.
  - Compra Agil (<= 6.900.000 CLP) y Licitaciones Publicas.
  - Alerta de costo base hotel > presupuesto mandante.
  - Discrepancia ID / Efecto ID.
  - Checklist de admisibilidad (Anexo 4, Escrituras, Poderes, Vigencias).

## Pasos:
1. Crear `tests/test_database.py` y correr la prueba (debe fallar).
2. Implementar `database.py` con `init_db`, metodos CRUD y `get_funnel_metrics`.
3. Ejecutar pruebas unitarias con `python -m unittest tests/test_database.py` y asegurar que pasen.
4. Escribir reporte en `.superpowers/sdd/2026-09-15-auth-crud-prototype/task-1-report.md`.
5. Hacer commit en git: `feat: modulo de base de datos sqlite y seed data de licitaciones`.
