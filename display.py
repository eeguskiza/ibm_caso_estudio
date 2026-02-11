"""display.py - Presentacion por terminal del sistema IBM System/370 (caso de estudio).

Este modulo se encarga de TODA la visualizacion por terminal. Cada funcion
print_* recibe los diccionarios generados por solver.py y los muestra
formateados con cajas Unicode, tablas alineadas y secciones numeradas.

No usa colores ANSI para garantizar compatibilidad con cualquier terminal.
Cada paso del flujo de resolucion tiene su propia funcion de impresion.
"""

from __future__ import annotations

from solver import DISK_MODELS, QUEUE_ORDER

# ---------------------------------------------------------------------------
# Constantes de formato y funciones auxiliares para cajas Unicode
# ---------------------------------------------------------------------------
# Se usan caracteres Unicode de dibujo de cajas (box-drawing) para crear
# marcos visuales en la terminal. El ancho fijo de 72 caracteres se ajusta
# a la mayoria de terminales estandar.

WIDTH = 72


def _box_line(text: str, width: int = WIDTH) -> str:
    """Linea centrada dentro de una caja Unicode (bordes dobles ║)."""
    inner = width - 2
    return f"\u2551{text:^{inner}}\u2551"


def _box_top(width: int = WIDTH) -> str:
    """Borde superior de caja: ╔════════╗"""
    return "\u2554" + "\u2550" * (width - 2) + "\u2557"


def _box_bottom(width: int = WIDTH) -> str:
    """Borde inferior de caja: ╚════════╝"""
    return "\u255A" + "\u2550" * (width - 2) + "\u255D"


def _box_sep(width: int = WIDTH) -> str:
    """Separador horizontal dentro de la caja."""
    return "\u2551" + "\u2500" * (width - 2) + "\u2551"


def _section(title: str, width: int = WIDTH) -> str:
    """Titulo de seccion con lineas decorativas a ambos lados."""
    side = (width - len(title) - 2) // 2
    trail = width - side - len(title) - 2
    return f"\u2500{'─' * side} {title} {'─' * trail}\u2500"


def _result_box(lines: list[str], width: int = WIDTH) -> str:
    """Caja completa para resultados destacados (DR final, victima, etc)."""
    top = _box_top(width)
    bottom = _box_bottom(width)
    inner = width - 2
    body = "\n".join(f"\u2551 {line:<{inner - 1}}\u2551" for line in lines)
    return f"{top}\n{body}\n{bottom}"


# ---------------------------------------------------------------------------
# 1. Intro
# ---------------------------------------------------------------------------

def print_intro() -> None:
    """Muestra la pantalla de bienvenida con la arquitectura del sistema."""
    print()
    print(_box_top())
    print(_box_line(""))
    print(_box_line('SISTEMA IBM "CASO DE ESTUDIO"'))
    print(_box_line("Resolucion de ejercicios de memoria virtual"))
    print(_box_line(""))
    print(_box_sep())
    print(_box_line(""))
    print(_box_line("Arquitectura del sistema:"))
    print(_box_line("Direccion virtual: 24 bits  (8 seg | 5 pag | 11 offset)"))
    print(_box_line("Tamano de pagina:  2 KB  (2048 bytes)"))
    print(_box_line("Traduccion:        DAT (Dynamic Address Translation)"))
    print(_box_line("Reemplazamiento:   LRU de 2a oportunidad (Q00-Q11 + HQ)"))
    print(_box_line("Almacenamiento:    EPS en disco (DASD)"))
    print(_box_line(""))
    print(_box_sep())
    print(_box_line(""))
    print(_box_line("Flujo:"))
    print(_box_line("dV -> descomposicion -> PTE -> [page fault -> LRU"))
    print(_box_line("-> page out/in] -> DR"))
    print(_box_line(""))
    print(_box_bottom())
    print()


# ---------------------------------------------------------------------------
# 2. Menu principal
# ---------------------------------------------------------------------------

def print_main_menu() -> None:
    """Muestra el menu principal."""
    print()
    print(_section("MENU PRINCIPAL"))
    print()
    print("  1. Ejercicios precargados")
    print("  2. Modo interactivo (introduce tus datos)")
    print("  3. Calculadora rapida")
    print("  0. Salir")
    print()


# ---------------------------------------------------------------------------
# 3. Descomposicion de dV
# ---------------------------------------------------------------------------

