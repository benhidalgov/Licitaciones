import os
import re
import unittest
from unittest.mock import patch
import app as flask_app
import database


class TestDetail(unittest.TestCase):
    def setUp(self):
        self.db_name = "test_detail_licitaciones.db"
        database.DB_NAME = self.db_name
        if os.path.exists(self.db_name):
            try:
                os.remove(self.db_name)
            except PermissionError:
                pass
        database.init_db()

        flask_app.app.config["TESTING"] = True
        flask_app.app.config["SECRET_KEY"] = "test-detail-secret"
        flask_app.app.config["CSRF_ENABLED"] = False
        self.client = flask_app.app.test_client()
        with self.client.session_transaction() as sess:
            sess["user"] = "admin"

    def tearDown(self):
        if os.path.exists(self.db_name):
            try:
                os.remove(self.db_name)
            except PermissionError:
                pass

    def test_view_detail_unauthenticated(self):
        unauth_client = flask_app.app.test_client()
        response = unauth_client.get("/licitaciones/1058-12-COT24")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.headers["Location"])

    def test_view_detail_success(self):
        response = self.client.get("/licitaciones/1058-12-COT24")
        self.assertEqual(response.status_code, 200)
        html = response.data.decode("utf-8")

        # Identification and TDR
        self.assertIn("1058-12-COT24", html)
        self.assertIn("Subsecretaria de Turismo", html)
        self.assertIn("Servicio de Banqueteria y Salones Jornada de Planificacion Estrategica", html)
        self.assertIn("Region Metropolitana (Santiago)", html)
        self.assertIn("Arriendo de salon plenario para 80 asistentes", html)

        # Admissibility checklist items
        self.assertIn("Anexo 4", html)
        self.assertIn("Escrituras", html)
        self.assertIn("Poderes", html)
        self.assertIn("Vigencias", html)

        # Budget amounts in CLP
        self.assertIn("$5.800.000 CLP", html)
        self.assertIn("$4.200.000 CLP", html)

        # Quick status change control
        self.assertIn("/licitaciones/1058-12-COT24/cambiar_estado", html)
        self.assertIn("Actualizar Estado", html)

        # Navigation links
        self.assertIn("/licitaciones", html)
        self.assertIn("/licitaciones/1058-12-COT24/eliminar", html)
        self.assertIn("DetailsAcquisition.aspx?idlicitacion=1058-12-COT24", html)
        self.assertIn("Ver ficha original en Mercado Publico", html)

    def test_view_detail_not_found(self):
        response = self.client.get("/licitaciones/NO-EXISTE-999")
        self.assertEqual(response.status_code, 404)

    def test_quick_status_change_success(self):
        response = self.client.post(
            "/licitaciones/1058-12-COT24/cambiar_estado",
            data={"estado_embudo": "Participada"},
            follow_redirects=True
        )
        self.assertEqual(response.status_code, 200)
        html = response.data.decode("utf-8")
        self.assertIn("Participada", html)

        # Check in database
        lic = database.get_licitacion_by_id("1058-12-COT24")
        self.assertEqual(lic["estado_embudo"], "Participada")

    def test_quick_status_change_invalid_status(self):
        response = self.client.post(
            "/licitaciones/1058-12-COT24/cambiar_estado",
            data={"estado_embudo": "EstadoInvalido"},
            follow_redirects=True
        )
        self.assertEqual(response.status_code, 200)
        lic = database.get_licitacion_by_id("1058-12-COT24")
        # Should stay in initial status
        self.assertEqual(lic["estado_embudo"], "Identificada")

    def test_quick_status_change_not_found(self):
        response = self.client.post(
            "/licitaciones/NO-EXISTE-999/cambiar_estado",
            data={"estado_embudo": "Participada"}
        )
        self.assertEqual(response.status_code, 404)

    def test_quick_status_change_unauthenticated(self):
        unauth_client = flask_app.app.test_client()
        response = unauth_client.post(
            "/licitaciones/1058-12-COT24/cambiar_estado",
            data={"estado_embudo": "Participada"}
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.headers["Location"])

    def test_detail_budget_deficit_alert(self):
        # 1840-22-COT24: Presupuesto 6.400.000 < Costo 6.700.000
        response = self.client.get("/licitaciones/1840-22-COT24")
        self.assertEqual(response.status_code, 200)
        html = response.data.decode("utf-8")

        self.assertIn("Inviable / Costo Excede", html)
        self.assertIn("$300.000 CLP", html)
        self.assertIn("Alerta", html)

    def test_detail_budget_viable(self):
        # 723-4-LP24: Presupuesto 28.000.000 > Costo 22.500.000
        response = self.client.get("/licitaciones/723-4-LP24")
        self.assertEqual(response.status_code, 200)
        html = response.data.decode("utf-8")

        self.assertIn("Viable / Margen Positivo", html)
        self.assertIn("$5.500.000 CLP", html)

    def test_detail_budget_no_informado(self):
        database.create_licitacion({
            "id_licitacion": "TEST-SIN-MONTO",
            "titulo": "Evento sin monto informado",
            "organismo": "Ministerio de Prueba",
            "categoria": "Eventos / Catering",
            "modalidad": "Licitacion Publica",
            "region": "Region Metropolitana",
            "presupuesto_mandante": 0,
            "costo_base_hotel": 0,
            "estado_embudo": "Identificada",
            "validacion_adjuntos": "Sin verificar",
            "tiene_anexo4": 0,
            "tiene_escrituras": 0,
            "tiene_poderes": 0,
            "tiene_vigencias": 0,
            "fecha_publicacion": "2026-10-23",
            "fecha_cierre": "2027-10-23",
            "descripcion_tdr": "Evento sin presupuesto publicado",
        })
        response = self.client.get("/licitaciones/TEST-SIN-MONTO")
        self.assertEqual(response.status_code, 200)
        html = response.data.decode("utf-8")

        self.assertIn("Monto no informado", html)
        self.assertIn("Presupuesto No Informado", html)
        self.assertNotIn("Viable / Margen Positivo", html)

    def test_detail_id_discrepancy_alert(self):
        # 805-19-LP24 has validacion_adjuntos = 'Error ID / Discrepancia'
        response = self.client.get("/licitaciones/805-19-LP24")
        self.assertEqual(response.status_code, 200)
        html = response.data.decode("utf-8")

        self.assertIn("Discrepancia ID", html)
        self.assertIn("Conflicto en TDR", html)

    def test_detail_id_verified(self):
        # 1058-12-COT24 has validacion_adjuntos = 'Valida'
        response = self.client.get("/licitaciones/1058-12-COT24")
        self.assertEqual(response.status_code, 200)
        html = response.data.decode("utf-8")

        self.assertIn("ID Verificado", html)

    def test_detail_admissibility_checklist(self):
        # 440-8-COT24: tiene_anexo4 = 0, others = 1
        response = self.client.get("/licitaciones/440-8-COT24")
        self.assertEqual(response.status_code, 200)
        html = response.data.decode("utf-8")

        self.assertIn("Pendiente / Exigido", html)
        self.assertIn("Presente / Aprobado", html)

    def test_detail_compra_agil_features(self):
        # 1058-12-COT24 is Compra Agil
        response = self.client.get("/licitaciones/1058-12-COT24")
        self.assertEqual(response.status_code, 200)
        html = response.data.decode("utf-8")

        self.assertIn("Compra Agil", html)
        self.assertIn("6.900.000 CLP", html)

    def test_detail_capacity_panel_adequate(self):
        # 1058-12-COT24 has 80 personas, SALON-DANUBIO (capacidad: 100)
        response = self.client.get("/licitaciones/1058-12-COT24")
        self.assertEqual(response.status_code, 200)
        html = response.data.decode("utf-8")

        self.assertIn("Dimensionamiento Operativo, Aforo y Horarios de Salones", html)
        self.assertIn("80 personas", html)
        self.assertIn("Salon Danubio", html)
        self.assertIn("Capacidad Adecuada", html)

    def test_detail_capacity_exceeded_alert(self):
        # Crear licitacion con sobrecupo (100 asistentes en salon de 40)
        database.create_licitacion({
            "id_licitacion": "TEST-SOBRECUPO-01",
            "titulo": "Encuentro Regional Aforo Excedido",
            "organismo": "Ministerio de Energia",
            "categoria": "Eventos / Catering",
            "modalidad": "Compra Agil",
            "region": "Region Metropolitana (Santiago)",
            "presupuesto_mandante": 6000000,
            "costo_base_hotel": 4000000,
            "estado_embudo": "Identificada",
            "validacion_adjuntos": "Valida",
            "tiene_anexo4": 1,
            "tiene_escrituras": 1,
            "tiene_poderes": 1,
            "tiene_vigencias": 1,
            "fecha_publicacion": "2026-10-01",
            "fecha_cierre": "2026-10-15",
            "descripcion_tdr": "Taller",
            "cantidad_asistentes": 100,
            "tipo_jornada": "Jornada Completa (8 hrs)",
            "horario_evento": "08:30 a 18:30 hrs",
            "id_salon_asignado": "SALON-PARRA"  # Capacidad: 40
        })

        response = self.client.get("/licitaciones/TEST-SOBRECUPO-01")
        self.assertEqual(response.status_code, 200)
        html = response.data.decode("utf-8")

        self.assertIn("Alerta de Inviabilidad Operativa: Aforo Excedido", html)
        self.assertIn("sobrecupo de", html)
        self.assertIn("60 personas", html)

    def test_detail_capacity_unassigned_salon(self):
        # 440-8-COT24 no tiene salon asignado inicialmente
        response = self.client.get("/licitaciones/440-8-COT24")
        self.assertEqual(response.status_code, 200)
        html = response.data.decode("utf-8")

        self.assertIn("Salon Pendiente de Asignacion", html)

    def test_detail_no_emojis(self):
        emoji_pattern = re.compile(
            "[\U00010000-\U0010ffff]|"
            "[\u2600-\u27bf]|"
            "[\u2300-\u23ff]|"
            "[\u2b50\u2b55\u2934\u2935\u25aa\u25ab\u25b6\u25c0\u25fb-\u25fe]"
        )
        sample_ids = ["1058-12-COT24", "1840-22-COT24", "805-19-LP24", "440-8-COT24"]
        for tender_id in sample_ids:
            response = self.client.get(f"/licitaciones/{tender_id}")
            self.assertEqual(response.status_code, 200)
            html = response.data.decode("utf-8")
            matches = emoji_pattern.findall(html)
            self.assertEqual(matches, [], f"Found emojis in detail view for {tender_id}: {matches}")

    @patch("mercado_publico.consultar_licitacion")
    def test_refrescar_licitacion_actualiza_desde_api(self, mock_consultar):
        # La ficha real trae montos/fechas anidados en Fechas y Moneda en la raiz
        mock_consultar.return_value = {
            "CodigoExterno": "1058-12-COT24",
            "Nombre": "Servicio de Banqueteria y Salones Jornada de Planificacion Estrategica",
            "CodigoEstado": 6,
            "Estado": "Cerrada",
            "FechaCierre": "2026-10-30T15:00:00",
            "Descripcion": "Arriendo de salon plenario para 80 asistentes",
            "Moneda": "CLP",
            "Comprador": {
                "NombreOrganismo": "Subsecretaria de Turismo",
                "RegionUnidad": "Region Metropolitana"
            },
            "Fechas": {"MontoEstimado": 6100000.0, "FechaCreacion": "2026-10-01T00:00:00"}
        }
        # El estado del embudo lo gestiona el equipo: el refresco no debe pisarlo
        database.update_licitacion("1058-12-COT24", {"estado_embudo": "Participada"})

        res = self.client.post("/licitaciones/1058-12-COT24/refrescar", follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        lic = database.get_licitacion_by_id("1058-12-COT24")
        self.assertEqual(lic["presupuesto_mandante"], 6100000)
        self.assertEqual(lic["costo_base_hotel"], 4575000)
        self.assertEqual(lic["fecha_cierre"], "2026-10-30")
        self.assertEqual(lic["fecha_publicacion"], "2026-10-01")
        self.assertEqual(lic["estado_embudo"], "Participada")

    @patch("mercado_publico.consultar_licitacion")
    def test_refrescar_rechaza_otro_codigo(self, mock_consultar):
        mock_consultar.return_value = {
            "CodigoExterno": "OTRO-CODIGO",
            "Nombre": "Otra licitacion",
            "Descripcion": "Hospedaje",
            "Moneda": "CLP",
            "MontoEstimado": 1,
            "Comprador": {"NombreOrganismo": "Otro Organismo"},
        }
        res = self.client.post("/licitaciones/1058-12-COT24/refrescar", follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        lic = database.get_licitacion_by_id("1058-12-COT24")
        self.assertIn("Banqueteria", lic["titulo"])
        self.assertEqual(lic["organismo"], "Subsecretaria de Turismo")

    def test_actualizar_documentos(self):
        res = self.client.post(
            "/licitaciones/1058-12-COT24/documentos",
            data={
                "tiene_anexo4": "on",
                "tiene_escrituras": "on",
                "tiene_poderes": "on",
                "tiene_vigencias": "on",
                "validacion_adjuntos": "Valida",
            },
            follow_redirects=True,
        )
        self.assertEqual(res.status_code, 200)
        lic = database.get_licitacion_by_id("1058-12-COT24")
        self.assertEqual(lic["validacion_adjuntos"], "Valida")
        self.assertEqual(lic["tiene_anexo4"], 1)
        self.assertEqual(lic["tiene_vigencias"], 1)

    def test_detalle_no_usa_fecha_cierre_como_fecha_evento(self):
        res = self.client.get("/licitaciones/1058-12-COT24")
        html = res.get_data(as_text=True)
        self.assertNotIn("fecha_inicio=2026-09-20", html)
        self.assertIn("licitacion=1058-12-COT24", html)

    def test_refrescar_licitacion_no_encontrada(self):
        res = self.client.post("/licitaciones/NO-EXISTE-01/refrescar")
        self.assertEqual(res.status_code, 404)

    def test_ficha_md_view(self):
        res = self.client.get("/licitaciones/1058-12-COT24/ficha.md")
        self.assertEqual(res.status_code, 200)
        self.assertIn("text/markdown", res.headers["Content-Type"])
        md = res.data.decode("utf-8")
        self.assertIn("# Servicio de Banqueteria y Salones", md)
        self.assertIn("1058-12-COT24", md)
        self.assertIn("$5.800.000 CLP", md)
        self.assertIn("## Necesidad (Descripcion TDR)", md)

    def test_ficha_md_descarga_adjunto(self):
        res = self.client.get("/licitaciones/1058-12-COT24/ficha.md?descargar=1")
        self.assertEqual(res.status_code, 200)
        self.assertIn("attachment", res.headers["Content-Disposition"])
        self.assertIn("ficha_1058-12-COT24.md", res.headers["Content-Disposition"])

    def test_ficha_md_no_encontrada(self):
        res = self.client.get("/licitaciones/NO-EXISTE-01/ficha.md")
        self.assertEqual(res.status_code, 404)

    @patch("mercado_publico.consultar_url_adjuntos")
    def test_adjuntos_redirige_al_visor_oficial(self, mock_adj):
        mock_adj.return_value = "https://www.mercadopublico.cl/Procurement/Modules/Attachment/ViewAttachment.aspx?enc=XYZ"
        res = self.client.get("/licitaciones/1058-12-COT24/adjuntos")
        self.assertEqual(res.status_code, 302)
        self.assertIn("ViewAttachment.aspx?enc=XYZ", res.headers["Location"])

    @patch("mercado_publico.consultar_url_adjuntos")
    def test_adjuntos_degrada_a_ficha_oficial(self, mock_adj):
        mock_adj.return_value = None
        res = self.client.get("/licitaciones/1058-12-COT24/adjuntos")
        self.assertEqual(res.status_code, 302)
        self.assertIn("idlicitacion=1058-12-COT24", res.headers["Location"])

    def test_adjuntos_no_encontrada(self):
        res = self.client.get("/licitaciones/NO-EXISTE-01/adjuntos")
        self.assertEqual(res.status_code, 404)


if __name__ == "__main__":
    unittest.main()
