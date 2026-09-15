# Asistente Virtual para Licitaciones de Mercado Publico

Prototipo Funcional de Prospeccion Comercial, Evaluacion Presupuestaria y Calificacion de Procesos Estatales.

**Iniciativa de Colaboracion Institucional:**
- **Entidad Beneficiaria:** Hotel Plaza San Francisco (Santiago de Chile)
- **Programa Academico:** Vinculacion con el Medio (VcM) - Escuela de Administracion y Negocios, DUOC UC

---

## 1. Resumen Ejecutivo y Objetivos del Sistema

El **Asistente Virtual para Licitaciones** es una plataforma web corporativa desarrollada para optimizar y sistematizar la deteccion, analisis y seguimiento de oportunidades comerciales de adquisicion estatal a traves del portal Mercado Publico de Chile (ChileCompra / Ley N 19.886).

### 1.1. Diagnostico Operativo Previo
Antes de esta implementacion, el equipo de ventas corporativas y gestion de eventos del Hotel Plaza San Francisco ejecutaba un proceso de prospeccion manual caracterizado por:
- **Ineficiencia Semantica y Dispersion:** Perdida de licitaciones relevantes debido a la rigidez de busqueda en portales oficiales y variaciones terminologicas (por ejemplo, "hospedaje" frente a "alojamiento", o "banqueteria" frente a "coffee break").
- **Alto Costo en Horas-Hombre:** Revision manual diaria de hasta 10 paginas de resultados (1 a 2 horas diarias), retrasando la formulacion de propuestas y cediendo ventaja competitiva a otros oferentes.
- **Inconsistencia de Datos ("Efecto ID"):** Frecuentes discrepancias entre los identificadores visibles en la ficha resumen del portal y los archivos y anexos descargables reales, provocando busquedas infructuosas.
- **Sobrecarga Administrativa en Procesos Inviables:** Ausencia de un filtro preliminar que contrastara el presupuesto maximo disponible del organismo mandante contra los costos operativos reales del hotel antes de iniciar la elaboracion de antecedentes.

### 1.2. Proposito de la Solucion
El prototipo centraliza las oportunidades detectadas, permitiendo:
1. Focalizar la prospeccion en los rubros prioritarios de **Alojamiento** y **Eventos / Catering**.
2. Priorizar oportunidades de **Compra Agil** bajo el limite normativo de hasta $6.900.000 CLP.
3. Contrastar de manera preventiva los presupuestos oficiales contra los costos base del hotel, advirtiendo margenes negativos o inviabilidad economica.
4. Auditar de manera preliminar los requisitos administrativos de admisibilidad (Anexo 4 de Pactos de Integridad, Escrituras, Poderes y Vigencias) para mitigar el riesgo de inadmisibilidad.
5. Gestionar el avance de cada oportunidad a traves de un embudo comercial estructurado.

---

## 2. Restricciones Operativas y Principios de Diseno

### 2.1. Arquitectura de Ejecucion 100% Web en Python
- **Mandato de Diseno:** La totalidad de la solucion funciona exclusivamente como aplicacion web (Flask) accesible desde el navegador institucional.
- **Justificacion Tecnica e Historica:** Durante las etapas preliminares del proyecto (Fase 1), los scripts locales y aplicaciones de escritorio ejecutadas en estaciones de trabajo fueron bloqueados por las politicas de seguridad perimetral, suites antivirus y firewalls corporativos del hotel.
- **Prohibicion Explicita:** Queda terminantemente prohibida la creacion o distribucion de scripts ejecutables locales en los puestos operativos del hotel. Todo procesamiento se realiza en el servidor web.

### 2.2. Politica Estricta de Supresion Total de Emojis
- **Norma Institucional:** Se erradica de forma total y absoluta el uso de emojis o iconografia informal en la interfaz de usuario, botones, insignias (badges), mensajes de retroalimentacion (flash), registros de consola (logs) y documentacion tecnica.
- **Formalidad Corporativa:** Todos los estados del sistema, alertas operativas y estados de validacion se comunican exclusivamente mediante nomenclatura formal de negocios, codigos de texto e indicadores de interfaz sobrios.

### 2.3. Identidad Visual Corporativa
- **Paleta de Colores:** Diseñada con Tailwind CSS CDN utilizando una combinacion sobria de azul marino profundo (`slate-900`, `blue-950`), gris pizarra (`slate-700`, `slate-600`, `slate-100`) y acentos institucionales formales (`emerald-700`, `amber-700`, `rose-700`).
- **Orientacion al Usuario:** Interfaz simplificada para uso inmediato por parte de ejecutivos de cuentas y personal de eventos sin formacion tecnica en programacion.

