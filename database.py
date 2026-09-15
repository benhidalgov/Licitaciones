import sqlite3
from typing import Any, Dict, List, Optional

DB_NAME = "licitaciones.db"


def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_db_connection()
    try:
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
                    "Hospedaje para expositores internacionales y arriendo de salon plenario con cabinas de traduccion simultanea."
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
        query = "SELECT * FROM licitaciones WHERE 1=1"
        params: List[Any] = []
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
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_licitacion_by_id(id_licitacion: str) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    try:
        row = conn.execute(
            "SELECT * FROM licitaciones WHERE id_licitacion = ?",
            (id_licitacion,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def create_licitacion(data: Dict[str, Any]) -> str:
    conn = get_db_connection()
    try:
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
        return str(data["id_licitacion"])
    finally:
        conn.close()


def update_licitacion(id_licitacion: str, data: Dict[str, Any]) -> bool:
    if not data:
        return False
    conn = get_db_connection()
    try:
        fields = []
        values = []
        for k, v in data.items():
            fields.append(f"{k} = ?")
            values.append(v)
        values.append(id_licitacion)
        query = f"UPDATE licitaciones SET {', '.join(fields)} WHERE id_licitacion = ?"
        cursor = conn.execute(query, values)
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def delete_licitacion(id_licitacion: str) -> bool:
    conn = get_db_connection()
    try:
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
