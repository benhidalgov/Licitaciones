import io
import os
import re
import unittest
from unittest.mock import patch
import app as flask_app
import database


class TestDashboard(unittest.TestCase):
    def setUp(self):
        self.db_name = "test_dash_licitaciones.db"
        database.DB_NAME = self.db_name
        if os.path.exists(self.db_name):
            try:
                os.remove(self.db_name)
            except PermissionError:
                pass
        database.init_db()

        flask_app.app.config["TESTING"] = True
        flask_app.app.config["SECRET_KEY"] = "test-dashboard-secret"
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

    def test_unauthenticated_redirect(self):
        unauth_client = flask_app.app.test_client()
        res_root = unauth_client.get("/")
        self.assertEqual(res_root.status_code, 302)
        self.assertIn("/login", res_root.headers["Location"])

        res_lic = unauth_client.get("/licitaciones")
        self.assertEqual(res_lic.status_code, 302)
        self.assertIn("/login", res_lic.headers["Location"])

    def test_dashboard_metrics_rendered(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        html = response.data.decode("utf-8")

        # Metric cards
        self.assertIn("Total Identificadas", html)
        self.assertIn("Calificadas", html)
        self.assertIn("Participadas", html)
        self.assertIn("Adjudicadas", html)
        self.assertIn("Compra Agil", html)

    def test_dashboard_filter_category(self):
        response = self.client.get("/?categoria=Alojamiento")
        self.assertEqual(response.status_code, 200)
        html = response.data.decode("utf-8")
        # Should include Alojamiento tender
        self.assertIn("723-4-LP24", html)
        # Should NOT include Banqueteria / Eventos tender
        self.assertNotIn("1058-12-COT24", html)

    def test_filtro_miles(self):
        env = flask_app.app.jinja_env
        self.assertEqual(env.filters["miles"](1234567), "1.234.567")
        self.assertEqual(env.filters["miles"](46), "46")
        self.assertEqual(env.filters["miles"]("no-numero"), "no-numero")

    def test_tope_compra_agil_editable_en_tablero(self):
        response = self.client.post(
            "/ajustes/tope_compra_agil",
            data={"tope_compra_agil": "7.500.000"},
            follow_redirects=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(database.get_tope_compra_agil(), 7500000)
        self.assertIn("7.500.000", response.data.decode("utf-8"))

        # Valor invalido no altera el tope guardado
        bad = self.client.post(
            "/ajustes/tope_compra_agil",
            data={"tope_compra_agil": "no-numero"},
            follow_redirects=True
        )
        self.assertEqual(database.get_tope_compra_agil(), 7500000)
        self.assertIn("numero entero mayor a cero", bad.data.decode("utf-8"))

    def test_margen_tolerancia_editable_en_tablero(self):
        response = self.client.post(
            "/ajustes/margen_tolerancia",
            data={"modo": "porcentaje", "valor": "10"},
            follow_redirects=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(database.get_margen_tolerancia(), {"modo": "porcentaje", "valor": 10})
        self.assertIn("10%", response.data.decode("utf-8"))

        # Un porcentaje fuera de rango no altera el valor guardado
        bad = self.client.post(
            "/ajustes/margen_tolerancia",
            data={"modo": "porcentaje", "valor": "150"},
            follow_redirects=True
        )
        self.assertEqual(database.get_margen_tolerancia(), {"modo": "porcentaje", "valor": 10})
        self.assertIn("entre 0 y 100", bad.data.decode("utf-8"))

    def test_margen_tolerancia_fijo_en_clp(self):
        response = self.client.post(
            "/ajustes/margen_tolerancia",
            data={"modo": "clp", "valor": "500.000"},
            follow_redirects=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(database.get_margen_tolerancia(), {"modo": "clp", "valor": 500000})

    def test_dashboard_filter_modalidad(self):
        response = self.client.get("/?modalidad=Compra+Agil")
        self.assertEqual(response.status_code, 200)
        html = response.data.decode("utf-8")
        self.assertIn("1058-12-COT24", html)
        self.assertNotIn("723-4-LP24", html)

    def test_dashboard_filter_estado(self):
        response = self.client.get("/?estado=Adjudicada")
        self.assertEqual(response.status_code, 200)
        html = response.data.decode("utf-8")
        self.assertIn("930-15-LP23", html)
        self.assertNotIn("1058-12-COT24", html)

    def test_dashboard_search_term(self):
        response = self.client.get("/?q=Turismo")
        self.assertEqual(response.status_code, 200)
        html = response.data.decode("utf-8")
        self.assertIn("Subsecretaria de Turismo", html)
        self.assertIn("1058-12-COT24", html)
        self.assertNotIn("723-4-LP24", html)

    def test_dashboard_search_by_id(self):
        response = self.client.get("/?q=805-19-LP24")
        self.assertEqual(response.status_code, 200)
        html = response.data.decode("utf-8")
        self.assertIn("805-19-LP24", html)
        self.assertIn("Gobierno Regional Metropolitano", html)
        self.assertNotIn("1058-12-COT24", html)

    def test_dashboard_combined_filters(self):
        response = self.client.get("/?categoria=Alojamiento&modalidad=Compra+Agil")
        self.assertEqual(response.status_code, 200)
        html = response.data.decode("utf-8")
        self.assertIn("440-8-COT24", html)
        self.assertNotIn("723-4-LP24", html)
        self.assertNotIn("1058-12-COT24", html)

    def test_dashboard_clp_formatting(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        html = response.data.decode("utf-8")
        # Check CLP format $5.800.000 CLP or $28.000.000 CLP
        self.assertIn("$5.800.000 CLP", html)
        self.assertIn("$28.000.000 CLP", html)

    def test_dashboard_budget_viability_indicator(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        html = response.data.decode("utf-8")
        # 1840-22-COT24: Presupuesto 6.400.000 < Costo 6.700.000 -> Inviable / Costo Excede
        self.assertIn("Inviable / Costo Excede", html)
        # Viable indicator
        self.assertIn("Viable / Margen Positivo", html)

    def test_dashboard_id_crosscheck_indicators(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        html = response.data.decode("utf-8")
        # 805-19-LP24 has validacion_adjuntos = 'Error ID / Discrepancia'
        self.assertIn("Discrepancia ID", html)
        # Normal tenders have validacion_adjuntos = 'Valida'
        self.assertIn("ID verificado", html)

    def test_dashboard_action_links(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        html = response.data.decode("utf-8")
        self.assertIn("/licitaciones/1058-12-COT24", html)
        self.assertIn(">Ver</a>", html)
        self.assertIn("Eliminar", html)

    def test_dashboard_no_emojis(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        html = response.data.decode("utf-8")
        # Regex matching emojis in unicode
        emoji_pattern = re.compile(
            "[\U00010000-\U0010ffff]|"
            "[\u2600-\u27bf]|"
            "[\u2300-\u23ff]|"
            "[\u2b50\u2b55\u2934\u2935\u25aa\u25ab\u25b6\u25c0\u25fb-\u25fe]"
        )
        matches = emoji_pattern.findall(html)
        self.assertEqual(matches, [], f"Found emojis in dashboard output: {matches}")

    def test_dashboard_renders_sync_button_and_ticket_status(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        html = response.data.decode("utf-8")
        self.assertIn("Sincronizar Mercado Publico", html)
        self.assertTrue("API activa" in html or "Ticket pendiente" in html)

    def test_sincronizar_route_unauthenticated(self):
        unauth_client = flask_app.app.test_client()
        res = unauth_client.post("/licitaciones/sincronizar")
        self.assertEqual(res.status_code, 302)
        self.assertIn("/login", res.headers["Location"])

    @patch("mercado_publico.sincronizar_licitaciones")
    def test_sincronizar_route_authenticated(self, mock_sync):
        mock_sync.return_value = {"total_consultadas": 0, "total_guardadas": 0, "mensaje": "ok"}
        res = self.client.post("/licitaciones/sincronizar", follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        html = res.data.decode("utf-8")
        self.assertIn("Sincronizar Mercado Publico", html)
        # Sin fecha explicita sincroniza la ultima semana
        mock_sync.assert_called_with(fecha=None, dias=7)

    def test_sincronizar_get_rechazado(self):
        res = self.client.get("/licitaciones/sincronizar")
        self.assertIn(res.status_code, (404, 405))

    @patch("mercado_publico.sincronizar_licitaciones")
    def test_sincronizar_fecha_invalida_no_llama_api(self, mock_sync):
        res = self.client.post(
            "/licitaciones/sincronizar", data={"fecha": "2026-01-01"}, follow_redirects=True
        )
        self.assertEqual(res.status_code, 200)
        self.assertIn("formato DDMMAAAA", res.get_data(as_text=True))
        mock_sync.assert_not_called()

    @patch("mercado_publico.sincronizar_licitaciones")
    def test_sincronizar_no_corre_dos_veces(self, mock_sync):
        adquirido = flask_app._sync_lock.acquire(blocking=False)
        self.assertTrue(adquirido)
        try:
            res = self.client.post("/licitaciones/sincronizar", follow_redirects=True)
        finally:
            flask_app._sync_lock.release()
        self.assertIn("Ya hay una sincronizacion en curso", res.get_data(as_text=True))
        mock_sync.assert_not_called()

    def test_busqueda_ignora_tildes(self):
        html = self.client.get("/licitaciones?q=Región").get_data(as_text=True)
        self.assertIn("1058-12-COT24", html)
        html = self.client.get("/licitaciones?q=Minería").get_data(as_text=True)
        self.assertIn("723-4-LP24", html)

    def test_filtro_cliente_clave_minsal(self):
        html = self.client.get("/licitaciones?cliente_clave=Minsal").get_data(as_text=True)
        self.assertIn("440-8-COT24", html)

    def test_margen_tolerancia_decimal(self):
        response = self.client.post(
            "/ajustes/margen_tolerancia",
            data={"modo": "porcentaje", "valor": "0,2"},
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            database.get_margen_tolerancia(), {"modo": "porcentaje", "valor": 0.2}
        )
        self.assertIn("0.2%", response.get_data(as_text=True))

    def test_exportacion_xlsx_con_enlace(self):
        response = self.client.get("/licitaciones/exportar.xlsx")
        self.assertEqual(response.status_code, 200)
        self.assertIn("spreadsheetml", response.headers["Content-Type"])
        from openpyxl import load_workbook
        libro = load_workbook(io.BytesIO(response.data))
        hoja = libro.active
        encabezados = [celda.value for celda in hoja[1]]
        self.assertIn("Ficha Mercado Publico", encabezados)

    def test_priorizadas_avisa_cuando_todo_cerro(self):
        html = self.client.get("/").get_data(as_text=True)
        self.assertIn("Todas las licitaciones registradas ya cerraron", html)

    def test_cabeceras_de_seguridad(self):
        response = self.client.get("/")
        self.assertEqual(response.headers["X-Frame-Options"], "DENY")
        self.assertEqual(response.headers["X-Content-Type-Options"], "nosniff")
        self.assertIn("Content-Security-Policy", response.headers)

    def test_metricas_enlazan_al_listado_filtrado(self):
        html = self.client.get("/").get_data(as_text=True)
        self.assertIn('id="oportunidades"', html)
        self.assertIn("estado=Identificada#oportunidades", html)
        self.assertIn("modalidad=Compra+Agil#oportunidades", html)

    def test_filtro_revisadas_por_usuario(self):
        with self.client.session_transaction() as sess:
            sess["user"] = "daniela"
            sess["nombre"] = "Daniela"
        self.client.post(
            "/licitaciones/723-4-LP24/decision", data={"decision": "revisar"}
        )

        html = self.client.get("/licitaciones?revisada_por=Daniela").get_data(as_text=True)
        self.assertIn("723-4-LP24", html)
        self.assertIn("Revisada por Daniela", html)
        self.assertNotIn("1058-12-COT24", html)

        pendientes = self.client.get("/licitaciones?revisada_por=pendientes").get_data(as_text=True)
        self.assertIn("1058-12-COT24", pendientes)
        self.assertNotIn("723-4-LP24", pendientes)

        # Si Mari vuelve a revisar, el filtro debe coincidir con el badge:
        # Daniela deja de ser la revisora vigente.
        with self.client.session_transaction() as sess:
            sess["user"] = "mari"
            sess["nombre"] = "Mari"
        self.client.post(
            "/licitaciones/723-4-LP24/decision", data={"decision": "revisar"}
        )
        por_daniela = self.client.get("/licitaciones?revisada_por=Daniela").get_data(as_text=True)
        self.assertNotIn("723-4-LP24", por_daniela)
        por_mari = self.client.get("/licitaciones?revisada_por=Mari").get_data(as_text=True)
        self.assertIn("723-4-LP24", por_mari)
        self.assertIn("Revisada por Mari", por_mari)


if __name__ == "__main__":
    unittest.main()

