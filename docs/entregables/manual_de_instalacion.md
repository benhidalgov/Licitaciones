# Manual de Instalacion

**Proyecto:** Copilot de Licitaciones y Operaciones Hoteleras
**Repositorio:** https://github.com/benhidalgov/Licitaciones

Este manual describe como instalar el sistema desde cero, tanto en una
estacion de trabajo local (desarrollo o uso interno) como en el servidor de
produccion (Render). Para el uso diario de la interfaz ver
`docs/MANUAL_DE_USO.md`; para el entorno de desarrollo ver
`ambiente_de_desarrollo.md`.

---

## 1. Requisitos del sistema

| Requisito | Minimo | Observacion |
| :--- | :--- | :--- |
| Sistema operativo | Windows 10 / 11, Linux o macOS | Instrucciones detalladas para Windows |
| Python | 3.10 o superior | Verificado en Python 3.12 (`python --version`) |
| Git | Cualquiera | Para clonar el repositorio |
| Navegador | Edge, Chrome, Firefox o Safari | El sistema es 100% web |
| Disco | ~100 MB | Codigo + entorno virtual + base de datos |
| Conexion a internet | Solo para clonar y para sincronizar con Mercado Publico | El resto funciona sin red |

No se necesita servidor de base de datos: SQLite viene con Python y el
archivo `licitaciones.db` se crea solo.

## 2. Instalacion local (paso a paso)

### Paso 1: Obtener el codigo

```powershell
cd C:\
git clone https://github.com/benhidalgov/Licitaciones.git
cd Licitaciones
```

### Paso 2: Crear el entorno virtual

```powershell
python -m venv env
```

En Windows, si el sistema bloquea la activacion con un error de politica
de ejecucion, ejecute primero:

```powershell
Set-ExecutionPolicy -Scope Process RemoteSigned
```

Luego active el entorno:

```powershell
env\Scripts\Activate.ps1
```

En Linux o macOS: `source env/bin/activate`.

> La terminal muestra `(env)` al inicio de la linea. Si no lo muestra, el
> entorno no esta activo y los siguientes comandos usarian Python del
> sistema.

### Paso 3: Instalar las dependencias

```powershell
pip install -r requirements.txt
```

Instala Flask (web), openpyxl (Excel), gunicorn (solo produccion) y tzdata
(zona horaria de Chile).

### Paso 4: Configurar las variables de entorno

```powershell
Copy-Item .env.example .env
```

Edite `.env` con el bloc de notas:

| Variable | Valor inicial | Recomendacion |
| :--- | :--- | :--- |
| `MERCADO_PUBLICO_TICKET` | `TU_TICKET_AQUI` | Pegue su ticket real de api.mercadopublico.cl para poder sincronizar |
| `FLASK_SECRET_KEY` | vacio | En local basta vacio; para exponer el sistema genere una con `python -c "import secrets; print(secrets.token_hex(32))"` |
| `PORT` | `5000` | Cambie si el puerto ya esta en uso |

El archivo `.env` esta en `.gitignore`: nunca se sube al repositorio.

### Paso 5: Primera ejecucion

```powershell
python run.py
```

En el primer arranque el sistema crea y siembra la base de datos
`licitaciones.db` (9 licitaciones, 17 salones, 8 reservas de ejemplo). La
ventana de la consola muestra:

```text
  Punto de Acceso Web: http://127.0.0.1:5000
[INFO] Servidor web iniciado. Presione CTRL+C para detener.
```

### Paso 6: Verificar la instalacion

1. Abra el navegador en `http://127.0.0.1:5000` (se redirige al login).
2. Ingrese con un usuario demo: `daniela` / `daniela123` (o `francisca`,
   `mari`, `admin` con clave igual al nombre + `123`).
3. Comprueba que el tablero carga con licitaciones y el boton
   "Sincronizar Mercado Publico".
4. (Opcional) Ejecute la suite de pruebas — debe terminar en verde:

```powershell
python -m pytest
```

Resultado esperado: `230 passed`.

Para detener el servidor: `CTRL+C` en la terminal.

## 3. Instalacion en produccion (Render)

1. **Cuenta y repositorio:** cree una cuenta en https://render.com y
   conecte el repositorio de GitHub del proyecto.
2. **Nuevo Web Service** desde el repositorio, con estos datos:
   * **Runtime:** Python 3
   * **Build Command:** `pip install -r requirements.txt`
   * **Start Command:**

```text
gunicorn wsgi:app --bind 0.0.0.0:$PORT --worker-class gthread --workers 1 --threads 4 --timeout 120
```

3. **Variables de entorno** (panel del servicio):

