#!/usr/bin/env python3
"""
Script de verificacion local de calidad y pruebas unitarias.
Copilot de Licitaciones y Operaciones Hoteleras.
Hotel Plaza San Francisco | DUOC UC

Uso:
    python verify.py

Retorna codigo 0 si todas las pruebas pasan exitosamente.
Retorna codigo 1 si existen fallos, errores o violaciones normativas.
"""

import os
import sys
import time
import unittest


def main():
    print("=" * 70)
    print("COPILOT DE LICITACIONES - PROTOCOLO DE VERIFICACION LOCAL")
    print("Hotel Plaza San Francisco | DUOC UC")
    print("=" * 70)
    print("[INFO] Buscando y ejecutando suite de pruebas unitarias en /tests...")

    repo_root = os.path.dirname(os.path.abspath(__file__))
    tests_dir = os.path.join(repo_root, "tests")

    start_time = time.time()
    loader = unittest.TestLoader()
    suite = loader.discover(start_dir=tests_dir, pattern="test_*.py")

    runner = unittest.TextTestRunner(verbosity=1)
    result = runner.run(suite)
    elapsed = time.time() - start_time

    total_tests = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    skipped = len(result.skipped)

    print("-" * 70)
    print(f"[INFO] Pruebas ejecutadas : {total_tests}")
    print(f"[INFO] Tiempo total       : {elapsed:.2f}s")
    print(f"[INFO] Omitidas (skipped) : {skipped}")
    print(f"[INFO] Fallos (failures)  : {failures}")
    print(f"[INFO] Errores (errors)   : {errors}")

    if result.wasSuccessful():
        print("[OK] Todas las pruebas han sido aprobadas exitosamente.")
        print("[OK] La rama cumple con los criterios de integracion.")
        print("=" * 70)
        return 0
    else:
        print("[FAIL] Se han detectado pruebas no superadas.")
        print("[FAIL] Resuelva los incidentes anteriores antes de integrar a 'main'.")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    sys.exit(main())
