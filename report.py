"""report.py - Generacion de informe HTML para el sistema IBM System/370.

Genera un archivo HTML standalone (CSS inline, sin dependencias externas)
con todos los pasos de resolucion de un ejercicio de memoria virtual.
El HTML incluye estilos responsive, colores para cada campo (S=azul,
P=verde, d=naranja, bit I=rojo/verde) y es apto para imprimir.

La funcion principal es generate_report(results) que recibe el dict
devuelto por solver.solve_full_exercise() y genera el archivo HTML.
"""

from __future__ import annotations

import os
from html import escape

from solver import DISK_MODELS, QUEUE_ORDER

# ---------------------------------------------------------------------------
# CSS del informe (inline, no necesita archivos externos)
# ---------------------------------------------------------------------------
# Diseno moderno con gradientes, esquinas redondeadas y sombras.
# Compatible con modo impresion (@media print).
# Usa fuentes monoespaciadas para valores hexadecimales y binarios.

CSS = """\
*, *::before, *::after { box-sizing: border-box; }
body {
    font-family: "Segoe UI", system-ui, -apple-system, sans-serif;
    background: #f4f6f9; color: #1a1a2e; margin: 0; padding: 20px;
}
.container { max-width: 880px; margin: 0 auto; }
header {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    color: #fff; padding: 28px 32px; border-radius: 10px;
    margin-bottom: 24px;
}
header h1 { margin: 0 0 6px 0; font-size: 1.5rem; letter-spacing: 0.5px; }
header .meta { font-size: 0.85rem; opacity: 0.85; line-height: 1.6; }
header .meta span { display: inline-block; margin-right: 18px; }
.section {
    background: #fff; border-radius: 10px; padding: 24px 28px;
    margin-bottom: 20px; box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
.section h2 {
    font-size: 1.1rem; color: #16213e; margin: 0 0 16px 0;
    padding-bottom: 8px; border-bottom: 2px solid #e8ecf1;
}
.mono { font-family: "Cascadia Code", "Fira Code", "Consolas", monospace; }
.bin-display {
    font-family: "Cascadia Code", "Fira Code", "Consolas", monospace;
    font-size: 1.05rem; letter-spacing: 1px; padding: 10px 14px;
    background: #f8f9fb; border-radius: 6px; display: inline-block;
    margin: 6px 0; border: 1px solid #e0e4ea;
}
.seg-color { color: #2563eb; font-weight: 700; }
.pag-color { color: #059669; font-weight: 700; }
.off-color { color: #d97706; font-weight: 700; }
.bit-i-0 { color: #059669; font-weight: 700; background: #d1fae5; padding: 0 3px; border-radius: 3px; }
.bit-i-1 { color: #dc2626; font-weight: 700; background: #fee2e2; padding: 0 3px; border-radius: 3px; }
.badge {
    display: inline-block; padding: 4px 14px; border-radius: 20px;
    font-size: 0.8rem; font-weight: 700; letter-spacing: 0.5px;
}
.badge-ok  { background: #d1fae5; color: #065f46; }
.badge-pf  { background: #fee2e2; color: #991b1b; }
table {
    width: 100%; border-collapse: collapse; margin: 10px 0;
    font-size: 0.9rem;
}
th {
    background: #1a1a2e; color: #fff; padding: 8px 12px;
    text-align: left; font-weight: 600; font-size: 0.8rem;
    letter-spacing: 0.3px;
}
td {
    padding: 7px 12px; border-bottom: 1px solid #eaedf2;
}
tr:nth-child(even) td { background: #f8f9fb; }
.val { font-family: "Cascadia Code", "Fira Code", "Consolas", monospace; font-weight: 600; }
.calc {
    font-family: "Cascadia Code", "Fira Code", "Consolas", monospace;
    background: #f8f9fb; padding: 8px 14px; border-radius: 6px;
    margin: 8px 0; border-left: 3px solid #94a3b8; font-size: 0.9rem;
    line-height: 1.7;
}
.result-box {
    background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
    border: 2px solid #059669; border-radius: 10px;
    padding: 20px 28px; text-align: center; margin: 16px 0;
}
.result-box .label { font-size: 0.85rem; color: #065f46; margin-bottom: 4px; }
.result-box .value {
    font-family: "Cascadia Code", "Fira Code", "Consolas", monospace;
    font-size: 1.6rem; font-weight: 700; color: #065f46;
}
.victim-box {
    background: #fee2e2; border: 2px solid #dc2626; border-radius: 10px;
    padding: 14px 20px; margin: 12px 0;
}
.victim-box .label { font-weight: 700; color: #991b1b; }
.step-list { padding-left: 0; list-style: none; counter-reset: step; }
.step-list li {
    counter-increment: step; padding: 6px 0 6px 36px; position: relative;
    border-bottom: 1px solid #f0f2f5; font-size: 0.9rem;
}
.step-list li::before {
    content: counter(step); position: absolute; left: 0; top: 6px;
    width: 24px; height: 24px; border-radius: 50%; background: #e0e4ea;
    color: #1a1a2e; font-size: 0.75rem; font-weight: 700;
    display: flex; align-items: center; justify-content: center;
}
.step-list li.step-victim::before { background: #dc2626; color: #fff; }
.changed { color: #dc2626; font-weight: 700; }
.arrow { color: #94a3b8; margin: 0 6px; }
.epa-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
@media (max-width: 600px) { .epa-grid { grid-template-columns: 1fr; } }
footer {
    text-align: center; padding: 18px; font-size: 0.75rem; color: #94a3b8;
}
@media print {
    body { background: #fff; padding: 0; }
    .section { box-shadow: none; break-inside: avoid; }
    header { background: #1a1a2e !important; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
}
"""