def print_decomposition(result: dict, rsize_kb: int | None = None, num_cells: int | None = None) -> None:
    """PASO 1: descomposicion de la direccion virtual."""
    a = result  # alias

    dv_bin = a["dv_bin"]
    s_bin = dv_bin[:8]
    p_bin = dv_bin[8:13]
    d_bin = dv_bin[13:]

    print()
    print(_section("PASO 1: DESCOMPOSICION DE LA DIRECCION VIRTUAL"))
    print()
    print(f"  dV (hex):    {a['dv_hex']}")
    print(f"  dV (bin):    {s_bin} | {p_bin} | {d_bin}")
    print(f"               {'S':^8}   {'P':^5}   {'d':^11}")
    print()
    print(f"  S  = {s_bin}b = {a['S_dec']} (0x{a['S_hex']})    segmento")
    print(f"  P  = {p_bin}b = {a['P_dec']} (0x{a['P_hex']})          pagina")
    print(f"  d  = {d_bin}b = {a['d_dec']} (0x{a['d_hex']})       desplazamiento")
    print()
    print(f"  N.Abs pagina = S x 32 + P = {a['S_dec']} x 32 + {a['P_dec']}"
          f" = {a['num_abs_page']} (0x{a['num_abs_page_hex']})")

    if rsize_kb is not None and num_cells is not None:
        print(f"  N.Celdas     = RSIZE / 2K = {rsize_kb} / 2 = {num_cells}")

    print()


# ---------------------------------------------------------------------------
# 4. Analisis de PTE
# ---------------------------------------------------------------------------

def print_pte_analysis(result: dict) -> None:
    """PASO 2: analisis de la PTE."""
    p = result  # alias

    pte_bin = p["pte_bin"]
    # Insertar espacios cada 4 bits para legibilidad
    spaced = " ".join(pte_bin[i:i+4] for i in range(0, 16, 4))

    # Flecha apuntando al bit I (posicion 2 desde la derecha = posicion 13 en el string con espacios)
    # En el string con espacios: "XXXX XXXX XXXX XXXX" (19 chars)
    # bit I es el 4to bit del ultimo grupo (posicion 13 contando desde 0: indice 16)
    # Posiciones en "XXXX XXXX XXXX XXXX":
    #   grupo 4 bits [0-3], espacio [4], grupo [5-8], espacio [9], grupo [10-13], espacio [14], grupo [15-18]
    # bit I en posicion 2 desde la derecha = bit 13 del binario (0-indexed desde la izq)
    # En el string con espacios eso es indice 16
    arrow_pos = 16
    arrow_line = " " * arrow_pos + "\u2191"
    arrow_label = " " * (arrow_pos - 1) + "bit I"

    print()
    print(_section("PASO 2: ANALISIS DE LA PTE"))
    print()
    print(f"  PTE (hex):   {p['pte_hex']}")
    print(f"  PTE (bin):   {spaced}")
    print(f"               {arrow_line}")
    print(f"               {arrow_label}")
    print()
    print(f"  Formato:     [13 bits datos | I | 2 bits]")
    print(f"  Bit I = {p['bit_I']}")
    print()

    if not p["is_page_fault"]:
        print(f"  -> No hay page fault. La pagina esta en memoria.")
        print(f"     N. celda = {p['cell_number']}")
        print(f"     DC       = 0x{p['dc_hex']}")
    else:
        print(f"  -> PAGE FAULT -- La pagina NO esta en memoria real.")

    print()


# ---------------------------------------------------------------------------
# 5. Direccion real
# ---------------------------------------------------------------------------

def print_real_address(result: dict) -> None:
    """Muestra el calculo de la direccion real."""
    r = result  # alias

    print()
    print(_section("DIRECCION REAL"))
    print()
    print(f"  DC = 0x{r['dc_hex']}  ({r['dc_dec']})")
    print(f"  DR = DC + d = {r['dr_dec']}")
    print()

    lines = [
        f"DR = 0x{r['dr_hex']}",
        f"     {r['dr_bin']}b",
    ]
    print(_result_box(lines))
    print()


# ---------------------------------------------------------------------------
# 6. LRU
# ---------------------------------------------------------------------------

