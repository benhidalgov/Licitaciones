# Task 2: Modulo de Autenticacion y Rutas Base en Flask

## Files:
- Create / Modify: `app.py`
- Create: `templates/base.html`
- Create: `templates/login.html`
- Test: `tests/test_auth.py`

## Interfaces:
- Consumes: `database.py` (`init_db`, `get_db_connection`)
- Produces:
  - `app`: instancia Flask
  - `@login_required`: decorador de proteccion de rutas
  - `GET /login` y `POST /login`: credenciales fijas para demo (`admin` / `admin123`)
  - `GET /logout`: limpieza de sesion
  - `GET /` y `GET /licitaciones`: ruta protegida con `@login_required` que renderiza una vista dashboard basica (que sera expandida en la Tarea 3)

## Global Constraints:
- Arquitectura 100% Web en Python (Flask).
- Supresion total y absoluta de emojis en templates, mensajes flash, formularios, botones y logs.
- Estilo corporativo formal y sobrio: paleta de colores azul marino (`#0F172A`, `#1E293B`, `#2563EB`), fondo pizarra suave (`#F8FAFC`), tipografia sans-serif limpia.
- Tailwind CSS cargado via CDN en `templates/base.html`.
- Formulario de login incluye cuadro formal con las credenciales demo: Usuario: `admin` | Contrasena: `admin123`.
- No subagents: haz todo el trabajo tu mismo.

## Pasos:
1. Crear `tests/test_auth.py` y ejecutarlo para comprobar que falle.
2. Crear `templates/base.html` y `templates/login.html`.
3. Implementar `app.py` con Flask, sesiones, `@login_required`, `/login`, `/logout` y ruta protegida inicial `/` (dashboard).
4. Ejecutar `python -m unittest tests/test_auth.py` y asegurar que todas las pruebas pasen.
5. Escribir reporte en `.superpowers/sdd/2026-09-15-auth-crud-prototype/task-2-report.md`.
6. Hacer commit en git: `feat: modulo de autenticacion corporativa y plantillas base`.