# ---------------------------------------------------------------------------
# Helpers HTML
# ---------------------------------------------------------------------------
# Funciones auxiliares para generar fragmentos de HTML reutilizables:
# escapado de texto, coloreado de bits, tablas, bloques EPA, etc.

def _h(text: str) -> str:
    """Escapa caracteres especiales HTML para evitar inyeccion."""
    return escape(str(text))


def _colored_bin_dv(dv_bin: str) -> str:
    """Colorea los 24 bits: S(8 azul) | P(5 verde) | d(11 naranja)."""
    s = dv_bin[:8]
    p = dv_bin[8:13]
    d = dv_bin[13:]
    return (
        f'<span class="seg-color">{_h(s)}</span>'
        f'<span style="color:#94a3b8"> | </span>'
        f'<span class="pag-color">{_h(p)}</span>'
        f'<span style="color:#94a3b8"> | </span>'
        f'<span class="off-color">{_h(d)}</span>'
    )


def _colored_bin_pte(pte_bin: str, bit_i: int) -> str:
    """PTE 16 bits con bit I resaltado. Bit I esta en posicion 13 (0-indexed desde izq)."""
    before = pte_bin[:13]
    i_bit = pte_bin[13]
    after = pte_bin[14:]
    cls = "bit-i-0" if bit_i == 0 else "bit-i-1"
    spaced_before = " ".join(before[j:j+4] for j in range(0, 12, 4)) + " " + before[12]
    return (
        f'{_h(spaced_before)}'
        f'<span class="{cls}">{_h(i_bit)}</span>'
        f'{_h(after)}'
    )


def _table(headers: list[str], rows: list[list[str]]) -> str:
    """Genera una tabla HTML simple."""
    ths = "".join(f"<th>{_h(h)}</th>" for h in headers)
    trs = ""
    for row in rows:
        tds = "".join(f"<td>{cell}</td>" for cell in row)
        trs += f"<tr>{tds}</tr>\n"
    return f"<table><thead><tr>{ths}</tr></thead><tbody>{trs}</tbody></table>"


def _queues_table(queues: dict, title: str) -> str:
    """Tabla de colas LRU."""
    colors = {
        "Q00": "#dbeafe", "Q01": "#e0e7ff", "Q10": "#ede9fe",
        "Q11": "#fce7f3", "HQ": "#fef3c7",
    }
    rows = []
    for name in QUEUE_ORDER:
        entries = queues.get(name, [])
        bg = colors.get(name, "#fff")
        if entries:
            cells_html = ", ".join(
                f"({c}, R={r}, C={cc})" for c, r, cc in entries
            )
        else:
            cells_html = '<span style="color:#94a3b8">(vacia)</span>'
        rows.append(
            f'<tr><td style="background:{bg};font-weight:700">'
            f'{_h(name)}</td><td>{cells_html}</td></tr>'
        )
    return (
        f'<p style="font-weight:600;margin-bottom:4px">{_h(title)}</p>'
        f'<table><thead><tr><th style="width:70px">Cola</th>'
        f'<th>Contenido (celda, R, C)</th></tr></thead>'
        f'<tbody>{"".join(rows)}</tbody></table>'
    )


