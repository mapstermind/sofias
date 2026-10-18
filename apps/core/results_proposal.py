"""Sample data for the results-dashboard proposal at /propuestas/resultados/.

A static page that shows the client a proposed layout for the NOM-035 results
page next to the real one. The numbers are invented but consistent: 148
questionnaires out of 180 activated accounts, Guía III, with the real Guía III
thresholds and score ceilings (`apps/nom035/_nom035_scoring.py`). Nothing here
reads the database.
"""

from dataclasses import dataclass

from apps.nom035 import constants as c

TOTAL = 148
REGISTERED = 180
# One participation tick per this many activated accounts.
TICK_ACCOUNTS = 4


@dataclass(frozen=True)
class Group:
    """The final score, a categoría or a dominio: its distribution and statistics."""

    key: str
    label: str
    counts: tuple[int, int, int, int, int]  # in c.NDR_ORDER
    mean: float
    median: float
    minimum: int
    maximum: int
    scale_max: int
    thresholds: tuple[int, int, int, int]  # upper bounds of nulo, bajo, medio, alto
    tier: str = ""  # "dominio" draws in the deeper dominio ramp
    children: tuple["Group", ...] = ()

    @property
    def n(self) -> int:
        return sum(self.counts)

    @property
    def levels(self) -> list[dict]:
        return [
            {
                "level": level,
                "label": c.NDR_LABELS[level],
                "count": count,
                "percent": round(count * 100 / self.n),
                "share": round(count * 100 / self.n, 2),
            }
            for level, count in zip(c.NDR_ORDER, self.counts)
        ]

    @property
    def at_risk(self) -> int:
        """Percent of questionnaires in alto or muy alto."""
        return round((self.counts[3] + self.counts[4]) * 100 / self.n)

    @property
    def strip_bands(self) -> tuple[tuple[float, str, str], ...]:
        prefix = "dom" if self.tier == "dominio" else "ndr"
        uppers = (*self.thresholds, float("inf"))
        return tuple(
            (upper, f"{prefix}-{level}", c.NDR_LABELS[level])
            for upper, level in zip(uppers, c.NDR_ORDER)
        )

    @property
    def strip_points(self) -> list[tuple[str, str, float]]:
        return [
            ("min", "Mín.", self.minimum),
            ("median", "Mediana", self.median),
            ("mean", "Prom.", self.mean),
            ("max", "Máx.", self.maximum),
        ]

    @property
    def ranges(self) -> list[dict]:
        """Each level's score range, as the guide's table states it."""
        b, m, a, mu = self.thresholds
        texts = (
            f"menos de {b}",
            f"{b} a menos de {m}",
            f"{m} a menos de {a}",
            f"{a} a menos de {mu}",
            f"{mu} o más",
        )
        return [
            {"level": level, "label": c.NDR_LABELS[level], "range": text}
            for level, text in zip(c.NDR_ORDER, texts)
        ]


def _dom(key, label, counts, stats, scale_max, thresholds):
    mean, median, minimum, maximum = stats
    return Group(
        key,
        label,
        counts,
        mean,
        median,
        minimum,
        maximum,
        scale_max,
        thresholds,
        "dominio",
    )


FINAL = Group(
    "final",
    "Calificación final",
    (22, 41, 47, 27, 11),
    86.4,
    84,
    21,
    171,
    288,
    (50, 75, 99, 140),
)