---

## 3. Modulos Funcionales del Prototipo

El prototipo consta de 4 modulos principales completamente articulados:

### 3.1. Modulo de Autenticacion Corporativa y Control de Acceso
- **Proteccion de Vistas:** Implementacion del decorador `@login_required` sobre todas las rutas operativas (`/`, `/licitaciones`, `/licitaciones/nueva`, fichas de detalle, edicion y eliminacion). Cualquier solicitud anonima es redirigida a `/login`.
- **Credenciales Demo Integradas:**
  - **Usuario:** `admin`
  - **Contrasena:** `admin123`
- **Gestion de Sesion:** Manejo seguro de sesion mediante `flask.session` con clave criptografica y cierre de sesion formal (`/logout`).

### 3.2. Tablero Principal de Gestion Comercial (Dashboard)
- **Embudo Comercial de 5 Etapas:**
  1. *Identificada:* Oportunidad detectada por rubro y plaza geografica.
  2. *Calificada:* Evaluacion economica y documental preliminar aprobada.
  3. *Participada:* Oferta tecnica y economica ingresada formalmente en Mercado Publico.
  4. *Adjudicada:* Proceso ganado por el hotel.
  5. *Descartada:* Desestimada por margen insuficiente, inviabilidad operativa o vencimiento.
- **Metricas Consolidadas en Tiempo Real:** Contadores agregados por cada etapa del embudo comercial y consolidacion financiera total (Presupuesto total identificado en CLP, Costo base proyectado y Margen estimado).
- **Motor de Filtrado Multicriterio:** Capacidad de filtrado combinable por parametros GET:
  - Busqueda por texto (titulo, organismo o identificador de licitacion).
  - Categoria comercial (Alojamiento, Eventos / Catering).
  - Modalidad de adquisicion (Compra Agil, Licitacion Publica).
  - Region geografica (Region Metropolitana, Valparaiso, OHiggins, etc.).
  - Estado en el embudo comercial.
- **Tabla de Oportunidades:** Listado relacional ordenado cronologicamente segun proximidad de la fecha de cierre de ofertas, con identificador oficial, organismo mandante, categoria, montos formateados en pesos chilenos (CLP) y badges de estado.

### 3.3. Ficha de Detalle y Evaluacion Integral
- **Identificacion y Metadatos:** Consulta completa de organismo mandante, region, modalidad, cronograma de publicacion y fecha limite de cierre.
- **Control Presupuestario Preventivo:**
  - Calculo automatico en pantalla de `Margen Bruto = Presupuesto Mandante - Costo Base Hotel`.
  - Calculo porcentual de margen sobre el presupuesto disponible.
  - Generacion de **Alerta de Inviabilidad Economica** en tonos de advertencia formal si el costo operativo supera el presupuesto oficial, evitando desgaste administrativo en propuestas a perdida.
- **Checklist de Admisibilidad Administrativa (Ley N 19.886):**
  - Verificacion obligatoria de los antecedentes habilitantes requeridos en bases:
    1. Anexo 4 (Declaracion Jurada y Pacto de Integridad).
    2. Escrituras Publicas de constitucion societaria.
    3. Poderes de representacion legal vigentes.
    4. Certificados de vigencia emitidos por el Conservador de Bienes Raices.
  - Indicador global de admisibilidad: `Cumplimiento Total` o `Faltan Requisitos Relevantes`.
- **Auditoria Documental ("Efecto ID"):**
  - Verificacion de consistencia entre el identificador visible y los documentos adjuntos (`Valida` vs `Error ID / Discrepancia`).
- **Gestion de Avance de Etapa:** Selector directo para actualizar el estado del embudo comercial con confirmacion visual mediante mensajes flash.

### 3.4. Modulo CRUD (Gestion de Licitaciones)
- **Creacion Segura (`/licitaciones/nueva`):**
  - Registro preventivo de la ruta antes de la captura dinamica de parametros (`/licitaciones/<id_licitacion>`) para evitar colisiones de enrutamiento en Flask.
  - Formulario organizado en 6 bloques tematicos: Identificacion y Organismo, Categoria y Modalidad, Evaluacion Economica, Fechas Criticas, Checklist de Admisibilidad y Extracto de TDR.
  - Validacion estricta en servidor: verificacion de campos obligatorios, integridad de valores enteros en CLP y rechazo de identificadores duplicados.
