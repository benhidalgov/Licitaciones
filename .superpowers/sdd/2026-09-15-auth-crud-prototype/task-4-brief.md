# Task 4: Ficha de Detalle de Licitacion (TDR, Admisibilidad y Control de Costos)

## Files:
- Modify: `app.py`
- Create: `templates/detail.html`
- Create: `tests/test_detail.py`

## Interfaces:
- Consumes:
  - `database.get_licitacion_by_id(id_licitacion)`
  - `database.update_licitacion(id_licitacion, data)`
  - `@login_required`
- Produces:
  - Ruta `GET /licitaciones/<id_licitacion>`:
    - Retorna codigo 404 si la licitacion no existe.
    - Renderiza `templates/detail.html` con todos los datos y calculos de viabilidad.
  - Ruta `POST /licitaciones/<id_licitacion>/cambiar_estado`:
    - Actualiza el estado en el embudo y redirige con mensaje flash formal.
  - Plantilla `templates/detail.html`:
    - Resumen ejecutivo, panel de control presupuestario preventivo con alertas formales.
    - Panel de validacion robusta (cruce de ID con adjuntos).
    - Checklist de admisibilidad administrativa formal (Anexo 4, Escrituras, Poderes, Vigencias).
    - Selector rapido de transicion de estado en el embudo.
    - Botones de navegacion: Volver al Dashboard, Editar, Eliminar.

## Global Constraints:
- Arquitectura 100% Web en Python (Flask).
- Supresion total y absoluta de emojis en templates, botones, badges, mensajes y logs.
- Diseno corporativo formal en tonos azul marino, gris pizarra y acentos sobrios con Tailwind CDN.
- No subagents: haz todo el trabajo tu mismo.

## Pasos:
1. Crear `tests/test_detail.py` con pruebas para visualizacion 200, 404 y cambio rapido de estado.
2. Implementar rutas en `app.py`.
3. Crear `templates/detail.html` respetando diseno corporativo y sin emojis.
4. Ejecutar `python -m unittest tests/test_detail.py` y suite completa `python -m unittest discover tests`.
5. Escribir reporte en `.superpowers/sdd/2026-09-15-auth-crud-prototype\task-4-report.md`.
6. Hacer commit en git: `feat: ficha de detalle con control presupuestario y checklist de admisibilidad`.