| Variable | Obligatoria | Valor |
| :--- | :---: | :--- |
| `FLASK_SECRET_KEY` | Si | Generada con `python -c "import secrets; print(secrets.token_hex(32))"` |
| `FLASK_COOKIE_SECURE` | Si | `1` (cookies solo por HTTPS) |
| `LICITACIONES_PASSWORD_ADMIN` | Si | Clave real del usuario admin |
| `LICITACIONES_PASSWORD_DANIELA` | Si | Clave real de Daniela |
| `LICITACIONES_PASSWORD_FRANCISCA` | Si | Clave real de Francisca |
| `LICITACIONES_PASSWORD_MARI` | Si | Clave real de Mari |
| `MERCADO_PUBLICO_TICKET` | Si | Ticket de la API |
| `LICITACIONES_DB_PATH` | Si | Ruta dentro del disco persistente, por ejemplo `/var/data/licitaciones.db` |

   El arranque falla a proposito si `FLASK_SECRET_KEY` falta o si las
   claves siguen siendo las demo: es una proteccion, no un error.

4. **Disco persistente:** cree un disco en Render y montelo en la raiz del
   proyecto (por ejemplo `/var/data`) para que `licitaciones.db` sobreviva
   a los redespliegues. Sin disco, cada despliegue empieza con la base
   sembrada de fabrica.
5. **Verificacion:** abra la URL pública de Render, ingrese con un usuario
   y confirme que el tablero carga. La primera sincronizacion tarda hasta
   unos minutos segun la semana consultada (corre en segundo plano y avisa
   al terminar).

## 4. Actualizacion a una nueva version

```powershell
git pull
pip install -r requirements.txt
python -m pytest
python run.py
```

La base de datos se conserva: `init_db` agrega columnas nuevas
automaticamente y no borra datos existentes. Ejecute los tests antes de
usar la version nueva; si estan en verde, la actualizacion esta lista.

## 5. Desinstalacion

1. Cierre el servidor (`CTRL+C`).
2. Borre la carpeta del proyecto completa (incluye `env/` y
   `licitaciones.db`).
3. Si definio `LICITACIONES_DB_PATH` apuntando fuera de la carpeta, borre
   tambien ese archivo.

No queda nada instalado en el sistema: el proyecto no escribe en el
registro de Windows ni instala servicios.

## 6. Solucion de problemas

| Sintoma | Causa | Solucion |
| :--- | :--- | :--- |
| `python` no se reconoce | Python no esta en el PATH | Reinstale Python marcando "Add python.exe to PATH" |
| `Activate.ps1` bloqueado por politica de ejecucion | Politica de PowerShell | `Set-ExecutionPolicy -Scope Process RemoteSigned` |
| `error: externally-managed-environment` | pip del sistema sin entorno | Active primero el entorno virtual (`env\Scripts\Activate.ps1`) |
| `Configure FLASK_SECRET_KEY en las variables de entorno` | Arranque de produccion sin la clave | Defina `FLASK_SECRET_KEY` (obligatoria fuera de local) |
| `Cambie las claves demo con LICITACIONES_PASSWORD_<USUARIO>` | Arranque con claves de ejemplo | Defina las cuatro claves reales por usuario |
| `OSError: [Errno 98] Address already in use` | Puerto 5000 ocupado | Cambie `PORT` en `.env` o cierre el proceso que lo usa |
| Sincronizacion responde HTTP 429 | Demasiadas consultas a la API | Suba `MERCADO_PUBLICO_INTERVALO_MS` a 700-1000 en `.env` y repita |
| Sincronizacion sugiere revisar el ticket | Ticket invalido o expirado | Verifique `MERCADO_PUBLICO_TICKET` en .env |
| El login responde 429 aunque la clave sea correcta | Intentos fallidos recientes | Espere 5 minutos (ventana de bloqueo) |
| La pagina se ve sin estilos | Falta `static/tailwind.css` | Restaure el archivo desde Git (esta versionado) |
| Los tests escriben en la base real | Nunca deberia ocurrir | Las pruebas usan BD temporales; si ocurre, verifique que no cambio `LICITACIONES_DB_PATH` en el entorno |

## 7. Documentos relacionados

| Documento | Contenido |
| :--- | :--- |
| `docs/MANUAL_DE_USO.md` | Manual operativo para el equipo comercial |
| `docs/entregables/ambiente_de_desarrollo.md` | Detalle del entorno de desarrollo |
| `docs/entregables/plan_de_pruebas.md` | Estrategia y casos de prueba |
| `docs/WORKFLOW.md` | Flujo de trabajo Git y validacion previa a cada entrega |
