import os
import re
import sqlite3
from datetime import date
from typing import Any, Dict, List, Optional, Tuple

DB_NAME = os.path.join(os.path.dirname(os.path.abspath(__file__)), "licitaciones.db")

ALLOWED_COLUMNS = {
    "titulo", "organismo", "categoria", "modalidad", "region",
    "presupuesto_mandante", "costo_base_hotel", "estado_embudo",
    "validacion_adjuntos", "tiene_anexo4", "tiene_escrituras",
    "tiene_poderes", "tiene_vigencias", "fecha_publicacion",
    "fecha_cierre", "descripcion_tdr",
    "cantidad_asistentes", "tipo_jornada", "horario_evento", "id_salon_asignado",
    "propiedad", "revisada", "motivo_descarte", "notas", "costeo_validado",
    "sello_mujer", "jornada_40h", "sello_sernatur", "inclusion_laboral",
    "adjudicatario", "puntaje_adjudicacion", "precio_final"
}

PROPIEDADES = ["Plaza San Francisco", "Hotel Ismael"]

MOTIVOS_DESCARTE = ["Precio", "Disponibilidad", "Fuera de alcance", "Otro"]

# Clientes clave que el equipo quiere monitorear (reunion de levantamiento).
# Nombre visible + alias de busqueda sobre `organismo` y `titulo`.
# ponytail: lista en codigo; mover a la tabla `ajustes` si el hotel la edita seguido.
CLIENTES_CLAVE = [
    ("Mineduc", ("ministerio de educacion", "subsecretaria de educacion", "mineduc")),
    ("Minsal", ("ministerio de salud", "subsecretaria de salud", "minsal")),
    ("U. de Chile", ("universidad de chile", "uchile")),
    ("Usach", ("universidad de santiago", "usach")),
    ("Productoras", ("productora", "produccion audiovisual", "productoras")),
]


def _sin_acentos(texto: str) -> str:
    import unicodedata
    return unicodedata.normalize("NFKD", texto or "").encode("ASCII", "ignore").decode("ascii")


def _alias_cliente_clave(nombre: str) -> Tuple[str, ...]:
    for cliente, alias in CLIENTES_CLAVE:
        if cliente.lower() == str(nombre or "").strip().lower():
            return alias
    return ()


def detectar_cliente_clave(texto: str) -> str:
    """Devuelve el nombre del cliente clave que aparece en el texto, o ''."""
    limpio = _sin_acentos(texto).lower()
    for cliente, alias in CLIENTES_CLAVE:
        if any(a in limpio for a in alias):
            return cliente
    return ""


def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.create_function("sin_acentos", 1, _sin_acentos)
    return conn


# Catalogo oficial de salones del Hotel Plaza San Francisco.
# Fuente: documento "SALONES HPSF.pdf" del hotel, tabla de aforos por montaje.
# Formato de cada fila: (nombre, piso, m2, U, auditorio, mesa imperial, escuela,
# mesa redonda 1,50 m 10 pax, mesa redonda 1,20 m 5 pax, coctel de pie).
# None significa que el catalogo no admite ese montaje en ese salon.
CATALOGO_SALONES_HPSF = [
    ("Ejecutivo", 2, 28, None, None, 8, None, None, None, None),
    ("Alerce", -2, 41, 20, 30, 20, 25, 30, 20, None),
    ("Roble", -2, 41, 20, 30, 20, 25, 30, 20, None),
    ("Mistral", -1, 47, 20, 30, 20, 25, 30, 25, None),
    ("Neruda", -1, 50, 20, 30, 20, 25, 30, 20, None),
    ("Parra", -1, 62, 20, 35, 20, 25, 40, 25, None),
    ("Ebro", 2, 48, 20, 30, 20, 25, 30, 25, None),
    ("Tiber", 2, 46, 15, 20, 15, 20, 30, 25, 15),
    ("Volga", 2, 49, 20, 30, 20, 25, 30, 25, 30),
    ("Duero", 2, 58, 25, 50, 25, 30, 40, 30, 30),
    ("Arrau", -1, 62, 25, 50, 25, 30, 40, 30, 30),
    ("Araucaria", -2, 105, 40, 100, 40, 60, 80, 40, 60),
    ("Sena", 2, 65, 30, 60, 30, 35, 50, 30, 40),
    ("Danubio", 2, 108, 35, 100, 35, 50, 70, 40, 80),
    ("Rhin", 2, 84, 20, 60, 20, 30, 50, 30, 60),
    ("Pergola", 1, 362, 60, 450, 60, 200, 280, 150, 300),
]

# "Tam" no tiene fila propia en el catalogo: aparece unicamente dentro de las
# combinaciones "Danubio Abierto" (158 m2) y "Dan+Tam+Rhin" (242 m2). Sus
# aforos se deducen por diferencia y solo se cargan los que coinciden en ambas
# combinaciones; el resto queda sin dato en vez de inventarse.
SALON_TAM_DEDUCIDO = ("Tam", 2, 50, None, None, None, 50, 30, None, 20)

_MONTAJES_TITULARES = (
    ("U", 3),
    ("Auditorio", 4),
    ("Mesa imperial", 5),
    ("Escuela", 6),
    ("Mesa redonda 1,50 m (10 pax)", 7),
    ("Mesa redonda 1,20 m (5 pax)", 8),
    ("Coctel de pie", 9),
)


def _tipo_por_aforo(capacidad: int) -> str:
    """Clasifica el salon por su aforo maximo documentado."""
    if capacidad <= 12:
        return "Mesa ejecutiva"
    if capacidad <= 40:
        return "Sala de reuniones"
    if capacidad <= 70:
        return "Salon de eventos"
    return "Salon de gran capacidad"


