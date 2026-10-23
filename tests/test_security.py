import os
import re
import unittest
import app as flask_app
import database


class TestSecurity(unittest.TestCase):
    def setUp(self):
        self.db_name = "test_security_licitaciones.db"
        database.DB_NAME = self.db_name
        if os.path.exists(self.db_name):
            try:
                os.remove(self.db_name)
            except PermissionError:
                pass
        database.init_db()

        flask_app.app.config["TESTING"] = True
        flask_app.app.config["SECRET_KEY"] = "test-security-secret"
        flask_app.app.config["CSRF_ENABLED"] = True
        flask_app._login_attempts.clear()
        self.client = flask_app.app.test_client()
        self.admin_password = flask_app.USERS["admin"]["password"]

    def tearDown(self):
        flask_app.app.config["CSRF_ENABLED"] = False
        flask_app._login_attempts.clear()
        if os.path.exists(self.db_name):
            try:
                os.remove(self.db_name)
            except PermissionError:
                pass

    def _get_csrf_token_from_login_page(self):
        response = self.client.get("/login")
        self.assertEqual(response.status_code, 200)
        match = re.search(r'name="csrf_token" value="([^"]+)"', response.data.decode("utf-8"))
        self.assertIsNotNone(match, "El formulario de login debe incluir el campo oculto csrf_token")
        return match.group(1)

    def test_login_form_includes_csrf_token(self):
        self._get_csrf_token_from_login_page()

    def test_post_without_csrf_token_is_rejected(self):
        self._get_csrf_token_from_login_page()
        response = self.client.post(
            "/login",
            data={"username": "admin", "password": self.admin_password}
        )
        self.assertEqual(response.status_code, 400)

    def test_post_with_invalid_csrf_token_is_rejected(self):
        self._get_csrf_token_from_login_page()
        response = self.client.post(
            "/login",
            data={"username": "admin", "password": self.admin_password, "csrf_token": "token-falso"}
        )
        self.assertEqual(response.status_code, 400)

    def test_post_with_valid_csrf_token_succeeds(self):
        token = self._get_csrf_token_from_login_page()
        response = self.client.post(
            "/login",
            data={"username": "admin", "password": self.admin_password, "csrf_token": token},
            follow_redirects=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Panel de Control", response.data)

    def test_logout_requires_post_method(self):
        response = self.client.get("/logout")
        self.assertEqual(response.status_code, 405)

    def test_session_cookie_flags(self):
        self.assertEqual(flask_app.app.config["SESSION_COOKIE_SAMESITE"], "Lax")
        self.assertTrue(flask_app.app.config["SESSION_COOKIE_HTTPONLY"])

    def test_login_rate_limit_blocks_after_repeated_failures(self):
        token = self._get_csrf_token_from_login_page()
        limit = flask_app.app.config["LOGIN_RATE_LIMIT"]
        for _ in range(limit):
            response = self.client.post(
                "/login",
                data={"username": "intruso", "password": "mal", "csrf_token": token}
            )
            self.assertEqual(response.status_code, 200)
            self.assertIn(b"Credenciales invalidas", response.data)

        blocked = self.client.post(
            "/login",
            data={"username": "admin", "password": self.admin_password, "csrf_token": token}
        )
        self.assertEqual(blocked.status_code, 429)
        self.assertIn(b"Demasiados intentos", blocked.data)

    def test_login_attempts_map_prunes_old_entries(self):
        viejo = flask_app.time.monotonic() - 1000
        flask_app._login_attempts.clear()
        for i in range(1001):
            flask_app._login_attempts[f"10.0.0.{i}"] = (1, viejo)
        flask_app._record_login_failure("nueva-ip")
        self.assertLess(len(flask_app._login_attempts), 1001)


if __name__ == "__main__":
    unittest.main()
