import os
import unittest
from datetime import date
import app as flask_app
import database


def _licitacion_informe(id_licitacion, estado="Identificada", presupuesto=1000):
    return {
        "id_licitacion": id_licitacion,
        "titulo": "Evento para informe",
        "organismo": "Ministerio de Prueba",
        "categoria": "Eventos / Catering",
        "modalidad": "Licitacion Publica",
        "region": "Region Metropolitana",
        "presupuesto_mandante": presupuesto,
        "costo_base_hotel": 500,
        "estado_embudo": estado,
        "validacion_adjuntos": "Valida",
        "tiene_anexo4": 1,
        "tiene_escrituras": 1,
        "tiene_poderes": 1,
        "tiene_vigencias": 1,
        "fecha_publicacion": date.today().isoformat(),
        "fecha_cierre": "2027-10-23",
        "descripcion_tdr": "Evento para informe",
    }


class TestInformes(unittest.TestCase):
    def setUp(self):
        self.db_name = "test_informes_licitaciones.db"
        database.DB_NAME = self.db_name
        if os.path.exists(self.db_name):
            try:
                os.remove(self.db_name)
            except PermissionError:
                pass
        database.init_db()
        database.create_licitacion(_licitacion_informe("TEST-INFORME-BASE"))

        flask_app.app.config["TESTING"] = True
        flask_app.app.config["SECRET_KEY"] = "test-informes-secret"
        flask_app.app.config["CSRF_ENABLED"] = False
        self.client = flask_app.app.test_client()
        with self.client.session_transaction() as sess:
            sess["user"] = "admin"
            sess["nombre"] = "Administrador"

    def tearDown(self):
        if os.path.exists(self.db_name):
            try:
                os.remove(self.db_name)
            except PermissionError:
                pass

    def test_informe_semanal_renderiza(self):
        response = self.client.get("/informes?periodo=semanal")
        self.assertEqual(response.status_code, 200)
        html = response.data.decode("utf-8")
        self.assertIn("Informe Semanal", html)
        self.assertIn("Gerencia General y Direccion de Finanzas", html)
        self.assertIn("Demanda por categoria", html)

    def test_informe_mensual_renderiza(self):
        response = self.client.get("/informes?periodo=mensual")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Informe Mensual", response.data.decode("utf-8"))

    def test_exportar_informe_csv(self):
        response = self.client.get("/informes/exportar.csv?periodo=semanal")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/csv", response.headers["Content-Type"])
        texto = response.data.decode("utf-8-sig")
        self.assertIn("Informe consolidado;Semanal", texto)
        self.assertIn("Categoria;Oportunidades", texto)

    def test_informe_requiere_login(self):
        response = flask_app.app.test_client().get("/informes")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.headers["Location"])

    def test_reporte_periodo_incluye_publicacion_del_dia(self):
        hoy = date.today().isoformat()
        database.create_licitacion(
            _licitacion_informe("TEST-INFORME-01", "Adjudicada", 999999999)
        )
        reporte = database.get_reporte_periodo(hoy, hoy)
        self.assertGreaterEqual(reporte["total"], 2)
        self.assertEqual(reporte["adjudicadas"], 1)
        self.assertIn("Ministerio de Prueba", {
            fila["organismo"] for fila in reporte["por_organismo"]
        })


if __name__ == "__main__":
    unittest.main()
