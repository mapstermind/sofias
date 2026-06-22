"""NOM-035 scoring configuration (data, keyed by surveys.Question.code).

Guía III (large / 72 items) — taxonomy, inverted items, and threshold tables are
transcribed authoritatively from `Ejemplo Reporte Resultados.pdf` (the official
NOM-035 mechanism). Item counts reconcile against every threshold table.

Guía II (small / 46 items) — the provided docs do not contain its tables, so the
taxonomy and inverted-item list are RECONSTRUCTED from the standard NOM-035 Guía II
structure and the threshold tables are PROPORTIONAL PLACEHOLDERS. All of Guía II is
flagged for domain-expert validation (see
docs/platform/nom-035-valoracion-supuestos.md).

NDR is classified only at the dominio, categoría and final levels — the standard
publishes no per-dimensión threshold table, so dimensión is used only to organise
the taxonomy source below, never scored.
"""

from apps.nom035 import constants as c

# The survey instrument this engine scores (surveys.Survey.key). The engine is
# NOM-035-specific: only submissions of this survey are scored.
NOM035_SURVEY_KEY = "nom035"

# ── Guía I (traumatic events) ───────────────────────────────────────────────
GUIA1_TRIGGER_CODE = "g1-1"
GUIA1_FOLLOWUP_CODES = [f"g1-{i}" for i in range(2, 16)]

# ── Categoría → Dominio structure (shared keys) ─────────────────────────────
CAT_AMBIENTE = "ambiente_de_trabajo"
CAT_FACTORES = "factores_propios_de_la_actividad"
CAT_TIEMPO = "organizacion_del_tiempo_de_trabajo"
CAT_LIDERAZGO = "liderazgo_y_relaciones_en_el_trabajo"
CAT_ENTORNO = "entorno_organizacional"

DOM_CONDICIONES = "condiciones_en_el_ambiente_de_trabajo"
DOM_CARGA = "carga_de_trabajo"
DOM_CONTROL = "falta_de_control_sobre_el_trabajo"
DOM_JORNADA = "jornada_de_trabajo"
DOM_INTERFERENCIA = "interferencia_relacion_trabajo_familia"
DOM_LIDERAZGO = "liderazgo"
DOM_RELACIONES = "relaciones_en_el_trabajo"
DOM_VIOLENCIA = "violencia"
DOM_RECONOCIMIENTO = "reconocimiento_del_desempeno"
DOM_PERTENENCIA = "insuficiente_sentido_de_pertenencia_e_inestabilidad"

_DOMINIO_CATEGORIA = {
    DOM_CONDICIONES: CAT_AMBIENTE,
    DOM_CARGA: CAT_FACTORES,
    DOM_CONTROL: CAT_FACTORES,
    DOM_JORNADA: CAT_TIEMPO,
    DOM_INTERFERENCIA: CAT_TIEMPO,
    DOM_LIDERAZGO: CAT_LIDERAZGO,
    DOM_RELACIONES: CAT_LIDERAZGO,
    DOM_VIOLENCIA: CAT_LIDERAZGO,
    DOM_RECONOCIMIENTO: CAT_ENTORNO,
    DOM_PERTENENCIA: CAT_ENTORNO,
}

# ── Guía III (large / 72) — authoritative dominio → item numbers ────────────
_LARGE_DOMINIO_ITEMS = {
    DOM_CONDICIONES: [1, 2, 3, 4, 5],
    DOM_CARGA: [6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 65, 66, 67, 68],
    DOM_CONTROL: [23, 24, 25, 26, 27, 28, 29, 30, 35, 36],
    DOM_JORNADA: [17, 18],
    DOM_INTERFERENCIA: [19, 20, 21, 22],
    DOM_LIDERAZGO: [31, 32, 33, 34, 37, 38, 39, 40, 41],
    DOM_RELACIONES: [42, 43, 44, 45, 46, 69, 70, 71, 72],
    DOM_VIOLENCIA: [57, 58, 59, 60, 61, 62, 63, 64],
    DOM_RECONOCIMIENTO: [47, 48, 49, 50, 51, 52],
    DOM_PERTENENCIA: [53, 54, 55, 56],
}

