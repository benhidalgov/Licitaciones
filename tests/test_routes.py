import os
import unittest
import app as flask_app
import database


class TestRutas(unittest.TestCase):
    def setUp(self):
        database.DB_NAME = "test_rutas_licitaciones.db"
        if os.path.exists(database.DB_NAME):
            os.remove(database.DB_NAME)
        database.init_db()
        flask_app.app.config["TESTING"] = True
        flask_app.app.config["CSRF_ENABLED"] = False
        self.client = flask_app.app.test_client()
        with self.client.session_transaction() as sess:
            sess["user"] = "admin"
            sess["nombre"] = "Administrador"

    def tearDown(self):
        if os.path.exists(database.DB_NAME):
            os.remove(database.DB_NAME)

    def test_rutas_get_sin_parametros_no_fallan(self):
        for regla in flask_app.app.url_map.iter_rules():
            if "GET" not in regla.methods or "<" in regla.rule or regla.endpoint == "static":
                continue
            respuesta = self.client.get(regla.rule)
            self.assertLess(
                respuesta.status_code, 500,
                f"{regla.rule} devolvio {respuesta.status_code}",
            )


if __name__ == "__main__":
    unittest.main()