def _epa_block(epa: dict, dc: dict, num_abs_page: int,
               disk_model: str, label: str) -> str:
    """Bloque EPA + DC para page-out o page-in."""
    disk = DISK_MODELS.get(disk_model, {})
    tpc = disk.get("tracks_per_cyl", "?")
    spt = disk.get("slots_per_track", "?")
    spc = epa["slots_per_cyl"]
    remainder = num_abs_page % spc

    calc = (
        f"N.Abs pagina {label} = {num_abs_page}<br>"
        f"Cilindro = {num_abs_page} // {spc} = <b>{epa['cylinder']}</b><br>"
        f"Resto&nbsp;&nbsp;&nbsp;&nbsp;= {num_abs_page} % {spc} = {remainder}<br>"
        f"Pista&nbsp;&nbsp;&nbsp;&nbsp;= {remainder} // {spt} = <b>{epa['track']}</b><br>"
        f"Registro&nbsp;= {remainder} % {spt} = <b>{epa['slot']}</b>"
    )

    table = _table(
        ["", "Valor"],
        [
            ["Disco", f'<span class="val">{_h(disk_model)}</span> '
             f'({tpc} pistas/cil, {spt} slots/pista = {spc} slots/cil)'],
            ["Cilindro", f'<span class="val">{epa["cylinder"]}</span>'],
            ["Pista", f'<span class="val">{epa["track"]}</span>'],
            ["Registro", f'<span class="val">{epa["slot"]}</span>'],
            ["DC", f'<span class="val">0x{dc["dc_hex"]}</span> ({dc["dc_dec"]})'],
        ],
    )
    return f'<div class="calc">{calc}</div>{table}'


# ---------------------------------------------------------------------------
# Secciones del informe
# ---------------------------------------------------------------------------
# Cada _section_* genera el HTML de un paso de la resolucion.
# Se ensamblan en generate_report() segun el tipo de ejercicio
# (con o sin page fault, con o sin page-out, etc).

def _section_header(results: dict) -> str:
    addr = results["address"]
    pte = results["pte"]
    dm = results.get("disk_model", "?")
    rsize = results.get("num_cells", 0) * 2

    return (
        '<header><h1>Resolucion &mdash; Sistema IBM Caso de Estudio</h1>'
        '<div class="meta">'
        f'<span>Disco: <b>{_h(dm)}</b></span>'
        f'<span>RSIZE: <b>{rsize} KB</b></span>'
        f'<span>dV: <b class="mono">0x{_h(addr["dv_hex"])}</b></span>'
        f'<span>PTE: <b class="mono">0x{_h(pte["pte_hex"])}</b></span>'
        '</div></header>'
    )


def _section_decomposition(results: dict) -> str:
    addr = results["address"]
    nc = results.get("num_cells", "?")
    rsize = results.get("num_cells", 0) * 2

    colored = _colored_bin_dv(addr["dv_bin"])

    table = _table(
        ["Campo", "Bits", "Binario", "Decimal", "Hex"],
        [
            ["<span class='seg-color'>S (segmento)</span>", "8",
             f'<span class="val">{_h(addr["dv_bin"][:8])}</span>',
             f'<span class="val">{addr["S_dec"]}</span>',
             f'<span class="val">0x{_h(addr["S_hex"])}</span>'],
            ["<span class='pag-color'>P (pagina)</span>", "5",
             f'<span class="val">{_h(addr["dv_bin"][8:13])}</span>',
             f'<span class="val">{addr["P_dec"]}</span>',
             f'<span class="val">0x{_h(addr["P_hex"])}</span>'],
            ["<span class='off-color'>d (offset)</span>", "11",
             f'<span class="val">{_h(addr["d_bin"])}</span>',
             f'<span class="val">{addr["d_dec"]}</span>',
             f'<span class="val">0x{_h(addr["d_hex"])}</span>'],
        ],
    )

    return (
        '<div class="section"><h2>Paso 1: Descomposicion de la Direccion Virtual</h2>'
        f'<p>dV = <span class="mono val">0x{_h(addr["dv_hex"])}</span></p>'
        f'<div class="bin-display">{colored}</div>'
        f'{table}'
        f'<div class="calc">'
        f'N.Abs pagina = S &times; 32 + P = {addr["S_dec"]} &times; 32 + {addr["P_dec"]}'
        f' = <b>{addr["num_abs_page"]}</b> (0x{_h(addr["num_abs_page_hex"])})<br>'
        f'N.Celdas = RSIZE / 2K = {rsize} / 2 = <b>{nc}</b>'
        f'</div></div>'
    )


