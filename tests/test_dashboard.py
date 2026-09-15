import os
import re
import unittest
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

    def test_dashboard_new_tender_button(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        html = response.data.decode("utf-8")
        self.assertIn("Registrar Nueva Licitacion", html)
        self.assertIn("/licitaciones/nueva", html)

    def test_dashboard_filter_category(self):
        response = self.client.get("/?categoria=Alojamiento")
        self.assertEqual(response.status_code, 200)
        html = response.data.decode("utf-8")
        # Should include Alojamiento tender
        self.assertIn("723-4-LP24", html)
        # Should NOT include Banqueteria / Eventos tender
        self.assertNotIn("1058-12-COT24", html)

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
        self.assertIn("ID Verificado", html)

    def test_dashboard_action_links(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        html = response.data.decode("utf-8")
        self.assertIn("/licitaciones/1058-12-COT24", html)
        self.assertIn("/licitaciones/1058-12-COT24/editar", html)
        self.assertIn("Ver Detalle", html)
        self.assertIn("Editar", html)
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


if __name__ == "__main__":
    unittest.main()