CATEGORIAS = (
    Group(
        "ambiente",
        "Ambiente de trabajo",
        (30, 52, 38, 20, 8),
        8.1,
        8,
        1,
        18,
        20,
        (5, 9, 11, 14),
        children=(
            _dom(
                "condiciones",
                "Condiciones en el ambiente de trabajo",
                (30, 52, 38, 20, 8),
                (8.1, 8, 1, 18),
                20,
                (5, 9, 11, 14),
            ),
        ),
    ),
    Group(
        "factores",
        "Factores propios de la actividad",
        (18, 35, 44, 33, 18),
        31.4,
        31,
        9,
        78,
        100,
        (15, 30, 45, 60),
        children=(
            _dom(
                "carga",
                "Carga de trabajo",
                (15, 30, 45, 38, 20),
                (24.6, 25, 6, 52),
                60,
                (15, 21, 27, 37),
            ),
            _dom(
                "control",
                "Falta de control sobre el trabajo",
                (28, 44, 40, 24, 12),
                (15.2, 15, 3, 33),
                40,
                (11, 16, 21, 25),
            ),
        ),
    ),
    Group(
        "tiempo",
        "Organización del tiempo de trabajo",
        (40, 46, 30, 22, 10),
        6.2,
        6,
        0,
        20,
        24,
        (5, 7, 10, 13),
        children=(
            _dom(
                "jornada",
                "Jornada de trabajo",
                (50, 40, 30, 18, 10),
                (1.8, 2, 0, 7),
                8,
                (1, 2, 4, 6),
            ),
            _dom(
                "interferencia",
                "Interferencia en la relación trabajo-familia",
                (38, 46, 34, 20, 10),
                (5.1, 5, 0, 14),
                16,
                (4, 6, 8, 10),
            ),
        ),
    ),
    Group(
        "liderazgo",
        "Liderazgo y relaciones en el trabajo",
        (25, 40, 41, 28, 14),
        24.8,
        24,
        5,
        77,
        104,
        (14, 29, 42, 58),
        children=(
            _dom(
                "liderazgo",
                "Liderazgo",
                (30, 38, 40, 26, 14),
                (12.7, 12, 2, 31),
                36,
                (9, 12, 16, 20),
            ),
            _dom(
                "relaciones",
                "Relaciones en el trabajo",
                (40, 45, 35, 18, 10),
                (12.4, 12, 3, 30),
                36,
                (10, 13, 17, 21),
            ),
            _dom(
                "violencia",
                "Violencia",
                (60, 40, 25, 15, 8),
                (8.3, 8, 0, 25),
                32,
                (7, 10, 13, 16),
            ),
        ),
    ),
    Group(
        "entorno",
        "Entorno organizacional",
        (35, 50, 33, 20, 10),
        11.9,
        12,
        2,
        34,
        40,
        (10, 14, 18, 23),
        children=(
            _dom(
                "reconocimiento",
                "Reconocimiento del desempeño",
                (30, 46, 38, 22, 12),
                (9.6, 10, 1, 22),
                24,
                (6, 10, 14, 18),
            ),
            _dom(
                "pertenencia",
                "Insuficiente sentido de pertenencia e inestabilidad",
                (40, 50, 30, 18, 10),
                (5.2, 5, 0, 14),
                16,
                (4, 6, 8, 10),
            ),
        ),
    ),
)

# The categoría the drill-down example selects.
SELECTED_CATEGORIA = CATEGORIAS[1]

AREAS = (
    {"label": "Operaciones", "registered": 70, "counts": (9, 16, 20, 12, 5)},
    {"label": "Ventas", "registered": 45, "counts": (6, 10, 11, 5, 2)},
    {"label": "Administración", "registered": 31, "counts": (5, 9, 8, 4, 2)},
    {"label": "Logística", "registered": 30, "counts": (2, 5, 7, 5, 2)},
    # Three respondents: hidden by the small-group rule.
    {"label": "Recursos Humanos", "registered": 4, "responded": 3, "counts": None},
)

SEX = (
    {"label": "Masculino", "value": 82, "color": "bg-series-1"},
    {"label": "Femenino", "value": 66, "color": "bg-series-2"},
)

AGES = (
    ("15", 2),
    ("20", 14),
    ("25", 21),
    ("30", 26),
    ("35", 24),
    ("40", 20),
    ("45", 16),
    ("50", 12),
    ("55", 8),
    ("60+", 5),
)