# ── Guía II (small / 46) — reconstructed dominio → item numbers ─────────────
_SMALL_DOMINIO_ITEMS = {
    DOM_CONDICIONES: [1, 2, 3],
    DOM_CARGA: [4, 5, 6, 7, 8, 9, 10, 11, 12, 41, 42, 43],
    DOM_CONTROL: [13, 14, 15, 16, 17, 18, 19, 20],
    DOM_JORNADA: [21, 22],
    DOM_INTERFERENCIA: [23, 24, 25],
    DOM_LIDERAZGO: [26, 27, 28, 29],
    DOM_RELACIONES: [30, 31, 32, 33],
    DOM_VIOLENCIA: [34, 35, 36, 37, 38, 39, 40],
    DOM_RECONOCIMIENTO: [44, 45, 46],
}


def _build_taxonomy(prefix, dominio_items):
    """{code: (categoria, dominio)} from a dominio → item-numbers map."""
    taxonomy = {}
    for dominio, numbers in dominio_items.items():
        categoria = _DOMINIO_CATEGORIA[dominio]
        for n in numbers:
            taxonomy[f"{prefix}-{n}"] = (categoria, dominio)
    return taxonomy


_TAXONOMY_LARGE = _build_taxonomy("g3", _LARGE_DOMINIO_ITEMS)
_TAXONOMY_SMALL = _build_taxonomy("g2", _SMALL_DOMINIO_ITEMS)

# ── Inverted items (scored 5 - value: Siempre→4 … Nunca→0) ──────────────────
# Guía III: the "4,3,2,1,0" group from the Ejemplo Reporte value table.
_INVERTED_LARGE = {
    f"g3-{n}"
    for n in [
        2,
        3,
        5,
        6,
        7,
        8,
        9,
        10,
        11,
        12,
        13,
        14,
        15,
        16,
        17,
        18,
        19,
        20,
        21,
        22,
        29,
        54,
        58,
        59,
        60,
        61,
        62,
        63,
        64,
        65,
        66,
        67,
        68,
        69,
        70,
        71,
        72,
    ]
}
# Guía II: reconstructed — positively-worded (non-inverted) items are the
# autonomy/development/leadership/recognition ones; the rest are inverted.
_SMALL_NON_INVERTED = {
    1,
    13,
    14,
    15,
    16,
    17,
    18,
    19,
    20,
    26,
    27,
    28,
    29,
    30,
    31,
    32,
    33,
    44,
    45,
    46,
}
_INVERTED_SMALL = {f"g2-{n}" for n in range(1, 47) if n not in _SMALL_NON_INVERTED}
INVERTED_ITEMS = _INVERTED_LARGE | _INVERTED_SMALL

# ── Threshold tables (ascending (upper_exclusive, level), last = inf) ───────
_INF = float("inf")


def _bands(b, m, a, mu):
    return [
        (b, c.NDR_NULO),
        (m, c.NDR_BAJO),
        (a, c.NDR_MEDIO),
        (mu, c.NDR_ALTO),
        (_INF, c.NDR_MUY_ALTO),
    ]


