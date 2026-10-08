"""
Modulo de integracion con API oficial de ChileCompra / Mercado Publico.
Permite consultar, filtrar semanticamente y sincronizar licitaciones y compras agiles
relevantes para la operacion del Hotel Plaza San Francisco.
"""

from datetime import datetime
import json
import logging
import os
import re
import ssl
from typing import Any, Dict, List, Optional
import unicodedata
import urllib.error
import urllib.parse
import urllib.request

import database

logger = logging.getLogger(__name__)

MERCADO_PUBLICO_BASE_URL = "https://api.mercadopublico.cl/servicios/v1/publico/licitaciones.json"

PATRON_ALOJAMIENTO = re.compile(
    r"\b(hospedaje|alojamiento|habitacion|habitaciones|pernoctacion|hotel|hoteles|hoteleria)\b",
    re.IGNORECASE
)

PATRON_EVENTOS = re.compile(
    r"\b(evento|eventos|catering|salon|salones|banqueteria|coffee break|coctel|cocteles|desayuno|almuerzo|cena|cenas)\b",
    re.IGNORECASE
)

PATRON_EXCLUSIONES = re.compile(
    r"\b(almacenamiento|almacen|habitabilidad|habitacional|vial|veredas|pavimentacion|petroleo|clinico|medicamento|medicamentos|quirurgico|oxigeno|repuesto|repuestos|techumbre|cubierta de zinc)\b",
    re.IGNORECASE
)


def _normalizar_texto(texto: str) -> str:
    """
    Normaliza el texto eliminando acentos y convirtiendo a minusculas
    para comparacion semantica uniforme.
    """
    if not texto:
        return ""
    nfkd = unicodedata.normalize("NFKD", texto)
    ascii_bytes = nfkd.encode("ASCII", "ignore")
    return ascii_bytes.decode("utf-8").lower()


def _create_ssl_context() -> ssl.SSLContext:
    """
    Genera contexto SSL para peticiones HTTPS.
    Respeta MERCADO_PUBLICO_SSL_VERIFY si se deshabilita explicitamente.
    """
    verify = os.environ.get("MERCADO_PUBLICO_SSL_VERIFY", "").strip().lower()
    if verify in ("0", "false", "no"):
        return ssl._create_unverified_context()
    try:
        return ssl.create_default_context()
    except Exception:
        return ssl._create_unverified_context()


def _fetch_url(url: str, timeout: int = 15) -> Optional[bytes]:
    """
    Ejecuta peticion HTTP a la API con gestion de contexto SSL
    y reintento tolerante a proxies corporativos de red.
    """
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Licitaciones-Hotel-Plaza-San-Francisco/1.0"}
    )
    ctx = _create_ssl_context()
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            return resp.read()
    except urllib.error.URLError as exc:
        if "CERTIFICATE_VERIFY_FAILED" in str(exc):
            try:
                unverified_ctx = ssl._create_unverified_context()
                with urllib.request.urlopen(req, timeout=timeout, context=unverified_ctx) as resp:
                    return resp.read()
            except Exception as retry_exc:
                logger.error(f"Error tras reintento SSL en {url}: {retry_exc}")
                return None
        logger.error(f"Error de red al consultar {url}: {exc}")
        return None
    except Exception as exc:
        logger.error(f"Error al consultar {url}: {exc}")
        return None


def parse_env_content(content: str) -> Dict[str, str]:
    """
    Parsea el contenido de un archivo .env en un diccionario clave-valor,
    ignorando lineas vacias, comentarios (#) y comillas circundantes.
    """
    env_vars: Dict[str, str] = {}
    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, val = line.split("=", 1)
            key = key.strip()
            val = val.strip()
            if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                val = val[1:-1]
            env_vars[key] = val
    return env_vars


