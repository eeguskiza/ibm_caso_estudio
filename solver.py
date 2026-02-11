"""solver.py - Logica de calculo pura para el sistema IBM System/370 (caso de estudio).

Este modulo contiene TODAS las funciones de calculo del sistema, sin ningun
print ni efecto visual. Cada funcion recibe datos de entrada y devuelve un
diccionario con todos los resultados intermedios para que display.py y
report.py puedan mostrarlos.

Arquitectura del sistema IBM System/370 (caso de estudio):
---------------------------------------------------------
  Direccion virtual: 24 bits = S(8 bits) | P(5 bits) | d(11 bits)
    - S = numero de segmento (256 segmentos posibles)
    - P = numero de pagina dentro del segmento (32 paginas por segmento)
    - d = desplazamiento dentro de la pagina (0 a 2047)

  Tamano de pagina: 2 KB (2048 bytes)
  Paginas por segmento: 32 (2^5)

  Traduccion: DAT (Dynamic Address Translation)
    - Se consulta la PTE (Page Table Entry) de la tabla de paginas
    - Si la pagina esta en memoria real (I=0), se obtiene la celda directamente
    - Si no esta (I=1), se produce un page fault y hay que cargarla

  PTE (16 bits): [13 bits datos | bit I | 2 bits]
    - bit I esta en la posicion 2 contando desde la derecha (bit 2)
    - I=0: los 13 bits superiores = numero de celda en memoria real
    - I=1: page fault, la pagina no esta cargada en memoria

  Reemplazamiento: LRU de 2a oportunidad
    - 5 colas ordenadas por frecuencia de uso: Q00, Q01, Q10, Q11, HQ
    - Cada entrada tiene: (celda, bit R, bit C)
      - R = referenciada, C = modificada (changed/dirty)
    - Se busca victima en Q00; si R=1 se da 2a oportunidad (R=0, al final)
    - Si Q00 queda vacia, las colas bajan un nivel

  Disco DASD: modelos 3330, 3340, 3350
    - EPA (External Page Address) = (cilindro, pista, registro)
    - Se calcula a partir del numero absoluto de pagina
"""

from __future__ import annotations

import copy
from typing import Optional

# ---------------------------------------------------------------------------
# Constantes del sistema
# ---------------------------------------------------------------------------

PAGE_SIZE = 2048          # Tamano de pagina: 2 KB (2048 bytes)
PAGES_PER_SEGMENT = 32    # Paginas por segmento: 2^5 = 32

# Modelos de disco DASD con sus geometrias (pistas por cilindro, slots por pista)
# Los slots por cilindro se calculan como: tracks_per_cyl * slots_per_track
DISK_MODELS: dict[str, dict[str, int]] = {
    "3330": {"tracks_per_cyl": 19, "slots_per_track": 6},   # 19*6 = 114 slots/cil
    "3340": {"tracks_per_cyl": 12, "slots_per_track": 3},   # 12*3 =  36 slots/cil
    "3350": {"tracks_per_cyl": 30, "slots_per_track": 8},   # 30*8 = 240 slots/cil
}

# Orden de las colas LRU de mayor a menor prioridad para buscar victima
QUEUE_ORDER = ["Q00", "Q01", "Q10", "Q11", "HQ"]


# ---------------------------------------------------------------------------
# 1. Descomposicion de direccion virtual
# ---------------------------------------------------------------------------

