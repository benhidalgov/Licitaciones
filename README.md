<div align="center">

# Copilot de Licitaciones y Operaciones Hoteleras

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/Framework-Flask_3.0-111111?style=flat-square&logo=flask)](https://flask.palletsprojects.com/)
[![Base de Datos](https://img.shields.io/badge/Database-SQLite3-003B57?style=flat-square&logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![Tests](https://img.shields.io/badge/Tests-130_Aprobadas-10B981?style=flat-square)](tests)
[![Interfaz](https://img.shields.io/badge/UI-Minimalist_Editorial-111111?style=flat-square)](templates)
[![Normativa](https://img.shields.io/badge/Mercado_Publico-Ley_19.886-0284C7?style=flat-square)](https://www.mercadopublico.cl/)

> Plataforma web para prospeccion comercial, control preventivo de costos, verificacion de aforo y agenda de salones para adquisiciones del Estado.

**Hotel Plaza San Francisco** | **Programa de Vinculacion con el Medio (VcM) DUOC UC**

[Inicio Rapido](#inicio-rapido) • [Caracteristicas](#caracteristicas-principales) • [Arquitectura](#arquitectura-del-sistema) • [Agenda de Salones](#catalogo-y-agenda-de-salones) • [Testing](#suite-de-pruebas-automatizadas)

</div>

---

## Descripcion General

El **Copilot de Licitaciones y Operaciones Hoteleras** es una solucion web disenada para el equipo comercial y de eventos del Hotel Plaza San Francisco (Santiago de Chile), desarrollada en alianza con la Escuela de Administracion y Negocios de DUOC UC.

El sistema resuelve la dispersion de ofertas en Mercado Publico automatizando el embudo de oportunidades de adquisicion estatal (ChileCompra / Ley N 19.886), evaluando la viabilidad economica de cada proceso, auditando requisitos administrativos de admisibilidad y coordinando la disponibilidad fisica de salones y aforos.

> [!NOTE]
> **Contexto Operativo:**
> El proceso manual previo implicaba la revision diaria de entre 12 y mas de 20 paginas de resultados de busqueda en el portal estatal, con riesgo constante de inconsistencias documentales ("Efecto ID"), colisiones de fechas en la agenda del hotel y desgaste administrativo en ofertas con costos superiores al presupuesto oficial.

---

## Caracteristicas Principales

### 1. Embudo Comercial y Prospeccion Focalizada
* **Segmentacion por Rubros Clave:** Filtro de oportunidades en las unidades de negocio estrategicas: **Alojamiento** (delegaciones, hospedaje) y **Eventos / Catering** (salones, jornadas, seminarios y alimentacion intramuros).
* **Priorizacion Compra Agil:** Marcador automatico para procesos bajo la modalidad Compra Agil con limite normativo vigente de hasta **$6.900.000 CLP**.
* **Alcance por Propiedad:** **Hotel Plaza San Francisco** (salones, eventos y habitaciones) y **Hotel Ismael** (solo hospedaje). Se descarta banqueteria o eventos fuera de las instalaciones.
* **Geolocalizacion Informativa:** La region se muestra como dato, pero no descarta automaticamente por comuna. Si el presupuesto deja margen, la oportunidad se evalua igualmente (Las Condes, Vitacura u otras).
* **Ciclo de Conversion de 5 Etapas:** Seguimiento de estado (`Identificada`, `Calificada`, `Participada`, `Adjudicada`, `Descartada`) con metricas financieras en tiempo real (monto total identificado, costo base proyectado y margen estimado).
* **Decision Operativa Compartida:** Marca `Revisada`, decision `Participamos` o `No participamos` con motivo (`Precio`, `Disponibilidad`, `Fuera de alcance`, `Otro`) y notas con autor y fecha.
* **Vista Priorizada del Dia:** Oportunidades abiertas con presupuesto viable y match de capacidad, con enlace directo a la ficha oficial de Mercado Publico.
* **Exportacion a Planilla:** Descarga CSV compatible con Excel del listado filtrado (indicadores, estado, motivo, aforo y notas).
* **Control de Llamadas a la API:** Las consultas a Mercado Publico se espacian (`MERCADO_PUBLICO_INTERVALO_MS`, 500 ms por defecto = 120 llamadas/min) y se reintenta con backoff exponencial ante HTTP 429 o 503, respetando `Retry-After`. Si la API aun bloquea fichas, el resumen de la sincronizacion lo indica para subir el intervalo en `.env` y repetir.

### 2. Control Financiero Preventivo y Admisibilidad Legal
* **Regla Mandatoria de Presupuesto:** Una oportunidad con costeo validado cuyo costo minimo (tarifa de salon + alimentacion o habitacion por persona) supera el presupuesto mandante se marca `Descartada` con motivo `Precio`. El valor importado desde la API es provisional hasta que el equipo complete la evaluacion operativa.
* **Auditoria Documental ("Efecto ID"):** Cotejo cruzado entre el identificador publicado en el portal y los correlativos de las bases descargables adjuntas.
* **Checklist de Admisibilidad (Ley N 19.886):** Verificacion de 4 antecedentes administrativos habilitantes para prevenir causales de inadmisibilidad:
  1. Anexo 4 (Declaracion Jurada y Pacto de Integridad).
  2. Escrituras Sociales y Estatutos Vigentes.
  3. Poderes de Representacion Legal.
  4. Certificados de Vigencia de la Sociedad (antiguedad menor a 60 dias).

### 3. Gestion de Salones, Aforo y Agenda de Ocupacion
* **Catalogo de 17 Espacios:** El catalogo incorpora los 5 salones confirmados y 12 espacios provisionales marcados como `[PROVISIONAL]`, pendientes de validacion de aforo, montaje y tarifa con el hotel:
  - *Gran Salon San Francisco (Plenario):* Capacidad de 300 personas.
  - *Salon Colonial (Banquete / Eventos):* Capacidad de 150 personas.
  - *Salon Alameda (Seminario / Conferencias):* Capacidad de 80 personas.
  - *Salon Londres (Reuniones / Taller):* Capacidad de 40 personas.
  - *Salon Directorio Ejecutivo:* Capacidad de 20 personas.
  - *12 espacios adicionales:* entre 25 y 120 personas, con montajes de teatro, escuela, banquete, coctel, isla y mesa ejecutiva.
* **Propuesta de Match por Capacidad:** El sistema propone los salones cuya capacidad maxima cubre el aforo requerido. La disponibilidad final siempre se valida en el PMS del hotel; no existe sincronizacion automatica con Mercado Publico.
* **Validacion de Aforo y Sobrecupo:** Verificacion entre la cantidad de asistentes solicitada y la capacidad del salon asignado, recomendando alternativas compatibles en caso de sobrecupo.
* **Agenda de Ocupacion y Reservas (Bookings):** Cronograma de fechas ocupadas con detalle de organismo contratante, asistentes, franja horaria y estado (`Confirmada`, `Tentativa`, `Bloqueo Interno`).
* **Motor de Deteccion de Colisiones:** Validacion matematica de cruce de fechas que impide la doble reserva de un mismo espacio en fechas solapadas y alerta en tiempo real en la ficha de licitacion.
* **Bloqueo Directo desde Licitacion:** Boton para transferir en un clic los datos del proceso licitatorio al formulario de reserva del hotel.

### 4. Analitica, Clientes Clave e Historial de OC
* **Monitoreo de Clientes Clave:** Lista configurable en `database.CLIENTES_CLAVE` (Mineduc, Minsal, U. de Chile, Usach y productoras). El tablero ofrece filtro y etiqueta `Cliente: ...`; la ficha muestra `Cliente clave: ...`. El reconocimiento tolera acentos y mayusculas.
* **Benchmarking de Adjudicaciones:** Bloque en la ficha para registrar adjudicatario, puntaje (0 a 100) y precio final. Calcula la desviacion sobre el presupuesto mandante y el margen sobre el costo minimo del hotel. La pagina `/analitica` concentra el comparativo ordenado por precio.
* **Historial de Ordenes de Compra:** Importador de `.xlsx` o `.csv` del archivo que entrega el hotel, con encabezados tolerantes (Organismo/Cliente, Objeto/Descripcion, Fecha y Monto) y soporte de formato chileno (`$1.234.567`, `15/03/2026`).
* **Cruce de Experiencia:** La ficha indica cuantas OC previas existen con el mismo organismo y por cuanto monto, para dimensionar la relacion historica antes de ofertar.
* **Ficha Resumen:** Fechas del evento, personas, salones u habitaciones sugeridos, servicios de alimentacion y desglose de ponderacion de criterios que suma 100. Se genera con reglas deterministas; si se configura `RESUMEN_IA_API_KEY` se enriquece con IA y degrada a reglas si falla.

### 5. Diseno Editorial Minimalista (Minimalist UI)
* **Paleta Calida Monocroma:** Lienzo suave `#FBFBFA` con tarjetas blancas planas `#FFFFFF` y bordes micro-precisos de `1px solid #EAEAEA`.
* **Jerarquia Tipografica:** Titulares en *Newsreader Serif*, controles en *Geist Sans* y metadatos en *Geist Mono*.
* **Bento Grid Asimetrico:** Tablero principal con paneles de conversion y atajos fisicos de teclado `<kbd>/</kbd>`.

---

## Requisitos Operativos y Principios de Diseno

> [!IMPORTANT]
> **Directriz de Arquitectura 100% Web:**
> Queda prohibida la distribucion o ejecucion de scripts locales o ejecutables en los puestos de trabajo del hotel. Toda la plataforma opera exclusivamente a traves del navegador web institucional servido por Flask, mitigando bloqueos por politicas de seguridad perimetral corporativa.

> [!IMPORTANT]
> **Politica Estricta de Cero Emojis:**
> De acuerdo con la normativa corporativa del proyecto, queda estrictamente prohibido el uso de caracteres o iconos emoji en codigo, plantillas, mensajes flash, registros de consola y documentacion. Todos los estados se expresan mediante nomenclatura formal y badges de texto estandarizados (`[OK]`, `[WARN]`, `[CRIT]`, `[INFO]`).

---

## Arquitectura del Sistema

```text
C:\Licitaciones\
|-- app.py                     # Controlador central Flask (rutas, auth, validaciones CRUD y reservas)
|-- database.py                # Capa relacional SQLite (esquema, consultas, seed, cruce de colisiones)
|-- mercado_publico.py         # Cliente API ChileCompra, normalizacion semantica y filtros
|-- resumen.py                 # Ficha resumen por reglas (IA opcional) y ponderacion de criterios
|-- run.py                     # Script de inicio oficial para entorno de ejecucion
|-- verify.py                  # Script de verificacion de calidad y suite de pruebas unitarias
|-- requirements.txt           # Dependencias minimas del sistema (Flask >= 3.0.0)
|-- ESPECIFICACION_REQUERIMIENTOS.md # Especificacion formal de reglas de negocio
|-- README.md                  # Manual tecnico y documentacion general del proyecto
|-- docs/                      # Guias tecnicas y protocolos de ingenieria
|   |-- ALINEACION_REUNION.md  # Brechas y plan de alineacion con la reunion de levantamiento
|   `-- WORKFLOW.md            # Protocolo de ramas Git, convenciones de commit y verificacion
|-- templates/                 # Plantillas HTML con Jinja2 y tokens Minimalist UI
|   |-- base.html              # Layout corporativo base, navegacion superior y CSS unificado
|   |-- login.html             # Acceso autenticado y credenciales demo
|   |-- dashboard.html         # Tablero Bento Grid con embudo de conversion y filtros
|   |-- detail.html            # Ficha de detalle, evaluacion financiera, checklist y aforo
|   |-- analitica.html         # Benchmarking de adjudicaciones e importador de historial de OC
|   |-- salones.html           # Catalogo de infraestructura y agenda de reservas
|   |-- salon_detail.html      # Ficha monografica por salon, montajes y cronograma
|   |-- reserva_form.html      # Formulario para registro, edicion y bloqueo de fechas
|   `-- 404.html               # Vista formal de recurso no encontrado
`-- tests/                     # Suite de pruebas automatizadas (TDD)
    |-- test_auth.py           # Autenticacion y proteccion de rutas
    |-- test_database.py       # Persistencia relacional, seeds y filtros
    |-- test_dashboard.py      # Metricas comerciales y filtros multicriterio
    |-- test_detail.py         # Evaluacion de margenes, checklist y alertas
    |-- test_crud_flow.py      # Eliminacion de licitaciones y rutas manuales retiradas
    |-- test_salones.py        # Catalogo de salones, reservas, colisiones y acciones
    |-- test_mercado_publico.py# Pruebas de cliente e integracion Mercado Publico
    |-- test_run.py            # Modulo de arranque del servidor
    |-- test_evaluacion.py     # Costeo minimo, descarte por presupuesto, decisiones y exportacion
    |-- test_bonus.py          # Clientes clave, benchmarking e importador de historial de OC
    `-- test_emoji_compliance.py # Auditoria regex de ausencia total de emojis
```

---

## Inicio Rapido

### 1. Requisitos Previos
* **Python:** 3.10 o superior (verificado en Python 3.12).
* **Navegador Web:** Edge, Chrome, Firefox o Safari.

### 2. Instalacion de Dependencias

```bash
pip install -r requirements.txt
```

> [!TIP]
> La unica dependencia de terceros requerida es `Flask>=3.0.0`. El motor de persistencia utiliza `sqlite3` provisto por la biblioteca estandar de Python.

### 3. Puesta en Marcha del Servidor

```bash
python run.py
```

Al iniciarse, el servidor verifica automaticamente la base de datos `licitaciones.db`, inicializa las tablas relacionales y siembra los registros de prueba si no existen.

```text
========================================================================
  COPILOT DE LICITACIONES Y OPERACIONES HOTELERAS
  Hotel Plaza San Francisco | Programa VcM DUOC UC
========================================================================
[INFO] Inicializando motor de persistencia SQLite...
[INFO] Esquema relacional y datos de prueba verificados correctamente.
[INFO] Arquitectura 100% Web activa. Acceso exclusivo mediante navegador.
========================================================================
  Punto de Acceso Web: http://127.0.0.1:5000
  Credenciales de Demostracion:
    - Usuario:         admin
    - Contrasena:      admin123
    - Perfiles:        daniela / francisca / mari
    - Claves:          <perfil>123
========================================================================
```

### 4. Acceso al Sistema
1. Abra su navegador en: `http://127.0.0.1:5000`
2. El sistema redirigira a la pantalla de autenticacion.
3. Ingrese con cualquiera de los perfiles demo:
   * **Daniela:** `daniela` / `daniela123`
   * **Francisca:** `francisca` / `francisca123`
   * **Mari Carmen:** `mari` / `mari123`
   * **Administrador:** `admin` / `admin123`

   Los tres perfiles operativos comparten estados, decisiones y notas.

---

## Catalogo y Agenda de Salones

> [!NOTE]
> El catalogo operativo contiene **17 espacios**. La tabla siguiente detalla los 5 salones confirmados; los otros 12 estan marcados como `[PROVISIONAL]` hasta que el hotel valide aforo, montaje y tarifa. Todos pertenecen al Hotel Plaza San Francisco. El Hotel Ismael opera solo alojamiento y no tiene salones asociados.

| Identificador | Salon | Formato Principal | Aforo Maximo | Horario Operativo | Ubicacion |
| :--- | :--- | :--- | :---: | :--- | :--- |
| `SALON-PLENARIO` | Gran Salon San Francisco | Plenario / Conferencia | 300 | 08:00 - 23:00 hrs | Nivel Subterraneo |
| `SALON-COLONIAL` | Salon Colonial | Banquete / Eventos | 150 | 08:00 - 23:00 hrs | Piso 1 - Hall Central |
| `SALON-ALAMEDA` | Salon Alameda | Seminario / Conferencias | 80 | 08:30 - 20:00 hrs | Piso 2 - Ala Poniente |
| `SALON-LONDRES` | Salon Londres | Reuniones / Taller | 40 | 08:30 - 19:30 hrs | Piso 2 - Ala Ejecutiva |
| `SALON-DIRECTORIO` | Salon Directorio Ejecutivo | Directorio / Mesa Ejecutiva | 20 | 08:00 - 20:00 hrs | Piso 3 - Area Presidencial |

---

## Suite de Pruebas Automatizadas y Flujo de Calidad

El proyecto se desarrolla bajo metodologia **Test-Driven Development (TDD)** con una suite de 130 pruebas unitarias e integradas que cubren autenticacion, base de datos, logica financiera, costeo minimo, prevencion de colisiones, integracion con Mercado Publico y cumplimiento normativo.

### 1. Verificacion Oficial Previa a Integracion

Para validar la suite completa y constatar que la rama de trabajo es apta para fusionarse a `main`:

```bash
python verify.py
```

### 2. Ejecucion Directa con Unittest

```bash
python -m unittest discover tests
```

### 3. Auditoria de Cumplimiento de Cero Emojis

Para ejecutar el escaneo independiente de expresiones regulares sobre la totalidad del repositorio:

```bash
python -m unittest tests/test_emoji_compliance.py
```

### 4. Protocolo de Ramas de Trabajo

Para consultar la politica de ramas tematicas (`feat/`, `fix/`, `refactor/`), convenciones de commit y pasos de integracion, revise [docs/WORKFLOW.md](docs/WORKFLOW.md).
