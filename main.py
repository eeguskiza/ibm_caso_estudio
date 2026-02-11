"""main.py - Punto de entrada del sistema IBM System/370 (caso de estudio).

Este es el archivo principal que arranca el programa. Ofrece 3 modos:
  1. Ejercicios precargados: seleccionar uno de exercises.py y resolverlo
  2. Modo interactivo: el usuario introduce sus propios datos paso a paso
  3. Calculadora rapida: operaciones individuales (descomponer dV, etc.)

Ejecutar:  python main.py
"""

from __future__ import annotations

import os
import sys

import solver
import display
from exercises import get_exercise_list, get_exercise_by_id, EXERCISES

# Importar report.py de forma segura: si el modulo no existe o no tiene
# la funcion generate_report(), simplemente se desactiva la opcion de informe
try:
    import report as _report_mod
    _has_report = hasattr(_report_mod, "generate_report")
except ImportError:
    _has_report = False


# ---------------------------------------------------------------------------
# Utilidades de entrada del usuario
# ---------------------------------------------------------------------------
# Todas las funciones input_* validan la entrada y repiten la pregunta
# hasta obtener un valor correcto. Esto evita que el programa crashee
# con datos invalidos.

def clear_screen() -> None:
    """Limpia la pantalla de la terminal (compatible Windows y Linux)."""
    os.system("cls" if os.name == "nt" else "clear")


def pause() -> None:
    """Pausa el programa esperando que el usuario pulse ENTER."""
    input("\n  Pulsa ENTER para continuar...")


def input_hex(prompt: str, length: int) -> str:
    """Pide un valor hexadecimal de longitud fija. Repite hasta obtener uno valido."""
    while True:
        raw = input(prompt).strip().upper()
        if len(raw) == length and all(c in "0123456789ABCDEF" for c in raw):
            return raw
        print(f"  Error: introduce exactamente {length} digitos hexadecimales.")


def input_int(prompt: str, positive: bool = True) -> int:
    """Pide un entero. Repite hasta obtener uno valido."""
    while True:
        raw = input(prompt).strip()
        try:
            val = int(raw)
        except ValueError:
            print("  Error: introduce un numero entero valido.")
            continue
        if positive and val <= 0:
            print("  Error: el valor debe ser positivo.")
            continue
        return val


def input_choice(prompt: str, valid: set[str]) -> str:
    """Pide una opcion de un conjunto. Repite hasta obtener una valida."""
    while True:
        raw = input(prompt).strip()
        if raw in valid:
            return raw
        print(f"  Opcion no valida. Opciones: {', '.join(sorted(valid))}")


def ask_yes_no(prompt: str) -> bool:
    """Pregunta s/n."""
    while True:
        raw = input(prompt).strip().lower()
        if raw in ("s", "si", "y", "yes"):
            return True
        if raw in ("n", "no"):
            return False
        print("  Introduce s o n.")


# ---------------------------------------------------------------------------
# Input de colas LRU
# ---------------------------------------------------------------------------
# Las colas se introducen una a una. Cada entrada tiene 3 valores:
# celda, R (referenciada) y C (modificada). Linea vacia termina la cola.

def input_queue(name: str) -> list[tuple[int, int, int]]:
    """Pide las entradas de una cola LRU interactivamente."""
    print(f"\n  Cola {name}  (formato: celda R C  |  linea vacia para terminar)")
    print(f"  Ejemplo: 17 1 0  ->  celda 17, R=1, C=0")
    entries: list[tuple[int, int, int]] = []
    while True:
        raw = input(f"    {name}> ").strip()
        if not raw:
            break
        parts = raw.split()
        if len(parts) != 3:
            print("    Error: introduce 3 valores separados por espacio (celda R C).")
            continue
        try:
            cell, r, c = int(parts[0]), int(parts[1]), int(parts[2])
        except ValueError:
            print("    Error: los tres valores deben ser enteros.")
            continue
        if r not in (0, 1) or c not in (0, 1):
            print("    Error: R y C deben ser 0 o 1.")
            continue
        entries.append((cell, r, c))
    return entries