def _filas_catalogo_salones() -> List[Tuple]:
    """Convierte la tabla del catalogo del hotel en filas de la tabla salones."""
    filas = []
    for fila in list(CATALOGO_SALONES_HPSF) + [SALON_TAM_DEDUCIDO]:
        nombre, piso, m2 = fila[0], fila[1], fila[2]
        aforos = [(titulo, fila[indice]) for titulo, indice in _MONTAJES_TITULARES
                  if fila[indice]]
        capacidad = max(valor for _, valor in aforos)
        filas.append((
            f"SALON-{_sin_acentos(nombre).upper()}",
            f"Salon {nombre}",
            _tipo_por_aforo(capacidad),
            capacidad,
            "Por confirmar con el hotel",
            0,  # el catalogo oficial no publica tarifas
            f"Piso {piso} - {m2} m2",
            "Por confirmar con el hotel",
            (
                "Aforos deducidos de las combinaciones Danubio Abierto (158 m2) y "
                "Dan+Tam+Rhin (242 m2); el salon no tiene fila propia en el "
                "catalogo, confirmar con el hotel: "
                if fila is SALON_TAM_DEDUCIDO
                else "Aforos del catalogo oficial: "
            )
            + ", ".join(f"{titulo} ({valor})" for titulo, valor in aforos)
            + f". Superficie {m2} m2. Tarifa por confirmar con el hotel.",
            "Plaza San Francisco",
            ", ".join(titulo for titulo, _ in aforos),
            1 if fila is SALON_TAM_DEDUCIDO else 0,
        ))
    return filas


