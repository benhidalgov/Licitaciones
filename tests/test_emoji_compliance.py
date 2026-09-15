import os
import re
import unittest


class TestEmojiCompliance(unittest.TestCase):
    """
    Verifica el cumplimiento de la restriccion global de diseño corporativo:
    Supresion total y absoluta de emojis en templates, controladores,
    modelos, scripts de inicio, logs y documentacion (README.md).
    """

    def setUp(self):
        self.emoji_pattern = re.compile(
            "[\U00010000-\U0010ffff]|"
            "[\u2600-\u27bf]|"
            "[\u2300-\u23ff]|"
            "[\u2b50\u2b55\u2934\u2935\u25aa\u25ab\u25b6\u25c0\u25fb-\u25fe]"
        )

    def test_repository_files_have_zero_emojis(self):
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        target_extensions = {".py", ".html", ".md", ".txt"}
        violations = []

        for root, dirs, files in os.walk(repo_root):
            # Excluir directorios internos de versionamiento y cache
            if any(part in root for part in [".git", "__pycache__", ".superpowers"]):
                continue

            for file_name in files:
                ext = os.path.splitext(file_name)[1].lower()
                if ext in target_extensions:
                    file_path = os.path.join(root, file_name)
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()
                            matches = self.emoji_pattern.findall(content)
                            if matches:
                                rel_path = os.path.relpath(file_path, repo_root)
                                violations.append((rel_path, matches))
                    except Exception as err:
                        self.fail(f"Error al leer archivo {file_path}: {err}")

        self.assertEqual(
            violations,
            [],
            f"Se detectaron violaciones a la politica de cero emojis en los siguientes archivos: {violations}"
        )