def print_queues_table(queues: dict, title: str = "") -> None:
    """Imprime las 5 colas LRU en formato tabla."""
    if title:
        print(f"  {title}:")
    print()
    print(f"  {'Cola':<6} {'Contenido'}")
    print(f"  {'─' * 6} {'─' * 50}")

    for name in QUEUE_ORDER:
        entries = queues.get(name, [])
        if entries:
            items = ", ".join(f"(celda={c}, R={r}, C={cc})" for c, r, cc in entries)
        else:
            items = "(vacia)"
        print(f"  {name:<6} {items}")
    print()


def print_lru_algorithm(result: dict) -> None:
    """PASO 3: algoritmo LRU de 2a oportunidad."""
    lru = result  # alias

    print()
    print(_section("PASO 3: ALGORITMO LRU 2a OPORTUNIDAD"))

    # Colas ANTES
    print_queues_table(lru["queues_before"], "Colas ANTES")

    # Pasos
    print("  Ejecucion del algoritmo:")
    print()
    for i, step in enumerate(lru["steps"], 1):
        print(f"    {i}. {step['detail']}")
    print()

    # Colas DESPUES
    print_queues_table(lru["queues_after"], "Colas DESPUES")

    # Resultado
    v_cell = lru["victim_cell"]
    v_r = lru["victim_R"]
    v_c = lru["victim_C"]
    lines = [
        f"VICTIMA: Celda {v_cell}, R={v_r}, C={v_c}",
    ]
    if lru["needs_pageout"]:
        lines.append("-> Se requiere PAGE-OUT (C=1, pagina modificada)")
    else:
        lines.append("-> NO se requiere page-out (C=0)")
    print(_result_box(lines))
    print()


# ---------------------------------------------------------------------------
# 7. Pagina desalojada
# ---------------------------------------------------------------------------

def print_evicted_page(result: dict) -> None:
    """PASO 4: identificacion de la pagina desalojada."""
    e = result  # alias

    print()
    print(_section("PASO 4: IDENTIFICACION DE PAGINA DESALOJADA"))
    print()
    print(f"  PFTE octetos 4-5 (hex): {e['pfte_hex']}")
    print(f"  N.Abs pagina           = 0x{e['pfte_hex']} = {e['num_abs_page']}")
    print(f"  Segmento desalojado    = {e['num_abs_page']} // 32 = {e['segment']}")
    print(f"  Pagina desalojada      = {e['num_abs_page']} % 32  = {e['page']}")
    print()
    print(f"  -> Se desaloja la pagina {e['page']} del segmento {e['segment']}")
    print()


# ---------------------------------------------------------------------------
# 8. Page-out
# ---------------------------------------------------------------------------

def _print_epa_block(epa: dict, dc: dict, num_abs_page: int, disk_model: str, label: str) -> None:
    """Bloque comun para page-out y page-in."""
    disk = DISK_MODELS[disk_model]
    tpc = disk["tracks_per_cyl"]
    spt = disk["slots_per_track"]
    spc = epa["slots_per_cyl"]

    print()
    print(f"  Disco modelo: {disk_model}  ({tpc} pistas/cil, {spt} slots/pista"
          f" = {spc} slots/cil)")
    print()
    print(f"  N.Abs pagina {label} = {num_abs_page}")
    print()
    print(f"  Cilindro  = {num_abs_page} // {spc} = {epa['cylinder']}")
    remainder = num_abs_page % spc
    print(f"  Resto     = {num_abs_page} %  {spc} = {remainder}")
    print(f"  Pista     = {remainder} // {spt} = {epa['track']}")
    print(f"  Registro  = {remainder} %  {spt} = {epa['slot']}")
    print()

    lines = [
        f"EPA = (cilindro={epa['cylinder']}, pista={epa['track']}, registro={epa['slot']})",
        f"DC  = 0x{dc['dc_hex']}  ({dc['dc_dec']})",
    ]
    print(_result_box(lines))
    print()


def print_pageout(result: dict, disk_model: str) -> None:
    """PASO 5: page-out (escribir pagina modificada a disco)."""
    epa = result["epa"]
    dc = result["dc"]
    # Obtener el num abs de la pagina desalojada (viene del caller)
    # Lo recibimos como parte del epa que ya fue calculado
    # Recalcular: cyl * spc + track * spt + slot
    spc = epa["slots_per_cyl"]
    spt = epa["slots_per_track"]
    num_abs_page = epa["cylinder"] * spc + epa["track"] * spt + epa["slot"]

    print()
    print(_section("PASO 5: PAGE-OUT (escritura a disco)"))
    _print_epa_block(epa, dc, num_abs_page, disk_model, "(desalojada)")