def init_db() -> None:
    conn = get_db_connection()
    try:
        cursor = conn.cursor()

        # Ajustes de negocio editables desde la interfaz (tope de Compra Agil, etc.)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ajustes (
                clave TEXT PRIMARY KEY,
                valor INTEGER NOT NULL
            )
        """)
        conn.commit()

        # La carga de datos de ejemplo ocurre una sola vez por base. Si el
        # equipo borra todo, el siguiente arranque no los resucita.
        cursor.execute("SELECT 1 FROM ajustes WHERE clave = 'seed_demo'")
        seed_demo_hecho = cursor.fetchone() is not None

        # 1. Tabla de Salones del Hotel
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS salones (
                id_salon TEXT PRIMARY KEY,
                nombre TEXT NOT NULL,
                tipo TEXT NOT NULL,
                capacidad_maxima INTEGER NOT NULL,
                horario_disponible TEXT NOT NULL,
                tarifa_referencial INTEGER NOT NULL DEFAULT 0,
                ubicacion TEXT NOT NULL DEFAULT '',
                equipamiento TEXT NOT NULL DEFAULT '',
                descripcion TEXT NOT NULL DEFAULT '',
                propiedad TEXT NOT NULL DEFAULT 'Plaza San Francisco',
                montajes TEXT NOT NULL DEFAULT '',
                es_provisional INTEGER NOT NULL DEFAULT 0
            )
        """)
        conn.commit()

        # Migracion de columnas en caso de tabla preexistente
        cursor.execute("PRAGMA table_info(salones)")
        existing_salon_cols = {row[1] for row in cursor.fetchall()}
        if "ubicacion" not in existing_salon_cols:
            cursor.execute("ALTER TABLE salones ADD COLUMN ubicacion TEXT NOT NULL DEFAULT ''")
        if "equipamiento" not in existing_salon_cols:
            cursor.execute("ALTER TABLE salones ADD COLUMN equipamiento TEXT NOT NULL DEFAULT ''")
        if "descripcion" not in existing_salon_cols:
            cursor.execute("ALTER TABLE salones ADD COLUMN descripcion TEXT NOT NULL DEFAULT ''")
        if "propiedad" not in existing_salon_cols:
            cursor.execute("ALTER TABLE salones ADD COLUMN propiedad TEXT NOT NULL DEFAULT 'Plaza San Francisco'")
        if "montajes" not in existing_salon_cols:
            cursor.execute("ALTER TABLE salones ADD COLUMN montajes TEXT NOT NULL DEFAULT ''")
        if "es_provisional" not in existing_salon_cols:
            cursor.execute("ALTER TABLE salones ADD COLUMN es_provisional INTEGER NOT NULL DEFAULT 0")
        conn.commit()

        seed_salones = _filas_catalogo_salones()
        cursor.executemany("""
            INSERT OR IGNORE INTO salones (
                id_salon, nombre, tipo, capacidad_maxima, horario_disponible, tarifa_referencial,
                ubicacion, equipamiento, descripcion, propiedad, montajes, es_provisional
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, seed_salones)
        conn.commit()

        # 2. Tabla de Reservas y Ocupacion de Salones (Agenda / Bookings)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reservas_salones (
                id_reserva INTEGER PRIMARY KEY AUTOINCREMENT,
                id_salon TEXT NOT NULL,
                cliente_evento TEXT NOT NULL,
                organismo_o_empresa TEXT NOT NULL,
                tipo_evento TEXT NOT NULL,
                fecha_inicio TEXT NOT NULL,
                fecha_fin TEXT NOT NULL,
                horario TEXT NOT NULL,
                asistentes_estimados INTEGER NOT NULL DEFAULT 0,
                estado_reserva TEXT NOT NULL DEFAULT 'Confirmada',
                id_licitacion TEXT NOT NULL DEFAULT '',
                contacto_responsable TEXT NOT NULL DEFAULT '',
                observaciones TEXT NOT NULL DEFAULT '',
                FOREIGN KEY (id_salon) REFERENCES salones(id_salon)
            )
        """)
        conn.commit()

        cursor.execute("SELECT COUNT(*) FROM reservas_salones")
        count_reservas = cursor.fetchone()[0]
        if count_reservas == 0 and not seed_demo_hecho:
            seed_reservas = [
                (
                    "SALON-DANUBIO",
                    "Jornada de Planificacion Estrategica de Turismo",
                    "Subsecretaria de Turismo",
                    "Licitacion Estatal (Compra Agil)",
                    "2026-09-20",
                    "2026-09-20",
                    "08:30 a 18:30 hrs",
                    80,
                    "Confirmada",
                    "1058-12-COT24",
                    "Camila Morales - Jefatura de Eventos",
                    "Bloqueo formal vinculado a orden de compra adjudicada. Servicio de coffee break continuo."
                ),
                (
                    "SALON-PERGOLA",
                    "Foro Regional de Sostenibilidad Urbana y Cambio Climatico",
                    "Gobierno Regional Metropolitano de Santiago (GORE)",
                    "Congreso Gubernamental",
                    "2026-09-24",
                    "2026-09-25",
                    "08:00 a 18:00 hrs",
                    250,
                    "Confirmada",
                    "805-19-LP24",
                    "Rodrigo Valenzuela - Direccion de Comunicaciones GORE",
                    "Uso de amplificacion total, cabinas de interpretacion y acreditacion de delegaciones."
                ),
                (
                    "SALON-PERGOLA",
                    "Encuentro Trimestral de Politica Financiera y Proyecciones",
                    "Banco Central de Chile",
                    "Evento Corporativo Institucional",
                    "2026-09-22",
                    "2026-09-22",
                    "09:00 a 14:00 hrs",
                    130,
                    "Confirmada",
                    "",
                    "Patricia Silva - Departamento de Protocolo",
                    "Montaje tipo auditorio con servicio de desayuno ejecutivo previo y coctel de cierre."
                ),
                (
                    "SALON-PARRA",
                    "Sesion Mensual de Comite de Innovacion Industrial",
                    "SOFOFA / Federacion Gremial",
                    "Reunion Gremial Privada",
                    "2026-09-23",
                    "2026-09-23",
                    "14:00 a 19:00 hrs",
                    35,
                    "Confirmada",
                    "",
                    "Ignacio Larrain - Coordinacion Sectorial",
                    "Mesa en herradura, videoconferencia internacional y estacion permanente de cafe."
                ),
                (
                    "SALON-SENA",
                    "Junta Extraordinaria de Directorio y Finanzas",
                    "Hotel Plaza San Francisco (Directorio General)",
                    "Bloqueo Interno / Sesion de Directorio",
                    "2026-09-26",
                    "2026-09-26",
                    "08:30 a 13:30 hrs",
                    18,
                    "Confirmada",
                    "",
                    "Gerencia de Administracion y Finanzas",
                    "Revision de presupuestos semestrales y politicas comerciales de licitaciones publicas."
                ),
                (
                    "SALON-PERGOLA",
                    "Mantencion Preventiva de Iluminacion Escenica y Climatizacion",
                    "Servicios de Infraestructura Hotelera",
                    "Bloqueo de Mantenimiento Operativo",
                    "2026-09-29",
                    "2026-09-30",
                    "07:00 a 19:00 hrs",
                    0,
                    "Bloqueo Interno",
                    "",
                    "Jefatura Tecnica de Mantenimiento",
                    "Calibracion tecnica de proyectores laser y revision de ductos de climatizacion central."
                ),
                (
                    "SALON-PERGOLA",
                    "Seminario de Gestion Presupuestaria del Sector Publico",
                    "Direccion de Presupuestos (DIPRES)",
                    "Licitacion Estatal (Compra Agil)",
                    "2026-10-05",
                    "2026-10-05",
                    "08:30 a 13:00 hrs",
                    120,
                    "Tentativa",
                    "1840-22-COT24",
                    "Marcelo Fuentes - Adquisiciones DIPRES",
                    "Pre-reserva en espera de adjudicacion final en portal Mercado Publico."
                ),
                (
                    "SALON-DANUBIO",
                    "Conferencia Anual de Rectores Universitarios",
                    "Consejo de Rectores de las Universidades Chilenas (CRUCH)",
                    "Congreso Academico",
                    "2026-10-10",
                    "2026-10-11",
                    "08:30 a 19:00 hrs",
                    60,
                    "Confirmada",
                    "512-10-LE24",
                    "Secretaria General CRUCH",
                    "Jornada doble con uso continuo de pantalla interactiva y servicio gastronomico."
                )
            ]
            cursor.executemany("""
                INSERT INTO reservas_salones (
                    id_salon, cliente_evento, organismo_o_empresa, tipo_evento,
                    fecha_inicio, fecha_fin, horario, asistentes_estimados,
                    estado_reserva, id_licitacion, contacto_responsable, observaciones
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, seed_reservas)
            conn.commit()

        # 2. Tabla de Licitaciones
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
                descripcion_tdr TEXT,
                cantidad_asistentes INTEGER NOT NULL DEFAULT 0,
                tipo_jornada TEXT NOT NULL DEFAULT '',
                horario_evento TEXT NOT NULL DEFAULT '',
                id_salon_asignado TEXT NOT NULL DEFAULT '',
                propiedad TEXT NOT NULL DEFAULT 'Plaza San Francisco',
                revisada INTEGER NOT NULL DEFAULT 0,
                motivo_descarte TEXT NOT NULL DEFAULT '',
                notas TEXT NOT NULL DEFAULT '',
                costeo_validado INTEGER NOT NULL DEFAULT 0,
                sello_mujer INTEGER NOT NULL DEFAULT 0,
                jornada_40h INTEGER NOT NULL DEFAULT 0,
                sello_sernatur INTEGER NOT NULL DEFAULT 0,
                inclusion_laboral INTEGER NOT NULL DEFAULT 0,
                adjudicatario TEXT NOT NULL DEFAULT '',
                puntaje_adjudicacion REAL NOT NULL DEFAULT 0,
                precio_final INTEGER NOT NULL DEFAULT 0
            )
        """)
        conn.commit()

        # Migracion de columnas en caso de tabla preexistente
        cursor.execute("PRAGMA table_info(licitaciones)")
        existing_cols = {row[1] for row in cursor.fetchall()}
        nuevas_columnas = [
            ("cantidad_asistentes", "INTEGER NOT NULL DEFAULT 0"),
            ("tipo_jornada", "TEXT NOT NULL DEFAULT ''"),
            ("horario_evento", "TEXT NOT NULL DEFAULT ''"),
            ("id_salon_asignado", "TEXT NOT NULL DEFAULT ''"),
            ("propiedad", "TEXT NOT NULL DEFAULT 'Plaza San Francisco'"),
            ("revisada", "INTEGER NOT NULL DEFAULT 0"),
            ("motivo_descarte", "TEXT NOT NULL DEFAULT ''"),
            ("notas", "TEXT NOT NULL DEFAULT ''"),
            ("costeo_validado", "INTEGER NOT NULL DEFAULT 0"),
            ("sello_mujer", "INTEGER NOT NULL DEFAULT 0"),
            ("jornada_40h", "INTEGER NOT NULL DEFAULT 0"),
            ("sello_sernatur", "INTEGER NOT NULL DEFAULT 0"),
            ("inclusion_laboral", "INTEGER NOT NULL DEFAULT 0"),
            ("adjudicatario", "TEXT NOT NULL DEFAULT ''"),
            ("puntaje_adjudicacion", "REAL NOT NULL DEFAULT 0"),
            ("precio_final", "INTEGER NOT NULL DEFAULT 0"),
        ]
        for nombre, definicion in nuevas_columnas:
            if nombre not in existing_cols:
                cursor.execute(f"ALTER TABLE licitaciones ADD COLUMN {nombre} {definicion}")
        conn.commit()

        # 3. Historial de Ordenes de Compra que entrega el hotel en Excel.
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS historial_oc (
                id_oc INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha TEXT NOT NULL DEFAULT '',
                organismo TEXT NOT NULL DEFAULT '',
                objeto TEXT NOT NULL DEFAULT '',
                monto INTEGER NOT NULL DEFAULT 0,
                modalidad TEXT NOT NULL DEFAULT '',
                archivo TEXT NOT NULL DEFAULT '',
                cargado_en TEXT NOT NULL DEFAULT ''
            )
        """)
        conn.commit()

        cursor.execute("SELECT COUNT(*) FROM licitaciones")
        count = cursor.fetchone()[0]
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
                    "Arriendo de salon plenario para 80 asistentes con servicio de coctel y coffee break continuo.",
                    80,
                    "Jornada Completa (8 hrs)",
                    "08:30 a 18:30 hrs",
                    "SALON-DANUBIO"
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
                    "Alojamiento single superior para 35 expertos extranjeros durante 4 noches con desayuno y cena ejecutiva.",
                    35,
                    "Jornada Completa (8 hrs)",
                    "09:00 a 18:00 hrs",
                    "SALON-PARRA"
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
                    "Servicio de alimentacion para 120 personas. El presupuesto mandante queda por debajo del costo base hotel.",
                    120,
                    "Media Jornada Manana (4 hrs)",
                    "08:30 a 13:00 hrs",
                    "SALON-PERGOLA"
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
                    "Bloqueo de 40 habitaciones ejecutivas y uso de salon de convenciones durante 2 jornadas.",
                    60,
                    "Jornada Completa (8 hrs)",
                    "08:30 a 19:00 hrs",
                    "SALON-DANUBIO"
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
                    "Cena de premiacion anual en salon principal para 150 colaboradores. Adjudicado con exito.",
                    150,
                    "Nocturno / Cena",
                    "19:30 a 23:30 hrs",
                    "SALON-PERGOLA"
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
                    "Hospedaje por turnos rotativos. Nota: Falta Anexo 4 de Pacto de Integridad en bases iniciales.",
                    20,
                    "Horario Especial",
                    "Turnos rotativos 24 hrs",
                    ""
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
                    "Alerta Efecto ID: El ID de la ficha resumen no coincide con el correlativo de las bases adjuntas.",
                    250,
                    "Jornada Completa (8 hrs)",
                    "08:00 a 18:00 hrs",
                    "SALON-PERGOLA"
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
                    "Descartada por conflicto de disponibilidad de salones para la fecha requerida por el mandante.",
                    70,
                    "Media Jornada Tarde (4 hrs)",
                    "15:00 a 19:30 hrs",
                    "SALON-DANUBIO"
                ),
                (
                    "620-14-LE24",
                    "Hospedaje y Salones Seminario Internacional de Ciberseguridad",
                    "Agencia Nacional de Inteligencia",
                    "Alojamiento",
                    "Licitacion Publica",
                    "Region Metropolitana (Santiago)",
                    22000000,
                    17500000,
                    "Identificada",
                    "Valida",
                    1, 1, 1, 1,
                    "2026-09-15", "2026-10-02",
                    "Hospedaje para expositores internacionales y arriendo de salon plenario con cabinas de traduccion simultanea.",
                    180,
                    "Jornada Completa (8 hrs)",
                    "08:30 a 18:30 hrs",
                    "SALON-PERGOLA"
                )
            ]
        if count == 0 and not seed_demo_hecho:
            cursor.executemany("""
                INSERT INTO licitaciones (
                    id_licitacion, titulo, organismo, categoria, modalidad, region,
                    presupuesto_mandante, costo_base_hotel, estado_embudo, validacion_adjuntos,
                    tiene_anexo4, tiene_escrituras, tiene_poderes, tiene_vigencias,
                    fecha_publicacion, fecha_cierre, descripcion_tdr,
                    cantidad_asistentes, tipo_jornada, horario_evento, id_salon_asignado
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, seed_data)
            conn.commit()
        elif not seed_demo_hecho:
            lic_updates = [(row[17], row[20], row[0]) for row in seed_data if row[20]]
            cursor.executemany("""
                UPDATE licitaciones SET cantidad_asistentes = ?, id_salon_asignado = ?
                WHERE id_licitacion = ? AND (id_salon_asignado = '' OR id_salon_asignado IS NULL)
            """, lic_updates)
            conn.commit()

        cursor.execute(
            "INSERT OR IGNORE INTO ajustes (clave, valor) VALUES ('seed_demo', 1)"
        )
        conn.commit()
    finally:
        conn.close()