def _section_pte(results: dict) -> str:
    pte = results["pte"]
    colored = _colored_bin_pte(pte["pte_bin"], pte["bit_I"])

    if pte["is_page_fault"]:
        badge = '<span class="badge badge-pf">PAGE FAULT</span>'
        detail = "La pagina NO esta en memoria real. Se necesita resolver el page fault."
    else:
        badge = '<span class="badge badge-ok">SIN PAGE FAULT</span>'
        detail = (
            f'La pagina esta en memoria real.<br>'
            f'N. celda = <span class="val">{pte["cell_number"]}</span> &nbsp; '
            f'DC = <span class="val">0x{_h(pte["dc_hex"])}</span>'
        )

    return (
        '<div class="section"><h2>Paso 2: Analisis de la PTE</h2>'
        f'<p>PTE = <span class="mono val">0x{_h(pte["pte_hex"])}</span></p>'
        f'<div class="bin-display">{colored}</div>'
        f'<p style="font-size:0.8rem;color:#64748b;margin:2px 0 10px 0">'
        f'Formato: [13 bits datos | <b>I</b> | 2 bits] &nbsp; Bit I = {pte["bit_I"]}</p>'
        f'<p>{badge}</p>'
        f'<p>{detail}</p>'
        '</div>'
    )


def _section_real_address(results: dict) -> str:
    dr = results["real_address"]
    return (
        '<div class="section"><h2>Direccion Real</h2>'
        f'<div class="calc">'
        f'DC = 0x{_h(dr["dc_hex"])} ({dr["dc_dec"]})<br>'
        f'DR = DC + d = {dr["dr_dec"]}'
        f'</div>'
        f'<div class="result-box">'
        f'<div class="label">RESULTADO FINAL</div>'
        f'<div class="value">DR = 0x{_h(dr["dr_hex"])}</div>'
        f'<div style="font-size:0.8rem;margin-top:4px;color:#065f46" class="mono">'
        f'{_h(dr["dr_bin"])}b</div>'
        f'</div></div>'
    )


def _section_lru(results: dict) -> str:
    lru = results["lru"]

    # Colas antes
    before = _queues_table(lru["queues_before"], "Colas ANTES")

    # Pasos
    steps_html = ""
    for step in lru["steps"]:
        cls = ' class="step-victim"' if step["action"] == "victim_found" else ""
        steps_html += f"<li{cls}>{_h(step['detail'])}</li>\n"

    # Colas despues
    after = _queues_table(lru["queues_after"], "Colas DESPUES")

    # Victima
    vc = lru["victim_cell"]
    vr = lru["victim_R"]
    vcc = lru["victim_C"]
    if lru["needs_pageout"]:
        po_text = "Se requiere PAGE-OUT (C=1, pagina modificada)"
    else:
        po_text = "NO se requiere page-out (C=0)"

    return (
        '<div class="section"><h2>Paso 3: Algoritmo LRU 2a Oportunidad</h2>'
        f'{before}'
        f'<p style="font-weight:600;margin:14px 0 4px 0">Ejecucion:</p>'
        f'<ol class="step-list">{steps_html}</ol>'
        f'{after}'
        f'<div class="victim-box">'
        f'<span class="label">VICTIMA: Celda {vc}, R={vr}, C={vcc}</span><br>'
        f'{po_text}</div>'
        '</div>'
    )


def _section_evicted(results: dict) -> str:
    ev = results["evicted_page"]
    return (
        '<div class="section"><h2>Paso 4: Identificacion de Pagina Desalojada</h2>'
        f'<div class="calc">'
        f'PFTE octetos 4-5 = 0x{_h(ev["pfte_hex"])}<br>'
        f'N.Abs pagina = 0x{_h(ev["pfte_hex"])} = <b>{ev["num_abs_page"]}</b><br>'
        f'Segmento = {ev["num_abs_page"]} // 32 = <b>{ev["segment"]}</b><br>'
        f'Pagina&nbsp;&nbsp;&nbsp;= {ev["num_abs_page"]} % 32 = <b>{ev["page"]}</b>'
        f'</div>'
        f'<p>Se desaloja la <b>pagina {ev["page"]}</b> del '
        f'<b>segmento {ev["segment"]}</b>.</p>'
        '</div>'
    )


def _section_pageout(results: dict) -> str:
    po = results["page_out"]
    epa = po["epa"]
    dc = po["dc"]
    spc = epa["slots_per_cyl"]
    spt = epa["slots_per_track"]
    nap = epa["cylinder"] * spc + epa["track"] * spt + epa["slot"]
    dm = results.get("disk_model", "?")
    block = _epa_block(epa, dc, nap, dm, "(desalojada)")
    return (
        '<div class="section"><h2>Paso 5: PAGE-OUT (escritura a disco)</h2>'
        f'{block}</div>'
    )


