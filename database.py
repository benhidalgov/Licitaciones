import os
import sqlite3
from typing import Any, Dict, List, Optional

DB_NAME = os.path.join(os.path.dirname(os.path.abspath(__file__)), "licitaciones.db")

ALLOWED_COLUMNS = {
    "titulo", "organismo", "categoria", "modalidad", "region",
    "presupuesto_mandante", "costo_base_hotel", "estado_embudo",
    "validacion_adjuntos", "tiene_anexo4", "tiene_escrituras",
    "tiene_poderes", "tiene_vigencias", "fecha_publicacion",
    "fecha_cierre", "descripcion_tdr",
    "cantidad_asistentes", "tipo_jornada", "horario_evento", "id_salon_asignado"
}


def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


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
                descripcion TEXT NOT NULL DEFAULT ''
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
        conn.commit()

        cursor.execute("SELECT COUNT(*) FROM salones")
        count_salones = cursor.fetchone()[0]
        seed_salones = [
            (
                "SALON-PLENARIO",
                "Gran Salon San Francisco (Plenario)",
                "Plenario / Conferencia",
                300,
                "08:00 - 23:00 hrs",
                850000,
                "Nivel Subterraneo - Centro de Convenciones",
                "Pantalla LED 4K, 4 proyectores laser, audio envolvente, cabinas de traduccion simultanea, climatizacion dual, microfonia inalambrica",
                "Espacio de maxima capacidad del Hotel Plaza San Francisco, configurable en montaje plenario, auditorio o cena de gala. Ideal para congresos de gran escala y foros gubernamentales."
            ),
            (
                "SALON-COLONIAL",
                "Salon Colonial",
                "Banquete / Eventos",
                150,
                "08:00 - 23:00 hrs",
                550000,
                "Piso 2 - Sector Oriente",
                "Proyector de alta resolucion, telon motorizado, iluminacion dimerizable, audio estereo, tarima desmontable, climatizacion independiente",
                "Salon clasico con terminaciones de estilo colonial y amplios ventanales. Especializado en almuerzos corporativos, cenas de clausura y ceremonias de premiacion."
            ),
            (
                "SALON-ALAMEDA",
                "Salon Alameda",
                "Seminario / Conferencias",
                80,
                "08:30 - 20:00 hrs",
                380000,
                "Piso 1 - Hall Principal",
                "Pantalla interactiva 85 pulgadas, streaming para transmision hibrida, microfono de atril y climatizacion automatica",
                "Espacio versatil ubicado a pasos del lobby central. Optimo para seminarios medianos, talleres de capacitacion tecnica y conferencias de prensa."
            ),
            (
                "SALON-LONDRES",
                "Salon Londres",
                "Reuniones / Taller",
                40,
                "08:30 - 19:30 hrs",
                260000,
                "Piso 2 - Ala Ejecutiva",
                "Pantalla Smart TV 75 pulgadas, camara para videoconferencia grupal, pizarra magnetica y conexion de red dedicada de alta velocidad",
                "Disenado para mesas redondas, sesiones de comite de expertos y jornadas de trabajo colaborativo de grupos de hasta 40 personas."
            ),
            (
                "SALON-DIRECTORIO",
                "Salon Directorio Ejecutivo",
                "Directorio / Mesa Ejecutiva",
                20,
                "08:00 - 20:00 hrs",
                190000,
                "Piso 3 - Area Presidencial",
                "Mesa de directorio ejecutiva en madera noble, pantalla 65 pulgadas para presentaciones, videoconferencia Polycom, coffeebar privado",
                "Ambiente exclusivo de alta privacidad para reuniones de directorio, juntas de accionistas y firmas protocolarias solemnes."
            )
        ]
        if count_salones == 0:
            cursor.executemany("""
                INSERT INTO salones (
                    id_salon, nombre, tipo, capacidad_maxima, horario_disponible, tarifa_referencial,
                    ubicacion, equipamiento, descripcion
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, seed_salones)
            conn.commit()
        else:
            salon_updates = [(s[6], s[7], s[8], s[0]) for s in seed_salones]
            cursor.executemany("""
                UPDATE salones SET ubicacion = ?, equipamiento = ?, descripcion = ?
                WHERE id_salon = ? AND (ubicacion = '' OR ubicacion IS NULL)
            """, salon_updates)
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
        if count_reservas == 0:
            seed_reservas = [
                (
                    "SALON-ALAMEDA",
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
                    "SALON-PLENARIO",
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
                    "SALON-COLONIAL",
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
                    "SALON-LONDRES",
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
                    "SALON-DIRECTORIO",
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
                    "SALON-PLENARIO",
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
                    "SALON-COLONIAL",
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
                    "SALON-ALAMEDA",
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
                id_salon_asignado TEXT NOT NULL DEFAULT ''
            )
        """)
        conn.commit()

        # Migracion de columnas en caso de tabla preexistente
        cursor.execute("PRAGMA table_info(licitaciones)")
        existing_cols = {row[1] for row in cursor.fetchall()}
        if "cantidad_asistentes" not in existing_cols:
            cursor.execute("ALTER TABLE licitaciones ADD COLUMN cantidad_asistentes INTEGER NOT NULL DEFAULT 0")
        if "tipo_jornada" not in existing_cols:
            cursor.execute("ALTER TABLE licitaciones ADD COLUMN tipo_jornada TEXT NOT NULL DEFAULT ''")
        if "horario_evento" not in existing_cols:
            cursor.execute("ALTER TABLE licitaciones ADD COLUMN horario_evento TEXT NOT NULL DEFAULT ''")
        if "id_salon_asignado" not in existing_cols:
            cursor.execute("ALTER TABLE licitaciones ADD COLUMN id_salon_asignado TEXT NOT NULL DEFAULT ''")
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
                    "SALON-ALAMEDA"
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
                    "SALON-LONDRES"
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
                    "SALON-COLONIAL"
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
                    "SALON-ALAMEDA"
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
                    "SALON-COLONIAL"
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
                    "SALON-PLENARIO"
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
                    "SALON-ALAMEDA"
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
                    "SALON-PLENARIO"
                )
            ]
        if count == 0:
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
        else:
            lic_updates = [(row[17], row[20], row[0]) for row in seed_data if row[20]]
            cursor.executemany("""
                UPDATE licitaciones SET cantidad_asistentes = ?, id_salon_asignado = ?
                WHERE id_licitacion = ? AND (id_salon_asignado = '' OR id_salon_asignado IS NULL)
            """, lic_updates)
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