# Guía III — authoritative (Ejemplo Reporte Resultados).
_THRESHOLDS_LARGE = {
    ("final", "final"): _bands(50, 75, 99, 140),
    (c.LEVEL_CATEGORIA, CAT_AMBIENTE): _bands(5, 9, 11, 14),
    (c.LEVEL_CATEGORIA, CAT_FACTORES): _bands(15, 30, 45, 60),
    (c.LEVEL_CATEGORIA, CAT_TIEMPO): _bands(5, 7, 10, 13),
    (c.LEVEL_CATEGORIA, CAT_LIDERAZGO): _bands(14, 29, 42, 58),
    (c.LEVEL_CATEGORIA, CAT_ENTORNO): _bands(10, 14, 18, 23),
    (c.LEVEL_DOMINIO, DOM_CONDICIONES): _bands(5, 9, 11, 14),
    (c.LEVEL_DOMINIO, DOM_CARGA): _bands(15, 21, 27, 37),
    (c.LEVEL_DOMINIO, DOM_CONTROL): _bands(11, 16, 21, 25),
    (c.LEVEL_DOMINIO, DOM_JORNADA): _bands(1, 2, 4, 6),
    (c.LEVEL_DOMINIO, DOM_INTERFERENCIA): _bands(4, 6, 8, 10),
    (c.LEVEL_DOMINIO, DOM_LIDERAZGO): _bands(9, 12, 16, 20),
    (c.LEVEL_DOMINIO, DOM_RELACIONES): _bands(10, 13, 17, 21),
    (c.LEVEL_DOMINIO, DOM_VIOLENCIA): _bands(7, 10, 13, 16),
    (c.LEVEL_DOMINIO, DOM_RECONOCIMIENTO): _bands(6, 10, 14, 18),
    (c.LEVEL_DOMINIO, DOM_PERTENENCIA): _bands(4, 6, 8, 10),
}

# Guía II — PLACEHOLDER thresholds, proportional to each group's max score.
# Fractions mirror the Guía III final table (50/75/99/140 of a 288 max).
_PLACEHOLDER_FRACTIONS = (50 / 288, 75 / 288, 99 / 288, 140 / 288)


def _proportional_bands(n_items):
    max_score = 4 * n_items
    cutoffs = [round(f * max_score) for f in _PLACEHOLDER_FRACTIONS]
    # Enforce strictly increasing bands (rounding can collide for small groups).
    for i in range(1, len(cutoffs)):
        if cutoffs[i] <= cutoffs[i - 1]:
            cutoffs[i] = cutoffs[i - 1] + 1
    return _bands(*cutoffs)


def _build_small_thresholds():
    thresholds = {("final", "final"): _proportional_bands(46)}
    cat_counts, dom_counts = {}, {}
    for categoria, dominio in _TAXONOMY_SMALL.values():
        cat_counts[categoria] = cat_counts.get(categoria, 0) + 1
        dom_counts[dominio] = dom_counts.get(dominio, 0) + 1
    for cat, n in cat_counts.items():
        thresholds[(c.LEVEL_CATEGORIA, cat)] = _proportional_bands(n)
    for dom, n in dom_counts.items():
        thresholds[(c.LEVEL_DOMINIO, dom)] = _proportional_bands(n)
    return thresholds


_THRESHOLDS_SMALL = _build_small_thresholds()

# ── "Necesidad de acción según NOM-035" per NDR level ───────────────────────
_ACTION_TEXT = {
    c.NDR_NULO: (
        "El riesgo resulta despreciable, por lo que no se requiere una acción "
        "adicional."
    ),
    c.NDR_BAJO: (
        "Es necesario observar y revisar periódicamente las condiciones de "
        "trabajo evaluadas."
    ),
    c.NDR_MEDIO: (
        "Se requiere revisar la política de prevención de riesgos psicosociales y "
        "reforzar su aplicación y difusión."
    ),
    c.NDR_ALTO: (
        "Se requiere realizar un análisis de cada categoría y dominio para "
        "establecer las acciones de intervención apropiadas."
    ),
    c.NDR_MUY_ALTO: (
        "Se requiere realizar el análisis de cada categoría y dominio para "
        "establecer acciones de intervención inmediatas, así como la atención "
        "clínica de los colaboradores que lo requieran."
    ),
}


# ── Accessors used by the engine ────────────────────────────────────────────
def taxonomy_for_variant(variant: str) -> dict[str, tuple[str, str]]:
    return _TAXONOMY_LARGE if variant == "large" else _TAXONOMY_SMALL


def is_inverted(code: str) -> bool:
    return code in INVERTED_ITEMS


def thresholds_for(level: str, key: str, variant: str) -> list[tuple[float, str]]:
    table = _THRESHOLDS_LARGE if variant == "large" else _THRESHOLDS_SMALL
    return table[(level, key)]


def action_text(ndr: str) -> str:
    return _ACTION_TEXT[ndr]