def input_all_queues() -> dict[str, list]:
    """Pide las 5 colas LRU interactivamente."""
    print("\n  Introduce el contenido de las colas LRU.")
    print("  Para cada cola, introduce las celdas de cabeza a cola.")
    queues = {}
    for name in solver.QUEUE_ORDER:
        queues[name] = input_queue(name)
    return queues


# ---------------------------------------------------------------------------
# Input de modelo de disco
# ---------------------------------------------------------------------------

def input_disk_model() -> str:
    """Pide el modelo de disco. Devuelve la clave para DISK_MODELS."""
    print("\n  Modelo de disco:")
    print("    1. 3330  (19 pistas/cil, 6 slots/pista)")
    print("    2. 3340  (12 pistas/cil, 3 slots/pista)")
    print("    3. 3350  (30 pistas/cil, 8 slots/pista)")
    print("    4. Otro  (introducir manualmente)")
    choice = input_choice("  Elige [1-4]: ", {"1", "2", "3", "4"})
    mapping = {"1": "3330", "2": "3340", "3": "3350"}
    if choice in mapping:
        return mapping[choice]
    # Manual
    tpc = input_int("  Pistas por cilindro: ")
    spt = input_int("  Slots por pista: ")
    model_name = f"custom_{tpc}x{spt}"
    solver.DISK_MODELS[model_name] = {"tracks_per_cyl": tpc, "slots_per_track": spt}
    return model_name


# ---------------------------------------------------------------------------
# Generar informe HTML (si report.py esta implementado)
# ---------------------------------------------------------------------------