- **Edicion Controlada (`/licitaciones/<id_licitacion>/editar`):**
  - Bloqueo en solo lectura del identificador oficial para resguardar la trazabilidad de la oportunidad.
  - Actualizacion dinamica de montos, checklist documental, estado y descripcion tecnica.
- **Eliminacion Segura (`/licitaciones/<id_licitacion>/eliminar`):**
  - Operacion procesada exclusivamente mediante metodo POST autenticado.
  - Modal de confirmacion con indicacion explicita del codigo de la licitacion antes de confirmar la baja en la base de datos.

---

## 4. Reglas de Negocio y Parametros Normativos Modelados

| Regla de Negocio | Parametro / Criterio | Aplicacion en el Sistema |
| :--- | :--- | :--- |
| **Matriz de Rubros Prioritarios** | Alojamiento / Eventos y Catering | Clasificacion de oportunidades segun habitacion/estadia vs salones/banqueteria. |
| **Geolocalizacion Primaria** | Region Metropolitana (Santiago Centro) | Prioridad en la captacion de eventos y estadias en el radio de cobertura del hotel. |
| **Tope Normativo Compra Agil** | Hasta 6.900.000 CLP | Distincion automatica de procesos de compra rapida segun normativa vigente de compras publicas. |
| **Consistencia Documental ("Efecto ID")** | Cotejo de ID contra bases adjuntas | Deteccion de licitaciones con errores de publicacion en el portal oficial para evitar descalificaciones. |
| **Causales de Inadmisibilidad** | 4 antecedentes habilitantes obligatorios | Auditoria de Anexo 4 (Pacto de Integridad), Escrituras, Poderes y Certificados de Vigencia. |
| **Control de Rentabilidad Minima** | Presupuesto Mandante vs Costo Hotel | Generacion de alerta de inviabilidad si el costo base supera el presupuesto asignado por el comprador. |

---

## 5. Arquitectura del Repositorio de Codigo

```text
C:\Licitaciones\
|-- app.py                    # Controlador principal Flask (enrutamiento, autenticacion, logica CRUD)
|-- database.py               # Capa de persistencia relacional SQLite y funciones de consulta
|-- run.py                    # Script de inicio oficial del servidor web local
|-- requirements.txt          # Dependencias minimas del entorno Python (Flask)
|-- ESPECIFICACION_REQUERIMIENTOS.md  # Documento base de requerimientos tecnicos y operacionales
|-- README.md                 # Manual formal del sistema, arquitectura y procedimientos
|-- templates/                # Vistas renderizadas en servidor con Jinja2 y Tailwind CSS
|   |-- base.html             # Plantilla estructural corporativa (encabezado, navegacion, mensajes)
|   |-- login.html            # Pantalla de inicio de sesion corporativa
|   |-- dashboard.html        # Tablero principal de gestion comercial y embudo
|   |-- detail.html           # Ficha de detalle, evaluacion economica y checklist
|   |-- form.html             # Formulario unificado de creacion y edicion de licitaciones
|   `-- 404.html              # Pantalla formal de recurso no encontrado
`-- tests/                    # Suite completa de pruebas automatizadas
    |-- __init__.py           # Inicializador del paquete de pruebas
    |-- test_auth.py          # Pruebas de autenticacion, control de sesion y rutas protegidas
    |-- test_database.py      # Pruebas de la capa SQLite (inicializacion, seed, consultas, CRUD)
    |-- test_dashboard.py     # Pruebas de metricas de embudo y filtros multicriterio
    |-- test_detail.py        # Pruebas de evaluacion financiera, checklist y cambio de estado
    |-- test_crud_flow.py     # Pruebas integrales de creacion, edicion, eliminacion y validaciones
    |-- test_run.py           # Pruebas del script de inicio run.py y mensajes de consola
    `-- test_emoji_compliance.py # Auditoria automatizada de ausencia total de emojis en el repositorio
