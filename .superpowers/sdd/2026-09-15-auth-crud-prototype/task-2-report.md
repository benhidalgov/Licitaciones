# Reporte de Implementacion - Tarea 2: Modulo de Autenticacion y Rutas Base en Flask

## Estado: DONE
- **Fecha:** 2026-09-15
- **Commit:** Pendiente de hash inmediato (`feat: modulo de autenticacion corporativa y plantillas base`)
- **Resumen de Pruebas:** 7 pruebas ejecutadas en `tests/test_auth.py` aprobadas (0.145s); 17 pruebas totales del repositorio aprobadas (0.222s).
- **Preocupaciones / Bloqueos:** Ninguno.

---

## Archivos Creados y Modificados
1. `app.py`: Aplicacion principal en Flask con configuracion de clave secreta, gestion nativa de sesion de usuario, decorador `@login_required`, endpoints de autenticacion (`/login`, `/logout`) y rutas base protegidas (`/` y `/licitaciones`).
2. `templates/base.html`: Plantilla base corporativa y formal construida con Tailwind CSS cargado via CDN. Incluye cabecera institucional "Hotel Plaza San Francisco | DUOC UC", barra de navegacion condicional al estado de sesion, bloque estandarizado de alertas flash (errores, alertas informativas y exito) y pie de pagina corporativo.
3. `templates/login.html`: Formulario de inicio de sesion con diseno sobrio en tonos azul marino y pizarra, inputs formales y cuadro destacado con las credenciales demo visibles (`admin` / `admin123`).
4. `templates/dashboard.html`: Vista protegida inicial del panel de control que sirve como punto de aterrizaje tras el login, preparada para la expansion completa en la Tarea 3.
5. `tests/test_auth.py`: Suite de 7 pruebas unitarias que verifican redirecciones no autenticadas, despliegue de credenciales demo, rechazo de credenciales erroneas con mensajes flash, inicio de sesion exitoso hacia el panel de control, acceso a rutas protegidas y cierre de sesion.

---

## Interfaces Implementadas en `app.py`
- `app`: Instancia central de Flask configurada con `secret_key = "licitaciones-secret-key-2026"`.
- `DEMO_USER = "admin"` y `DEMO_PASS = "admin123"`: Credenciales fijas para demostracion ejecutiva.
- `@login_required`: Decorador funcional que valida la existencia de la clave `"user"` en la sesion de Flask. Redirige a `/login` si el usuario no esta autenticado.
- `GET /login`: Renderiza el formulario corporativo con el panel informativo de credenciales demo.
- `POST /login`: Valida usuario y contrasena contra las credenciales demo. Si es correcto, establece `session["user"]` y redirige al dashboard. Si es incorrecto, envia mensaje flash de error formal ("Credenciales invalidas...") y vuelve a renderizar el formulario.
- `GET /logout`: Elimina la sesion activa del usuario y redirige a la pantalla de login con mensaje flash informativo.
- `GET /` y `GET /licitaciones`: Rutas protegidas mediante `@login_required` que renderizan el dashboard principal con el usuario autenticado.

---

## Verificacion y Resultados de Pruebas
Comando ejecutado:
`python -m unittest tests/test_auth.py`

Salida:
```text
.......
----------------------------------------------------------------------
Ran 7 tests in 0.145s

OK
```

Suite integral del proyecto:
`python -m unittest discover tests`

Salida:
```text
.................
----------------------------------------------------------------------
Ran 17 tests in 0.222s

OK
```

Detalle de casos de prueba en `tests/test_auth.py`:
- `test_redirect_to_login_when_unauthenticated`: Verifica que peticiones no autenticadas a `/` sean redirigidas con codigo 302 a `/login`.
- `test_licitaciones_route_redirect_to_login_when_unauthenticated`: Verifica que peticiones no autenticadas a `/licitaciones` sean redirigidas a `/login`.
- `test_login_page_renders_demo_credentials`: Verifica que la pagina de login contenga visibles las credenciales demo `admin` y `admin123`, ademas del texto `Iniciar Sesion`.
- `test_login_failure_invalid_credentials`: Verifica el rechazo de credenciales invalidas y el despliegue del mensaje flash respectivo.
- `test_login_success`: Verifica la autenticacion exitosa y redireccion al `Panel de Control` con codigo 200.
- `test_licitaciones_accessible_when_authenticated`: Verifica el acceso a la ruta `/licitaciones` tras autenticarse.
- `test_logout`: Verifica el cierre de sesion efectivo y el retorno al formulario de login.

---

## Cumplimiento de Restricciones Globales
- **Arquitectura 100% Web en Python (Flask):** Interaccion pura a traves de navegador web con plantillas Jinja2 y servidor Flask.
- **Supresion total y absoluta de emojis:** Verificado de manera automatizada en templates, flash messages, botones, codigo y logs (0 emojis encontrados).
- **Diseno corporativo sobrio:** Paleta cromatica ejecutiva en azul marino (`#0F172A`, `#1E293B`, `#2563EB`) y pizarra suave (`#F8FAFC`), tipografia sans-serif limpia, componentes estilizados con Tailwind CSS CDN.
- **Credenciales demo visibles:** Cuadro informativo en el login indicando claramente Usuario: `admin` | Contrasena: `admin123`.
- **Ejecucion autonoma:** Sin uso de subagentes.
