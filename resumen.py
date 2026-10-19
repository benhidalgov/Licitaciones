"""
Generacion de ficha resumen de licitaciones.

Modo por defecto: reglas deterministas sobre la descripcion TDR (cero costo,
funciona offline). Si se configura una API de IA en el entorno, se enriquece el
resumen con un modelo de lenguaje; si falla o no hay llave, se degrada a reglas.
"""

import json
import os
import re
import urllib.request
from datetime import datetime
from typing import Any, Dict, List, Optional

import mercado_publico

# Servicios de alimentacion intramuros que el hotel puede prestar.
SERVICIOS_ALIMENTACION = {
    "Coffee break": r"coffee[\s-]?break|panecer[oa]?",
    "Desayuno": r"desayuno",
    "Almuerzo": r"almuerzo|lunch",
    "Cena": r"cena",
    "Coctel": r"c[oó]ctel|cocteler[oa]?",
    "Catering": r"cat[e]?ring|banqueter[oa]?",
}

# Fechas en texto: "15 de marzo de 2026", "15/03/2026", "15-03-2026".
PATRON_FECHA_TEXTO = re.compile(
    r"\b(\d{1,2}\s*(?:de\s*)?[/-]?\s*\d{1,2}[/-]\s*\d{2,4}|\d{1,2}\s+de\s+[a-z]+(?:\s+de\s+\d{4})?)\b",
    re.IGNORECASE
)

MESES = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
    "julio": 7, "agosto": 8, "septiembre": 9, "octubre": 10, "noviembre": 11,
    "diciembre": 12,
}


def get_ia_config() -> Dict[str, str]:
    """
    Lee la configuracion opcional de IA desde el entorno. Sin llave valida,
    retorna vacio y el resumen usa reglas.
    """
    mercado_publico.load_env_file()
    return {
        "api_key": os.environ.get("RESUMEN_IA_API_KEY", "").strip(),
        "model": os.environ.get("RESUMEN_IA_MODELO", "").strip() or "gpt-4o-mini",
        "url": os.environ.get("RESUMEN_IA_URL", "").strip() or "https://api.openai.com/v1/chat/completions",
    }


def _buscar_servicios(texto: str) -> List[str]:
    encontrados = []
    for nombre, patron in SERVICIOS_ALIMENTACION.items():
        if re.search(patron, texto, re.IGNORECASE):
            encontrados.append(nombre)
    return encontrados


def _buscar_fechas(texto: str) -> List[str]:
    fechas = []
    for match in PATRON_FECHA_TEXTO.finditer(texto):
        fecha = match.group(1).strip()
        if fecha not in fechas:
            fechas.append(fecha)
    return fechas[:6]


def _buscar_salones_habitaciones(lic: Dict[str, Any]) -> Dict[str, Any]:
    categoria = lic.get("categoria", "")
    asistentes = int(lic.get("cantidad_asistentes") or 0)
    if categoria == "Alojamiento":
        return {
            "tipo": "Habitaciones",
            "requerimiento": f"{asistentes} habitaciones/huespedes estimados" if asistentes else "Alojamiento corporativo (aforo por confirmar)",
            "alternativas": [],
        }

    salones = mercado_publico.database.get_salones_aptos(asistentes, propiedad=lic.get("propiedad"))
    if asistentes and salones:
        alternativas = [f"{s['nombre']} ({s['capacidad_maxima']} pers.)" for s in salones[:4]]
        requerimiento = f"{asistentes} asistentes; {len(salones)} salon(es) con capacidad suficiente"
    elif asistentes:
        alternativas = []
        requerimiento = f"{asistentes} asistentes; sin salon de capacidad suficiente"
    else:
        salones = mercado_publico.database.get_all_salones()
        alternativas = [f"{s['nombre']} ({s['capacidad_maxima']} pers.)" for s in salones[:4]]
        requerimiento = "Salones requeridos (aforo por confirmar)"

    return {"tipo": "Salones", "requerimiento": requerimiento, "alternativas": alternativas}


