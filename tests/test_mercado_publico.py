import io
import json
import os
import re
import unittest
from unittest.mock import patch, MagicMock
import database
import mercado_publico


class TestMercadoPublico(unittest.TestCase):
    def setUp(self):
        self.db_name = "test_mp_licitaciones.db"
        database.DB_NAME = self.db_name
        if os.path.exists(self.db_name):
            try:
                os.remove(self.db_name)
            except PermissionError:
                pass
        database.init_db()

    def tearDown(self):
        if os.path.exists(self.db_name):
            try:
                os.remove(self.db_name)
            except PermissionError:
                pass

    def test_load_env_file(self):
        test_env_content = """
# Comentario de prueba
TEST_KEY_ONE=valor1
TEST_KEY_TWO="valor con espacios"
TEST_KEY_THREE='valor simple'
INVALID_LINE_WITHOUT_EQUALS
"""
        env_dict = mercado_publico.parse_env_content(test_env_content)
        self.assertEqual(env_dict.get("TEST_KEY_ONE"), "valor1")
        self.assertEqual(env_dict.get("TEST_KEY_TWO"), "valor con espacios")
        self.assertEqual(env_dict.get("TEST_KEY_THREE"), "valor simple")
        self.assertNotIn("INVALID_LINE_WITHOUT_EQUALS", env_dict)

    def test_filtrar_y_clasificar_alojamiento(self):
        item = {
            "CodigoExterno": "2050-10-LP24",
            "Nombre": "Servicio de hospedaje para delegacion deportiva nacional",
            "CodigoEstado": 5,
            "FechaCierre": "2026-10-25T15:00:00",
            "FechaCreacion": "2026-10-01T10:00:00",
            "Descripcion": "Alojamiento en habitaciones singles y dobles en Santiago",
            "Comprador": {
                "NombreOrganismo": "Instituto Nacional de Deportes",
                "RegionUnidad": "Region Metropolitana de Santiago"
            },
            "MontoEstimado": 8500000
        }
        res = mercado_publico.filtrar_y_clasificar_licitacion(item)
        self.assertIsNotNone(res)
        self.assertEqual(res["id_licitacion"], "2050-10-LP24")
        self.assertEqual(res["categoria"], "Alojamiento")
        self.assertEqual(res["organismo"], "Instituto Nacional de Deportes")
        self.assertEqual(res["presupuesto_mandante"], 8500000)
        self.assertEqual(res["modalidad"], "Licitacion Publica")

    def test_filtrar_y_clasificar_eventos_compra_agil(self):
        item = {
            "CodigoExterno": "1100-33-COT24",
            "Nombre": "Servicio de coffee break y salones para jornada institucional",
            "CodigoEstado": 5,
            "FechaCierre": "2026-10-18T18:00:00",
            "FechaCreacion": "2026-10-05T09:00:00",
            "Descripcion": "Banqueteria y arriendo de salon para 50 personas",
            "Comprador": {
                "NombreOrganismo": "Servicio de Evaluacion Ambiental",
                "RegionUnidad": "Region Metropolitana"
            },
            "MontoEstimado": 4200000
        }
        res = mercado_publico.filtrar_y_clasificar_licitacion(item)
        self.assertIsNotNone(res)
        self.assertEqual(res["id_licitacion"], "1100-33-COT24")
        self.assertEqual(res["categoria"], "Eventos / Catering")
        self.assertEqual(res["modalidad"], "Compra Agil")
        self.assertLessEqual(res["presupuesto_mandante"], 6900000)

    def test_tope_compra_agil_configurable(self):
        database.set_tope_compra_agil(1000000)
        self.assertEqual(database.get_tope_compra_agil(), 1000000)

        item = {
            "CodigoExterno": "1100-44-LP24",
            "Nombre": "Servicio de coffee break y salones",
            "FechaCierre": "2026-10-18T18:00:00",
            "FechaCreacion": "2026-10-05T09:00:00",
            "Descripcion": "Banqueteria y arriendo de salon para 50 personas",
            "Comprador": {
                "NombreOrganismo": "Servicio de Evaluacion Ambiental",
                "RegionUnidad": "Region Metropolitana"
            },
            "MontoEstimado": 4200000
        }
        # Con tope de 1.000.000 CLP el mismo monto deja de calificar como Compra Agil
        self.assertEqual(mercado_publico.filtrar_y_clasificar_licitacion(item)["modalidad"], "Licitacion Publica")

    def test_filtrar_y_clasificar_descarte_no_relevante(self):
        item = {
            "CodigoExterno": "999-88-LP24",
            "Nombre": "Adquisicion de medicamentos e insumos clinicos para hospital",
            "CodigoEstado": 5,
            "FechaCierre": "2026-10-30T12:00:00",
            "Descripcion": "Insumos hospitalarios y material quirurgico de urgencia",
            "Comprador": {
                "NombreOrganismo": "Servicio de Salud Metropolitano",
                "RegionUnidad": "Region Metropolitana"
            },
            "MontoEstimado": 15000000
        }
        res = mercado_publico.filtrar_y_clasificar_licitacion(item)
        self.assertIsNone(res)

    def test_filtrar_y_clasificar_descarta_moneda_no_clp(self):
        # Montos en UF/USD no son comparables con el tope CLP ni con el costo base
        item = {
            "CodigoExterno": "5000-5-COT26",
            "Nombre": "Servicio de hospedaje para comite de expertos",
            "CodigoEstado": 5,
            "FechaCierre": "2026-10-25T12:00:00",
            "Moneda": "UF",
            "Comprador": {
                "NombreOrganismo": "Organismo Extranjero",
                "RegionUnidad": "Region Metropolitana"
            },
            "MontoEstimado": 500
        }
        self.assertIsNone(mercado_publico.filtrar_y_clasificar_licitacion(item))

    @patch("urllib.request.urlopen")
    def test_consultar_licitacion_api_mock(self, mock_urlopen):
        fake_api_response = {
            "Cantidad": 1,
            "FechaCreacion": "2026-10-07T16:00:00",
            "Version": "v1",
            "Listado": [
                {
                    "CodigoExterno": "1058-12-COT24",
                    "Nombre": "Servicio de Banqueteria y Salones",
                    "CodigoEstado": 5,
                    "FechaCierre": "2026-10-15T18:00:00",
                    "FechaCreacion": "2026-10-01T10:00:00",
                    "Descripcion": "Jornada de planificacion",
                    "Comprador": {
                        "NombreOrganismo": "Subsecretaria de Turismo",
                        "RegionUnidad": "Region Metropolitana de Santiago"
                    },
                    "MontoEstimado": 5800000
                }
            ]
        }
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(fake_api_response).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_response

        resultado = mercado_publico.consultar_licitacion("1058-12-COT24", ticket="MOCK_TICKET_123")
        self.assertIsNotNone(resultado)
        self.assertEqual(resultado["CodigoExterno"], "1058-12-COT24")
        self.assertEqual(resultado["Nombre"], "Servicio de Banqueteria y Salones")

    def test_consultar_sin_ticket_retorna_error(self):
        # Empty or placeholder ticket should raise ValueError or return None gracefully
        res = mercado_publico.consultar_licitacion("1058-12-COT24", ticket="")
        self.assertIsNone(res)

        res_ph = mercado_publico.consultar_licitacion("1058-12-COT24", ticket="TU_TICKET_AQUI")
        self.assertIsNone(res_ph)

    @patch("mercado_publico._fetch_url")
    def test_consultar_url_adjuntos_extrae_token(self, mock_fetch):
        # El HTML real usa rutas relativas y entidades; el regex busca ViewAttachment.aspx?enc=
        mock_fetch.return_value = b"<img onclick=\"open(&#39;../Attachment/ViewAttachment.aspx?enc=AbC123%2Fz-x&#39;,'x')\"/>"
        url = mercado_publico.consultar_url_adjuntos("1058-12-COT24")
        self.assertEqual(
            url,
            "https://www.mercadopublico.cl/Procurement/Modules/Attachment/ViewAttachment.aspx?enc=AbC123%2Fz-x"
        )
        self.assertIn("idlicitacion=1058-12-COT24", mock_fetch.call_args[0][0])

    @patch("mercado_publico._fetch_url")
    def test_consultar_url_adjuntos_sin_token(self, mock_fetch):
        mock_fetch.return_value = b"<html><body>Sin anexos</body></html>"
        self.assertIsNone(mercado_publico.consultar_url_adjuntos("1058-12-COT24"))

    @patch("urllib.request.urlopen")
    def test_sincronizar_licitaciones_mock(self, mock_urlopen):
        fake_batch_response = {
            "Cantidad": 3,
            "FechaCreacion": "2026-10-07T16:00:00",
            "Version": "v1",
            "Listado": [
                {
                    "CodigoExterno": "3001-1-COT24",
                    "Nombre": "Servicio de banqueteria y salones para conferencia universitaria",
                    "CodigoEstado": 5,
                    "FechaCierre": "2026-10-20T17:00:00",
                    "FechaCreacion": "2026-10-05T09:00:00",
                    "Descripcion": "Coffee break continuo para 80 personas",
                    "Comprador": {
                        "NombreOrganismo": "Universidad de Santiago",
                        "RegionUnidad": "Region Metropolitana"
                    },
                    "MontoEstimado": 4500000
                },
                {
                    "CodigoExterno": "3002-2-LP24",
                    "Nombre": "Construccion de veredas y pavimentacion",
                    "CodigoEstado": 5,
                    "FechaCierre": "2026-10-22T17:00:00",
                    "FechaCreacion": "2026-10-05T09:00:00",
                    "Descripcion": "Obras viales",
                    "Comprador": {
                        "NombreOrganismo": "Municipalidad de Maipu",
                        "RegionUnidad": "Region Metropolitana"
                    },
                    "MontoEstimado": 35000000
                },
                {
                    "CodigoExterno": "3003-3-COT24",
                    "Nombre": "Alojamiento y hospedaje delegacion de investigacion",
                    "CodigoEstado": 5,
                    "FechaCierre": "2026-10-25T18:00:00",
                    "FechaCreacion": "2026-10-06T11:00:00",
                    "Descripcion": "Hospedaje de 4 noches en Santiago Centro",
                    "Comprador": {
                        "NombreOrganismo": "Ministerio de Ciencias",
                        "RegionUnidad": "Region Metropolitana de Santiago"
                    },
                    "MontoEstimado": 5200000
                }
            ]
        }
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(fake_batch_response).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_response

        resumen = mercado_publico.sincronizar_licitaciones(
            fecha="07102026",
            ticket="TICKET_TEST_VALIDO"
        )
        self.assertEqual(resumen["total_consultadas"], 3)
        self.assertEqual(resumen["total_pertinentes"], 2)  # Banqueteria + Alojamiento
        self.assertEqual(resumen["total_descartadas"], 1)  # Obras viales
        self.assertEqual(resumen["total_guardadas"], 2)

        # Verify items were saved in database
        lic1 = database.get_licitacion_by_id("3001-1-COT24")
        self.assertIsNotNone(lic1)
        self.assertEqual(lic1["categoria"], "Eventos / Catering")
        self.assertEqual(lic1["modalidad"], "Compra Agil")

        lic2 = database.get_licitacion_by_id("3003-3-COT24")
        self.assertIsNotNone(lic2)
        self.assertEqual(lic2["categoria"], "Alojamiento")

        # Pasada multipledia: consulta varias fechas y reutiliza los mismos items
        resumen_multi = mercado_publico.sincronizar_licitaciones(ticket="TICKET_TEST_VALIDO", dias=3)
        self.assertEqual(resumen_multi["total_consultadas"], 9)
        self.assertEqual(resumen_multi["total_guardadas"], 6)

    @patch("urllib.request.urlopen")
    def test_sincronizar_enriquece_con_ficha_detalle(self, mock_urlopen):
        # Listado por fecha: solo 4 campos basicos (como la API real)
        batch = {
            "Cantidad": 1, "FechaCreacion": "2026-10-07T16:00:00", "Version": "v1",
            "Listado": [{
                "CodigoExterno": "7000-7-COT26",
                "Nombre": "Servicio de banqueteria para asamblea anual",
                "CodigoEstado": 5,
                "FechaCierre": "2026-10-20T17:00:00"
            }]
        }
        # Ficha por codigo: montos y comprador anidados, como la API real
        detalle = {
            "Cantidad": 1, "Version": "v1",
            "Listado": [{
                "CodigoExterno": "7000-7-COT26",
                "Nombre": "Servicio de banqueteria para asamblea anual",
                "CodigoEstado": 5,
                "FechaCierre": None,
                "Descripcion": "Coffee break y coctel para 120 personas",
                "Comprador": {
                    "NombreOrganismo": "SERVICIO NACIONAL DE TURISMO",
                    "RegionUnidad": "Region de Valparaiso"
                },
                "Fechas": {
                    "MontoEstimado": 4800000.0,
                    "FechaCreacion": "2026-10-01T00:00:00",
                    "FechaCierre": "2026-10-20T17:00:00"
                }
            }]
        }

        def fake_urlopen(req, *args, **kwargs):
            url = getattr(req, "full_url", str(req))
            data = detalle if "codigo=" in url else batch
            resp = MagicMock()
            resp.read.return_value = json.dumps(data).encode("utf-8")
            cm = MagicMock()
            cm.__enter__.return_value = resp
            return cm

        mock_urlopen.side_effect = fake_urlopen

        resumen = mercado_publico.sincronizar_licitaciones(fecha="07102026", ticket="TICKET_TEST_VALIDO")
        self.assertEqual(resumen["total_guardadas"], 1)

        lic = database.get_licitacion_by_id("7000-7-COT26")
        self.assertEqual(lic["presupuesto_mandante"], 4800000)
        self.assertEqual(lic["costo_base_hotel"], 3600000)
        self.assertEqual(lic["organismo"], "SERVICIO NACIONAL DE TURISMO")
        self.assertEqual(lic["region"], "Region de Valparaiso")
        self.assertEqual(lic["fecha_publicacion"], "2026-10-01")
        self.assertEqual(lic["fecha_cierre"], "2026-10-20")

    def test_no_emojis_in_mercado_publico_module(self):
        emoji_pattern = re.compile(
            "[\U00010000-\U0010ffff]|"
            "[\u2600-\u27bf]|"
            "[\u2300-\u23ff]|"
            "[\u2b50\u2b55\u2934\u2935\u25aa\u25ab\u25b6\u25c0\u25fb-\u25fe]"
        )
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        target_file = os.path.join(repo_root, "mercado_publico.py")
        if os.path.exists(target_file):
            with open(target_file, "r", encoding="utf-8") as f:
                content = f.read()
                matches = emoji_pattern.findall(content)
                self.assertEqual(
                    matches,
                    [],
                    f"Se detectaron emojis prohibidos en {target_file}: {matches}"
                )

    def test_no_prohibited_terms_in_mercado_publico(self):
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        target_file = os.path.join(repo_root, "mercado_publico.py")
        forbidden = "".join(["a", "i", "o", "p", "s"])
        if os.path.exists(target_file):
            with open(target_file, "r", encoding="utf-8") as f:
                content = f.read()
                self.assertNotIn(
                    forbidden,
                    content.lower(),
                    f"El archivo {target_file} contiene el termino prohibido."
                )


if __name__ == "__main__":
    unittest.main()
