import os
import unittest
import app as flask_app
import database


class TestAuth(unittest.TestCase):
    def setUp(self):
        database.DB_NAME = "test_auth_licitaciones.db"
        if os.path.exists(database.DB_NAME):
            os.remove(database.DB_NAME)
        database.init_db()
        flask_app.app.config["TESTING"] = True
        flask_app.app.config["SECRET_KEY"] = "test-secret"
        self.client = flask_app.app.test_client()

    def tearDown(self):
        if os.path.exists(database.DB_NAME):
            os.remove(database.DB_NAME)

    def test_redirect_to_login_when_unauthenticated(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.headers["Location"])

    def test_licitaciones_route_redirect_to_login_when_unauthenticated(self):
        response = self.client.get("/licitaciones")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.headers["Location"])

    def test_login_page_renders_demo_credentials(self):
        response = self.client.get("/login")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"admin", response.data)
        self.assertIn(b"admin123", response.data)
        self.assertIn(b"Iniciar Sesion", response.data)

    def test_login_failure_invalid_credentials(self):
        response = self.client.post(
            "/login",
            data={"username": "user", "password": "wrongpassword"},
            follow_redirects=True
        )
        self.assertIn(b"Credenciales invalidas", response.data)

    def test_login_success(self):
        response = self.client.post(
            "/login",
            data={"username": "admin", "password": "admin123"},
            follow_redirects=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Panel de Control", response.data)

    def test_licitaciones_accessible_when_authenticated(self):
        self.client.post("/login", data={"username": "admin", "password": "admin123"})
        response = self.client.get("/licitaciones")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Panel de Control", response.data)

    def test_logout(self):
        # Login first
        self.client.post("/login", data={"username": "admin", "password": "admin123"})
        # Logout
        response = self.client.get("/logout", follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Iniciar Sesion", response.data)


if __name__ == "__main__":
    unittest.main()