def decompose_virtual_address(dv_hex: str) -> dict:
    """Descompone una direccion virtual de 24 bits en S(8), P(5), d(11).

    Recibe la dV como string hexadecimal de 6 digitos (ej: "03FFA3").
    Devuelve dict con todos los campos descompuestos en decimal, hex y binario.
    """
    value = int(dv_hex, 16)
    dv_bin = format(value, "024b")   # 24 bits en binario

    # Extraer cada campo usando mascaras de bits:
    # - S ocupa los bits 23..16 (8 bits mas significativos)
    # - P ocupa los bits 15..11 (siguientes 5 bits)
    # - d ocupa los bits 10..0  (11 bits menos significativos)
    s = (value >> 16) & 0xFF    # segmento: desplazar 16 y enmascarar 8 bits
    p = (value >> 11) & 0x1F    # pagina: desplazar 11 y enmascarar 5 bits
    d = value & 0x7FF           # desplazamiento: enmascarar 11 bits

    # Numero absoluto de pagina = segmento * 32 + pagina
    # Identifica unicamente la pagina en todo el espacio virtual
    num_abs_page = s * PAGES_PER_SEGMENT + p

    return {
        "dv_hex": f"{value:06X}",
        "dv_bin": dv_bin,
        "S_dec": s,
        "S_hex": f"{s:02X}",
        "P_dec": p,
        "P_hex": f"{p:02X}",
        "d_dec": d,
        "d_hex": f"{d:03X}",
        "d_bin": format(d, "011b"),
        "num_abs_page": num_abs_page,
        "num_abs_page_hex": f"{num_abs_page:04X}",
    }


# ---------------------------------------------------------------------------
# 2. Numero de celdas
# ---------------------------------------------------------------------------

def calculate_num_cells(rsize_kb: int) -> int:
    """N de celdas de memoria real (1 celda = 1 pagina = 2 KB)."""
    return rsize_kb // 2


# ---------------------------------------------------------------------------
# 3. Analisis de PTE
# ---------------------------------------------------------------------------

def analyze_pte(pte_hex: str) -> dict:
    """Analiza una PTE de 16 bits: extrae bit I y, si valida, el n de celda.

    Formato PTE (16 bits, de MSB a LSB):
        [13 bits datos][bit I][2 bits]

    El bit I (invalidacion) esta en la posicion 2 contando desde 0 por
    la derecha. Es el indicador clave:
      - I=0: la pagina esta en memoria real -> los 13 bits superiores
             indican el numero de celda donde esta cargada
      - I=1: page fault -> la pagina NO esta en memoria y hay que cargarla

    Recibe la PTE como string hexadecimal de 4 digitos (ej: "05E8").
    """
    value = int(pte_hex, 16)
    pte_bin = format(value, "016b")   # 16 bits en binario

    # Extraer bit I: desplazar 2 posiciones a la derecha y enmascarar 1 bit
    # Ejemplo: PTE=05E8 = 0000 0101 1110 1000b -> bit en posicion 2 = 0 (I=0)
    bit_i = (value >> 2) & 1
    is_page_fault = bit_i == 1

    result: dict = {
        "pte_hex": f"{value:04X}",
        "pte_bin": pte_bin,
        "bit_I": bit_i,
        "is_page_fault": is_page_fault,
    }

    if not is_page_fault:
        # Si I=0, los 13 bits superiores son el numero de celda
        # Se obtienen desplazando 3 posiciones (bit I + 2 bits inferiores)
        cell_number = value >> 3
        # DC (direccion de comienzo) = celda * tamano_pagina
        dc = cell_number * PAGE_SIZE
        result["cell_number"] = cell_number
        result["dc_hex"] = f"{dc:06X}"

    return result


# ---------------------------------------------------------------------------
# 4. Calculo de direccion real
# ---------------------------------------------------------------------------

def calculate_real_address(cell_number: int, d_bin: str) -> dict:
    """Calcula la direccion real: DR = DC + d.

    La direccion real se compone de:
      DC = celda * 2048 (inicio del marco de pagina en memoria real)
      d  = desplazamiento dentro de la pagina (los 11 bits del offset)
      DR = DC + d (direccion fisica final)
    """
    dc = cell_number * PAGE_SIZE   # direccion de comienzo del marco
    d = int(d_bin, 2)              # desplazamiento en decimal
    dr = dc + d                    # direccion real final

    return {
        "dc_dec": dc,
        "dc_hex": f"{dc:06X}",
        "dr_dec": dr,
        "dr_hex": f"{dr:06X}",
        "dr_bin": format(dr, "024b"),
    }