def _open_in_browser(filepath: str) -> None:
    """Abre un archivo en el navegador, compatible con WSL y Linux nativo."""
    import subprocess
    abs_path = os.path.abspath(filepath)

    # Detectar si estamos en WSL (Windows Subsystem for Linux)
    is_wsl = "WSL_DISTRO_NAME" in os.environ
    if not is_wsl:
        try:
            with open("/proc/version") as f:
                is_wsl = "microsoft" in f.read().lower()
        except OSError:
            pass

    if is_wsl:
        # En WSL: convertir ruta Linux a ruta Windows y abrir con explorer.exe
        try:
            win_path = subprocess.check_output(
                ["wslpath", "-w", abs_path],
                stderr=subprocess.DEVNULL,
            ).decode().strip()
            subprocess.Popen(
                ["cmd.exe", "/c", "start", "", win_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return
        except (FileNotFoundError, subprocess.SubprocessError):
            pass

    # Linux nativo o fallback: usar webbrowser estandar
    import webbrowser
    webbrowser.open(f"file://{abs_path}")


def offer_report(result: dict) -> None:
    """Pregunta si generar informe HTML; lo abre en el navegador."""
    if not _has_report:
        return
    if ask_yes_no("  Generar informe HTML? (s/n): "):
        try:
            path = _report_mod.generate_report(result)
            print(f"  Informe generado: {path}")
            _open_in_browser(path)
        except Exception as e:
            print(f"  Error al generar informe: {e}")


# ---------------------------------------------------------------------------
# OPCION 1: Ejercicios precargados
# ---------------------------------------------------------------------------

def run_preloaded() -> None:
    clear_screen()
    print("\n  EJERCICIOS PRECARGADOS\n")

    exercises = get_exercise_list()
    for i, ex in enumerate(exercises, 1):
        print(f"    {i:>2}. [{ex['id']:>10}]  {ex['title']}")
    print(f"     0. Volver")

    valid = {str(i) for i in range(len(exercises) + 1)}
    choice = input_choice("\n  Elige ejercicio: ", valid)
    if choice == "0":
        return

    idx = int(choice) - 1
    ex = EXERCISES[idx]

    print(f"\n  {ex['title']}")
    if ex.get("description"):
        for line in ex["description"].split("\n"):
            print(f"  {line}")

    if ex.get("partial"):
        _run_partial_exercise(ex)
    else:
        _run_full_exercise(ex)


def _run_partial_exercise(ex: dict) -> None:
    """Ejecuta un ejercicio parcial (solo page-out: EPA + DC)."""
    p = ex["params"]
    disk = solver.DISK_MODELS[p["disk_model"]]

    epa = solver.calculate_epa(
        p["num_abs_page"],
        disk["tracks_per_cyl"],
        disk["slots_per_track"],
    )
    dc = solver.calculate_dc(p["cell_number"])

    result_block = {"epa": epa, "dc": dc}
    display.print_pageout(result_block, p["disk_model"])
    pause()


def _run_full_exercise(ex: dict) -> None:
    """Ejecuta un ejercicio completo con solve_full_exercise."""
    try:
        result = solver.solve_full_exercise(**ex["params"])
        display.print_full_exercise(result)
        offer_report(result)
    except Exception as e:
        print(f"\n  ERROR al resolver el ejercicio: {e}")
    pause()


# ---------------------------------------------------------------------------
# OPCION 2: Modo interactivo
# ---------------------------------------------------------------------------

def run_interactive() -> None:
    clear_screen()
    print("\n  MODO INTERACTIVO — introduce tus datos paso a paso\n")

    # a) Modelo de disco
    disk_model = input_disk_model()
    disk = solver.DISK_MODELS[disk_model]

    # b) RSIZE
    rsize_kb = input_int("\n  Memoria real instalada (RSIZE) en KB: ")
    num_cells = solver.calculate_num_cells(rsize_kb)
    print(f"  -> N.Celdas = {rsize_kb} / 2 = {num_cells}")

    # c) Direccion virtual
    dv_hex = input_hex("\n  Direccion virtual (6 digitos hex): ", 6)
    addr = solver.decompose_virtual_address(dv_hex)
    display.print_decomposition(addr, rsize_kb=rsize_kb, num_cells=num_cells)

    # d) PTE
    pte_hex = input_hex("  Contenido de la PTE (4 digitos hex): ", 4)
    pte = solver.analyze_pte(pte_hex)
    display.print_pte_analysis(pte)

    if not pte["is_page_fault"]:
        # Sin page fault -> DR directa
        dr = solver.calculate_real_address(pte["cell_number"], addr["d_bin"])
        display.print_real_address(dr)
        display.print_final_result(dr["dr_hex"])

        result = {
            "address": addr, "num_cells": num_cells, "pte": pte,
            "page_fault": False, "real_address": dr, "disk_model": disk_model,
        }
        offer_report(result)
        pause()
        return

    # --- Page fault ---
    print("  Se necesita resolver el page fault.\n")

    # e) Colas LRU
    queues = input_all_queues()
    lru = solver.run_lru_second_chance(queues)
    display.print_lru_algorithm(lru)

    # f) PFTE
    pfte_hex = input_hex(
        f"\n  Octetos 4-5 de la PFTE de la celda victima {lru['victim_cell']}"
        f" (4 digitos hex): ",
        4,
    )
    evicted = solver.identify_evicted_page(pfte_hex)
    display.print_evicted_page(evicted)

    # Construir resultado completo para display y report
    result: dict = {
        "address": addr, "num_cells": num_cells, "pte": pte,
        "page_fault": True, "disk_model": disk_model, "lru": lru,
        "evicted_page": evicted,
    }

    # g) Page-out si C=1
    if lru["needs_pageout"]:
        epa_out = solver.calculate_epa(
            evicted["num_abs_page"],
            disk["tracks_per_cyl"],
            disk["slots_per_track"],
        )
        dc_out = solver.calculate_dc(lru["victim_cell"])
        result["page_out"] = {"epa": epa_out, "dc": dc_out}
        display.print_pageout(result["page_out"], disk_model)

    # h) Page-in
    epa_in = solver.calculate_epa(
        addr["num_abs_page"],
        disk["tracks_per_cyl"],
        disk["slots_per_track"],
    )
    dc_in = solver.calculate_dc(lru["victim_cell"])
    result["page_in"] = {"epa": epa_in, "dc": dc_in}
    display.print_pagein(result["page_in"], disk_model)

    # i) Actualizacion de tablas
    new_pte = solver.build_new_pte(lru["victim_cell"])
    result["new_pte"] = new_pte
    display.print_table_updates(new_pte)

    # j) DR final
    dr = solver.calculate_real_address(lru["victim_cell"], addr["d_bin"])
    result["real_address"] = dr
    display.print_real_address(dr)
    display.print_final_result(dr["dr_hex"])

    # k) Informe
    offer_report(result)
    pause()


# ---------------------------------------------------------------------------
# OPCION 3: Calculadora rapida
# ---------------------------------------------------------------------------

def run_calculator() -> None:
    while True:
        clear_screen()
        display.print_calculator_menu()
        choice = input_choice("  Elige operacion [0-8]: ",
                              {str(i) for i in range(9)})

        if choice == "0":
            return

        if choice == "1":
            dv = input_hex("\n  Direccion virtual (6 digitos hex): ", 6)
            r = solver.decompose_virtual_address(dv)
            display.print_decomposition(r)

        elif choice == "2":
            pte = input_hex("\n  PTE (4 digitos hex): ", 4)
            r = solver.analyze_pte(pte)
            display.print_pte_analysis(r)

        elif choice == "3":
            cell = input_int("\n  Numero de celda: ", positive=False)
            d_dec = input_int("  Desplazamiento (decimal, 0-2047): ", positive=False)
            if d_dec < 0 or d_dec > 2047:
                print("  Error: desplazamiento fuera de rango (0-2047).")
            else:
                d_bin = format(d_dec, "011b")
                r = solver.calculate_real_address(cell, d_bin)
                display.print_real_address(r)

        elif choice == "4":
            nap = input_int("\n  N.Abs pagina: ", positive=False)
            dm = input_disk_model()
            disk = solver.DISK_MODELS[dm]
            r = solver.calculate_epa(nap, disk["tracks_per_cyl"], disk["slots_per_track"])
            spc = r["slots_per_cyl"]
            spt = r["slots_per_track"]
            remainder = nap % spc
            print(f"\n  Cilindro  = {nap} // {spc} = {r['cylinder']}")
            print(f"  Resto     = {nap} %  {spc} = {remainder}")
            print(f"  Pista     = {remainder} // {spt} = {r['track']}")
            print(f"  Registro  = {remainder} %  {spt} = {r['slot']}")
            print(f"\n  EPA = (cilindro={r['cylinder']}, pista={r['track']},"
                  f" registro={r['slot']})")

        elif choice == "5":
            cell = input_int("\n  Numero de celda: ", positive=False)
            r = solver.calculate_dc(cell)
            print(f"\n  DC = {cell} x 2048 = {r['dc_dec']}")
            print(f"  DC (hex) = 0x{r['dc_hex']}")
            print(f"  DC (bin) = {r['dc_bin']}")

        elif choice == "6":
            cell = input_int("\n  Numero de celda: ", positive=False)
            r = solver.build_new_pte(cell)
            display.print_table_updates(r)

        elif choice == "7":
            pfte = input_hex("\n  PFTE octetos 4-5 (4 digitos hex): ", 4)
            r = solver.identify_evicted_page(pfte)
            display.print_evicted_page(r)

        elif choice == "8":
            rsize = input_int("\n  RSIZE en KB: ")
            n = solver.calculate_num_cells(rsize)
            print(f"\n  N.Celdas = {rsize} / 2 = {n}")

        pause()


# ---------------------------------------------------------------------------
# Bucle principal
# ---------------------------------------------------------------------------

def main() -> None:
    clear_screen()
    display.print_intro()

    while True:
        display.print_main_menu()
        choice = input_choice("  Elige opcion [0-3]: ", {"0", "1", "2", "3"})

        if choice == "0":
            print("\n  Hasta luego.\n")
            break
        elif choice == "1":
            run_preloaded()
        elif choice == "2":
            run_interactive()
        elif choice == "3":
            run_calculator()


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\n\n  Salida limpia (Ctrl+C). Hasta luego.\n")
        sys.exit(0)