def _ponderar_criterios(lic: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Desglose de ponderacion de criterios de evaluacion del hotel.
    Los pesos suman 100 y se aplican al costo minimo vs. presupuesto.
    """
    presupuesto = int(lic.get("presupuesto_mandante") or 0)
    costo = int(lic.get("costo_base_hotel") or 0)
    asistentes = int(lic.get("cantidad_asistentes") or 0)
    salon_id = lic.get("id_salon_asignado") or ""

    # Presupuesto: margen positivo puntua; deficit, cero.
    if presupuesto > 0 and costo > 0 and costo <= presupuesto:
        margen_pct = round(((presupuesto - costo) / presupuesto) * 100, 1)
        puntuacion_presupuesto = min(100, int(margen_pct * 4))
    else:
        puntuacion_presupuesto = 0

    salon = mercado_publico.database.get_salon_by_id(salon_id) if salon_id else None
    if salon and asistentes:
        holgura = salon["capacidad_maxima"] - asistentes
        puntuacion_capacidad = 100 if holgura >= 0 else max(0, 100 + holgura)
    elif asistentes:
        puntuacion_capacidad = 50  # hay aforo pero sin salon asignado
    else:
        puntuacion_capacidad = 70  # aforo desconocido

    sellos = [bool(lic.get(k)) for k in ("sello_mujer", "jornada_40h", "sello_sernatur", "inclusion_laboral")]
    puntuacion_sellos = int(round(100 * sum(sellos) / len(sellos)))

    documentos = [bool(lic.get(k)) for k in ("tiene_anexo4", "tiene_escrituras", "tiene_poderes", "tiene_vigencias")]
    puntuacion_admisibilidad = int(round(100 * sum(documentos) / len(documentos)))

    return [
        {"criterio": "Presupuesto (mandatorio)", "peso": 35, "puntuacion": puntuacion_presupuesto},
        {"criterio": "Capacidad y disponibilidad", "peso": 25, "puntuacion": puntuacion_capacidad},
        {"criterio": "Sellos y exigencias tecnicas", "peso": 20, "puntuacion": puntuacion_sellos},
        {"criterio": "Admisibilidad documental", "peso": 20, "puntuacion": puntuacion_admisibilidad},
    ]


def generar_resumen_reglas(lic: Dict[str, Any]) -> Dict[str, Any]:
    """Ficha resumen construida con reglas deterministas sobre el TDR."""
    texto = mercado_publico._normalizar_texto(
        f"{lic.get('titulo', '')} {lic.get('descripcion_tdr', '')}"
    )

    fechas = _buscar_fechas(texto)
    servicios = _buscar_servicios(texto)
    espacio = _buscar_salones_habitaciones(lic)
    ponderacion = _ponderar_criterios(lic)

    puntaje_total = int(round(
        sum(c["peso"] * c["puntuacion"] for c in ponderacion) / 100
    ))

    lineas = [
        f"Fecha publicacion: {lic.get('fecha_publicacion', 'n/d')}. "
        f"Cierre de ofertas: {lic.get('fecha_cierre', 'n/d')}.",
    ]
    if fechas:
        lineas.append("Fechas del evento en el TDR: " + "; ".join(fechas) + ".")
    else:
        lineas.append("Fechas del evento: no se detectaron fechas explicitas en el TDR.")

    asistentes = int(lic.get("cantidad_asistentes") or 0)
    lineas.append(
        f"Personas: {asistentes} asistentes estimados."
        if asistentes else "Personas: aforo no especificado en el TDR."
    )

    lineas.append(f"Espacio: {espacio['requerimiento']}.")
    if espacio["alternativas"]:
        lineas.append("Salones propuestos: " + "; ".join(espacio["alternativas"]) + ". Disponibilidad a validar en PMS.")

    lineas.append(
        "Alimentacion intramuros: " + (", ".join(servicios) + "." if servicios else "no se detectaron servicios de alimentacion.")
    )
    lineas.append("Propiedad sugerida: " + lic.get("propiedad", "Plaza San Francisco") + ".")

    return {
        "fuente": "reglas",
        "texto": " ".join(lineas),
        "fechas_evento": fechas,
        "personas": asistentes,
        "servicios_alimentacion": servicios,
        "espacio": espacio,
        "ponderacion": ponderacion,
        "puntaje_total": puntaje_total,
    }


def _generar_resumen_ia(lic: Dict[str, Any], config: Dict[str, str]) -> Optional[Dict[str, Any]]:
    """
    Envia el TDR a un modelo de lenguaje. Requiere RESUMEN_IA_API_KEY.
    Retorna None si falla, para degradar a reglas.
    """
    base = generar_resumen_reglas(lic)
    prompt = (
        "Eres un asistente comercial del Hotel Plaza San Francisco. Resume la siguiente "
        "licitacion en un parrafo claro para el equipo de eventos, cubriendo fechas del "
        "evento, cantidad de personas, requerimientos de salones o habitaciones y "
        "servicios de alimentacion. Solo usa datos del texto; no inventes.\n\n"
        f"Titulo: {lic.get('titulo', '')}\n"
        f"Organismo: {lic.get('organismo', '')}\n"
        f"Descripcion TDR: {lic.get('descripcion_tdr', '')}\n"
    )
    payload = {
        "model": config["model"],
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
        "max_tokens": 400,
    }
    req = urllib.request.Request(
        config["url"],
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config['api_key']}",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        texto = data["choices"][0]["message"]["content"].strip()
        return {**base, "fuente": "ia", "texto": texto, "modelo": config["model"]}
    except Exception as exc:  # noqa: BLE001 - degradar a reglas es intencional
        base["error_ia"] = str(exc)
        return None


def generar_resumen(lic: Dict[str, Any], usar_ia: bool = True) -> Dict[str, Any]:
    """
    Ficha resumen de una licitacion. Usa IA si esta configurada y el llamado
    funciona; en cualquier otro caso usa reglas deterministas.
    """
    base = generar_resumen_reglas(lic)
    if not usar_ia:
        return base

    config = get_ia_config()
    if not config["api_key"]:
        return base

    return _generar_resumen_ia(lic, config) or base