def _section_pagein(results: dict) -> str:
    pi = results["page_in"]
    epa = pi["epa"]
    dc = pi["dc"]
    spc = epa["slots_per_cyl"]
    spt = epa["slots_per_track"]
    nap = epa["cylinder"] * spc + epa["track"] * spt + epa["slot"]
    dm = results.get("disk_model", "?")
    block = _epa_block(epa, dc, nap, dm, "(solicitada)")
    return (
        '<div class="section"><h2>Paso 6: PAGE-IN (lectura desde disco)</h2>'
        f'{block}</div>'
    )


def _section_table_updates(results: dict) -> str:
    npte = results["new_pte"]
    pte_orig = results["pte"]
    addr = results["address"]
    cell = npte["cell_number"]

    # PTE del segmento referenciado: antes (page fault) -> despues (valida)
    rows_ref = [
        [f'PTE del segmento {addr["S_dec"]}, pagina {addr["P_dec"]}',
         f'<span class="val">0x{_h(pte_orig["pte_hex"])}</span> (I=1)',
         f'<span class="val changed">0x{_h(npte["bi_0_hex"])}</span> (I=0)'],
    ]

    # PTE del segmento desalojado (si tenemos los datos)
    if "evicted_page" in results:
        ev = results["evicted_page"]
        rows_ref.append(
            [f'PTE del segmento {ev["segment"]}, pagina {ev["page"]}',
             '<span class="val">(valida)</span>',
             f'<span class="val changed">0x{_h(npte["bi_1_hex"])}</span> (I=1)'],
        )

    table_pte = _table(["Entrada", "ANTES", "DESPUES"], rows_ref)

    return (
        '<div class="section"><h2>Paso 7: Actualizacion de Tablas</h2>'
        f'<p>Celda asignada: <span class="val">{cell}</span></p>'
        f'{table_pte}'
        f'<div class="calc">'
        f'BI(0) = <span class="val">0x{_h(npte["bi_0_hex"])}</span>'
        f' = {_h(npte["bi_0_bin"])} &nbsp; (pagina valida, I=0)<br>'
        f'BI(1) = <span class="val">0x{_h(npte["bi_1_hex"])}</span>'
        f' = {_h(npte["bi_1_bin"])} &nbsp; (pagina invalida, I=1)'
        f'</div></div>'
    )


# ---------------------------------------------------------------------------
# Funcion principal
# ---------------------------------------------------------------------------

def generate_report(results: dict, filename: str = "informe_ibm.html") -> str:
    """Genera un informe HTML completo con todos los pasos de resolucion.

    Recibe el dict devuelto por solver.solve_full_exercise() que contiene
    todos los resultados intermedios. Ensambla las secciones segun el tipo
    de ejercicio (con/sin page fault) y escribe el fichero HTML.

    Devuelve la ruta absoluta del archivo generado.
    """
    sections = []

    # Cabecera
    sections.append(_section_header(results))

    # Contenedor principal
    sections.append('<div class="container">')

    # Paso 1: descomposicion
    sections.append(_section_decomposition(results))

    # Paso 2: PTE
    sections.append(_section_pte(results))

    if not results.get("page_fault", False):
        # Sin page fault: DR directa
        sections.append(_section_real_address(results))
    else:
        # Page fault: pasos adicionales
        if "lru" in results:
            sections.append(_section_lru(results))

        if "evicted_page" in results:
            sections.append(_section_evicted(results))

        if "page_out" in results:
            sections.append(_section_pageout(results))

        if "page_in" in results:
            sections.append(_section_pagein(results))

        if "new_pte" in results:
            sections.append(_section_table_updates(results))

        if "real_address" in results:
            sections.append(_section_real_address(results))

    sections.append(
        '<footer>Generado por IBM Caso de Estudio &mdash; '
        'Memoria Virtual System/370</footer>'
    )
    sections.append('</div>')  # container

    body = "\n".join(sections)

    html = (
        '<!DOCTYPE html>\n'
        '<html lang="es">\n'
        '<head>\n'
        '<meta charset="UTF-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
        '<title>Informe IBM Caso de Estudio</title>\n'
        f'<style>{CSS}</style>\n'
        '</head>\n'
        f'<body>\n{body}\n</body>\n'
        '</html>\n'
    )

    filepath = os.path.abspath(filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)

    return filepath