GUIA1 = (
    {"label": "Sin acontecimiento", "value": 118, "color": "bg-neutral-300"},
    {
        "label": "Acontecimiento sin requerir valoración",
        "value": 24,
        "color": "bg-[#CA9429]",
    },
    {"label": "Requiere valoración clínica", "value": 6, "color": "bg-[#7A1010]"},
)

# What the proposal changes and what the client has to settle, in the order
# the page lists them.
DECISIONS = (
    {
        "title": "Una cifra nueva: porcentaje en alto o muy alto",
        "today": "Cada categoría muestra cómo se reparte entre los cinco niveles; ninguna cifra la resume.",
        "proposal": "Cada fila de Categorías y de Dominios lleva una etiqueta con el porcentaje de cuestionarios en alto o muy alto, para ver de un vistazo dónde se concentra el riesgo.",
        "cost": "Es una suma de la distribución, no un nivel de riesgo de la empresa ni del área: el tablero evita dar ese veredicto a propósito. Si se lee como veredicto, quitamos la etiqueta y queda solo la barra.",
        "question": "¿Se queda la etiqueta?",
    },
    {
        "title": "La escala de la gráfica principal",
        "today": "Todas las distribuciones usan la misma escala, de 0 a 100 %, para compararlas entre sí.",
        "proposal": "La gráfica principal termina en la decena siguiente al nivel con más cuestionarios (aquí, 40 %) y lo dice debajo. Las columnas ganan altura y se leen mejor.",
        "cost": "Dos gráficas con escalas distintas solo se comparan por sus cifras, no por la altura. Al elegir otra categoría en Ver, la escala puede cambiar.",
        "question": "¿Escala variable o de 0 a 100 % en todas?",
    },
    {
        "title": "Gráficas nuevas solo para la pantalla",
        "today": "El tablero y el reporte en PDF dibujan las mismas cuatro gráficas.",
        "proposal": "El tablero estrena sus propias gráficas; el reporte y su PDF se quedan como están.",
        "cost": "Hay que mantener dos versiones de cada gráfica, y el tablero y el reporte se verán distintos. Llevar el nuevo estilo al reporte sería un cambio aparte, porque el PDF dibuja menos estilos que el navegador.",
        "question": "¿Está bien que el reporte se vea distinto del tablero por ahora?",
    },
    {
        "title": "Dos escalas de color para los niveles",
        "today": "La calificación final y las categorías usan la escala clara; los dominios, una escala más profunda, para distinguirlos.",
        "proposal": "Se conservan las dos. En Con una categoría elegida se ven juntas: la gráfica principal en la clara y los dominios en la profunda.",
        "cost": "Ninguno si se distinguen bien; si confunden, pasar a una sola escala obliga a marcar los dominios de otra forma.",
        "question": "Al verlas lado a lado, ¿se distinguen bien?",
    },
    {
        "title": "En el teléfono",
        "today": "Cada sección es una tarjeta de ancho completo, una debajo de otra.",
        "proposal": "Todo pasa a una sola columna en este orden: filtros, gráfica principal, categorías, participación, Guía I, quienes respondieron y por área. Bajo las columnas, Muy alto se parte en dos líneas.",
        "cost": "Falta revisarla en un teléfono de 360 px de ancho antes de construirla.",
        "question": "¿Es el orden correcto para el teléfono?",
    },
    {
        "title": "Estadísticas por categoría y dominio: el selector Ver",
        "today": "Las estadísticas de categorías y dominios son una sección propia, debajo de la distribución.",
        "proposal": "Un selector Ver, junto a la encuesta, elige entre la calificación final y una categoría. Con una categoría, el recuadro principal muestra su distribución y sus estadísticas, y la columna derecha sus dominios, cada uno con las suyas.",
        "cost": "Ver va aparte de Filtros porque hace otra cosa: los filtros cambian a quién se cuenta y Ver cambia qué se mide. Por eso participación, Guía I y quienes respondieron no cambian al elegir una categoría.",
        "question": "¿Las barras de Por área deben mostrar también la categoría elegida, en lugar de la calificación final? Los datos existen: el reporte ya los calcula por área.",
    },
    {
        "title": "Tamaños de texto y tarjetas",
        "today": "Los títulos de sección miden 20 px y las cifras 31 px; las tarjetas son blancas, con borde fino y esquinas de 12 px.",
        "proposal": "El título del recuadro principal sube a 31 px y su cifra a 39 px; las tarjetas pierden el borde y redondean más sus esquinas, sobre un fondo gris.",
        "cost": "Es un cambio al sistema de diseño, no solo a esta página: si se aprueba, pasa a /estilos/ y a la guía de diseño.",
        "question": "¿Este estilo es solo del tablero o de toda la plataforma?",
    },
    {
        "title": "Filtrar desde Por área",
        "today": "El nombre de cada área es un enlace que la agrega a los filtros.",
        "proposal": "Un botón redondo al final de la fila hace lo mismo: agrega el área a los filtros y todas las gráficas se recalculan. En esta página el botón no hace nada.",
        "cost": "Un botón más por fila; el nombre puede seguir siendo enlace.",
        "question": "¿Botón, enlace en el nombre o ambos?",
    },
)


