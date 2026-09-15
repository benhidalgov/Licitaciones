# Task 3: Dashboard de Licitaciones, Metricas del Embudo y Filtros

## Files:
- Modify: `app.py`
- Modify / Expand: `templates/dashboard.html`
- Create: `tests/test_dashboard.py`

## Interfaces:
- Consumes:
  - `database.get_all_licitaciones(categoria=None, modalidad=None, estado=None, q=None)`
  - `database.get_funnel_metrics()`
  - `@login_required`
- Produces:
  - Rutas `GET /` y `GET /licitaciones`:
    - Gestiona filtros `categoria`, `modalidad`, `estado`, `q`.
    - Provee filtro/helper para formatear montos en CLP (ej. `$5.800.000 CLP`).
    - Renderiza `templates/dashboard.html` con metricas, licitaciones y filtros activos.
  - Plantilla `templates/dashboard.html`:
    - Tarjetas de resumen del Embudo de Conversion (Total Identificadas, Calificadas, Participadas, Adjudicadas, Compra Agil).
    - Barra de filtros interactiva con selectores y busqueda textual.
    - Boton "Registrar Nueva Licitacion" (apuntando a `/licitaciones/nueva`).
    - Tabla corporativa completa con indicadores de viabilidad presupuestaria (alerta si costo base > presupuesto mandante), validacion robusta (ID Verificado vs Discrepancia ID) y estado del embudo.
    - Columnas de accion con enlaces a "Ver Detalle", "Editar" y "Eliminar".

## Global Constraints:
- Arquitectura 100% Web en Python (Flask).
- Supresion total y absoluta de emojis en templates, botones, badges, mensajes y logs.
- Diseno corporativo formal en tonos azul marino, gris pizarra y acentos sobrios con Tailwind CDN.
- No subagents: haz todo el trabajo tu mismo.

## Pasos:
1. Crear `tests/test_dashboard.py` con pruebas para metricas, filtros y busqueda, y verificar fallo inicial.
2. Actualizar `app.py` integrando `database.get_all_licitaciones`, `database.get_funnel_metrics` y formateador de montos en CLP.
3. Actualizar `templates/dashboard.html` con las tarjetas del embudo, barra de filtros, tabla y badges de reglas de negocio.
4. Ejecutar `python -m unittest tests/test_dashboard.py` y suite completa `python -m unittest discover tests`.
5. Escribir reporte en `.superpowers/sdd/2026-09-15-auth-crud-prototype/task-3-report.md`.
6. Hacer commit en git: `feat: tablero principal con embudo comercial, filtros y tabla de licitaciones`.
