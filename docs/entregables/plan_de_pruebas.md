# Plan de Pruebas

**Proyecto:** Copilot de Licitaciones y Operaciones Hoteleras
**Repositorio:** https://github.com/benhidalgov/Licitaciones
**Suite actual:** 230 pruebas automatizadas — todas en verde (0 fallos)

---

## 1. Objetivo y alcance

Verificar que el sistema cumple sus reglas de negocio y no introduce
regresiones antes de cada entrega:

* Autenticacion y control de acceso.
* Integridad de datos en SQLite (esquema, claves, transacciones).
* Reglas comerciales: embudo, costeo minimo, descartes, priorizacion.
* Agenda de salones: aforo y prevencion de doble reserva.
* Integracion con la API de Mercado Publico (simulada en los tests).
* Exportaciones (CSV/Excel) seguras para Excel.
* Requisitos transversales: cero emojis, hora de Chile, CSRF.

**Fuera de alcance (seccion 11):** pruebas de carga, pruebas contra la API
real de Mercado Publico y validacion visual del navegador.

## 2. Estrategia

* Enfoque **Test-Driven Development**: los tests se escriben junto con cada
  funcionalidad y son la condicion de aceptacion de la rama `main`.
* Nivel **funcional de caja negra** para las rutas: se invoca la aplicacion
  Flask con su `test_client` (peticiones HTTP reales, sin levantar servidor).
* Nivel **unitario/integracion** para la capa de datos: se ejercitan las
  funciones de `database.py` directamente sobre una base SQLite de prueba.
* **Sin red:** todas las llamadas a la API de Mercado Publico se simulan
  con `unittest.mock`; ningun test depende de internet ni de un ticket real.

## 3. Ambiente y datos de prueba

| Elemento | Valor |
| :--- | :--- |
| Runner | `python -m pytest` (tambien compatible con `python -m unittest`) |
| Entorno | Entorno virtual `env/` con `requirements.txt` |
| Base de datos | SQLite temporal por archivo de test (`test_*_licitaciones.db`), creada en `setUp` y borrada en `tearDown` |
| Aislamiento | Nunca se toca `licitaciones.db` ni el archivo `.env` |
| Usuarios demo | `admin`, `daniela`, `francisca`, `mari` (claves de prueba locales) |
| Datos semilla | 9 licitaciones, 17 salones, 8 reservas (cargados por `init_db`) |
| Duracion | ~13 segundos para la suite completa |

## 4. Tipos de prueba y distribucion

| Tipo | Archivos de prueba | Pruebas | Que cubre |
| :--- | :--- | ---: | :--- |
| Autenticacion y seguridad | `test_auth.py`, `test_security.py` | 16 | Login, sesiones, CSRF, bloqueo por intentos fallidos, token en formularios |
| Base de datos | `test_database.py`, `test_validation.py` | 29 | CRUD, filtros, claves foraneas, marcas de hora de Chile, cierres automaticos |
| Agenda de salones | `test_salones.py` | 25 | Catalogo, aforos, colisiones de fechas al crear y al editar, montajes |
| Evaluacion comercial | `test_evaluacion.py` | 18 | Costo minimo, descarte por presupuesto, decisiones, exportaciones CSV/Excel |
| Detalle de licitacion | `test_detail.py` | 31 | Ficha, bloques plegados, match de salones por capacidad, documentos |
| Mercado Publico | `test_mercado_publico.py` | 33 | Filtros, clasificacion, rate limit y reintentos 429/503, mensajes de error |
| Tablero y rutas | `test_dashboard.py`, `test_routes.py` | 37 | Filtros, paginacion, metricas, sincronizacion en segundo plano |
| Informes | `test_informes.py` | 10 | Reportes por periodo, clientes clave, cierre de embudo |
| Bonus / reglas extra | `test_bonus.py` | 21 | Priorizacion, margen de tolerancia, sellos, UTM |
| Operacion y arranque | `test_run.py`, `test_crud_flow.py` | 9 | Flujo completo de creacion/edicion/borrado, banner de arranque |
| Cumplimiento | `test_emoji_compliance.py` | 1 | Cero emojis en codigo, plantillas y documentacion |
| **Total** | **15 archivos** | **230** | |

## 5. Casos de prueba representativos

Cada caso esta automatizado en el archivo indicado.

