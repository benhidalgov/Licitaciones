# Protocolo y Flujo de Trabajo de Ingenieria (Git Workflow)
## Proyecto: Copilot de Licitaciones y Operaciones Hoteleras
### Hotel Plaza San Francisco | Programa VcM DUOC UC

---

## 1. Principio Rector

La plataforma opera en un entorno corporativo donde la confiabilidad de la agenda de salones y la precision de las alertas de costos son criticas. Por ello:

* La rama `main` debe permanecer siempre en estado desplegable, estable y con el 100% de las pruebas automatizadas aprobadas.
* Queda desaconsejado el commit o push directo a `main` para desarrollos o refactorizaciones de mediana y gran envergadura.
* Cada cambio debe aislarse en su respectiva rama tematica antes de su integracion.

---

## 2. Nomenclatura Estandar de Ramas

Las ramas de trabajo deben crearse a partir de `main` actualizado, siguiendo el formato `<tipo>/<alcance-kebab-case>`:

| Prefijo | Proposito | Ejemplos |
| :--- | :--- | :--- |
| `feat/` | Nuevas caracteristicas funcionales | `feat/mercado-publico-sync`, `feat/reportes-ejecutivos` |
| `fix/` | Correccion de defectos o errores de logica | `fix/aforo-solapamiento`, `fix/margen-display` |
| `refactor/` | Reestructuracion interna sin cambio funcional | `refactor/modularizacion-blueprints`, `refactor/consultas-db` |
| `docs/` | Modificaciones o adiciones documentales | `docs/actualizacion-manual`, `docs/guia-despliegue` |
| `test/` | Nuevas pruebas unitarias o de integracion | `test/admisibilidad-anexo4`, `test/rendimiento-agenda` |

---

## 3. Convencion de Mensajes de Commit (Conventional Commits)

Evitar mensajes genericos (`"fixes"`, `"update"`, `"push"`). Emplear la estructura formal:

```text
<tipo>: <descripcion breve en presente indicativo>

[cuerpo opcional detallando el motivo o impacto]
```

### Tipos admitidos:
* `feat`: Incorporacion de una nueva funcionalidad.
* `fix`: Correccion de un error en produccion o pruebas.
* `refactor`: Limpieza o redistribucion de codigo sin alterar la logica de negocio.
* `test`: Adicion o correccion de pruebas unitarias.
* `docs`: Documentacion tecnica, manuales de usuario o requerimientos.
* `chore`: Actualizacion de dependencias o configuraciones secundarias.

---

## 4. Ciclo Operativo Paso a Paso

### Paso 1: Sincronizar rama base
```bash
git checkout main
git pull origin main
```

### Paso 2: Crear rama de trabajo
```bash
git checkout -b feat/nombre-de-la-tarea
```

### Paso 3: Desarrollo con garantia de calidad
Durante el desarrollo, asegurarse de mantener o agregar las pruebas unitarias correspondientes en el directorio `tests/`.

### Paso 4: Validacion previa obligatoria
Antes de confirmar o solicitar fusion, ejecutar el script de verificacion oficial:
```bash
python verify.py
```
> [!IMPORTANT]
> El script debe retornar `[OK] Todas las pruebas han sido aprobadas exitosamente.` (codigo de salida 0). Si alguna prueba falla, debe corregirse antes de proceder.

### Paso 5: Confirmar cambios
```bash
git add .
git commit -m "feat: implementacion de nuevo filtro por region"
```

### Paso 6: Integracion a `main`
Opcion A (Via GitHub Pull Request - Recomendado en equipo):
```bash
git push -u origin feat/nombre-de-la-tarea
# Crear PR hacia main en la interfaz de GitHub
```

Opcion B (Fusion local controlada):
```bash
git checkout main
git pull origin main
git merge --no-ff feat/nombre-de-la-tarea
python verify.py
git push origin main
git branch -d feat/nombre-de-la-tarea
```

---

## 5. Politicas Obligatorias del Proyecto

1. **Politica Estricta de Cero Emojis:**
   Prohibido incluir caracteres emoji en codigo, plantillas HTML, mensajes flash, registros de consola y documentacion. Esta regla es evaluada automaticamente por `tests/test_emoji_compliance.py`.
2. **Ejecucion 100% Web:**
   No distribuir archivos ejecutables (`.exe`) ni scripts que deban ser ejecutados localmente por el usuario final en los computadores del hotel. Todo debe servirse a traves de la interfaz web en Flask.
3. **Integridad Documental ("Efecto ID"):**
   Cualquier funcionalidad relacionada con Mercado Publico debe validar los identificadores contra los adjuntos reales y no confiar en resúmenes preliminares.