def load_env_file(filepath: Optional[str] = None) -> Dict[str, str]:
    """
    Carga variables desde el archivo .env hacia os.environ.
    Si no se indica ruta, busca .env en el directorio raiz del proyecto.
    """
    if filepath is None:
        filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")

    if not os.path.isfile(filepath):
        return {}

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        parsed = parse_env_content(content)
        for k, v in parsed.items():
            if k not in os.environ:
                os.environ[k] = v
        return parsed
    except Exception as exc:
        logger.warning(f"Error al leer archivo de entorno {filepath}: {exc}")
        return {}


def get_ticket() -> Optional[str]:
    """
    Retorna el Ticket / API Key configurado en las variables de entorno.
    Retorna None si no existe o mantiene el valor placeholder predeterminado.
    """
    load_env_file()
    ticket = os.environ.get("MERCADO_PUBLICO_TICKET", "").strip()
    if not ticket or ticket == "TU_TICKET_AQUI":
        return None
    return ticket


def filtrar_y_clasificar_licitacion(item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Aplica filtro semantico de pertinencia hotelera y clasifica la licitacion
    segun categoria de servicio y modalidad de compra publica.
    Retorna el diccionario estructurado para la base de datos o None si se descarta.
    """
    codigo = str(item.get("CodigoExterno") or "").strip()
    nombre = str(item.get("Nombre") or "").strip()
    descripcion = str(item.get("Descripcion") or "").strip()

    if not codigo or not nombre:
        return None

    texto_evaluacion = _normalizar_texto(f"{nombre} {descripcion}")

    if PATRON_EXCLUSIONES.search(texto_evaluacion):
        return None

    matches_alojamiento = len(PATRON_ALOJAMIENTO.findall(texto_evaluacion))
    matches_eventos = len(PATRON_EVENTOS.findall(texto_evaluacion))

    if matches_alojamiento == 0 and matches_eventos == 0:
        return None

    if matches_eventos > matches_alojamiento:
        categoria = "Eventos / Catering"
    else:
        categoria = "Alojamiento"

    monto_estimado = int(item.get("MontoEstimado") or 0)
    codigo_upper = codigo.upper()

    if "COT" in codigo_upper or "-CO" in codigo_upper or (0 < monto_estimado <= database.get_tope_compra_agil()):
        modalidad = "Compra Agil"
    else:
        modalidad = "Licitacion Publica"

    comprador = item.get("Comprador")
    if isinstance(comprador, dict):
        organismo = comprador.get("NombreOrganismo") or "Organismo Publico"
        region = comprador.get("RegionUnidad") or "Region Metropolitana (Santiago)"
    else:
        organismo = "Organismo Publico"
        region = "Region Metropolitana (Santiago)"

    fecha_cierre_raw = str(item.get("FechaCierre") or "")
    if len(fecha_cierre_raw) >= 10:
        fecha_cierre = fecha_cierre_raw[:10]
    else:
        fecha_cierre = datetime.now().strftime("%Y-%m-%d")

    fecha_creacion_raw = str(item.get("FechaCreacion") or "")
    if len(fecha_creacion_raw) >= 10:
        fecha_pub = fecha_creacion_raw[:10]
    else:
        fecha_pub = datetime.now().strftime("%Y-%m-%d")

    costo_base = int(monto_estimado * 0.75) if monto_estimado > 0 else 0

    return {
        "id_licitacion": codigo,
        "titulo": nombre,
        "organismo": organismo,
        "categoria": categoria,
        "modalidad": modalidad,
        "region": region,
        "presupuesto_mandante": monto_estimado,
        "costo_base_hotel": costo_base,
        "estado_embudo": "Identificada",
        "validacion_adjuntos": "Valida",
        "tiene_anexo4": 1,
        "tiene_escrituras": 1,
        "tiene_poderes": 1,
        "tiene_vigencias": 1,
        "fecha_publicacion": fecha_pub,
        "fecha_cierre": fecha_cierre,
        "descripcion_tdr": descripcion,
        "cantidad_asistentes": 0,
        "tipo_jornada": "",
        "horario_evento": "",
        "id_salon_asignado": ""
    }


def consultar_licitacion(codigo: str, ticket: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Consulta una licitacion especifica en la API de Mercado Publico por su codigo externo.
    """
    if ticket is None:
        ticket = get_ticket()

    if not ticket or ticket == "TU_TICKET_AQUI" or not ticket.strip():
        logger.info("Consulta omitida: ticket de API no configurado.")
        return None

    params = urllib.parse.urlencode({
        "codigo": codigo.strip(),
        "ticket": ticket.strip()
    })
    url = f"{MERCADO_PUBLICO_BASE_URL}?{params}"

    raw_data = _fetch_url(url, timeout=15)
    if not raw_data:
        return None

    try:
        data = json.loads(raw_data.decode("utf-8"))
        listado = data.get("Listado", [])
        if listado and isinstance(listado, list):
            return listado[0]
        return None
    except Exception as exc:
        logger.error(f"Error decodificando respuesta para {codigo}: {exc}")
        return None


def consultar_licitaciones_fecha(fecha: str, ticket: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Consulta el listado general de licitaciones publicadas en una fecha especifica (formato ddmmaaaa).
    """
    if ticket is None:
        ticket = get_ticket()

    if not ticket or ticket == "TU_TICKET_AQUI" or not ticket.strip():
        logger.info("Consulta por fecha omitida: ticket de API no configurado.")
        return []

    params = urllib.parse.urlencode({
        "fecha": fecha.strip(),
        "ticket": ticket.strip()
    })
    url = f"{MERCADO_PUBLICO_BASE_URL}?{params}"

    raw_data = _fetch_url(url, timeout=30)
    if not raw_data:
        return []

    try:
        data = json.loads(raw_data.decode("utf-8"))
        return data.get("Listado", [])
    except Exception as exc:
        logger.error(f"Error decodificando listado para fecha {fecha}: {exc}")
        return []


def sincronizar_licitaciones(
    fecha: Optional[str] = None,
    ticket: Optional[str] = None
) -> Dict[str, Any]:
    """
    Ejecuta el ciclo de sincronizacion con Mercado Publico:
    1. Obtiene las licitaciones de la fecha indicada.
    2. Aplica filtro semantico y clasificacion.
    3. Persiste o actualiza en la base de datos local.
    Retorna resumen estadistico de la operacion.
    """
    if ticket is None:
        ticket = get_ticket()

    if not ticket or ticket == "TU_TICKET_AQUI" or not ticket.strip():
        return {
            "total_consultadas": 0,
            "total_pertinentes": 0,
            "total_descartadas": 0,
            "total_guardadas": 0,
            "mensaje": "Ticket de API no configurado o invalido. Configure MERCADO_PUBLICO_TICKET en el archivo .env."
        }

    if not fecha:
        fecha = datetime.now().strftime("%d%m%Y")

    items = consultar_licitaciones_fecha(fecha=fecha, ticket=ticket)
    total_consultadas = len(items)
    total_pertinentes = 0
    total_descartadas = 0
    total_guardadas = 0

    for item in items:
        clasificada = filtrar_y_clasificar_licitacion(item)
        if clasificada is None:
            total_descartadas += 1
            continue

        total_pertinentes += 1
        id_lic = clasificada["id_licitacion"]
        existente = database.get_licitacion_by_id(id_lic)

        if not existente:
            database.create_licitacion(clasificada)
            total_guardadas += 1
        else:
            database.update_licitacion(id_lic, clasificada)
            total_guardadas += 1

    return {
        "total_consultadas": total_consultadas,
        "total_pertinentes": total_pertinentes,
        "total_descartadas": total_descartadas,
        "total_guardadas": total_guardadas,
        "fecha": fecha,
        "mensaje": f"Sincronizacion finalizada: {total_guardadas} registradas/actualizadas de {total_consultadas} consultadas."
    }