def _ceiling(percents) -> int:
    """The hero chart's top: the next multiple of 10 above the largest share."""
    return max(10, -(-max(percents) // 10) * 10)


def hero(group: Group) -> dict:
    """The lollipop chart: one stem per level on a variable 0–ceiling scale.

    The level holding the largest share starts selected, as the page opens.
    """
    levels = group.levels
    top = _ceiling([lv["percent"] for lv in levels])
    selected = max(range(len(levels)), key=lambda i: levels[i]["count"])
    return {
        "group": group,
        "ceiling": top,
        "gridlines": [
            {"label": f"{v} %", "bottom": round(v * 100 / top, 2)}
            for v in range(10, top + 1, 10)
        ],
        "columns": [
            {
                **lv,
                "height": round(lv["share"] * 100 / top, 2),
                "selected": i == selected,
            }
            for i, lv in enumerate(levels)
        ],
        "selected": levels[selected],
    }


def areas() -> list[dict]:
    rows = []
    for area in AREAS:
        counts = area["counts"]
        responded = area.get("responded") or sum(counts)
        rows.append(
            {
                "label": area["label"],
                "registered": area["registered"],
                "responded": responded,
                "participation": round(responded * 100 / area["registered"]),
                "levels": (
                    [
                        {"level": level, "share": round(n * 100 / responded, 2)}
                        for level, n in zip(c.NDR_ORDER, counts)
                    ]
                    if counts
                    else None
                ),
            }
        )
    return rows


def participation() -> dict:
    ticks = -(-REGISTERED // TICK_ACCOUNTS)
    answered = round(TOTAL / TICK_ACCOUNTS)
    return {
        "registered": REGISTERED,
        "responded": TOTAL,
        "pending": REGISTERED - TOTAL,
        "percent": round(TOTAL * 100 / REGISTERED),
        "ticks": [i < answered for i in range(ticks)],
        "per_tick": TICK_ACCOUNTS,
    }


def profile() -> dict:
    most = max(n for _, n in AGES)
    return {
        "sex": [{**s, "percent": round(s["value"] * 100 / TOTAL)} for s in SEX],
        "ages": [
            {"label": label, "value": n, "height": round(n * 100 / most, 2)}
            for label, n in AGES
        ],
    }


def guia1() -> dict:
    return {
        "positive": GUIA1[2]["value"],
        "slices": [{**s, "share": round(s["value"] * 100 / TOTAL, 2)} for s in GUIA1],
    }


def context() -> dict:
    return {
        "total": TOTAL,
        "final": FINAL,
        "final_hero": hero(FINAL),
        "categorias": CATEGORIAS,
        "selected_categoria": SELECTED_CATEGORIA,
        "categoria_hero": hero(SELECTED_CATEGORIA),
        "areas": areas(),
        "participation": participation(),
        "profile": profile(),
        "guia1": guia1(),
        "decisions": DECISIONS,
    }