| ID | Caso | Resultado esperado | Test |
| :--- | :--- | :--- | :--- |
| TC-01 | Login con credenciales correctas | Sesion iniciada, redireccion al tablero | `test_auth` |
| TC-02 | 5 logins fallidos desde la misma IP | Sexto intento responde HTTP 429 (bloqueo de 5 min) | `test_security` |
| TC-03 | POST sin token CSRF | HTTP 400, la accion no se ejecuta | `test_security` |
| TC-04 | Segunda reserva confirmada en un slot ocupado (crear) | Se rechaza con mensaje de conflicto | `test_salones` |
| TC-05 | Mover una reserva a un slot ocupado (editar) | Se rechaza: `update_reserva` devuelve colision dentro de la transaccion | `test_salones` |
| TC-06 | Evaluacion con asistentes que superan el presupuesto | Se descarta automatica con motivo `Precio` | `test_evaluacion` |
| TC-07 | Titulo que empieza con `=` en la exportacion CSV | La celda viaja con comilla inicial (no es formula) | `test_evaluacion` |
| TC-08 | Mismo titulo en la exportacion Excel | Celda guardada como texto, sin celdas de tipo formula | `test_evaluacion` |
| TC-09 | API responde 429 de forma persistente | Reintentos con backoff, aviso con `MERCADO_PUBLICO_INTERVALO_MS` | `test_mercado_publico` |
| TC-10 | API responde 401 (ticket malo) | El mensaje sugiere revisar el ticket, no el intervalo | `test_mercado_publico` |
| TC-11 | Guardar nota/historial por la tarde | Marca de hora con hora de Chile, no UTC | `test_database`, `test_evaluacion` |
| TC-12 | Sincronizar | La peticion responde de inmediato; el resultado se muestra en la siguiente carga del tablero | `test_dashboard` |
| TC-13 | Dos sincronizaciones simultaneas | La segunda recibe "ya hay una sincronizacion en curso" | `test_dashboard` |
| TC-14 | Asistentes por encima del aforo del salon | Se rechaza la reserva o se sugiere otro montaje | `test_salones`, `test_detail` |
| TC-15 | Cualquier archivo con emojis | La suite falla (`test_emoji_compliance`) | `test_emoji_compliance` |
| TC-16 | Licitacion con fecha de cierre pasada | Pasa a estado `Cerrada` al entrar al tablero | `test_database` |
| TC-17 | Ruta protegida sin sesion | Redireccion a `/login` | `test_auth` |
| TC-18 | Arranque con claves demo en produccion (`wsgi.py`) | El arranque falla con error claro | `test_run` |

## 6. Pruebas no funcionales y de seguridad

| Area | Estado | Como se verifica |
| :--- | :---: | :--- |
| CSRF en todos los POST | Automatica | `test_security` |
| Bloqueo de fuerza bruta en login | Automatica | `test_security` |
| Cookies de sesion `HttpOnly` / `SameSite` | Configuracion | Valores fijados en `app.py` (`SESSION_COOKIE_HTTPONLY`, `SameSite=Lax`); sin test automatizado |
| Cabeceras de seguridad | Automatica | `X-Frame-Options: DENY` y `X-Content-Type-Options: nosniff` verificadas en `test_dashboard`; `Referrer-Policy` fijada en `app.py` |
| SQL parametrizado (sin inyeccion) | Revision de codigo | Todas las consultas usan parametros `?`; `test_validation` verifica integridad y claves foraneas |
| XSS | Por framework | Jinja2 escapa por defecto; no se usan filtros `|safe` en plantillas (verificado por revision) |
| Limite de subida (16 MB) | Configuracion | `MAX_CONTENT_LENGTH` en `app.py`; exceso responde HTTP 413 |
| Cero emojis | Automatica | `test_emoji_compliance` |
| Hora de Chile en marcas de tiempo | Automatica | `test_database`, `test_evaluacion` |

## 7. Datos de prueba

* **Semilla oficial:** 9 licitaciones (una con presupuesto insuficiente, una
  con discrepancia de ID, etc.), 17 salones del catalogo del hotel y 8
  reservas con un conflicto de fechas ya existente para probar deteccion.
* **Aislamiento:** cada archivo de test crea y borra su propia base
  `test_*_licitaciones.db`; ninguna prueba escribe en la base de produccion.
* **Externo simulado:** las respuestas de la API de Mercado Publico son
  JSON fijos dentro de los tests (429, 401, fichas, listados).

## 8. Criterios de aceptacion

1. `python -m pytest` termina con codigo de salida 0 y **230/230** pruebas
   en verde.
2. Ninguna prueba toca `licitaciones.db` ni `.env`.
3. Cero emojis en el repositorio (TC-15).
4. Todo cambio en `main` paso por la validacion del Paso 4 de
   `docs/WORKFLOW.md` antes del push.

## 9. Proceso de regresion

| Momento | Accion |
| :--- | :--- |
| Cada cambio local | `python -m pytest` antes de commitear |
| Antes de fusionar a `main` | Validacion obligatoria (WORKFLOW Paso 4) |
| Despues de cada merge | `git pull` y suite completa en `main` |
| Proximo paso recomendado | Integrar el mismo comando en CI (GitHub Actions) para que corra en cada Pull Request |

## 10. Verificaciones manuales (smoke test)

Antes de un despliegue, recorrer a mano en el navegador:

1. Login con `daniela` y logout.
2. Abrir una licitacion, agregar una nota y verla en el historial con la
   hora correcta.
3. Exportar el listado a CSV y a Excel y abrirlos en Excel.
4. Crear una reserva y intentar crear otra superpuesta (debe rechazar).
5. Presionar "Sincronizar Mercado Publico" y comprobar que el tablero
   responde de inmediato y luego muestra el resultado.
6. Revisar que el dashboard muestra la hora y fechas de hoy.

## 11. Limites del plan

* No se ejecutan pruebas de carga ni de rendimiento (el uso esperado es un
  equipo de 4 personas).
* La sincronizacion real contra la API de Mercado Publico no se prueba en
  la suite (se simula); se valida una vez en produccion con un ticket valido.
* No hay pruebas automatizadas de renderizado visual (el HTML se verifica
  por presencia de elementos clave, no por capturas).
* El comportamiento tras el proxy de Render (IP real del cliente) se
  verifico con `ProxyFix` en codigo, pero su confirmacion final es manual
  en produccion.