def get_all_salones() -> List[Dict[str, Any]]:
    conn = get_db_connection()
    try:
        rows = conn.execute("SELECT * FROM salones ORDER BY capacidad_maxima ASC").fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_salon_by_id(id_salon: str) -> Optional[Dict[str, Any]]:
    if not id_salon:
        return None
    conn = get_db_connection()
    try:
        row = conn.execute("SELECT * FROM salones WHERE id_salon = ?", (id_salon,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_salones_aptos(
    capacidad_minima: int,
    propiedad: Optional[str] = None
) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    try:
        query = "SELECT * FROM salones WHERE capacidad_maxima >= ?"
        params: List[Any] = [capacidad_minima]
        if propiedad:
            query += " AND propiedad = ?"
            params.append(propiedad)
        query += " ORDER BY capacidad_maxima ASC"
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


# Costos minimos referenciales para el descarte por presupuesto. El hotel puede
# ajustarlos en el codigo mientras no exista una pantalla de parametros.
# ponytail: constantes simples; mover a `ajustes` si el hotel cambia tarifas seguido.
COSTO_ALIMENTACION_PERSONA = 15000
COSTO_HABITACION_PERSONA = 65000


def calcular_costo_minimo(
    categoria: str,
    cantidad_asistentes: int,
    id_salon: Optional[str] = None
) -> int:
    """Costo minimo operativo: salon + alimentacion o habitacion por persona."""
    asistentes = max(0, int(cantidad_asistentes or 0))
    salon = get_salon_by_id(id_salon) if id_salon else None
    costo = int(salon["tarifa_referencial"]) if salon else 0
    if categoria == "Alojamiento":
        costo += asistentes * COSTO_HABITACION_PERSONA
    else:
        costo += asistentes * COSTO_ALIMENTACION_PERSONA
    return costo


def registrar_evaluacion(id_licitacion: str, datos: Dict[str, Any]) -> Dict[str, Any]:
    """
    Guarda la evaluacion operativa y aplica la regla de presupuesto mandatorio.
    Retorna el registro actualizado.
    """
    lic = get_licitacion_by_id(id_licitacion)
    if not lic:
        return {}

    cambios = dict(datos)
    if (
        cambios.get("costeo_validado")
        and cambios.get("costo_base_hotel", 0) > 0
        and lic["estado_embudo"] != "Adjudicada"
    ):
        if cambios["costo_base_hotel"] > lic["presupuesto_mandante"]:
            cambios["estado_embudo"] = "Descartada"
            cambios["motivo_descarte"] = "Precio"
        elif lic["estado_embudo"] == "Descartada" and lic["motivo_descarte"] == "Precio":
            cambios["estado_embudo"] = "Calificada"
            cambios["motivo_descarte"] = ""

    update_licitacion(id_licitacion, cambios)
    return get_licitacion_by_id(id_licitacion) or {}


def _filtros_reservas(
    id_salon: Optional[str] = None,
    fecha_desde: Optional[str] = None,
    q: Optional[str] = None
) -> Tuple[str, List[Any]]:
    """WHERE compartido entre listado y conteo: los filtros no pueden divergir."""
    where = " WHERE 1=1"
    params: List[Any] = []
    if id_salon:
        where += " AND r.id_salon = ?"
        params.append(id_salon)
    if fecha_desde:
        where += " AND r.fecha_fin >= ?"
        params.append(fecha_desde)
    if q:
        where += " AND (r.cliente_evento LIKE ? OR r.organismo_o_empresa LIKE ? OR r.tipo_evento LIKE ? OR r.id_licitacion LIKE ?)"
        term = f"%{q}%"
        params.extend([term, term, term, term])
    return where, params


def count_reservas(
    id_salon: Optional[str] = None,
    fecha_desde: Optional[str] = None,
    q: Optional[str] = None
) -> int:
    where, params = _filtros_reservas(id_salon, fecha_desde, q)
    conn = get_db_connection()
    try:
        row = conn.execute(
            "SELECT COUNT(*) AS total FROM reservas_salones r" + where, params
        ).fetchone()
        return int(row["total"])
    finally:
        conn.close()


def get_all_reservas(
    id_salon: Optional[str] = None,
    fecha_desde: Optional[str] = None,
    q: Optional[str] = None,
    limit: Optional[int] = None,
    offset: int = 0
) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    try:
        where, params = _filtros_reservas(id_salon, fecha_desde, q)
        query = """
            SELECT r.*,
                   s.nombre AS nombre_salon,
                   s.tipo AS tipo_salon,
                   s.capacidad_maxima AS capacidad_salon,
                   s.horario_disponible AS horario_salon,
                   s.ubicacion AS ubicacion_salon
            FROM reservas_salones r
            LEFT JOIN salones s ON r.id_salon = s.id_salon
        """ + where + " ORDER BY r.fecha_inicio ASC, r.id_reserva ASC"
        if limit is not None:
            query += " LIMIT ? OFFSET ?"
            params = params + [int(limit), int(offset)]
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_reservas_by_salon(id_salon: str) -> List[Dict[str, Any]]:
    return get_all_reservas(id_salon=id_salon) if id_salon else []


def get_conflictos_reserva(
    id_salon: str,
    fecha_inicio: str,
    fecha_fin: str,
    exclude_id_reserva: Optional[int] = None
) -> List[Dict[str, Any]]:
    if not id_salon or not fecha_inicio or not fecha_fin:
        return []
    conn = get_db_connection()
    try:
        query = """
            SELECT r.*,
                   s.nombre AS nombre_salon
            FROM reservas_salones r
            LEFT JOIN salones s ON r.id_salon = s.id_salon
            WHERE r.id_salon = ?
              AND r.fecha_inicio <= ?
              AND r.fecha_fin >= ?
        """
        params = [id_salon, fecha_fin, fecha_inicio]
        if exclude_id_reserva:
            query += " AND r.id_reserva != ?"
            params.append(exclude_id_reserva)
        query += " ORDER BY r.fecha_inicio ASC"
        rows = conn.execute(query, tuple(params)).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_salon_detalle(id_salon: str) -> Optional[Dict[str, Any]]:
    salon = get_salon_by_id(id_salon)
    if not salon:
        return None
    reservas = get_reservas_by_salon(id_salon)
    return {**salon, "reservas": reservas, "total_reservas": len(reservas)}


ALLOWED_COLUMNS_RESERVAS = {
    "id_salon", "cliente_evento", "organismo_o_empresa", "tipo_evento",
    "fecha_inicio", "fecha_fin", "horario", "asistentes_estimados",
    "estado_reserva", "id_licitacion", "contacto_responsable", "observaciones"
}


def get_reserva_by_id(id_reserva: int) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    try:
        row = conn.execute("""
            SELECT r.*,
                   s.nombre AS nombre_salon
            FROM reservas_salones r
            LEFT JOIN salones s ON r.id_salon = s.id_salon
            WHERE r.id_reserva = ?
        """, (id_reserva,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def update_reserva(id_reserva: int, data: Dict[str, Any]) -> bool:
    valid_data = {k: v for k, v in data.items() if k in ALLOWED_COLUMNS_RESERVAS}
    if not valid_data:
        return False
    conn = get_db_connection()
    try:
        fields = [f"{k} = ?" for k in valid_data]
        values = list(valid_data.values()) + [id_reserva]
        cursor = conn.execute(f"UPDATE reservas_salones SET {', '.join(fields)} WHERE id_reserva = ?", values)
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def delete_reserva(id_reserva: int) -> bool:
    conn = get_db_connection()
    try:
        cursor = conn.execute("DELETE FROM reservas_salones WHERE id_reserva = ?", (id_reserva,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def create_reserva(data: Dict[str, Any]) -> Optional[int]:
    conn = get_db_connection()
    try:
        payload = {
            "asistentes_estimados": 0, "estado_reserva": "Confirmada",
            "id_licitacion": "", "contacto_responsable": "", "observaciones": "",
            **data
        }
        # BEGIN IMMEDIATE serializa el chequeo y el INSERT: dos usuarios no
        # pueden pasar el control de colisiones a la vez.
        conn.execute("BEGIN IMMEDIATE")
        if payload["estado_reserva"] == "Confirmada":
            choque = conn.execute("""
                SELECT 1 FROM reservas_salones
                WHERE id_salon = ? AND estado_reserva = 'Confirmada'
                  AND fecha_inicio <= ? AND fecha_fin >= ?
                LIMIT 1
            """, (payload["id_salon"], payload["fecha_fin"], payload["fecha_inicio"])).fetchone()
            if choque:
                conn.rollback()
                return None
        cursor = conn.execute("""
            INSERT INTO reservas_salones (
                id_salon, cliente_evento, organismo_o_empresa, tipo_evento,
                fecha_inicio, fecha_fin, horario, asistentes_estimados,
                estado_reserva, id_licitacion, contacto_responsable, observaciones
            ) VALUES (
                :id_salon, :cliente_evento, :organismo_o_empresa, :tipo_evento,
                :fecha_inicio, :fecha_fin, :horario, :asistentes_estimados,
                :estado_reserva, :id_licitacion, :contacto_responsable, :observaciones
            )
        """, payload)
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()



def _filtros_licitaciones(
    categoria: Optional[str] = None,
    modalidad: Optional[str] = None,
    estado: Optional[str] = None,
    q: Optional[str] = None,
    propiedad: Optional[str] = None,
    cliente_clave: Optional[str] = None
) -> Tuple[str, List[Any]]:
    """Construye el WHERE compartido entre listado y conteo (evita divergencia)."""
    where = " WHERE 1=1"
    params: List[Any] = []
    if categoria:
        where += " AND l.categoria = ?"
        params.append(categoria)
    if modalidad:
        where += " AND l.modalidad = ?"
        params.append(modalidad)
    if estado:
        where += " AND l.estado_embudo = ?"
        params.append(estado)
    if propiedad:
        where += " AND l.propiedad = ?"
        params.append(propiedad)
    if cliente_clave:
        alias = _alias_cliente_clave(cliente_clave)
        if alias:
            # SQLite LIKE no ignora tildes: "educacion" no calza con "Educación".
            where += " AND (" + " OR ".join(
                "(sin_acentos(l.organismo) LIKE ? OR sin_acentos(l.titulo) LIKE ?)"
                for _ in alias
            ) + ")"
            for a in alias:
                params.extend([f"%{a}%", f"%{a}%"])
        else:
            where += " AND 1=0"  # cliente fuera de la lista configurable
    if q:
        where += " AND (l.id_licitacion LIKE ? OR l.titulo LIKE ? OR l.organismo LIKE ? OR l.notas LIKE ?)"
        term = f"%{q}%"
        params.extend([term, term, term, term])
    return where, params


def count_licitaciones(
    categoria: Optional[str] = None,
    modalidad: Optional[str] = None,
    estado: Optional[str] = None,
    q: Optional[str] = None,
    propiedad: Optional[str] = None,
    cliente_clave: Optional[str] = None
) -> int:
    where, params = _filtros_licitaciones(categoria, modalidad, estado, q, propiedad, cliente_clave)
    conn = get_db_connection()
    try:
        row = conn.execute(
            "SELECT COUNT(*) AS total FROM licitaciones l" + where, params
        ).fetchone()
        return int(row["total"])
    finally:
        conn.close()


def get_all_licitaciones(
    categoria: Optional[str] = None,
    modalidad: Optional[str] = None,
    estado: Optional[str] = None,
    q: Optional[str] = None,
    propiedad: Optional[str] = None,
    cliente_clave: Optional[str] = None,
    limit: Optional[int] = None,
    offset: int = 0
) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    try:
        where, params = _filtros_licitaciones(categoria, modalidad, estado, q, propiedad, cliente_clave)
        query = """
            SELECT l.*,
                   s.nombre AS nombre_salon,
                   s.capacidad_maxima AS capacidad_salon,
                   s.tipo AS tipo_salon,
                   s.horario_disponible AS horario_salon,
                   s.es_provisional AS salon_provisional
            FROM licitaciones l
            LEFT JOIN salones s ON l.id_salon_asignado = s.id_salon
        """ + where + " ORDER BY l.fecha_cierre ASC"
        if limit is not None:
            query += " LIMIT ? OFFSET ?"
            params = params + [int(limit), int(offset)]
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_licitaciones_para_reserva(limit: int = 300) -> List[Dict[str, Any]]:
    """Opciones del formulario de reserva: recientes, sin descartadas, con tope."""
    conn = get_db_connection()
    try:
        rows = conn.execute("""
            SELECT id_licitacion, titulo
            FROM licitaciones
            WHERE estado_embudo != 'Descartada'
            ORDER BY fecha_cierre DESC
            LIMIT ?
        """, (int(limit),)).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_licitacion_by_id(id_licitacion: str) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    try:
        query = """
            SELECT l.*,
                   s.nombre AS nombre_salon,
                   s.capacidad_maxima AS capacidad_salon,
                   s.tipo AS tipo_salon,
                   s.horario_disponible AS horario_salon,
                   s.es_provisional AS salon_provisional
            FROM licitaciones l
            LEFT JOIN salones s ON l.id_salon_asignado = s.id_salon
            WHERE l.id_licitacion = ?
        """
        row = conn.execute(query, (id_licitacion,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_oportunidades_prioritarias(
    hoy: Optional[str] = None,
    limit: int = 8,
    **filtros
) -> List[Dict[str, Any]]:
    """
    Oportunidades abiertas con match viable: presupuesto cubre el costo y, si
    hay aforo, el salon asignado tiene capacidad suficiente.

    `filtros` acepta los mismos nombres que `_filtros_licitaciones`, de modo que
    el bloque priorizado respete la misma busqueda que el listado de abajo.
    """
    fecha_referencia = hoy or date.today().isoformat()
    conn = get_db_connection()
    try:
        query = """
            SELECT l.*,
                   s.nombre AS nombre_salon,
                   s.capacidad_maxima AS capacidad_salon,
                   s.es_provisional AS salon_provisional
            FROM licitaciones l
            LEFT JOIN salones s ON l.id_salon_asignado = s.id_salon
            WHERE l.estado_embudo NOT IN ('Descartada', 'Adjudicada')
              AND l.fecha_cierre >= ?
              AND l.presupuesto_mandante > 0
              AND l.costo_base_hotel <= l.presupuesto_mandante
              AND (
                    l.cantidad_asistentes = 0
                    OR l.id_salon_asignado = ''
                    OR s.capacidad_maxima >= l.cantidad_asistentes
              )
        """
        params: List[Any] = [fecha_referencia]

        # Los filtros del tablero se reutilizan tal cual; solo se retira la
        # clausula WHERE porque la base de esta consulta ya la trae.
        extra_where, extra_params = _filtros_licitaciones(**filtros)
        query += extra_where.replace(" WHERE 1=1", "", 1)
        params.extend(extra_params)

        query += " ORDER BY l.fecha_cierre ASC LIMIT ?"
        params.append(int(limit))
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def marcar_inviables() -> int:
    """Descarta oportunidades con costeo validado que superan el presupuesto."""
    conn = get_db_connection()
    try:
        cursor = conn.execute("""
            UPDATE licitaciones
            SET estado_embudo = 'Descartada', motivo_descarte = 'Precio'
            WHERE costeo_validado = 1
              AND presupuesto_mandante > 0
              AND costo_base_hotel > presupuesto_mandante
              AND estado_embudo NOT IN ('Descartada', 'Adjudicada')
        """)
        conn.commit()
        return cursor.rowcount
    finally:
        conn.close()


def create_licitacion(data: Dict[str, Any]) -> str:
    conn = get_db_connection()
    try:
        payload = {
            "cantidad_asistentes": 0, "tipo_jornada": "",
            "horario_evento": "", "id_salon_asignado": "",
            "propiedad": "Plaza San Francisco", "revisada": 0,
            "motivo_descarte": "", "notas": "", "costeo_validado": 0,
            "sello_mujer": 0, "jornada_40h": 0,
            "sello_sernatur": 0, "inclusion_laboral": 0,
            **data
        }
        conn.execute("""
            INSERT INTO licitaciones (
                id_licitacion, titulo, organismo, categoria, modalidad, region,
                presupuesto_mandante, costo_base_hotel, estado_embudo, validacion_adjuntos,
                tiene_anexo4, tiene_escrituras, tiene_poderes, tiene_vigencias,
                fecha_publicacion, fecha_cierre, descripcion_tdr,
                cantidad_asistentes, tipo_jornada, horario_evento, id_salon_asignado,
                propiedad, revisada, motivo_descarte, notas, costeo_validado,
                sello_mujer, jornada_40h, sello_sernatur, inclusion_laboral
            ) VALUES (
                :id_licitacion, :titulo, :organismo, :categoria, :modalidad, :region,
                :presupuesto_mandante, :costo_base_hotel, :estado_embudo, :validacion_adjuntos,
                :tiene_anexo4, :tiene_escrituras, :tiene_poderes, :tiene_vigencias,
                :fecha_publicacion, :fecha_cierre, :descripcion_tdr,
                :cantidad_asistentes, :tipo_jornada, :horario_evento, :id_salon_asignado,
                :propiedad, :revisada, :motivo_descarte, :notas, :costeo_validado,
                :sello_mujer, :jornada_40h, :sello_sernatur, :inclusion_laboral
            )
        """, payload)
        conn.commit()
        return str(data["id_licitacion"])
    finally:
        conn.close()


def update_licitacion(id_licitacion: str, data: Dict[str, Any]) -> bool:
    valid_data = {k: v for k, v in data.items() if k in ALLOWED_COLUMNS}
    if not valid_data:
        return False
    conn = get_db_connection()
    try:
        fields = [f"{k} = ?" for k in valid_data]
        values = list(valid_data.values()) + [id_licitacion]
        cursor = conn.execute(f"UPDATE licitaciones SET {', '.join(fields)} WHERE id_licitacion = ?", values)
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def append_nota(id_licitacion: str, linea: str) -> bool:
    """Agrega una nota en una sola escritura, sin leer y reescribir el historial."""
    conn = get_db_connection()
    try:
        cursor = conn.execute("""
            UPDATE licitaciones
            SET notas = CASE WHEN notas = '' THEN ? ELSE notas || char(10) || ? END
            WHERE id_licitacion = ?
        """, (linea, linea, id_licitacion))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def delete_licitacion(id_licitacion: str) -> bool:
    conn = get_db_connection()
    try:
        conn.execute(
            "UPDATE reservas_salones SET id_licitacion = '' WHERE id_licitacion = ?",
            (id_licitacion,)
        )
        cursor = conn.execute(
            "DELETE FROM licitaciones WHERE id_licitacion = ?",
            (id_licitacion,)
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def get_funnel_metrics() -> Dict[str, int]:
    conn = get_db_connection()
    try:
        rows = conn.execute(
            "SELECT estado_embudo, COUNT(*) as total FROM licitaciones GROUP BY estado_embudo"
        ).fetchall()
        ca_row = conn.execute(
            "SELECT COUNT(*) as total FROM licitaciones WHERE modalidad = 'Compra Agil'"
        ).fetchone()

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
    finally:
        conn.close()


TOPE_COMPRA_AGIL_DEFECTO = 6900000


def get_tope_compra_agil() -> int:
    conn = get_db_connection()
    try:
        row = conn.execute(
            "SELECT valor FROM ajustes WHERE clave = 'tope_compra_agil'"
        ).fetchone()
        return int(row["valor"]) if row else TOPE_COMPRA_AGIL_DEFECTO
    finally:
        conn.close()


def set_tope_compra_agil(valor: int) -> None:
    conn = get_db_connection()
    try:
        conn.execute(
            "INSERT OR REPLACE INTO ajustes (clave, valor) VALUES ('tope_compra_agil', ?)",
            (int(valor),)
        )
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Historial de Ordenes de Compra (Excel que entrega el hotel).
# El equipo aun no confirma las cabeceras exactas: se aceptan alias y las
# columnas que falten quedan vacias en vez de abortar la carga.
# ---------------------------------------------------------------------------

COLUMNAS_OC = {
    "fecha": ("fecha", "fecha adjudicacion", "fecha oc", "fechaa o"),
    "organismo": ("organismo", "cliente", "comprador", "institucion", "unidad de gasto"),
    "objeto": ("objeto", "descripcion", "materia", "glosa", "nombre"),
    "monto": ("monto", "monto total", "precio", "monto adjudicado", "valor"),
    "modalidad": ("modalidad", "tipo", "tipo de compra"),
}


def _normalizar_encabezado(texto: Any) -> str:
    limpio = _sin_acentos(str(texto or "")).lower().replace(".", "")
    limpio = re.sub(r"\([^)]*\)", " ", limpio).replace("$", " ")
    return " ".join(limpio.split())


def _monto_oc(valor: Any) -> int:
    """Pesos chilenos: '$1.234.567', '1.234.567', '4800000.0' o '1234567'."""
    if isinstance(valor, (int, float)):
        return int(valor)
    s = str(valor or "").strip()
    decimal = re.search(r"[,.]\d{1,2}$", s)
    if decimal:
        s = s[:decimal.start()]
    digitos = re.sub(r"\D", "", s)
    return int(digitos) if digitos else 0


def _fecha_oc(valor: Any) -> str:
    s = str(valor or "").strip()
    m = re.match(r"^(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{2,4})$", s)
    if m:
        dia, mes, anio = m.groups()
        anio = f"20{anio}" if len(anio) == 2 else anio
        return f"{anio}-{int(mes):02d}-{int(dia):02d}"
    return s[:10] if re.match(r"^\d{4}-\d{2}-\d{2}", s) else s


def importar_historial_oc(filas: List[List[Any]], archivo: str = "") -> int:
    """
    Importa la hoja ya leida del Excel de OC. Primera fila = encabezados.
    Retorna la cantidad de filas insertadas.
    """
    if not filas:
        return 0

    encabezados = [_normalizar_encabezado(c) for c in filas[0]]
    idx: Dict[str, int] = {}
    for campo, alias in COLUMNAS_OC.items():
        for i, enc in enumerate(encabezados):
            if enc in alias:
                idx[campo] = i
                break

    if "objeto" not in idx and "organismo" not in idx:
        return 0  # ninguna columna reconocible: no es un Excel de OC

    def celda(fila: List[Any], campo: str) -> str:
        i = idx.get(campo)
        if i is None or i >= len(fila):
            return ""
        return str(fila[i] or "").strip()

    hoy = date.today().isoformat()
    registros = []
    for fila in filas[1:]:
        objeto = celda(fila, "objeto")
        organismo = celda(fila, "organismo")
        if not objeto and not organismo:
            continue
        registros.append((
            _fecha_oc(celda(fila, "fecha")),
            organismo,
            objeto,
            _monto_oc(celda(fila, "monto")),
            celda(fila, "modalidad"),
            archivo,
            hoy,
        ))

    if not registros:
        return 0

    conn = get_db_connection()
    try:
        # Re-subir el mismo archivo reemplaza su carga anterior, no la duplica.
        if archivo:
            conn.execute("DELETE FROM historial_oc WHERE archivo = ?", (archivo,))
        conn.executemany(
            """
            INSERT INTO historial_oc
                (fecha, organismo, objeto, monto, modalidad, archivo, cargado_en)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            registros,
        )
        conn.commit()
        return len(registros)
    finally:
        conn.close()


def get_historial_oc(limit: int = 500) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM historial_oc ORDER BY fecha DESC LIMIT ?",
            (int(limit),)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_resumen_historial_oc() -> Dict[str, int]:
    conn = get_db_connection()
    try:
        row = conn.execute(
            "SELECT COUNT(*) AS registros, COALESCE(SUM(monto), 0) AS monto FROM historial_oc"
        ).fetchone()
        return {"registros": int(row["registros"]), "monto_total": int(row["monto"])}
    finally:
        conn.close()


def get_experiencia_organismo(organismo: str) -> Dict[str, int]:
    """
    Cruce de experiencia: OC que comparten un termino significativo (>= 5
    letras) con el organismo de la licitacion.
    ponytail: comparacion en memoria sobre una palabra comun; basta mientras el
    historial sea de cientos de filas, no de decenas de miles.
    """
    # Palabras que aparecen en casi cualquier organismo publico y no identifican
    # a un cliente: sin este filtro Mineduc "comparte" historial con Minsal.
    genericas = {
        "ministerio", "servicio", "servicios", "nacional", "gobierno",
        "regional", "subsecretaria", "direccion", "consejo", "agencia",
        "instituto", "universidad", "municipalidad", "corporacion",
        "fundacion", "comision", "secretaria", "departamento", "unidad",
        "division", "centro",
    }
    propio = {w for w in _sin_acentos(organismo).lower().split() if len(w) >= 5} - genericas
    if not propio:
        return {"registros": 0, "monto_total": 0}

    registros = monto_total = 0
    for oc in get_historial_oc(limit=5000):
        otro = {w for w in _sin_acentos(oc["organismo"]).lower().split() if len(w) >= 5} - genericas
        if propio & otro:
            registros += 1
            monto_total += int(oc["monto"])
    return {"registros": registros, "monto_total": monto_total}


# ---------------------------------------------------------------------------
# Benchmarking de adjudicaciones: quien gano, con que puntaje y a que precio.
# La fuente la carga el equipo (la API publica no expone puntajes).
# ---------------------------------------------------------------------------

def get_benchmarking(licitaciones: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """Comparacion entre lo adjudicado, lo que pide el mandante y nuestro costo."""
    if licitaciones is None:
        licitaciones = get_all_licitaciones(limit=5000)

    filas = []
    for lic in licitaciones:
        precio = int(lic.get("precio_final") or 0)
        if precio <= 0:
            continue
        presupuesto = int(lic.get("presupuesto_mandante") or 0)
        costo = int(lic.get("costo_base_hotel") or 0)
        filas.append({
            "id_licitacion": lic["id_licitacion"],
            "titulo": lic["titulo"],
            "organismo": lic["organismo"],
            "adjudicatario": lic.get("adjudicatario") or "",
            "puntaje_adjudicacion": lic.get("puntaje_adjudicacion") or 0,
            "precio_final": precio,
            "presupuesto_mandante": presupuesto,
            "costo_base_hotel": costo,
            # > 0 el adjudicatario pago mas de lo que pedia el mandante
            "desviacion_pct": round(((precio - presupuesto) / presupuesto) * 100, 1) if presupuesto else 0,
            # > 0 hay espacio para ofertar por debajo del precio observado
            "margen_vs_costo": precio - costo,
        })
    filas.sort(key=lambda f: f["precio_final"], reverse=True)
    return {
        "filas": filas,
        "adjudicaciones": len(filas),
        "precio_promedio": int(round(sum(f["precio_final"] for f in filas) / len(filas))) if filas else 0,
    }
