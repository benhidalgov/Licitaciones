import io
import re
import sys
import unittest
from unittest.mock import patch

import run


class TestRunScript(unittest.TestCase):
    def setUp(self):
        self.emoji_pattern = re.compile(
            "[\U00010000-\U0010ffff]|"
            "[\u2600-\u27bf]|"
            "[\u2300-\u23ff]|"
            "[\u2b50\u2b55\u2934\u2935\u25aa\u25ab\u25b6\u25c0\u25fb-\u25fe]"
        )

    def test_run_module_imports_cleanly(self):
        self.assertTrue(hasattr(run, "main"))
        self.assertTrue(callable(run.main))

    @patch("run.app.run")
    @patch("run.database.init_db")
    def test_run_main_initializes_db_and_starts_server(self, mock_init_db, mock_app_run):
        captured_stdout = io.StringIO()
        with patch("sys.stdout", captured_stdout):
            run.main()

        mock_init_db.assert_called_once()
        mock_app_run.assert_called_once_with(host="127.0.0.1", port=5000, debug=True)

        output = captured_stdout.getvalue()
        self.assertIn("ASISTENTE VIRTUAL PARA LICITACIONES", output)
        self.assertIn("http://127.0.0.1:5000", output)
        self.assertIn("admin", output)
        self.assertIn("admin123", output)

        # Verification of zero emojis in printed console messages
        matches = self.emoji_pattern.findall(output)
        self.assertEqual(matches, [], f"Se encontraron emojis en los mensajes de consola de run.py: {matches}")

    def test_no_emojis_in_run_py_source(self):
        with open("run.py", "r", encoding="utf-8") as f:
            content = f.read()
        matches = self.emoji_pattern.findall(content)
        self.assertEqual(matches, [], f"Se encontraron emojis en el codigo fuente de run.py: {matches}")