def get_salones_aptos(capacidad_minima: int) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM salones WHERE capacidad_maxima >= ? ORDER BY capacidad_maxima ASC",
            (capacidad_minima,)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_all_reservas(
    id_salon: Optional[str] = None,
    fecha_desde: Optional[str] = None,
    q: Optional[str] = None
) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    try:
        query = """
            SELECT r.*,
                   s.nombre AS nombre_salon,
                   s.tipo AS tipo_salon,
                   s.capacidad_maxima AS capacidad_salon,
                   s.horario_disponible AS horario_salon,
                   s.ubicacion AS ubicacion_salon
            FROM reservas_salones r
            LEFT JOIN salones s ON r.id_salon = s.id_salon
            WHERE 1=1
        """
        params: List[Any] = []
        if id_salon:
            query += " AND r.id_salon = ?"
            params.append(id_salon)
        if fecha_desde:
            query += " AND r.fecha_fin >= ?"
            params.append(fecha_desde)
        if q:
            query += " AND (r.cliente_evento LIKE ? OR r.organismo_o_empresa LIKE ? OR r.tipo_evento LIKE ? OR r.id_licitacion LIKE ?)"
            term = f"%{q}%"
            params.extend([term, term, term, term])
        query += " ORDER BY r.fecha_inicio ASC, r.id_reserva ASC"
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


def create_reserva(data: Dict[str, Any]) -> int:
    conn = get_db_connection()
    try:
        payload = {
            "asistentes_estimados": 0, "estado_reserva": "Confirmada",
            "id_licitacion": "", "contacto_responsable": "", "observaciones": "",
            **data
        }
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



def get_all_licitaciones(
    categoria: Optional[str] = None,
    modalidad: Optional[str] = None,
    estado: Optional[str] = None,
    q: Optional[str] = None
) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    try:
        query = """
            SELECT l.*,
                   s.nombre AS nombre_salon,
                   s.capacidad_maxima AS capacidad_salon,
                   s.tipo AS tipo_salon,
                   s.horario_disponible AS horario_salon
            FROM licitaciones l
            LEFT JOIN salones s ON l.id_salon_asignado = s.id_salon
            WHERE 1=1
        """
        params: List[Any] = []
        if categoria:
            query += " AND l.categoria = ?"
            params.append(categoria)
        if modalidad:
            query += " AND l.modalidad = ?"
            params.append(modalidad)
        if estado:
            query += " AND l.estado_embudo = ?"
            params.append(estado)
        if q:
            query += " AND (l.id_licitacion LIKE ? OR l.titulo LIKE ? OR l.organismo LIKE ?)"
            term = f"%{q}%"
            params.extend([term, term, term])
        query += " ORDER BY l.fecha_cierre ASC"
        rows = conn.execute(query, params).fetchall()
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
                   s.horario_disponible AS horario_salon
            FROM licitaciones l
            LEFT JOIN salones s ON l.id_salon_asignado = s.id_salon
            WHERE l.id_licitacion = ?
        """
        row = conn.execute(query, (id_licitacion,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def create_licitacion(data: Dict[str, Any]) -> str:
    conn = get_db_connection()
    try:
        payload = {
            "cantidad_asistentes": 0, "tipo_jornada": "",
            "horario_evento": "", "id_salon_asignado": "",
            **data
        }
        conn.execute("""
            INSERT INTO licitaciones (
                id_licitacion, titulo, organismo, categoria, modalidad, region,
                presupuesto_mandante, costo_base_hotel, estado_embudo, validacion_adjuntos,
                tiene_anexo4, tiene_escrituras, tiene_poderes, tiene_vigencias,
                fecha_publicacion, fecha_cierre, descripcion_tdr,
                cantidad_asistentes, tipo_jornada, horario_evento, id_salon_asignado
            ) VALUES (
                :id_licitacion, :titulo, :organismo, :categoria, :modalidad, :region,
                :presupuesto_mandante, :costo_base_hotel, :estado_embudo, :validacion_adjuntos,
                :tiene_anexo4, :tiene_escrituras, :tiene_poderes, :tiene_vigencias,
                :fecha_publicacion, :fecha_cierre, :descripcion_tdr,
                :cantidad_asistentes, :tipo_jornada, :horario_evento, :id_salon_asignado
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
