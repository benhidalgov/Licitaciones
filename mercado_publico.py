"""
Modulo de integracion con API oficial de ChileCompra / Mercado Publico.
Permite consultar, filtrar semanticamente y sincronizar licitaciones y compras agiles
relevantes para la operacion del Hotel Plaza San Francisco.
"""

from datetime import datetime, timedelta
import json
import logging
import os
import re
import ssl
import time
from typing import Any, Dict, List, Optional
import unicodedata
import urllib.error
import urllib.parse
import urllib.request

import database

logger = logging.getLogger(__name__)

MERCADO_PUBLICO_BASE_URL = "https://api.mercadopublico.cl/servicios/v1/publico/licitaciones.json"
MP_FICHA_URL = "https://www.mercadopublico.cl/Procurement/Modules/RFB/DetailsAcquisition.aspx?idlicitacion="

VOCAB_ALOJAMIENTO = (
    "hospedaje", "alojamiento", "habitacion", "habitaciones",
    "pernoctacion", "hotel", "hoteles", "hoteleria",
)

VOCAB_EVENTOS = (
    "evento", "eventos", "catering", "salon", "salones", "banqueteria",
    "coctel", "cocteles", "desayuno", "almuerzo", "cena", "cenas",
    "coffee break",
)

PATRON_ALOJAMIENTO = re.compile(
    r"\b(" + "|".join(VOCAB_ALOJAMIENTO) + r")\b",
    re.IGNORECASE
)

PATRON_EVENTOS = re.compile(
    r"\b(" + "|".join(VOCAB_EVENTOS) + r")\b",
    re.IGNORECASE
)

# Palabras de una sola linea para el rescate por tipeo ("coffee break" se queda
# solo en el regex exacto).
FUZZY_ALOJAMIENTO = tuple(w for w in VOCAB_ALOJAMIENTO if " " not in w)
FUZZY_EVENTOS = tuple(w for w in VOCAB_EVENTOS if " " not in w)

PATRON_EXCLUSIONES = re.compile(
    r"\b(almacenamiento|almacen|habitabilidad|habitacional|vial|veredas|pavimentacion|petroleo|clinico|medicamento|medicamentos|quirurgico|oxigeno|repuesto|repuestos|techumbre|cubierta de zinc)\b",
    re.IGNORECASE
)

PATRON_ASISTENTES = re.compile(
    r"\b(\d{1,4})\s*(personas|asistentes|participantes|delegados|huespedes)\b",
    re.IGNORECASE
)

# Restriccion de alcance: el hotel solo ejecuta servicios dentro de sus
# instalaciones. Se descartan eventos y banqueteria a domicilio o en exteriores.
PATRON_EXCLUSIONES_FUERA = re.compile(
    r"\b(a domicilio|servicio a domicilio|evento a domicilio|fuera del hotel|fuera de la instalacion|fuera de las instalaciones|aire libre|espacio publico|plaza publica|via publica|exteriores|outdoor)\b",
    re.IGNORECASE
)


