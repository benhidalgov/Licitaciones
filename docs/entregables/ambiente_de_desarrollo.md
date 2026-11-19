# Implementacion del Ambiente de Desarrollo

**Proyecto:** Copilot de Licitaciones y Operaciones Hoteleras
**Institucion:** Hotel Plaza San Francisco — Programa de Vinculacion con el Medio (VcM) DUOC UC
**Repositorio:** https://github.com/benhidalgov/Licitaciones

---

## 1. Descripcion general del sistema

Aplicacion web para la prospeccion comercial de licitaciones publicas de
Chile (Mercado Publico), control preventivo de costos, verificacion de
aforo y agenda de salones del hotel.

| Componente | Tecnologia |
| :--- | :--- |
| Lenguaje | Python 3.10 o superior |
| Framework web | Flask 3.0 |
| Base de datos | SQLite 3 (archivo unico `licitaciones.db`) |
| Cliente de API | `urllib` de la biblioteca estandar (sin dependencia extra) |
| Excel | openpyxl |
| Servidor en produccion | Gunicorn (worker gthread) sobre Render |

## 2. Requisitos previos

* Python 3.10 o superior (`python --version`)
* `pip` incluido en la instalacion de Python
* Git (para clonar el repositorio)
* Cuenta en https://api.mercadopublico.cl para obtener el ticket de API
  (opcional para desarrollo sin sincronizacion)

## 3. Creacion del entorno virtual

Se crea una carpeta `env/` aislada con las dependencias del proyecto.

En Windows (PowerShell):

```powershell
python -m venv env
env\Scripts\Activate.ps1
```

En Linux o macOS:

```bash
python3 -m venv env
source env/bin/activate
```

## 4. Instalacion de dependencias

Con el entorno virtual activado:

```bash
pip install -r requirements.txt
```

Dependencias instaladas:

| Paquete | Para que sirve |
| :--- | :--- |
| `flask` | Framework web |
| `gunicorn` | Servidor WSGI en produccion (Render) |
| `openpyxl` | Lectura del historial de OC en `.xlsx` y exportacion a Excel |
| `tzdata` | Zona horaria de Chile para las fechas de informes y cierres |

## 5. Configuracion de variables de entorno

Se copia la plantilla y se edita el archivo `.env` en la raiz del repositorio
(nunca se versiona; esta en `.gitignore`):

```powershell
Copy-Item .env.example .env
```

| Variable | Obligatoria | Descripcion |
| :--- | :---: | :--- |
| `MERCADO_PUBLICO_TICKET` | No (si) | Ticket oficial de la API de Mercado Publico |
| `MERCADO_PUBLICO_INTERVALO_MS` | No | Milisegundos minimos entre consultas (500 por defecto) |
| `FLASK_SECRET_KEY` | Si (en produccion) | Firma de sesiones; se genera con `python -c "import secrets; print(secrets.token_hex(32))"` |
| `LICITACIONES_PASSWORD_ADMIN` / `_DANIELA` / `_FRANCISCA` / `_MARI` | Si (en produccion) | Claves reales por usuario; el arranque falla si siguen siendo las demo |
| `PORT` / `HOST` | No | Puerto y host del servidor local (5000 / 127.0.0.1) |
| `LICITACIONES_DB_PATH` | No | Ruta alternativa de la base de datos |
| `RESUMEN_IA_API_KEY` / `_MODELO` / `_URL` | No | Enriquecimiento del resumen con IA; sin llave el sistema usa reglas deterministicas |

En produccion (Render) estas variables se configuran en el panel del
servicio, no en un archivo `.env`.

## 6. Base de datos

* SQLite no necesita servidor: al primer arranque se crea el archivo
  `licitaciones.db` junto al codigo, con las 6 tablas y los datos semilla.
* El esquema y la carga inicial estan en `database.py` (`init_db`).
* Para regenerar una base limpia de cero: cerrar el servidor, borrar
  `licitaciones.db` y arrancar de nuevo.
* El script equivalente en SQL puro esta en
  `docs/entregables/script_poblar_tablas.sql`.

## 7. Ejecucion local

```bash
python run.py
```

El servidor queda en `http://127.0.0.1:5000` (o el puerto indicado en
`PORT`). Usuarios de demo (solo local): `daniela`, `francisca`, `mari`,
`admin` con clave igual al nombre + `123`.

## 8. Ejecucion de pruebas

```bash
python -m pytest
```

Suite de 230 pruebas: autenticacion, base de datos, logica financiera,
prevencion de colisiones, integracion con Mercado Publico y verificacion de
cero emojis. Los tests usan bases SQLite temporales y nunca tocan
`licitaciones.db` ni `.env`.

## 9. Despliegue en produccion (Render)

* Punto de entrada WSGI: `wsgi.py` (valida que exista `FLASK_SECRET_KEY`
  y que las claves demo hayan sido reemplazadas antes de arrancar).
* **Start Command** en Render:

```text
gunicorn wsgi:app --bind 0.0.0.0:$PORT --worker-class gthread --workers 1 --threads 4 --timeout 120
```

* Disco persistente montado en la raiz del proyecto para conservar
  `licitaciones.db` entre reinicios.
* El trafico llega tras el proxy de Render; la aplicacion usa `ProxyFix`
  para leer la IP real de cada cliente (control de intentos de login).

## 10. Estructura del repositorio

```text
app.py               Controlador Flask (rutas, auth, exportaciones)
database.py          Esquema SQLite, consultas, semilla y reglas de negocio
mercado_publico.py   Cliente de la API de ChileCompra / Mercado Publico
resumen.py           Ficha resumen por reglas (IA opcional)
run.py               Arranque local
wsgi.py              Punto de entrada para Gunicorn/Render
requirements.txt     Dependencias
.env.example         Plantilla de variables de entorno
templates/           Plantillas Jinja2
static/              Estilos Tailwind compilados
tests/               Suite de pruebas (pytest)
docs/                Manual de uso, workflow de Git y entregables
```
