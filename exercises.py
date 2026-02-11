"""exercises.py - Ejercicios precargados del PDF y apuntes del alumno.

Contiene 9 ejercicios del PDF de la asignatura y de apuntes de clase.
Cada ejercicio es un diccionario con:
  - id: identificador corto (ej: "3a")
  - title: titulo descriptivo
  - description: explicacion del ejercicio (incluye avisos sobre erratas)
  - partial: True si es un ejercicio parcial (solo page-out, sin flujo completo)
  - params: parametros para pasar directamente a solver.solve_full_exercise()

Algunos ejercicios tienen erratas conocidas del enunciado original:
  - PTE que dice page fault pero el bit I indica lo contrario
  - Celdas duplicadas en colas LRU
Estos casos estan documentados con AVISO en la descripcion.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Ejercicios precargados
# ---------------------------------------------------------------------------

EXERCISES: list[dict] = [
    # ------------------------------------------------------------------
    # Ejercicio 3a — Sin page fault
    # ------------------------------------------------------------------
    {
        "id": "3a",
        "title": "Ejercicio 3a -- dV=03FFA3, PTE=05E8 (sin page fault)",
        "description": (
            "Disco 3330, RSIZE=100K. PTE con I=0, traduccion directa.\n"
            "No se necesita LRU ni acceso a disco."
        ),
        "partial": False,
        "params": {
            "dv_hex": "03FFA3",
            "pte_hex": "05E8",
            "rsize_kb": 100,
            "disk_model": "3330",
            "queues": None,
            "pfte_bytes_45_hex": None,
        },
    },
    # ------------------------------------------------------------------
    # Ejercicio 3b — Page fault
    # ------------------------------------------------------------------
    {
        "id": "3b",
        "title": "Ejercicio 3b -- dV=03FFA3, PTE=103C (page fault)",
        "description": (
            "Disco 3330, RSIZE=100K. PTE con I=1, page fault.\n"
            "LRU de 2a oportunidad con todas las colas pobladas.\n"
            "PFTE octetos 4-5 = 05A2."
        ),
        "partial": False,
        "params": {
            "dv_hex": "03FFA3",
            "pte_hex": "103C",
            "rsize_kb": 100,
            "disk_model": "3330",
            "queues": {
                "Q00": [(17, 1, 0), (25, 1, 1), (14, 1, 0)],
                "Q01": [(31, 1, 1), (48, 1, 1), (33, 1, 1), (29, 1, 1)],
                "Q10": [(35, 1, 0), (22, 1, 1)],
                "Q11": [(20, 0, 1), (37, 1, 1), (34, 1, 1)],
                "HQ":  [(32, 1, 0), (36, 1, 1), (28, 1, 0)],
            },
            "pfte_bytes_45_hex": "05A2",
        },
    },
    # ------------------------------------------------------------------
    # Ejercicio 4a — Page fault
    # ------------------------------------------------------------------
    {
        "id": "4a",
        "title": "Ejercicio 4a -- dV=03F7A3, PTE=0134 (page fault)",
        "description": (
            "Disco 3350, RSIZE=100K. PTE con I=1, page fault.\n"
            "PFTE octetos 4-5 = 05A2."
        ),
        "partial": False,
        "params": {
            "dv_hex": "03F7A3",
            "pte_hex": "0134",
            "rsize_kb": 100,
            "disk_model": "3350",
            "queues": {
                "Q00": [(17, 1, 0), (25, 1, 1), (14, 1, 0)],
                "Q01": [(31, 1, 1), (48, 1, 1), (23, 0, 1), (29, 1, 1)],
                "Q10": [(35, 1, 0), (22, 1, 1)],
                "Q11": [(20, 0, 1), (37, 1, 1), (34, 1, 1)],
                "HQ":  [(32, 1, 0), (36, 1, 1), (28, 1, 0)],
            },
            "pfte_bytes_45_hex": "05A2",
        },
    },
    # ------------------------------------------------------------------
    # Ejercicio 4b — PTE=1033
    # NOTA: PTE=1033 tiene bit I=0 (sin page fault real).
    #   El enunciado dice page fault; es posible que la PTE correcta
    #   sea 1034 (bit I=1). Se incluye tal cual del enunciado.
    # ------------------------------------------------------------------
    {
        "id": "4b",
        "title": "Ejercicio 4b -- dV=03F7A3, PTE=1033",
        "description": (
            "Disco 3350, RSIZE=100K.\n"
            "AVISO: El enunciado indica page fault, pero PTE=1033 tiene\n"
            "bit I=0 (sin page fault). Posible errata: quiza PTE=1034.\n"
            "Se incluyen colas y PFTE por si se corrige la PTE.\n"
            "PFTE octetos 4-5 = 05A2."
        ),
        "partial": False,
        "params": {
            "dv_hex": "03F7A3",
            "pte_hex": "1033",
            "rsize_kb": 100,
            "disk_model": "3350",
            "queues": {
                "Q00": [(17, 1, 0), (25, 1, 1), (14, 1, 0)],
                "Q01": [(31, 1, 1), (48, 1, 1), (23, 0, 1), (29, 1, 1)],
                "Q10": [(35, 1, 0), (22, 1, 1)],
                "Q11": [(20, 0, 1), (37, 1, 1), (34, 1, 1)],
                "HQ":  [(32, 1, 0), (36, 1, 1), (28, 1, 0)],
            },
            "pfte_bytes_45_hex": "05A2",
        },
    },
    # ------------------------------------------------------------------
    # Ejercicio 5a — Sin page fault
    # NOTA: PTE=0004 tiene bit I=1 (page fault real).
    #   El enunciado dice sin page fault. Posible que las PTEs de 5a y
    #   5b esten intercambiadas (5a->0133 I=0, 5b->0004 I=1).
    #   Se incluye tal cual del enunciado.
    # ------------------------------------------------------------------
    {
        "id": "5a",
        "title": "Ejercicio 5a -- dV=05F7FF, PTE=0004",
        "description": (
            "Disco 3350, RSIZE=100K.\n"
            "AVISO: El enunciado dice sin page fault, pero PTE=0004 tiene\n"
            "bit I=1 (page fault). Posible errata: puede que las PTEs de\n"
            "5a y 5b esten intercambiadas (5a->0133, 5b->0004).\n"
            "Sin colas LRU; si la PTE real da page fault, fallara."
        ),
        "partial": False,
        "params": {
            "dv_hex": "05F7FF",
            "pte_hex": "0004",
            "rsize_kb": 100,
            "disk_model": "3350",
            "queues": None,
            "pfte_bytes_45_hex": None,
        },
    },
    # ------------------------------------------------------------------
    # Ejercicio 5b — Page fault
    # NOTA: PTE=0133 tiene bit I=0 (sin page fault real).
    #   Ver nota del ejercicio 5a: posible intercambio.
    # ------------------------------------------------------------------
    {
        "id": "5b",
        "title": "Ejercicio 5b -- dV=05F7FF, PTE=0133",
        "description": (
            "Disco 3350, RSIZE=100K.\n"
            "AVISO: El enunciado dice page fault, pero PTE=0133 tiene\n"
            "bit I=0 (sin page fault). Posible errata: ver nota de 5a.\n"
            "Se incluyen colas y PFTE por si se corrige la PTE.\n"
            "PFTE octetos 4-5 = 0545."
        ),
        "partial": False,
        "params": {
            "dv_hex": "05F7FF",
            "pte_hex": "0133",
            "rsize_kb": 100,
            "disk_model": "3350",
            "queues": {
                "Q00": [(13, 1, 0), (24, 1, 1), (17, 1, 0)],
                "Q01": [(29, 1, 1), (22, 1, 1), (23, 0, 1), (21, 1, 1)],
                "Q10": [(35, 1, 0), (22, 1, 1)],
                "Q11": [(20, 0, 1), (37, 1, 1), (34, 1, 1)],
                "HQ":  [(32, 1, 0), (36, 1, 1), (28, 1, 0)],
            },
            "pfte_bytes_45_hex": "0545",
        },
    },
    # ------------------------------------------------------------------
    # Ejercicio 6 — Solo page-out (parcial)
    # ------------------------------------------------------------------
    {
        "id": "6",
        "title": "Ejercicio 6 -- Solo page-out: pagina 1442, celda 23",
        "description": (
            "Disco 3350, RSIZE=100K. Ejercicio parcial:\n"
            "solo calcula EPA y DC del page-out.\n"
            "Pagina absoluta = 1442, celda victima = 23."
        ),
        "partial": True,
        "params": {
            "num_abs_page": 1442,
            "cell_number": 23,
            "disk_model": "3350",
            "rsize_kb": 100,
        },
    },
    # ------------------------------------------------------------------
    # Examen extra 23/24
    # NOTA: PTE=5484 tiene bit I=1 (page fault).
    #   Los apuntes dicen I=0; la verificacion muestra I=1.
    #   Celda 25 aparece en Q11 y HQ (posible error de datos).
    # ------------------------------------------------------------------
    {
        "id": "exam2324",
        "title": "Examen extra 23/24 -- dV=04560A, PTE=5484",
        "description": (
            "Disco 3330, RSIZE=100K.\n"
            "AVISO: Los apuntes indican I=0, pero PTE=5484 tiene bit I=1\n"
            "(page fault). dV alternativa: 045613.\n"
            "Celda 25 aparece en Q11 y HQ (posible error de datos).\n"
            "Datos del examen pueden no ser exactos."
        ),
        "partial": False,
        "params": {
            "dv_hex": "04560A",
            "pte_hex": "5484",
            "rsize_kb": 100,
            "disk_model": "3330",
            "queues": {
                "Q00": [(16, 1, 1), (24, 1, 1), (15, 1, 1)],
                "Q01": [(29, 1, 1), (30, 1, 1)],
                "Q10": [(22, 1, 1)],
                "Q11": [(25, 1, 1)],
                "HQ":  [(32, 1, 0), (36, 1, 1), (28, 1, 0), (25, 1, 0)],
            },
            "pfte_bytes_45_hex": None,
        },
    },
    # ------------------------------------------------------------------
    # Ejercicio extra (apuntes)
    # NOTA: Celda 32 aparece en Q10 y HQ (posible error de datos).
    # ------------------------------------------------------------------
    {
        "id": "extra1",
        "title": "Ejercicio extra (apuntes) -- dV=00A845, PTE=2565",
        "description": (
            "Disco 3350, RSIZE=100K. PTE con I=1, page fault.\n"
            "PFTE octetos 4-5 = 1542.\n"
            "AVISO: Celda 32 aparece en Q10 y HQ (posible error de datos)."
        ),
        "partial": False,
        "params": {
            "dv_hex": "00A845",
            "pte_hex": "2565",
            "rsize_kb": 100,
            "disk_model": "3350",
            "queues": {
                "Q00": [(13, 1, 1), (24, 1, 1), (15, 1, 1)],
                "Q01": [(29, 1, 1), (30, 1, 1)],
                "Q10": [(32, 1, 1)],
                "Q11": [(25, 0, 1)],
                "HQ":  [(32, 1, 0), (36, 1, 1), (28, 1, 0)],
            },
            "pfte_bytes_45_hex": "1542",
        },
    },
]


# ---------------------------------------------------------------------------
# Funciones de acceso a los ejercicios
# ---------------------------------------------------------------------------
# Estas funciones abstraen el acceso a la lista EXERCISES para que main.py
# no dependa directamente de la estructura interna.

def get_exercise_list() -> list[dict]:
    """Devuelve lista resumida (id + title) para mostrar en el menu de seleccion."""
    return [{"id": ex["id"], "title": ex["title"]} for ex in EXERCISES]


def get_exercise_by_id(exercise_id: str) -> dict | None:
    """Busca un ejercicio por su id. Devuelve el dict completo o None."""
    for ex in EXERCISES:
        if ex["id"] == exercise_id:
            return ex
    return None