def print_pagein(result: dict, disk_model: str) -> None:
    """PASO 6: page-in (leer pagina solicitada desde disco)."""
    epa = result["epa"]
    dc = result["dc"]
    spc = epa["slots_per_cyl"]
    spt = epa["slots_per_track"]
    num_abs_page = epa["cylinder"] * spc + epa["track"] * spt + epa["slot"]

    print()
    print(_section("PASO 6: PAGE-IN (lectura desde disco)"))
    _print_epa_block(epa, dc, num_abs_page, disk_model, "(solicitada)")


# ---------------------------------------------------------------------------
# 9. Actualizacion de tablas
# ---------------------------------------------------------------------------

def print_table_updates(result: dict) -> None:
    """PASO 7: actualizacion de tablas (PTE nueva)."""
    pte = result  # alias

    print()
    print(_section("PASO 7: ACTUALIZACION DE TABLAS"))
    print()
    print(f"  Celda asignada: {pte['cell_number']}")
    print()
    print(f"  Nueva PTE para pagina entrante (valida):")
    print(f"    BI(0) = 0x{pte['bi_0_hex']}  =  {pte['bi_0_bin']}")
    print()
    print(f"  PTE para pagina desalojada (invalida):")
    print(f"    BI(1) = 0x{pte['bi_1_hex']}  =  {pte['bi_1_bin']}")
    print()


# ---------------------------------------------------------------------------
# 10. Resultado final
# ---------------------------------------------------------------------------

def print_final_result(dr_hex: str) -> None:
    """Caja destacada con la direccion real final."""
    print()
    lines = [
        "",
        "RESULTADO FINAL",
        "",
        f"Direccion Real (DR) = 0x{dr_hex}",
        "",
    ]
    print(_result_box(lines))
    print()


# ---------------------------------------------------------------------------
# 11. (print_queues_table ya definida arriba, seccion 6)
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# 12. Menu calculadora rapida
# ---------------------------------------------------------------------------

def print_calculator_menu() -> None:
    """Menu de la calculadora rapida."""
    print()
    print(_section("CALCULADORA RAPIDA"))
    print()
    print("  1. Descomponer direccion virtual (dV -> S, P, d)")
    print("  2. Analizar PTE (hex -> bit I, celda)")
    print("  3. Calcular direccion real (celda + d -> DR)")
    print("  4. Calcular EPA (N.Abs pagina -> cilindro, pista, slot)")
    print("  5. Calcular DC (celda -> direccion de comienzo)")
    print("  6. Construir PTE (celda -> BI(0), BI(1))")
    print("  7. Identificar pagina desalojada (PFTE -> segmento, pagina)")
    print("  8. Calcular numero de celdas (RSIZE -> N.Celdas)")
    print("  0. Volver al menu principal")
    print()


# ---------------------------------------------------------------------------
# Funcion de conveniencia: imprimir ejercicio completo
# ---------------------------------------------------------------------------

def print_full_exercise(result: dict) -> None:
    """Imprime todos los pasos de un ejercicio resuelto por solve_full_exercise."""
    # Paso 1: descomposicion
    print_decomposition(
        result["address"],
        rsize_kb=result["num_cells"] * 2,
        num_cells=result["num_cells"],
    )

    # Paso 2: PTE
    print_pte_analysis(result["pte"])

    if not result["page_fault"]:
        # Sin page fault -> DR directa
        print_real_address(result["real_address"])
        print_final_result(result["real_address"]["dr_hex"])
        return

    # Page fault -> pasos adicionales
    # Paso 3: LRU
    if "lru" in result:
        print_lru_algorithm(result["lru"])

    # Paso 4: pagina desalojada
    if "evicted_page" in result:
        print_evicted_page(result["evicted_page"])

    # Paso 5: page-out
    if "page_out" in result:
        print_pageout(result["page_out"], result["disk_model"])

    # Paso 6: page-in
    if "page_in" in result:
        print_pagein(result["page_in"], result["disk_model"])

    # Paso 7: actualizacion de tablas
    if "new_pte" in result:
        print_table_updates(result["new_pte"])

    # Resultado final
    if "real_address" in result:
        print_real_address(result["real_address"])
        print_final_result(result["real_address"]["dr_hex"])