```

---

## 6. Instrucciones de Instalacion y Puesta en Marcha

### 6.1. Requisitos Previos
- **Python:** Version 3.10 o superior (verificado en Python 3.12).
- **Sistema Operativo:** Compatible con Windows, Linux y macOS.
- **Navegador Web:** Edge, Chrome, Firefox o Safari con conexion a internet para la carga de Tailwind CSS via CDN.

### 6.2. Instalacion de Dependencias
Abra un terminal en la raiz del proyecto y ejecute:

```bash
pip install -r requirements.txt
```

*Nota: La unica dependencia externa requerida es `Flask>=3.0.0`. El motor de persistencia utiliza `sqlite3` incluido en la biblioteca estandar de Python.*

### 6.3. Inicio del Servidor Web
Ejecute el script de inicio oficial:

```bash
python run.py
```

El script inicializara automaticamente la base de datos `licitaciones.db` con los datos de demostracion preconfigurados si aun no existe, e iniciara el servidor web corporativo.

En la consola se visualizara un mensaje formal con el siguiente formato:

```text
========================================================================
  ASISTENTE VIRTUAL PARA LICITACIONES (MERCADO PUBLICO)
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
========================================================================
[INFO] Servidor web iniciado en modo local. Presione CTRL+C para detener.
========================================================================
```

### 6.4. Acceso al Sistema
1. Abra su navegador web e ingrese a la direccion: `http://127.0.0.1:5000`
2. El sistema lo redirigira a la pantalla de acceso corporativo (`/login`).
3. Ingrese con las credenciales demo:
   - **Usuario:** `admin`
   - **Contrasena:** `admin123`
4. Presione **Iniciar Sesion** para ingresar al Tablero Principal.

---

## 7. Suite de Verificacion Automatizada (Testing)

El sistema cuenta con una suite completa de pruebas unitarias y de integracion desarrolladas bajo la metodologia Test-Driven Development (TDD).

### 7.1. Ejecucion de la Suite Completa
Para ejecutar la totalidad de las pruebas automatizadas del proyecto, ejecute en la raiz del repositorio:

```bash
python -m unittest discover tests
```

### 7.2. Cobertura de Pruebas
La suite ejecuta mas de 60 pruebas automatizadas organizadas en 7 modulos de prueba:
1. `tests/test_auth.py`: Valida el bloqueo de accesos no autorizados en todas las rutas, renderizado de credenciales demo, validacion de errores en formulario de login, inicio exitoso de sesion y cierre formal de sesion.
2. `tests/test_database.py`: Verifica la creacion del esquema SQLite, carga inicial de datos (seed), consultas por identificador, calculo de metricas agregadas del embudo, filtros multicriterio, insercion, modificacion y eliminacion de registros.
3. `tests/test_dashboard.py`: Evalua el calculo de totales por etapa del embudo comercial, totales monetarios, filtros por categoria, modalidad, region y texto, asi como el ordenamiento cronologico por fecha de cierre.
4. `tests/test_detail.py`: Comprueba el calculo de margenes brutos y porcentuales, disparo de alerta por costo hotel superior al presupuesto mandante, verificacion de causales de inadmisibilidad documental (Anexo 4, escrituras, poderes, vigencias), validacion de adjuntos y transicion de estados en el embudo comercial.
5. `tests/test_crud_flow.py`: Audita el flujo completo de creacion (`/licitaciones/nueva`), prevencion de colision con rutas dinamicas, rechazo de IDs duplicados, validaciones de campos requeridos y formatos monetarios, edicion protegida y eliminacion confirmada por POST.
6. `tests/test_run.py`: Valida la invocacion correcta del inicializador de base de datos y arranque de servidor en `run.py`, la emision de mensajes formales de consola y la ausencia de emojis en la salida estandar.
7. `tests/test_emoji_compliance.py`: Realiza un escaneo exhaustivo en todo el repositorio (archivos `.py`, `.html`, `.md`, `.txt`) mediante expresiones regulares unicode para asegurar la supresion total y absoluta de emojis segun la restriccion de diseno corporativo.

---

## 8. Verificacion de Ausencia de Emojis

Para auditar de forma independiente que ningun archivo de codigo, plantilla o documentacion contenga caracteres emoji, se puede ejecutar el siguiente comando en terminal:

```bash
python -c "import os, re; p = re.compile(r'[\U00010000-\U0010ffff]|[\u2600-\u27bf]|[\u2300-\u23ff]|[\u2b50\u2b55\u2934\u2935\u25aa\u25ab\u25b6\u25c0\u25fb-\u25fe]'); [print(f'Alerta en: {os.path.join(r, f)}') for r, d, fs in os.walk('.') if not any(x in r for x in ['.git', '__pycache__', '.superpowers']) for f in fs if f.endswith(('.py', '.html', '.md', '.txt')) and p.search(open(os.path.join(r, f), encoding='utf-8').read())]; print('Auditoria de emojis completada exitosamente.')"
```

El resultado esperado es la confirmacion de 0 alertas y la salida:
`Auditoria de emojis completada exitosamente.`
