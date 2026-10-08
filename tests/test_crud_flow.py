import os
import unittest
import app as flask_app
import database


class TestCrudFlow(unittest.TestCase):
    def setUp(self):
        self.db_name = "test_crud_licitaciones.db"
        database.DB_NAME = self.db_name
        if os.path.exists(self.db_name):
            try:
                os.remove(self.db_name)
            except PermissionError:
                pass
        database.init_db()

        flask_app.app.config["TESTING"] = True
        flask_app.app.config["SECRET_KEY"] = "test-crud-secret"
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

    def test_unauthenticated_access_blocked(self):
        unauth = flask_app.app.test_client()

        # POST /licitaciones/1058-12-COT24/eliminar
        r5 = unauth.post("/licitaciones/1058-12-COT24/eliminar")
        self.assertEqual(r5.status_code, 302)
        self.assertIn("/login", r5.headers["Location"])

    def test_manual_form_routes_removed(self):
        # Las licitaciones llegan solo desde la API: no hay alta ni edicion manual.
        self.assertEqual(self.client.get("/licitaciones/nueva").status_code, 404)
        self.assertEqual(self.client.get("/licitaciones/1058-12-COT24/editar").status_code, 404)

    def test_delete_licitacion_post_success(self):
        response = self.client.post("/licitaciones/1058-12-COT24/eliminar", follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        html = response.data.decode("utf-8")

        # Redirected to dashboard
        self.assertIn("Tablero Principal", html)

        # Database verification
        item = database.get_licitacion_by_id("1058-12-COT24")
        self.assertIsNone(item)

    def test_delete_licitacion_post_not_found(self):
        response = self.client.post("/licitaciones/NO-EXISTE-999/eliminar")
        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