# Campos que gestiona el equipo del hotel: una sincronizacion no debe pisarlos.
CAMPOS_LOCALES = (
    "estado_embudo", "revisada", "motivo_descarte", "notas", "propiedad",
    "cantidad_asistentes", "tipo_jornada", "horario_evento", "id_salon_asignado",
    "costo_base_hotel", "costeo_validado", "sello_mujer", "jornada_40h",
    "sello_sernatur", "inclusion_laboral"
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


def _distancia_edicion(a: str, b: str, tope: int) -> int:
    """
    Distancia de Levenshtein limitada por `tope`: devuelve `tope + 1` en cuanto
    cualquier celda supera el tope, asi no calcula la matriz completa.
    """
    if abs(len(a) - len(b)) > tope:
        return tope + 1

    fila = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        anterior = fila[0]
        fila[0] = i
        mejor = i
        for j, cb in enumerate(b, 1):
            actual = fila[j]
            fila[j] = min(
                fila[j] + 1,
                fila[j - 1] + 1,
                anterior + (ca != cb),
            )
            anterior = actual
            if fila[j] < mejor:
                mejor = fila[j]
        if mejor > tope:
            return tope + 1
    return fila[len(b)]


def contar_terminos_fuzzy(texto: str, vocabulario) -> int:
    """
    Cuenta cuantas palabras del vocabulario aparecen en el texto, tolerando
    tipeos del comprador publico ("catring" por "catering", "hospedagh" por
    "hospedaje"). Distancia de edicion a mano: una palabra corta admite un
    error, una larga dos. Sin dependencias NLP.
    """
    if not texto:
        return 0

    tokens = [t for t in set(re.findall(r"[a-z]+", texto)) if len(t) >= 4]
    encontradas = 0
    for palabra in vocabulario:
        tope = 1 if len(palabra) <= 7 else 2
        if palabra in tokens:
            encontradas += 1
            continue
        for token in tokens:
            if abs(len(token) - len(palabra)) > tope:
                continue
            if _distancia_edicion(token, palabra, tope) <= tope:
                encontradas += 1
                break
    return encontradas


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


MP_REINTENTOS_LIMITE = 3
MP_ESPERA_MAX_S = 60

# Estado compartido entre consultas de una misma sincronizacion.
_ultima_consulta = {"ts": 0.0}
_ssl_roto = {"v": False}
avisos_rate_limit = {"cantidad": 0}


def _intervalo_ms() -> int:
    """Milisegundos minimos entre consultas. Se lee en cada llamada porque el
    .env se carga despues de importar el modulo. 0 desactiva el espaciado."""
    try:
        return max(0, int(os.environ.get("MERCADO_PUBLICO_INTERVALO_MS", "500") or 0))
    except ValueError:
        return 500


def _esperar_rate_limit() -> None:
    """Espacia las consultas contra la API para no disparar su limite."""
    intervalo = _intervalo_ms()
    if intervalo <= 0:
        _ultima_consulta["ts"] = time.monotonic()
        return
    espera = intervalo / 1000.0 - (time.monotonic() - _ultima_consulta["ts"])
    if espera > 0:
        time.sleep(espera)
    _ultima_consulta["ts"] = time.monotonic()


def _espera_reintento(exc: urllib.error.HTTPError, intento: int) -> float:
    """Respeta Retry-After si la API lo envia; si no, backoff exponencial."""
    cabecera = exc.headers.get("Retry-After") if exc.headers else None
    try:
        if cabecera:
            return min(float(cabecera), float(MP_ESPERA_MAX_S))
    except (TypeError, ValueError):
        pass
    return float(min(4 * (2 ** intento), MP_ESPERA_MAX_S))


def _contexto_peticion() -> ssl.SSLContext:
    """Si la red corporativa ya rompio la verificacion SSL, se va directo al
    contexto sin verificacion y se ahorra un intento por consulta."""
    if _ssl_roto["v"]:
        return ssl._create_unverified_context()
    return _create_ssl_context()


def _leer(req: urllib.request.Request, timeout: int, contexto: ssl.SSLContext) -> bytes:
    """
    Ejecuta la peticion. Si falla la verificacion del certificado (proxy
    corporativo que intercepta SSL) se reintenta una vez sin verificar.
    """
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=contexto) as resp:
            return resp.read()
    except urllib.error.URLError as exc:
        if "CERTIFICATE_VERIFY_FAILED" not in str(exc):
            raise
        _ssl_roto["v"] = True
        logger.warning(f"Fallo de verificacion SSL; reintento sin verificar en {req.full_url}")
        with urllib.request.urlopen(req, timeout=timeout, context=ssl._create_unverified_context()) as resp:
            return resp.read()