# ---------------------------------------------------------------------------
# 5. LRU de 2a oportunidad
# ---------------------------------------------------------------------------

def run_lru_second_chance(queues: dict) -> dict:
    """Ejecuta el algoritmo LRU de 2a oportunidad sobre las colas.

    Cada entrada en las colas es una tupla (cell_number, R_bit, C_bit):
      - R_bit (Referenced): 1 si la pagina fue referenciada recientemente
      - C_bit (Changed/Dirty): 1 si la pagina fue modificada

    Algoritmo paso a paso:
    1. Mirar la cabeza de Q00.
    2. Si R=0 -> es la victima, se extrae de la cola.
    3. Si R=1 -> se le da una "segunda oportunidad": poner R=0 y mover
       al final de Q00. Continuar con la siguiente entrada.
    4. Si Q00 queda vacia sin haber encontrado victima -> rotacion:
       Q01 pasa a ser Q00, Q10->Q01, Q11->Q10, HQ->Q11.
       Se repite desde el paso 1 con la nueva Q00.

    El bit C de la victima determina si hace falta page-out:
      - C=0: la pagina no fue modificada, no hay que escribirla a disco
      - C=1: la pagina fue modificada, hay que hacer page-out antes de reusarla
    """
    queues_before = copy.deepcopy(queues)
    q: dict[str, list] = copy.deepcopy(queues)

    for name in QUEUE_ORDER:
        q.setdefault(name, [])

    steps: list[dict] = []
    max_iterations = 1000

    for _ in range(max_iterations):
        # Si Q00 esta vacia, intentar bajar colas
        if not q["Q00"]:
            if not any(q[k] for k in QUEUE_ORDER[1:]):
                raise RuntimeError("LRU: todas las colas estan vacias, no hay victima posible")
            steps.append({
                "action": "rotate_queues",
                "detail": "Q00 vacia -> Q01->Q00, Q10->Q01, Q11->Q10, HQ->Q11",
            })
            q["Q00"] = q["Q01"]
            q["Q01"] = q["Q10"]
            q["Q10"] = q["Q11"]
            q["Q11"] = q["HQ"]
            q["HQ"] = []
            continue

        # Examinar la cabeza de Q00
        cell, r, c = q["Q00"][0]

        if r == 0:
            # Victima encontrada
            q["Q00"].pop(0)
            steps.append({
                "action": "victim_found",
                "cell": cell,
                "R": r,
                "C": c,
                "detail": f"Celda {cell} con R=0 -> VICTIMA",
            })
            return {
                "victim_cell": cell,
                "victim_R": r,
                "victim_C": c,
                "needs_pageout": c == 1,
                "steps": steps,
                "queues_before": queues_before,
                "queues_after": q,
            }
        else:
            # Segunda oportunidad: R=1 -> R=0, mover al final de Q00
            q["Q00"].pop(0)
            q["Q00"].append((cell, 0, c))
            steps.append({
                "action": "second_chance",
                "cell": cell,
                "R_before": 1,
                "R_after": 0,
                "detail": f"Celda {cell} con R=1 -> R=0, mover al final de Q00",
            })

    raise RuntimeError("LRU: limite de iteraciones alcanzado sin encontrar victima")


# ---------------------------------------------------------------------------
# 6. Identificar pagina desalojada
# ---------------------------------------------------------------------------

def identify_evicted_page(pfte_bytes_45_hex: str) -> dict:
    """Identifica la pagina desalojada a partir de los octetos 4-5 de la PFTE.

    La PFTE (Page Frame Table Entry) contiene informacion sobre la pagina
    que actualmente ocupa una celda. Los octetos 4-5 guardan el numero
    absoluto de la pagina cargada en esa celda. A partir de ese numero
    se calcula a que segmento y pagina pertenece la pagina desalojada.
    """
    num_abs = int(pfte_bytes_45_hex, 16)
    segment = num_abs // PAGES_PER_SEGMENT
    page = num_abs % PAGES_PER_SEGMENT

    return {
        "pfte_hex": pfte_bytes_45_hex.upper(),
        "num_abs_page": num_abs,
        "segment": segment,
        "page": page,
    }


