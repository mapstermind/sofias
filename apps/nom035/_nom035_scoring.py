"""NOM-035 scoring configuration (data, keyed by surveys.Question.code).

All data below is transcribed authoritatively from the single source of truth,
`docs/internal/roadmap_context/Guias de Referencia.md`:

- Guía III (large / 72 items) and Guía II (small / 46 items) — taxonomy
  (Categoría/Dominio/Dimensión → items), inverted-item lists, and threshold tables
  come straight from that document's Guía II and Guía III sections. Item counts
  reconcile against every threshold table.

NDR is classified only at the dominio, categoría and final levels — the standard
publishes no per-dimensión threshold table, so dimensión is used only to organise
the taxonomy source below, never scored.
"""

from apps.nom035 import constants as c

# The survey instrument this engine scores (surveys.Survey.key). The engine is
# NOM-035-specific: only submissions of this survey are scored.
NOM035_SURVEY_KEY = "nom035"

# ── Guía I (traumatic events) ───────────────────────────────────────────────
# Section I is the trigger; the follow-ups split into three sections whose
# per-section "Sí" counts drive the official clinical-referral rule (see
# scoring.guia1_positive and Guias de Referencia.md, "Interpretación ... GR.I").
GUIA1_TRIGGER_CODE = "g1-1"  # Sección I — acontecimiento traumático severo
GUIA1_SECTION_II_CODES = ["g1-2", "g1-3"]  # Recuerdos persistentes
GUIA1_SECTION_III_CODES = [f"g1-{i}" for i in range(4, 11)]  # Esfuerzo por evitar
GUIA1_SECTION_IV_CODES = [f"g1-{i}" for i in range(11, 16)]  # Afectación

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

# Display labels (official NOM-035 names) for categoría and dominio keys.
_GROUP_LABELS = {
    CAT_AMBIENTE: "Ambiente de trabajo",
    CAT_FACTORES: "Factores propios de la actividad",
    CAT_TIEMPO: "Organización del tiempo de trabajo",
    CAT_LIDERAZGO: "Liderazgo y relaciones en el trabajo",
    CAT_ENTORNO: "Entorno organizacional",
    DOM_CONDICIONES: "Condiciones en el ambiente de trabajo",
    DOM_CARGA: "Carga de trabajo",
    DOM_CONTROL: "Falta de control sobre el trabajo",
    DOM_JORNADA: "Jornada de trabajo",
    DOM_INTERFERENCIA: "Interferencia en la relación trabajo-familia",
    DOM_LIDERAZGO: "Liderazgo",
    DOM_RELACIONES: "Relaciones en el trabajo",
    DOM_VIOLENCIA: "Violencia",
    DOM_RECONOCIMIENTO: "Reconocimiento del desempeño",
    DOM_PERTENENCIA: "Insuficiente sentido de pertenencia e inestabilidad",
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

# ── Guía II (small / 46) — authoritative dominio → item numbers ─────────────
# From Guias de Referencia.md, Guía II "Grupos de ítems por dimensión, dominio y
# categoría". Guía II has no "Entorno organizacional" categoría (no Reconocimiento
# / Pertenencia dominios); items 41–43 (clientes) and 44–46 (jefe) are conditional.
_SMALL_DOMINIO_ITEMS = {
    DOM_CONDICIONES: [1, 2, 3],
    DOM_CARGA: [4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 41, 42, 43],
    DOM_CONTROL: [18, 19, 20, 21, 22, 26, 27],
    DOM_JORNADA: [14, 15],
    DOM_INTERFERENCIA: [16, 17],
    DOM_LIDERAZGO: [23, 24, 25, 28, 29],
    DOM_RELACIONES: [30, 31, 32, 44, 45, 46],
    DOM_VIOLENCIA: [33, 34, 35, 36, 37, 38, 39, 40],
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
# Guía II: from the value table in Guias de Referencia.md. Items 18–33 score
# Siempre→0 … Nunca→4 (non-inverted); items 1–17 and 34–46 score 4→0 (inverted).
_SMALL_NON_INVERTED = set(range(18, 34))
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

# Guía II — authoritative (Guias de Referencia.md, Guía II range tables).
_THRESHOLDS_SMALL = {
    ("final", "final"): _bands(20, 45, 70, 90),
    (c.LEVEL_CATEGORIA, CAT_AMBIENTE): _bands(3, 5, 7, 9),
    (c.LEVEL_CATEGORIA, CAT_FACTORES): _bands(10, 20, 30, 40),
    (c.LEVEL_CATEGORIA, CAT_TIEMPO): _bands(4, 6, 9, 12),
    (c.LEVEL_CATEGORIA, CAT_LIDERAZGO): _bands(10, 18, 28, 38),
    (c.LEVEL_DOMINIO, DOM_CONDICIONES): _bands(3, 5, 7, 9),
    (c.LEVEL_DOMINIO, DOM_CARGA): _bands(12, 16, 20, 24),
    (c.LEVEL_DOMINIO, DOM_CONTROL): _bands(5, 8, 11, 14),
    (c.LEVEL_DOMINIO, DOM_JORNADA): _bands(1, 2, 4, 6),
    (c.LEVEL_DOMINIO, DOM_INTERFERENCIA): _bands(1, 2, 4, 6),
    (c.LEVEL_DOMINIO, DOM_LIDERAZGO): _bands(3, 5, 8, 11),
    (c.LEVEL_DOMINIO, DOM_RELACIONES): _bands(5, 8, 11, 14),
    (c.LEVEL_DOMINIO, DOM_VIOLENCIA): _bands(7, 10, 13, 16),
}

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


def group_label(key: str) -> str:
    """Human-readable Spanish name for a categoría or dominio key."""
    return _GROUP_LABELS.get(key, key.replace("_", " ").capitalize())