def _fetch_url(url: str, timeout: int = 15) -> Optional[bytes]:
    """
    Peticion HTTP a la API con espaciado de rate limit, reintento ante 429/503
    y tolerancia a proxies corporativos de red.
    """
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Licitaciones-Hotel-Plaza-San-Francisco/1.0"}
    )

    for intento in range(MP_REINTENTOS_LIMITE + 1):
        _esperar_rate_limit()
        try:
            return _leer(req, timeout, _contexto_peticion())
        except urllib.error.HTTPError as exc:
            # HTTPError hereda de URLError: hay que evaluarlo antes, si no un
            # 429 queda clasificado como error de red o de certificado.
            if exc.code in (429, 503) and intento < MP_REINTENTOS_LIMITE:
                espera = _espera_reintento(exc, intento)
                logger.warning(
                    f"Mercado Publico respondio HTTP {exc.code}; reintento en {espera}s ({url})"
                )
                time.sleep(espera)
                continue
            # Solo se cuenta lo que queda sin resolver: la ficha completa.
            avisos_rate_limit["cantidad"] += 1
            logger.error(f"Mercado Publico respondio HTTP {exc.code} en {url}")
            return None
        except urllib.error.URLError as exc:
            logger.error(f"Error de red al consultar {url}: {exc}")
            return None
        except Exception as exc:
            logger.error(f"Error al consultar {url}: {exc}")
            return None

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

    if PATRON_EXCLUSIONES_FUERA.search(texto_evaluacion):
        return None

    matches_alojamiento = len(PATRON_ALOJAMIENTO.findall(texto_evaluacion))
    matches_eventos = len(PATRON_EVENTOS.findall(texto_evaluacion))

    # Si el regex estricto no calza, se reintenta tolerando tipeos de compra
    # ("catring", "hospedagh"). Solo se rescata, nunca se descarta con fuzzy.
    if matches_alojamiento == 0 and matches_eventos == 0:
        matches_alojamiento = contar_terminos_fuzzy(texto_evaluacion, FUZZY_ALOJAMIENTO)
        matches_eventos = contar_terminos_fuzzy(texto_evaluacion, FUZZY_EVENTOS)
        if matches_alojamiento == 0 and matches_eventos == 0:
            return None

    if matches_eventos > matches_alojamiento:
        categoria = "Eventos / Catering"
    else:
        categoria = "Alojamiento"

    fechas = item.get("Fechas") or {}
    monto_estimado = int(item.get("MontoEstimado") or fechas.get("MontoEstimado") or 0)
    codigo_upper = codigo.upper()

    if "COT" in codigo_upper or "-CO" in codigo_upper or (0 < monto_estimado <= database.get_tope_compra_agil()):
        modalidad = "Compra Agil"
    else:
        modalidad = "Licitacion Publica"

    comprador = item.get("Comprador")
    if isinstance(comprador, dict):
        organismo = comprador.get("NombreOrganismo") or "Organismo Publico"
        region = comprador.get("RegionUnidad") or "No informada"
    else:
        organismo = "Organismo Publico"
        region = "No informada"

    # El tope de Compra Agil y el costo base estan en CLP: montos en otra
    # moneda no son comparables, se descartan en lugar de clasificar mal.
    # La API real trae Moneda en la raiz del item (p. ej. "CLP", "UF").
    if str(item.get("Moneda") or "CLP").upper() != "CLP":
        return None

    fecha_cierre_raw = str(item.get("FechaCierre") or fechas.get("FechaCierre") or "")
    if len(fecha_cierre_raw) >= 10:
        fecha_cierre = fecha_cierre_raw[:10]
    else:
        fecha_cierre = datetime.now().strftime("%Y-%m-%d")

    fecha_creacion_raw = str(item.get("FechaCreacion") or fechas.get("FechaCreacion") or "")
    if len(fecha_creacion_raw) >= 10:
        fecha_pub = fecha_creacion_raw[:10]
    else:
        fecha_pub = datetime.now().strftime("%Y-%m-%d")

    costo_base = int(monto_estimado * 0.75) if monto_estimado > 0 else 0

    # Estimacion simple de aforo para proponer matches de capacidad. Si no se
    # puede inferir, el equipo lo completa en la evaluacion operativa.
    match_asistentes = PATRON_ASISTENTES.search(texto_evaluacion)
    cantidad_asistentes = int(match_asistentes.group(1)) if match_asistentes else 0

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
        "cantidad_asistentes": cantidad_asistentes,
        "tipo_jornada": "",
        "horario_evento": "",
        "id_salon_asignado": "",
        "propiedad": "Plaza San Francisco",
        "revisada": 0,
        "motivo_descarte": "",
        "notas": "",
        "costeo_validado": 0,
        "sello_mujer": 0,
        "jornada_40h": 0,
        "sello_sernatur": 0,
        "inclusion_laboral": 0
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