# ---------------------------------------------------------------------------
# 7. Calculo de EPA
# ---------------------------------------------------------------------------

def calculate_epa(num_abs_page: int, tracks_per_cyl: int, slots_per_track: int) -> dict:
    """Calcula la EPA (External Page Address) en disco DASD.

    Cada pagina en disco se localiza por su EPA = (cilindro, pista, registro).
    El calculo se basa en la geometria del disco:
      - slots_per_cyl = pistas_por_cilindro * slots_por_pista
      - cilindro = N.Abs_pagina // slots_por_cilindro
      - resto    = N.Abs_pagina %  slots_por_cilindro
      - pista    = resto // slots_por_pista
      - registro = resto %  slots_por_pista
    """
    slots_per_cyl = tracks_per_cyl * slots_per_track  # total de paginas por cilindro
    cylinder = num_abs_page // slots_per_cyl           # en que cilindro esta
    remainder = num_abs_page % slots_per_cyl           # posicion dentro del cilindro
    track = remainder // slots_per_track               # en que pista del cilindro
    slot = remainder % slots_per_track                 # en que registro de la pista

    return {
        "cylinder": cylinder,
        "track": track,
        "slot": slot,
        "slots_per_cyl": slots_per_cyl,
        "slots_per_track": slots_per_track,
    }


# ---------------------------------------------------------------------------
# 8. Calculo de DC
# ---------------------------------------------------------------------------

def calculate_dc(cell_number: int) -> dict:
    """Calcula la direccion de comienzo (DC) de una celda."""
    dc = cell_number * PAGE_SIZE

    return {
        "dc_dec": dc,
        "dc_hex": f"{dc:06X}",
        "dc_bin": format(dc, "024b"),
    }


# ---------------------------------------------------------------------------
# 9. Construir nueva PTE
# ---------------------------------------------------------------------------

def build_new_pte(cell_number: int) -> dict:
    """Construye las PTE valida (I=0) e invalida (I=1) para un numero de celda.

    Tras un page fault, se actualizan dos PTEs:
      - BI(0) para la pagina entrante: I=0 (valida, ya esta en memoria)
      - BI(1) para la pagina desalojada: I=1 (invalida, ya no esta en memoria)

    Formato: [13 bits = cell_number | bit I | 00]
      - Los 13 bits superiores contienen el numero de celda
      - bit I indica si la pagina es valida (0) o invalida (1)
      - Los 2 bits inferiores siempre son 00
    """
    upper_13 = cell_number & 0x1FFF   # asegurar que cabe en 13 bits
    bi_0 = (upper_13 << 3) | 0b000   # I=0: pagina valida (entrante)
    bi_1 = (upper_13 << 3) | 0b100   # I=1: pagina invalida (desalojada)

    return {
        "cell_number": cell_number,
        "bi_0_hex": f"{bi_0:04X}",
        "bi_0_bin": format(bi_0, "016b"),
        "bi_1_hex": f"{bi_1:04X}",
        "bi_1_bin": format(bi_1, "016b"),
    }


# ---------------------------------------------------------------------------
# 10. Ejercicio completo
# ---------------------------------------------------------------------------

