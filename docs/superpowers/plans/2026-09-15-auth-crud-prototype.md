# Prototipo de Autenticacion y CRUD de Licitaciones - Plan de Implementacion

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Construir un prototipo web interactivo y ligero en Python (Flask) con autenticacion de usuario demo y un CRUD completo de licitaciones de prueba (Mercado Publico) que modele las reglas de negocio y restricciones operativas del Hotel Plaza San Francisco y DUOC UC.

**Architecture:** Aplicacion web con backend en Flask, renderizado de plantillas HTML con Jinja2 y Tailwind CSS (via CDN) para un diseno corporativo ejecutivo sobrio (azul marino, pizarra). Persistencia local con SQLite y carga automatica de datos de prueba representativos del embudo comercial, control preventivo de costos, validacion de adjuntos y checklist de admisibilidad administrativa.

**Tech Stack:** Python 3.12, Flask 3.1, SQLite3, Jinja2, Tailwind CSS (CDN), pytest / unittest.

**Spec:** [ESPECIFICACION_REQUERIMIENTOS.md](file:///C:/Licitaciones/ESPECIFICACION_REQUERIMIENTOS.md)

## Global Constraints

- Arquitectura 100% Web: la aplicacion se ejecuta como servidor local y se interactua exclusivamente desde el navegador. Prohibidos scripts de consola o ejecutables de escritorio para el usuario final.
- Supresion total de emojis: queda terminantemente prohibido el uso de emojis en interfaces, mensajes flash, botones, etiquetas, logs y codigo. El diseno debe ser sobrio y corporativo.
- Modelo de autenticacion simple para demostracion: usuario y contrasena fijos (por ejemplo `admin` / `admin123`) con gestion nativa de sesion en Flask.
- Reglas de negocio contempladas: categorias Alojamiento y Eventos/Catering, modalidad Compra Agil (tope 6.900.000 CLP), alerta presupuestaria preventiva (Costo Base Hotel > Presupuesto Mandante), validacion robusta de ID contra adjuntos y checklist de admisibilidad (Anexo 4, Escrituras, Poderes, Vigencias).

---

### Task 1: Configuracion del Entorno y Modulo de Base de Datos (SQLite)

**Files:**
- Create: `database.py`
- Test: `tests/test_database.py`

**Interfaces:**
- Produces:
  - `init_db()`: inicializa el esquema en `licitaciones.db` si no existe y carga licitaciones de prueba iniciales.
  - `get_db_connection()`: retorna una conexion sqlite3 con `row_factory = sqlite3.Row`.
  - `get_all_licitaciones(categoria=None, modalidad=None, estado=None, q=None)` -> List[dict]
  - `get_licitacion_by_id(id_licitacion)` -> Optional[dict]
  - `create_licitacion(data)` -> str (id_licitacion)
  - `update_licitacion(id_licitacion, data)` -> bool
  - `delete_licitacion(id_licitacion)` -> bool
  - `get_funnel_metrics()` -> dict con conteos por estado (Identificada, Calificada, Participada, Adjudicada, Descartada, Compra Agil)

- [ ] **Step 1: Escribir prueba unitaria para inicializacion y operaciones basicas de base de datos**

```python
# tests/test_database.py
import os
import unittest
import database

class TestDatabase(unittest.TestCase):
    def setUp(self):
        database.DB_NAME = "test_licitaciones.db"
        if os.path.exists(database.DB_NAME):
            os.remove(database.DB_NAME)
        database.init_db()

    def tearDown(self):
        if os.path.exists(database.DB_NAME):
            os.remove(database.DB_NAME)

    def test_seed_data_loaded(self):
        licitaciones = database.get_all_licitaciones()
        self.assertGreaterEqual(len(licitaciones), 8)

    def test_create_and_get_licitacion(self):
        nueva = {
            "id_licitacion": "9999-01-LP26",
            "titulo": "Servicio de Alojamiento Corporativo Test",
            "organismo": "Ministerio de Economia",
            "categoria": "Alojamiento",
            "modalidad": "Licitacion Publica",
            "region": "Region Metropolitana (Santiago)",
            "presupuesto_mandante": 15000000,
            "costo_base_hotel": 12000000,
            "estado_embudo": "Identificada",
            "validacion_adjuntos": "Valida",
            "tiene_anexo4": 1,
            "tiene_escrituras": 1,
            "tiene_poderes": 1,
            "tiene_vigencias": 1,
            "fecha_publicacion": "2026-09-10",
            "fecha_cierre": "2026-09-25",
            "descripcion_tdr": "Servicio de 50 habitaciones para delegacion oficial."
        }
        database.create_licitacion(nueva)
        item = database.get_licitacion_by_id("9999-01-LP26")
        self.assertIsNotNone(item)
        self.assertEqual(item["titulo"], "Servicio de Alojamiento Corporativo Test")

    def test_update_and_delete_licitacion(self):
        item = database.get_licitacion_by_id("1058-12-COT24")
        self.assertIsNotNone(item)
        database.update_licitacion("1058-12-COT24", {"estado_embudo": "Calificada"})
        updated = database.get_licitacion_by_id("1058-12-COT24")
        self.assertEqual(updated["estado_embudo"], "Calificada")
        
        database.delete_licitacion("1058-12-COT24")
        deleted = database.get_licitacion_by_id("1058-12-COT24")
        self.assertIsNone(deleted)

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Ejecutar prueba y verificar que falle por modulo ausente**

Run: `python -m unittest tests/test_database.py`
Expected: FAIL con `ModuleNotFoundError: No module named 'database'`

- [ ] **Step 3: Implementar `database.py` con esquema, seed data de 8-10 licitaciones realistas y metodos CRUD**

```python
# database.py
import sqlite3
import os

DB_NAME = "licitaciones.db"

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS licitaciones (
            id_licitacion TEXT PRIMARY KEY,
            titulo TEXT NOT NULL,
            organismo TEXT NOT NULL,
            categoria TEXT NOT NULL,
            modalidad TEXT NOT NULL,
            region TEXT NOT NULL,
            presupuesto_mandante INTEGER NOT NULL,
            costo_base_hotel INTEGER NOT NULL,
            estado_embudo TEXT NOT NULL,
            validacion_adjuntos TEXT NOT NULL,
            tiene_anexo4 INTEGER NOT NULL DEFAULT 1,
            tiene_escrituras INTEGER NOT NULL DEFAULT 1,
            tiene_poderes INTEGER NOT NULL DEFAULT 1,
            tiene_vigencias INTEGER NOT NULL DEFAULT 1,
            fecha_publicacion TEXT NOT NULL,
            fecha_cierre TEXT NOT NULL,
            descripcion_tdr TEXT
        )
    """)
    conn.commit()

    cursor.execute("SELECT COUNT(*) FROM licitaciones")
    count = cursor.fetchone()[0]
    if count == 0:
        seed_data = [
            (
                "1058-12-COT24",
                "Servicio de Banqueteria y Salones Jornada de Planificacion Estrategica",
                "Subsecretaria de Turismo",
                "Eventos / Catering",
                "Compra Agil",
                "Region Metropolitana (Santiago)",
                5800000,
                4200000,
                "Identificada",
                "Valida",
                1, 1, 1, 1,
                "2026-09-12", "2026-09-20",
                "Arriendo de salon plenario para 80 asistentes con servicio de coctel y coffee break continuo."
            ),
            (
                "723-4-LP24",
                "Hospedaje y Alimentacion Delegacion Internacional Encuentro Minero",
                "Ministerio de Mineria",
                "Alojamiento",
                "Licitacion Publica",
                "Region Metropolitana (Santiago)",
                28000000,
                22500000,
                "Calificada",
                "Valida",
                1, 1, 1, 1,
                "2026-09-08", "2026-09-28",
                "Alojamiento single superior para 35 expertos extranjeros durante 4 noches con desayuno y cena ejecutiva."
            ),
            (
                "1840-22-COT24",
                "Catering y Coffee Break Seminario Innovacion Publica",
                "Direccion de Presupuestos (DIPRES)",
                "Eventos / Catering",
                "Compra Agil",
                "Region Metropolitana (Santiago)",
                6400000,
                6700000,
                "Identificada",
                "Valida",
                1, 1, 1, 1,
                "2026-09-14", "2026-09-21",
                "Servicio de alimentacion para 120 personas. El presupuesto mandante queda por debajo del costo base hotel."
            ),
            (
                "512-10-LE24",
                "Alojamiento y Salones para Conferencia Anual de Rectores",
                "Consejo de Rectores de las Universidades Chilenas (CRUCH)",
                "Alojamiento",
                "Licitacion Publica",
                "Region Metropolitana (Santiago)",
                18500000,
                14200000,
                "Participada",
                "Valida",
                1, 1, 1, 1,
                "2026-08-25", "2026-09-15",
                "Bloqueo de 40 habitaciones ejecutivas y uso de salon de convenciones durante 2 jornadas."
            ),
            (
                "930-15-LP23",
                "Servicio Integral de Eventos de Cierre Ano Fiscal",
                "Servicio de Impuestos Internos (SII)",
                "Eventos / Catering",
                "Licitacion Publica",
                "Region Metropolitana (Santiago)",
                12000000,
                9500000,
                "Adjudicada",
                "Valida",
                1, 1, 1, 1,
                "2026-08-01", "2026-08-20",
                "Cena de premiacion anual en salon principal para 150 colaboradores. Adjudicado con exito."
            ),
            (
                "440-8-COT24",
                "Alojamiento de Emergencia Personal Medico",
                "Servicio de Salud Metropolitano Central",
                "Alojamiento",
                "Compra Agil",
                "Region Metropolitana (Santiago)",
                4500000,
                3800000,
                "Calificada",
                "Valida",
                0, 1, 1, 1,
                "2026-09-13", "2026-09-18",
                "Hospedaje por turnos rotativos. Nota: Falta Anexo 4 de Pacto de Integridad en bases iniciales."
            ),
            (
                "805-19-LP24",
                "Arriendo de Salones y Equipamiento Audiovisual para Foro Regional",
                "Gobierno Regional Metropolitano de Santiago",
                "Eventos / Catering",
                "Licitacion Publica",
                "Region Metropolitana (Santiago)",
                9800000,
                7500000,
                "Identificada",
                "Error ID / Discrepancia",
                1, 1, 1, 1,
                "2026-09-11", "2026-09-24",
                "Alerta Efecto ID: El ID de la ficha resumen no coincide con el correlativo de las bases adjuntas."
            ),
            (
                "310-7-COT24",
                "Servicio de Coctel Protocolar Visita Delegacion Extranjera",
                "Ministerio de Relaciones Exteriores",
                "Eventos / Catering",
                "Compra Agil",
                "Region Metropolitana (Santiago)",
                5100000,
                4100000,
                "Descartada",
                "Valida",
                1, 1, 1, 1,
                "2026-09-02", "2026-09-09",
                "Descartada por conflicto de disponibilidad de salones para la fecha requerida por el mandante."
            )
        ]
        cursor.executemany("""
            INSERT INTO licitaciones (
                id_licitacion, titulo, organismo, categoria, modalidad, region,
                presupuesto_mandante, costo_base_hotel, estado_embudo, validacion_adjuntos,
                tiene_anexo4, tiene_escrituras, tiene_poderes, tiene_vigencias,
                fecha_publicacion, fecha_cierre, descripcion_tdr
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, seed_data)
        conn.commit()
    conn.close()

def get_all_licitaciones(categoria=None, modalidad=None, estado=None, q=None):
    conn = get_db_connection()
    query = "SELECT * FROM licitaciones WHERE 1=1"
    params = []
    if categoria:
        query += " AND categoria = ?"
        params.append(categoria)
    if modalidad:
        query += " AND modalidad = ?"
        params.append(modalidad)
    if estado:
        query += " AND estado_embudo = ?"
        params.append(estado)
    if q:
        query += " AND (id_licitacion LIKE ? OR titulo LIKE ? OR organismo LIKE ?)"
        term = f"%{q}%"
        params.extend([term, term, term])
    query += " ORDER BY fecha_cierre ASC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_licitacion_by_id(id_licitacion):
    conn = get_db_connection()
    row = conn.execute("SELECT * FROM licitaciones WHERE id_licitacion = ?", (id_licitacion,)).fetchone()
    conn.close()
    return dict(row) if row else None

def create_licitacion(data):
    conn = get_db_connection()
    conn.execute("""
        INSERT INTO licitaciones (
            id_licitacion, titulo, organismo, categoria, modalidad, region,
            presupuesto_mandante, costo_base_hotel, estado_embudo, validacion_adjuntos,
            tiene_anexo4, tiene_escrituras, tiene_poderes, tiene_vigencias,
            fecha_publicacion, fecha_cierre, descripcion_tdr
        ) VALUES (
            :id_licitacion, :titulo, :organismo, :categoria, :modalidad, :region,
            :presupuesto_mandante, :costo_base_hotel, :estado_embudo, :validacion_adjuntos,
            :tiene_anexo4, :tiene_escrituras, :tiene_poderes, :tiene_vigencias,
            :fecha_publicacion, :fecha_cierre, :descripcion_tdr
        )
    """, data)
    conn.commit()
    conn.close()
    return data["id_licitacion"]

def update_licitacion(id_licitacion, data):
    conn = get_db_connection()
    fields = []
    values = []
    for k, v in data.items():
        fields.append(f"{k} = ?")
        values.append(v)
    values.append(id_licitacion)
    query = f"UPDATE licitaciones SET {', '.join(fields)} WHERE id_licitacion = ?"
    cursor = conn.execute(query, values)
    conn.commit()
    changed = cursor.rowcount > 0
    conn.close()
    return changed

def delete_licitacion(id_licitacion):
    conn = get_db_connection()
    cursor = conn.execute("DELETE FROM licitaciones WHERE id_licitacion = ?", (id_licitacion,))
    conn.commit()
    changed = cursor.rowcount > 0
    conn.close()
    return changed

def get_funnel_metrics():
    conn = get_db_connection()
    rows = conn.execute("SELECT estado_embudo, COUNT(*) as total FROM licitaciones GROUP BY estado_embudo").fetchall()
    ca_row = conn.execute("SELECT COUNT(*) as total FROM licitaciones WHERE modalidad = 'Compra Agil'").fetchone()
    conn.close()
    
    metrics = {
        "Identificada": 0,
        "Calificada": 0,
        "Participada": 0,
        "Adjudicada": 0,
        "Descartada": 0,
        "Compra_Agil": ca_row["total"] if ca_row else 0,
        "Total": 0
    }
    for r in rows:
        metrics[r["estado_embudo"]] = r["total"]
        metrics["Total"] += r["total"]
    return metrics
```

- [ ] **Step 4: Ejecutar prueba y verificar que pase**

Run: `python -m unittest tests/test_database.py`
Expected: PASS (3 tests OK)

- [ ] **Step 5: Commit de Task 1**

```bash
git add database.py tests/test_database.py
git commit -m "feat: modulo de base de datos sqlite y seed data de licitaciones"
```

---

### Task 2: Modulo de Autenticacion y Rutas Base en Flask

**Files:**
- Create: `app.py`
- Create: `templates/base.html`
- Create: `templates/login.html`
- Test: `tests/test_auth.py`

**Interfaces:**
- Consumes: `database.py` (`init_db`)
- Produces:
  - Rutas:
    - `GET /login`: formulario de login corporativo
    - `POST /login`: autentica usuario/contrasena y establece sesion
    - `GET /logout`: limpia sesion y redirige a login
    - Decorador `@login_required`: protege rutas que requieran usuario autenticado

- [ ] **Step 1: Escribir prueba unitaria para autenticacion y control de acceso**

```python
# tests/test_auth.py
import unittest
import app as flask_app
import database
import os

class TestAuth(unittest.TestCase):
    def setUp(self):
        database.DB_NAME = "test_auth_licitaciones.db"
        if os.path.exists(database.DB_NAME):
            os.remove(database.DB_NAME)
        database.init_db()
        flask_app.app.config["TESTING"] = True
        flask_app.app.config["SECRET_KEY"] = "test-secret"
        self.client = flask_app.app.test_client()

    def tearDown(self):
        if os.path.exists(database.DB_NAME):
            os.remove(database.DB_NAME)

    def test_redirect_to_login_when_unauthenticated(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.headers["Location"])

    def test_login_failure_invalid_credentials(self):
        response = self.client.post("/login", data={"username": "user", "password": "wrongpassword"}, follow_redirects=True)
        self.assertIn(b"Credenciales invalidas", response.data)

    def test_login_success(self):
        response = self.client.post("/login", data={"username": "admin", "password": "admin123"}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Panel de Control", response.data)

    def test_logout(self):
        # Login first
        self.client.post("/login", data={"username": "admin", "password": "admin123"})
        # Logout
        response = self.client.get("/logout", follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Iniciar Sesion", response.data)

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Ejecutar prueba y verificar que falle por modulo o rutas no implementadas**

Run: `python -m unittest tests/test_auth.py`
Expected: FAIL

- [ ] **Step 3: Implementar `templates/base.html` y `templates/login.html` con estilo corporativo y sin emojis**

Plantilla `templates/base.html`:
- Estilo Tailwind CSS vía CDN (`https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4` o Tailwind CDN oficial).
- Paleta ejecutiva: azul marino (`#0F172A`, `#1E293B`, `#2563EB`), fondo claro (`#F8FAFC`), texto formal.
- Barra superior con marca "Hotel Plaza San Francisco | DUOC UC", modulo activo, usuario conectado y boton "Cerrar Sesion".
- Sin emojis en toda la interfaz.

Plantilla `templates/login.html`:
- Formulario limpio y formal de inicio de sesion.
- Tarjeta corporativa con cuadro informativo que indica las credenciales demo: Usuario: `admin` / Contrasena: `admin123`.
- Manejo de alertas de error en rojo sobrio.

- [ ] **Step 4: Implementar autenticacion en `app.py`**

```python
# app.py (fragmento inicial)
from flask import Flask, render_template, request, redirect, url_for, session, flash
from functools import wraps
import database

app = Flask(__name__)
app.secret_key = "licitaciones-secret-key-2026"

DEMO_USER = "admin"
DEMO_PASS = "admin123"

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = request.form.get("username")
        password = request.form.get("password")
        if user == DEMO_USER and password == DEMO_PASS:
            session["user"] = user
            flash("Sesion iniciada correctamente.", "info")
            return redirect(url_for("dashboard"))
        else:
            flash("Credenciales invalidas. Ingrese las credenciales de prueba proporcionadas.", "error")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("user", None)
    flash("Ha cerrado sesion correctamente.", "info")
    return redirect(url_for("login"))
```

- [ ] **Step 5: Ejecutar pruebas de autenticacion y verificar que pasen**

Run: `python -m unittest tests/test_auth.py`
Expected: PASS (4 tests OK)

- [ ] **Step 6: Commit de Task 2**

```bash
git add app.py templates/base.html templates/login.html tests/test_auth.py
git commit -m "feat: modulo de autenticacion corporativa y plantillas base"
```

---

### Task 3: Dashboard de Licitaciones, Metricas del Embudo y Filtros

**Files:**
- Modify: `app.py`
- Create: `templates/dashboard.html`
- Test: `tests/test_dashboard.py`

**Interfaces:**
- Consumes: `database.get_all_licitaciones`, `database.get_funnel_metrics`
- Produces:
  - Ruta `GET /` o `GET /licitaciones`:
    - Tarjetas de resumen del Embudo de Conversion (Total Identificadas, Calificadas, Participadas, Adjudicadas, Descartadas y Compra Agil).
    - Barra de filtros: por Categoria (Alojamiento, Eventos), Modalidad (Compra Agil, Licitacion Publica), Estado del Embudo y Busqueda textual.
    - Tabla corporativa con columnas: ID Licitacion, Titulo y Organismo, Categoria, Modalidad, Presupuesto Mandante vs Costo Hotel (con indicador de viabilidad), Cruce ID (Valida vs Discrepancia) y Acciones (Ver, Editar, Eliminar).
    - Boton visible "Registrar Nueva Licitacion".

- [ ] **Step 1: Escribir pruebas para ruta del Dashboard y filtros**

```python
# tests/test_dashboard.py
import unittest
import app as flask_app
import database
import os

class TestDashboard(unittest.TestCase):
    def setUp(self):
        database.DB_NAME = "test_dash_licitaciones.db"
        if os.path.exists(database.DB_NAME):
            os.remove(database.DB_NAME)
        database.init_db()
        flask_app.app.config["TESTING"] = True
        self.client = flask_app.app.test_client()
        with self.client.session_transaction() as sess:
            sess["user"] = "admin"

    def tearDown(self):
        if os.path.exists(database.DB_NAME):
            os.remove(database.DB_NAME)

    def test_dashboard_metrics_rendered(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Total Identificadas", response.data)
        self.assertIn(b"Compra Agil", response.data)

    def test_dashboard_filter_category(self):
        response = self.client.get("/?categoria=Alojamiento")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Hospedaje", response.data)

    def test_dashboard_search_term(self):
        response = self.client.get("/?q=Turismo")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Subsecretaria de Turismo", response.data)

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Ejecutar prueba y verificar fallo por ausencia de plantilla o logica**

Run: `python -m unittest tests/test_dashboard.py`
Expected: FAIL

- [ ] **Step 3: Implementar logica de Dashboard en `app.py` y disenar `templates/dashboard.html`**

En `app.py`:
- Endpoint `@app.route("/")` y `@app.route("/licitaciones")` que toma parametros `categoria`, `modalidad`, `estado`, `q`, llama a `database.get_all_licitaciones(...)` y `database.get_funnel_metrics()`.

En `templates/dashboard.html`:
- Tarjetas con metricas del embudo con bordes y acentos visuales limpios.
- Formulario de filtros responsivo.
- Tabla corporativa con badge de advertencia si `costo_base_hotel > presupuesto_mandante` ("Inviable / Costo Excede").
- Badge para estado de validacion ("ID Verificado" o "Discrepancia ID").
- Indicador especial para Compra Agil.
- Estilo estricto sin emojis.

- [ ] **Step 4: Ejecutar prueba y verificar que pase**

Run: `python -m unittest tests/test_dashboard.py`
Expected: PASS (3 tests OK)

- [ ] **Step 5: Commit de Task 3**

```bash
git add app.py templates/dashboard.html tests/test_dashboard.py
git commit -m "feat: tablero principal con embudo comercial, filtros y tabla de licitaciones"
```

---

### Task 4: Ficha de Detalle de Licitacion (TDR, Admisibilidad y Control de Costos)

**Files:**
- Modify: `app.py`
- Create: `templates/detail.html`
- Test: `tests/test_detail.py`

**Interfaces:**
- Consumes: `database.get_licitacion_by_id`, `database.update_licitacion`
- Produces:
  - Ruta `GET /licitaciones/<id_licitacion>`:
    - Ficha detallada con informacion del mandante, categoria, fechas limite.
    - Seccion de Analisis Preventivo de Costos: Presupuesto Mandante, Costo Base Hotel, Margen/Diferencia y estado de viabilidad financiera.
    - Seccion de Validacion Robusta: cotejo de ID con archivos adjuntos.
    - Checklist de Admisibilidad Administrativa: badges formales que indican estado de Anexo 4 (Pactos de Integridad), Escrituras, Poderes de Representacion y Vigencias.
    - Resumen de Terminos de Referencia (TDR) extraidos.
    - Accion rapida: Cambio de estado en el embudo comercial (Identificada -> Calificada -> Participada -> Adjudicada -> Descartada).

- [ ] **Step 1: Escribir pruebas para la Ficha de Detalle y cambio rapido de estado**

```python
# tests/test_detail.py
import unittest
import app as flask_app
import database
import os

class TestDetail(unittest.TestCase):
    def setUp(self):
        database.DB_NAME = "test_detail_licitaciones.db"
        if os.path.exists(database.DB_NAME):
            os.remove(database.DB_NAME)
        database.init_db()
        flask_app.app.config["TESTING"] = True
        self.client = flask_app.app.test_client()
        with self.client.session_transaction() as sess:
            sess["user"] = "admin"

    def tearDown(self):
        if os.path.exists(database.DB_NAME):
            os.remove(database.DB_NAME)

    def test_view_detail_success(self):
        response = self.client.get("/licitaciones/1058-12-COT24")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Subsecretaria de Turismo", response.data)
        self.assertIn(b"Anexo 4", response.data)

    def test_view_detail_not_found(self):
        response = self.client.get("/licitaciones/NO-EXISTE-999")
        self.assertEqual(response.status_code, 404)

    def test_quick_status_change(self):
        response = self.client.post("/licitaciones/1058-12-COT24/cambiar_estado", data={"estado_embudo": "Participada"}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        lic = database.get_licitacion_by_id("1058-12-COT24")
        self.assertEqual(lic["estado_embudo"], "Participada")

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Ejecutar prueba y verificar fallo**

Run: `python -m unittest tests/test_detail.py`
Expected: FAIL

- [ ] **Step 3: Implementar endpoints de detalle y plantilla `templates/detail.html`**

En `app.py`:
- `@app.route("/licitaciones/<id_licitacion>")`
- `@app.route("/licitaciones/<id_licitacion>/cambiar_estado", methods=["POST"])`

En `templates/detail.html`:
- Bloques informativos ejecutivos y claros.
- Panel de control presupuestario con alerta visual en caso de que costo supere presupuesto.
- Tabla/Checklist de admisibilidad administrativa formal con etiquetas "Presente / Aprobado" o "Pendiente / Exigido".
- Selector y boton "Actualizar Estado en Embudo".
- Boton para volver al Dashboard, editar o eliminar.

- [ ] **Step 4: Ejecutar prueba y verificar que pase**

Run: `python -m unittest tests/test_detail.py`
Expected: PASS (3 tests OK)

- [ ] **Step 5: Commit de Task 4**

```bash
git add app.py templates/detail.html tests/test_detail.py
git commit -m "feat: ficha de detalle con control presupuestario y checklist de admisibilidad"
```

---

### Task 5: Formularios de Creacion, Edicion y Eliminacion de Licitaciones

**Files:**
- Modify: `app.py`
- Create: `templates/form.html`
- Test: `tests/test_crud_flow.py`

**Interfaces:**
- Consumes: `database.create_licitacion`, `database.update_licitacion`, `database.delete_licitacion`
- Produces:
  - Rutas:
    - `GET /licitaciones/nueva`: formulario para crear nueva licitacion de prueba.
    - `POST /licitaciones/nueva`: procesa alta y redirige al detalle con mensaje flash.
    - `GET /licitaciones/<id_licitacion>/editar`: formulario precargado para edicion.
    - `POST /licitaciones/<id_licitacion>/editar`: procesa actualizacion y redirige al detalle.
    - `POST /licitaciones/<id_licitacion>/eliminar`: elimina registro y redirige al listado principal.

- [ ] **Step 1: Escribir pruebas para el ciclo completo de creacion, modificacion y eliminacion**

```python
# tests/test_crud_flow.py
import unittest
import app as flask_app
import database
import os

class TestCrudFlow(unittest.TestCase):
    def setUp(self):
        database.DB_NAME = "test_crud_licitaciones.db"
        if os.path.exists(database.DB_NAME):
            os.remove(database.DB_NAME)
        database.init_db()
        flask_app.app.config["TESTING"] = True
        self.client = flask_app.app.test_client()
        with self.client.session_transaction() as sess:
            sess["user"] = "admin"

    def tearDown(self):
        if os.path.exists(database.DB_NAME):
            os.remove(database.DB_NAME)

    def test_create_licitacion_post(self):
        payload = {
            "id_licitacion": "5555-22-COT26",
            "titulo": "Servicio de Coctel para Bienvenida de Alumnos",
            "organismo": "DUOC UC Casa Central",
            "categoria": "Eventos / Catering",
            "modalidad": "Compra Agil",
            "region": "Region Metropolitana (Santiago)",
            "presupuesto_mandante": "4500000",
            "costo_base_hotel": "3200000",
            "estado_embudo": "Identificada",
            "validacion_adjuntos": "Valida",
            "tiene_anexo4": "1",
            "tiene_escrituras": "1",
            "tiene_poderes": "1",
            "tiene_vigencias": "1",
            "fecha_publicacion": "2026-09-15",
            "fecha_cierre": "2026-09-22",
            "descripcion_tdr": "Banqueteria protocolar para autoridades."
        }
        response = self.client.post("/licitaciones/nueva", data=payload, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"5555-22-COT26", response.data)
        item = database.get_licitacion_by_id("5555-22-COT26")
        self.assertIsNotNone(item)

    def test_edit_licitacion_post(self):
        payload = {
            "titulo": "Servicio de Banqueteria Actualizado",
            "organismo": "Subsecretaria de Turismo",
            "categoria": "Eventos / Catering",
            "modalidad": "Compra Agil",
            "region": "Region Metropolitana (Santiago)",
            "presupuesto_mandante": "6000000",
            "costo_base_hotel": "4500000",
            "estado_embudo": "Calificada",
            "validacion_adjuntos": "Valida",
            "tiene_anexo4": "1",
            "tiene_escrituras": "1",
            "tiene_poderes": "1",
            "tiene_vigencias": "1",
            "fecha_publicacion": "2026-09-12",
            "fecha_cierre": "2026-09-20",
            "descripcion_tdr": "Actualizado para agregar mas estaciones de cafe."
        }
        response = self.client.post("/licitaciones/1058-12-COT24/editar", data=payload, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        item = database.get_licitacion_by_id("1058-12-COT24")
        self.assertEqual(item["titulo"], "Servicio de Banqueteria Actualizado")

    def test_delete_licitacion_post(self):
        response = self.client.post("/licitaciones/1058-12-COT24/eliminar", follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        item = database.get_licitacion_by_id("1058-12-COT24")
        self.assertIsNone(item)

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Ejecutar prueba y verificar fallo**

Run: `python -m unittest tests/test_crud_flow.py`
Expected: FAIL

- [ ] **Step 3: Implementar endpoints CRUD y plantilla `templates/form.html`**

En `app.py`:
- Logica para `/licitaciones/nueva` (GET y POST con conversion limpia de montos y checkboxes).
- Logica para `/licitaciones/<id_licitacion>/editar` (GET y POST).
- Logica para `/licitaciones/<id_licitacion>/eliminar` (POST con confirmacion).

En `templates/form.html`:
- Formulario organizado por secciones (Datos Generales, Analisis Financiero y Presupuestario, Criterios de Admisibilidad y Documentacion).
- Botones de accion "Guardar Licitacion" y "Cancelar".
- Campos prellenados cuando se edita un registro existente.

- [ ] **Step 4: Ejecutar prueba y verificar que pase**

Run: `python -m unittest tests/test_crud_flow.py`
Expected: PASS (3 tests OK)

- [ ] **Step 5: Commit de Task 5**

```bash
git add app.py templates/form.html tests/test_crud_flow.py
git commit -m "feat: formularios de creacion, edicion y eliminacion de licitaciones"
```

---

### Task 6: Verificacion Integral y Documentacion de Ejecucion Web

**Files:**
- Create: `run.py`
- Modify: `README.md`
- Test: Ejecutar suite completa `python -m unittest discover tests`

- [ ] **Step 1: Crear script de lanzamiento `run.py` que inicialice la BD y levante el servidor web**

```python
# run.py
import database
import app

if __name__ == "__main__":
    database.init_db()
    print("Iniciando Asistente Virtual para Licitaciones - Prototipo Web")
    print("Servidor disponible en: http://127.0.0.1:5000")
    print("Credenciales de prueba: Usuario: admin | Contrasena: admin123")
    app.app.run(host="127.0.0.1", port=5000, debug=True)
```

- [ ] **Step 2: Ejecutar toda la suite de pruebas automatizadas**

Run: `python -m unittest discover tests`
Expected: Todos los tests pasan exitosamente sin errores ni advertencias.

- [ ] **Step 3: Actualizar `README.md` con instrucciones claras de inicio**

Incluir:
- Descripcion del prototipo y objetivos de negocio.
- Instrucciones de inicio (`python run.py` o `python app.py`).
- Credenciales de acceso para demostracion.
- Explicacion de las reglas de negocio reflejadas (Compra Agil, Embudo, Checklist Admisibilidad, Control Presupuestario).
- Sin uso de emojis en toda la documentacion.

- [ ] **Step 4: Commit de Task 6**

```bash
git add run.py README.md
git commit -m "docs: instrucciones de ejecucion web y script de inicio del prototipo"
```