# El token "enc" se extrae del HTML publico de la ficha del portal: si ChileCompra
# cambia el marcado o pone reCAPTCHA tambien en la ficha, esto deja de funcionar
# y hay que degradar al link directo de la ficha oficial.
def consultar_url_adjuntos(codigo: str) -> Optional[str]:
    """
    Retorna la URL del visor oficial de anexos (ViewAttachment.aspx) de la
    licitacion, extraida de la ficha web publica. No requiere ticket.
    """
    raw = _fetch_url(f"{MP_FICHA_URL}{codigo.strip()}", timeout=30)
    if not raw:
        return None
    match = re.search(r"ViewAttachment\.aspx\?enc=([A-Za-z0-9%+/_-]+)", raw.decode("utf-8", errors="replace"))
    if not match:
        return None
    return f"https://www.mercadopublico.cl/Procurement/Modules/Attachment/ViewAttachment.aspx?enc={match.group(1)}"


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
    ticket: Optional[str] = None,
    dias: int = 1
) -> Dict[str, Any]:
    """
    Ejecuta el ciclo de sincronizacion con Mercado Publico:
    1. Obtiene las licitaciones publicadas en las ultimas N fechas (dias) desde la fecha base.
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
    base = datetime.strptime(fecha, "%d%m%Y")

    total_consultadas = 0
    total_pertinentes = 0
    total_descartadas = 0
    total_guardadas = 0

    avisos_rate_limit["cantidad"] = 0

    for dia in range(dias):
        fecha_dia = (base - timedelta(days=dia)).strftime("%d%m%Y")
        items = consultar_licitaciones_fecha(fecha=fecha_dia, ticket=ticket)
        total_consultadas += len(items)

        for item in items:
            clasificada = filtrar_y_clasificar_licitacion(item)
            if clasificada is None:
                total_descartadas += 1
                continue

            total_pertinentes += 1

            # El listado por fecha trae solo datos basicos; la ficha detalle aporta
            # presupuesto, organismo y fechas reales (solo se consulta lo pertinente).
            detalle = consultar_licitacion(clasificada["id_licitacion"], ticket=ticket) or {}
            if detalle.get("CodigoExterno") == clasificada["id_licitacion"]:
                merged = {**item, **{k: v for k, v in detalle.items() if v is not None}}
                reclasificada = filtrar_y_clasificar_licitacion(merged)
                if reclasificada is None:
                    # La ficha completa lo descarta (moneda no CLP o exclusion en la descripcion)
                    total_pertinentes -= 1
                    total_descartadas += 1
                    continue
                clasificada = reclasificada

            id_lic = clasificada["id_licitacion"]
            existente = database.get_licitacion_by_id(id_lic)

            if not existente:
                database.create_licitacion(clasificada)
            else:
                for campo in CAMPOS_LOCALES:
                    if campo in ("costo_base_hotel", "costeo_validado") and not existente["costeo_validado"]:
                        continue
                    clasificada[campo] = existente[campo]
                database.update_licitacion(id_lic, clasificada)
            total_guardadas += 1

    total_descartadas += database.marcar_inviables()

    mensaje = (
        f"Sincronizacion finalizada ({dias} dia(s) desde {fecha}): "
        f"{total_guardadas} registradas/actualizadas de {total_consultadas} consultadas."
    )
    if avisos_rate_limit["cantidad"]:
        mensaje += (
            f" La API bloqueo {avisos_rate_limit['cantidad']} consulta(s) por limite "
            f"de llamadas (HTTP 429) y quedaron sin datos de detalle. Suba "
            f"MERCADO_PUBLICO_INTERVALO_MS en .env y repita la sincronizacion."
        )

    return {
        "total_consultadas": total_consultadas,
        "total_pertinentes": total_pertinentes,
        "total_descartadas": total_descartadas,
        "total_guardadas": total_guardadas,
        "fecha": fecha,
        "avisos_rate_limit": avisos_rate_limit["cantidad"],
        "mensaje": mensaje,
    }