def solve_full_exercise(
    dv_hex: str,
    pte_hex: str,
    rsize_kb: int,
    disk_model: str,
    queues: Optional[dict] = None,
    pfte_bytes_45_hex: Optional[str] = None,
) -> dict:
    """Orquesta el flujo completo de traduccion de direccion virtual.

    Esta es la funcion principal que encadena todos los pasos de resolucion.
    Recibe los datos del problema y devuelve un dict con TODOS los resultados
    intermedios, listos para que display.py los muestre y report.py genere
    el informe HTML.

    Flujo sin page fault (pagina ya en memoria):
        1. Descomponer dV -> S, P, d
        2. Analizar PTE -> I=0, obtener celda
        3. Calcular DR = DC + d -> FIN

    Flujo con page fault (pagina NO en memoria):
        1. Descomponer dV -> S, P, d
        2. Analizar PTE -> I=1 (page fault)
        3. LRU 2a oportunidad -> encontrar celda victima
        4. Identificar pagina desalojada (PFTE)
        5. Si C=1: PAGE-OUT (escribir pagina modificada a disco, EPA + DC)
        6. PAGE-IN (leer pagina solicitada desde disco, EPA + DC)
        7. Actualizar PTEs: BI(0) para entrante, BI(1) para desalojada
        8. Calcular DR = DC + d -> FIN

    Parametros:
        dv_hex:   direccion virtual, 6 digitos hex (ej: "03FFA3")
        pte_hex:  contenido de la PTE, 4 digitos hex (ej: "05E8")
        rsize_kb: memoria real instalada en KB (ej: 100)
        disk_model: modelo de disco ("3330", "3340" o "3350")
        queues:   colas LRU (solo si hay page fault)
        pfte_bytes_45_hex: octetos 4-5 de la PFTE de la celda victima
    """
    result: dict = {}
    disk = DISK_MODELS[disk_model]

    # --- Paso 1: descomponer la direccion virtual en S, P, d ---
    addr = decompose_virtual_address(dv_hex)
    result["address"] = addr

    # --- Paso 2: calcular numero de celdas de memoria real ---
    result["num_cells"] = calculate_num_cells(rsize_kb)

    # --- Paso 3: analizar la PTE para ver si hay page fault ---
    pte = analyze_pte(pte_hex)
    result["pte"] = pte
    result["disk_model"] = disk_model

    if not pte["is_page_fault"]:
        # ---- CAMINO SIN PAGE FAULT ----
        # La pagina ya esta en memoria real, traduccion directa
        result["page_fault"] = False
        dr = calculate_real_address(pte["cell_number"], addr["d_bin"])
        result["real_address"] = dr
    else:
        # ---- CAMINO CON PAGE FAULT ----
        # La pagina no esta en memoria, hay que cargarla
        result["page_fault"] = True

        if queues is None:
            raise ValueError("Page fault detectado pero no se proporcionaron colas LRU")

        # --- Paso 4: ejecutar LRU para encontrar la celda victima ---
        lru = run_lru_second_chance(queues)
        result["lru"] = lru

        # --- Paso 5: identificar que pagina ocupa actualmente la celda victima ---
        if pfte_bytes_45_hex is not None:
            evicted = identify_evicted_page(pfte_bytes_45_hex)
            result["evicted_page"] = evicted

            # --- Paso 6a: PAGE-OUT si la pagina victima fue modificada (C=1) ---
            # Hay que escribir la pagina modificada a disco antes de reemplazarla
            if lru["needs_pageout"]:
                epa_out = calculate_epa(
                    evicted["num_abs_page"],
                    disk["tracks_per_cyl"],
                    disk["slots_per_track"],
                )
                dc_out = calculate_dc(lru["victim_cell"])
                result["page_out"] = {"epa": epa_out, "dc": dc_out}

        # --- Paso 6b: PAGE-IN (traer la pagina solicitada desde disco) ---
        # Se lee la pagina del disco y se carga en la celda que acaba de quedar libre
        epa_in = calculate_epa(
            addr["num_abs_page"],
            disk["tracks_per_cyl"],
            disk["slots_per_track"],
        )
        dc_in = calculate_dc(lru["victim_cell"])
        result["page_in"] = {"epa": epa_in, "dc": dc_in}

        # --- Paso 7: construir las nuevas PTEs ---
        # BI(0) para la pagina entrante (valida, I=0)
        # BI(1) para la pagina desalojada (invalida, I=1)
        new_pte = build_new_pte(lru["victim_cell"])
        result["new_pte"] = new_pte

        # --- Paso 8: calcular la direccion real final ---
        # Ahora la pagina solicitada esta en la celda victima
        dr = calculate_real_address(lru["victim_cell"], addr["d_bin"])
        result["real_address"] = dr

    return result
