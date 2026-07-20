"""
Declarative source of truth for the NOM-035 survey instrument.

Transcribed from docs/internal/roadmap_context/Guias de Referencia.pdf:
- Guía I  — Acontecimientos traumáticos severos (Sí/No), applies to everyone.
- Guía II — Factores de riesgo psicosocial (Likert), small variant (<=50).
- Guía III — ... y entorno organizacional (Likert), large variant (>50).

Each question carries a stable `code` (the integration key for the future
valuation engine). Conditional branching is expressed via `visible_when` rules
(see apps/surveys/visibility.py). No scoring data lives here.
"""

SURVEY_KEY = "nom035"
SURVEY_TITLE = "Encuesta NOM-035"
SURVEY_DESCRIPTION = (
    "Identificación y análisis de los factores de riesgo psicosocial y "
    "evaluación del entorno organizacional (NOM-035-STPS-2018)."
)
HEADCOUNT_THRESHOLD = 50

# 5-point scale, value 1 = Siempre … 5 = Nunca.
LIKERT_LABELS = ["Siempre", "Casi siempre", "Algunas veces", "Casi nunca", "Nunca"]

# Branching gates (boolean Sí/No questions that reveal a following block).
GATE_CLIENTES = "En mi trabajo debo brindar servicio a clientes o usuarios."
GATE_JEFE = "Soy jefe de otros trabajadores."


def _likert(code, text):
    return {
        "code": code,
        "question_type": "likert",
        "text": text,
        "config": {"labels": LIKERT_LABELS},
    }


def _boolean(code, text, visible_when=None):
    return {
        "code": code,
        "question_type": "boolean",
        "text": text,
        "config": {},
        "visible_when": visible_when,
    }


# ---------------------------------------------------------------------------
# Guía I — Acontecimientos traumáticos severos (boolean)
# ---------------------------------------------------------------------------

GUIA_I_TRIGGER = [
    "¿Ha presenciado o sufrido alguna vez, durante o con motivo del trabajo, un "
    "acontecimiento como los siguientes: un accidente que tenga como consecuencia "
    "la muerte, la pérdida de un miembro o una lesión grave; asaltos; actos "
    "violentos que derivaron en lesiones graves; secuestro; amenazas; o cualquier "
    "otro que ponga en riesgo su vida o salud, y/o la de otras personas?",
]

GUIA_I_FOLLOWUP = [
    "¿Ha tenido recuerdos recurrentes sobre el acontecimiento que le provocan malestares?",
    "¿Ha tenido sueños de carácter recurrente sobre el acontecimiento, que le producen malestar?",
    "¿Se ha esforzado por evitar todo tipo de sentimientos, conversaciones o "
    "situaciones que le puedan recordar el acontecimiento?",
    "¿Se ha esforzado por evitar todo tipo de actividades, lugares o personas que "
    "motivan recuerdos del acontecimiento?",
    "¿Ha tenido dificultad para recordar alguna parte importante del evento?",
    "¿Ha disminuido su interés en sus actividades cotidianas?",
    "¿Se ha sentido alejado o distante de los demás?",
    "¿Ha notado que tiene dificultad para expresar sus sentimientos?",
    "¿Ha tenido la impresión de que su vida se va a acortar, que va a morir antes "
    "que otras personas o que tiene un futuro limitado?",
    "¿Ha tenido usted dificultades para dormir?",
    "¿Ha estado particularmente irritable o le han dado arranques de coraje?",
    "¿Ha tenido dificultad para concentrarse?",
    "¿Ha estado nervioso o constantemente en alerta?",
    "¿Se ha sobresaltado fácilmente por cualquier cosa?",
]

# ---------------------------------------------------------------------------
# Guía II — 46 ítems (Likert), small variant
# ---------------------------------------------------------------------------

GUIA_II_MAIN = [
    "Mi trabajo me exige hacer mucho esfuerzo físico.",
    "Me preocupa sufrir un accidente en mi trabajo.",
    "Considero que las actividades que realizo son peligrosas.",
    "Por la cantidad de trabajo que tengo debo quedarme tiempo adicional a mi turno.",
    "Por la cantidad de trabajo que tengo debo trabajar sin parar.",
    "Considero que es necesario mantener un ritmo de trabajo acelerado.",
    "Mi trabajo exige que esté muy concentrado.",
    "Mi trabajo requiere que memorice mucha información.",
    "Mi trabajo exige que atienda varios asuntos al mismo tiempo.",
    "En mi trabajo soy responsable de cosas de mucho valor.",
    "Respondo ante mi jefe por los resultados de toda mi área de trabajo.",
    "En mi trabajo me dan órdenes contradictorias.",
    "Considero que en mi trabajo me piden hacer cosas innecesarias.",
    "Trabajo horas extras más de tres veces a la semana.",
    "Mi trabajo me exige laborar en días de descanso, festivos o fines de semana.",
    "Considero que el tiempo en el trabajo es mucho y perjudica mis actividades "
    "familiares o personales.",
    "Pienso en las actividades familiares o personales cuando estoy en mi trabajo.",
    "Mi trabajo permite que desarrolle nuevas habilidades.",
    "En mi trabajo puedo aspirar a un mejor puesto.",
    "Durante mi jornada de trabajo puedo tomar pausas cuando las necesito.",
    "Puedo decidir la velocidad a la que realizo mis actividades en mi trabajo.",
    "Puedo cambiar el orden de las actividades que realizo en mi trabajo.",
    "Me informan con claridad cuáles son mis funciones.",
    "Me explican claramente los resultados que debo obtener en mi trabajo.",
    "Me informan con quién puedo resolver problemas o asuntos de trabajo.",
    "Me permiten asistir a capacitaciones relacionadas con mi trabajo.",
    "Recibo capacitación útil para hacer mi trabajo.",
    "Mi jefe tiene en cuenta mis puntos de vista y opiniones.",
    "Mi jefe ayuda a solucionar los problemas que se presentan en el trabajo.",
    "Puedo confiar en mis compañeros de trabajo.",
    "Cuando tenemos que realizar trabajo de equipo los compañeros colaboran.",
    "Mis compañeros de trabajo me ayudan cuando tengo dificultades.",
    "En mi trabajo puedo expresarme libremente sin interrupciones.",
    "Recibo críticas constantes a mi persona y/o trabajo.",
    "Recibo burlas, calumnias, difamaciones, humillaciones o ridiculizaciones.",
    "Se ignora mi presencia o se me excluye de las reuniones de trabajo y en la "
    "toma de decisiones.",
    "Se manipulan las situaciones de trabajo para hacerme parecer un mal trabajador.",
    "Se ignoran mis éxitos laborales y se atribuyen a otros trabajadores.",
    "Me bloquean o impiden las oportunidades que tengo para obtener ascenso o "
    "mejora en mi trabajo.",
    "He presenciado actos de violencia en mi centro de trabajo.",
]

GUIA_II_CLIENTES = [
    "Atiendo clientes o usuarios muy enojados.",
    "Mi trabajo me exige atender personas muy necesitadas de ayuda o enfermas.",
    "Para hacer mi trabajo debo demostrar sentimientos distintos a los míos.",
]

GUIA_II_JEFE = [
    "Comunican tarde los asuntos de trabajo.",
    "Dificultan el logro de los resultados del trabajo.",
    "Ignoran las sugerencias para mejorar su trabajo.",
]

# ---------------------------------------------------------------------------
# Guía III — 72 ítems (Likert), large variant
# ---------------------------------------------------------------------------

GUIA_III_MAIN = [
    "El espacio donde trabajo me permite realizar mis actividades de manera "
    "segura e higiénica.",
    "Mi trabajo me exige hacer mucho esfuerzo físico.",
    "Me preocupa sufrir un accidente en mi trabajo.",
    "Considero que en mi trabajo se aplican las normas de seguridad y salud en el "
    "trabajo.",
    "Considero que las actividades que realizo son peligrosas.",
    "Por la cantidad de trabajo que tengo debo quedarme tiempo adicional a mi turno.",
    "Por la cantidad de trabajo que tengo debo trabajar sin parar.",
    "Considero que es necesario mantener un ritmo de trabajo acelerado.",
    "Mi trabajo exige que esté muy concentrado.",
    "Mi trabajo requiere que memorice mucha información.",
    "En mi trabajo tengo que tomar decisiones difíciles muy rápido.",
    "Mi trabajo exige que atienda varios asuntos al mismo tiempo.",
    "En mi trabajo soy responsable de cosas de mucho valor.",
    "Respondo ante mi jefe por los resultados de toda mi área de trabajo.",
    "En el trabajo me dan órdenes contradictorias.",
    "Considero que en mi trabajo me piden hacer cosas innecesarias.",
    "Trabajo horas extras más de tres veces a la semana.",
    "Mi trabajo me exige laborar en días de descanso, festivos o fines de semana.",
    "Considero que el tiempo en el trabajo es mucho y perjudica mis actividades "
    "familiares o personales.",
    "Debo atender asuntos de trabajo cuando estoy en casa.",
    "Pienso en las actividades familiares o personales cuando estoy en mi trabajo.",
    "Pienso que mis responsabilidades familiares afectan mi trabajo.",
    "Mi trabajo permite que desarrolle nuevas habilidades.",
    "En mi trabajo puedo aspirar a un mejor puesto.",
    "Durante mi jornada de trabajo puedo tomar pausas cuando las necesito.",
    "Puedo decidir cuánto trabajo realizo durante la jornada laboral.",
    "Puedo decidir la velocidad a la que realizo mis actividades en mi trabajo.",
    "Puedo cambiar el orden de las actividades que realizo en mi trabajo.",
    "Los cambios que se presentan en mi trabajo dificultan mi labor.",
    "Cuando se presentan cambios en mi trabajo se tienen en cuenta mis ideas o "
    "aportaciones.",
    "Me informan con claridad cuáles son mis funciones.",
    "Me explican claramente los resultados que debo obtener en mi trabajo.",
    "Me explican claramente los objetivos de mi trabajo.",
    "Me informan con quién puedo resolver problemas o asuntos de trabajo.",
    "Me permiten asistir a capacitaciones relacionadas con mi trabajo.",
    "Recibo capacitación útil para hacer mi trabajo.",
    "Mi jefe ayuda a organizar mejor el trabajo.",
    "Mi jefe tiene en cuenta mis puntos de vista y opiniones.",
    "Mi jefe me comunica a tiempo la información relacionada con el trabajo.",
    "La orientación que me da mi jefe me ayuda a realizar mejor mi trabajo.",
    "Mi jefe ayuda a solucionar los problemas que se presentan en el trabajo.",
    "Puedo confiar en mis compañeros de trabajo.",
    "Entre compañeros solucionamos los problemas de trabajo de forma respetuosa.",
    "En mi trabajo me hacen sentir parte del grupo.",
    "Cuando tenemos que realizar trabajo de equipo los compañeros colaboran.",
    "Mis compañeros de trabajo me ayudan cuando tengo dificultades.",
    "Me informan sobre lo que hago bien en mi trabajo.",
    "La forma como evalúan mi trabajo en mi centro de trabajo me ayuda a mejorar "
    "mi desempeño.",
    "En mi centro de trabajo me pagan a tiempo mi salario.",
    "El pago que recibo es el que merezco por el trabajo que realizo.",
    "Si obtengo los resultados esperados en mi trabajo me recompensan o reconocen.",
    "Las personas que hacen bien el trabajo pueden crecer laboralmente.",
    "Considero que mi trabajo es estable.",
    "En mi trabajo existe continua rotación de personal.",
    "Siento orgullo de laborar en este centro de trabajo.",
    "Me siento comprometido con mi trabajo.",
    "En mi trabajo puedo expresarme libremente sin interrupciones.",
    "Recibo críticas constantes a mi persona y/o trabajo.",
    "Recibo burlas, calumnias, difamaciones, humillaciones o ridiculizaciones.",
    "Se ignora mi presencia o se me excluye de las reuniones de trabajo y en la "
    "toma de decisiones.",
    "Se manipulan las situaciones de trabajo para hacerme parecer un mal trabajador.",
    "Se ignoran mis éxitos laborales y se atribuyen a otros trabajadores.",
    "Me bloquean o impiden las oportunidades que tengo para obtener ascenso o "
    "mejora en mi trabajo.",
    "He presenciado actos de violencia en mi centro de trabajo.",
]

GUIA_III_CLIENTES = [
    "Atiendo clientes o usuarios muy enojados.",
    "Mi trabajo me exige atender personas muy necesitadas de ayuda o enfermas.",
    "Para hacer mi trabajo debo demostrar sentimientos distintos a los míos.",
    "Mi trabajo me exige atender situaciones de violencia.",
]

GUIA_III_JEFE = [
    "Comunican tarde los asuntos de trabajo.",
    "Dificultan el logro de los resultados del trabajo.",
    "Cooperan poco cuando se necesita.",
    "Ignoran las sugerencias para mejorar su trabajo.",
]


def _likert_block(prefix, texts, start):
    """Build likert question dicts with codes prefix-<n> starting at `start`."""
    return [_likert(f"{prefix}-{start + i}", text) for i, text in enumerate(texts)]


def build_modules():
    """Return the ordered list of module dicts that define the NOM-035 survey."""
    g2_clientes_gate_code = "g2-clientes"
    g2_jefe_gate_code = "g2-jefe"
    g3_clientes_gate_code = "g3-clientes"
    g3_jefe_gate_code = "g3-jefe"

    return [
        # --- Guía I (all respondents) ---
        {
            "key": "g1-trigger",
            "intro": (
                "Cuestionario para identificar a los trabajadores que fueron "
                "sujetos a acontecimientos traumáticos severos"
            ),
            "title": "Acontecimiento traumático severo",
            "applies_to": "all",
            "questions": [_boolean("g1-1", GUIA_I_TRIGGER[0])],
        },
        {
            "key": "g1-recuerdos",
            "title": "Recuerdos persistentes sobre el acontecimiento (durante el último mes)",
            "applies_to": "all",
            "visible_when": {"any_in_module": "g1-trigger", "equals": True},
            "questions": [
                _boolean(f"g1-{i + 2}", text)
                for i, text in enumerate(GUIA_I_FOLLOWUP[0:2], start=0)
            ],
        },
        {
            "key": "g1-esfuerzo",
            "title": (
                "Esfuerzo por evitar circunstancias parecidas o asociadas al "
                "acontecimiento (durante el último mes)"
            ),
            "applies_to": "all",
            "visible_when": {"any_in_module": "g1-trigger", "equals": True},
            "questions": [
                _boolean(f"g1-{i + 2}", text)
                for i, text in enumerate(GUIA_I_FOLLOWUP[2:9], start=2)
            ],
        },
        {
            "key": "g1-afectacion",
            "title": "Afectación (durante el último mes)",
            "applies_to": "all",
            "visible_when": {"any_in_module": "g1-trigger", "equals": True},
            "questions": [
                _boolean(f"g1-{i + 2}", text)
                for i, text in enumerate(GUIA_I_FOLLOWUP[9:14], start=9)
            ],
        },
        # --- Guía II (small variant) ---
        {
            "key": "g2-main-1",
            "intro": (
                "Cuestionario para identificar los factores de riesgo "
                "psicosocial en los centros de trabajo"
            ),
            "description": (
                "Para responder las preguntas siguientes considere las "
                "condiciones de su centro de trabajo, así como la cantidad y "
                "ritmo de trabajo en los últimos 3 meses."
            ),
            "applies_to": "small",
            "questions": _likert_block("g2", GUIA_II_MAIN[0:9], 1),
        },
        {
            "key": "g2-main-2",
            "description": (
                "Las preguntas siguientes están relacionadas con las "
                "actividades que realiza en su trabajo y las responsabilidades "
                "que tiene."
            ),
            "applies_to": "small",
            "questions": _likert_block("g2", GUIA_II_MAIN[9:13], 10),
        },
        {
            "key": "g2-main-3",
            "description": (
                "Las preguntas siguientes están relacionadas con el tiempo "
                "destinado a su trabajo y sus responsabilidades familiares."
            ),
            "applies_to": "small",
            "questions": _likert_block("g2", GUIA_II_MAIN[13:22], 14),
        },
        {
            "key": "g2-main-4",
            "description": (
                "Las preguntas siguientes están relacionadas con la "
                "capacitación e información que recibe sobre su trabajo."
            ),
            "applies_to": "small",
            "questions": _likert_block("g2", GUIA_II_MAIN[22:27], 23),
        },
        {
            "key": "g2-main-5",
            "description": (
                "Las preguntas siguientes se refieren a las relaciones con "
                "sus compañeros de trabajo y su jefe."
            ),
            "applies_to": "small",
            "questions": _likert_block("g2", GUIA_II_MAIN[27:40], 28),
        },
        {
            "key": "g2-clientes-gate",
            "applies_to": "small",
            "questions": [_boolean(g2_clientes_gate_code, GATE_CLIENTES)],
        },
        {
            "key": "g2-clientes-followup",
            "description": (
                "Las preguntas siguientes están relacionadas con la atención "
                "a clientes y usuarios."
            ),
            "applies_to": "small",
            "visible_when": {"question": g2_clientes_gate_code, "equals": True},
            "questions": [
                _likert(f"g2-{41 + i}", text) for i, text in enumerate(GUIA_II_CLIENTES)
            ],
            "_gate_followups": (
                g2_clientes_gate_code,
                [f"g2-{41 + i}" for i in range(len(GUIA_II_CLIENTES))],
            ),
        },
        {
            "key": "g2-jefe-gate",
            "applies_to": "small",
            "questions": [_boolean(g2_jefe_gate_code, GATE_JEFE)],
        },
        {
            "key": "g2-jefe-followup",
            "description": (
                "Las siguientes preguntas están relacionadas con las "
                "actitudes de los trabajadores que supervisa."
            ),
            "applies_to": "small",
            "visible_when": {"question": g2_jefe_gate_code, "equals": True},
            "questions": [
                _likert(f"g2-{44 + i}", text) for i, text in enumerate(GUIA_II_JEFE)
            ],
            "_gate_followups": (
                g2_jefe_gate_code,
                [f"g2-{44 + i}" for i in range(len(GUIA_II_JEFE))],
            ),
        },
        # --- Guía III (large variant) ---
        {
            "key": "g3-main-1",
            "intro": (
                "Cuestionario para identificar los factores de riesgo "
                "psicosocial y evaluar el entorno organizacional en los "
                "centros de trabajo"
            ),
            "description": (
                "Para responder las siguientes preguntas considere las "
                "condiciones ambientales de su centro de trabajo."
            ),
            "applies_to": "large",
            "questions": _likert_block("g3", GUIA_III_MAIN[0:5], 1),
        },
        {
            "key": "g3-main-2",
            "description": (
                "Para responder a las preguntas siguientes piense en la "
                "cantidad y ritmo de trabajo que tiene."
            ),
            "applies_to": "large",
            "questions": _likert_block("g3", GUIA_III_MAIN[5:8], 6),
        },
        {
            "key": "g3-main-3",
            "description": (
                "Las preguntas siguientes están relacionadas con el "
                "esfuerzo mental que le exige su trabajo."
            ),
            "applies_to": "large",
            "questions": _likert_block("g3", GUIA_III_MAIN[8:12], 9),
        },
        {
            "key": "g3-main-4",
            "description": (
                "Las preguntas siguientes están relacionadas con las "
                "actividades que realiza en su trabajo y las "
                "responsabilidades que tiene."
            ),
            "applies_to": "large",
            "questions": _likert_block("g3", GUIA_III_MAIN[12:16], 13),
        },
        {
            "key": "g3-main-5",
            "description": (
                "Las preguntas siguientes están relacionadas con su "
                "jornada de trabajo."
            ),
            "applies_to": "large",
            "questions": _likert_block("g3", GUIA_III_MAIN[16:22], 17),
        },
        {
            "key": "g3-main-6",
            "description": (
                "Las preguntas siguientes están relacionadas con las "
                "decisiones que puede tomar en su trabajo."
            ),
            "applies_to": "large",
            "questions": _likert_block("g3", GUIA_III_MAIN[22:28], 23),
        },
        {
            "key": "g3-main-7",
            "description": (
                "Las preguntas siguientes están relacionadas con cualquier "
                "tipo de cambio que ocurra en su trabajo (considere los "
                "últimos cambios realizados)."
            ),
            "applies_to": "large",
            "questions": _likert_block("g3", GUIA_III_MAIN[28:30], 29),
        },
        {
            "key": "g3-main-8",
            "description": (
                "Las preguntas siguientes están relacionadas con la "
                "capacitación e información que se le proporciona sobre su "
                "trabajo."
            ),
            "applies_to": "large",
            "questions": _likert_block("g3", GUIA_III_MAIN[30:36], 31),
        },
        {
            "key": "g3-main-9",
            "description": (
                "Las preguntas siguientes están relacionadas con el o los "
                "jefes con quien tiene contacto."
            ),
            "applies_to": "large",
            "questions": _likert_block("g3", GUIA_III_MAIN[36:41], 37),
        },
        {
            "key": "g3-main-10",
            "description": (
                "Las preguntas siguientes se refieren a las relaciones con "
                "sus compañeros."
            ),
            "applies_to": "large",
            "questions": _likert_block("g3", GUIA_III_MAIN[41:46], 42),
        },
        {
            "key": "g3-main-11",
            "description": (
                "Las preguntas siguientes están relacionadas con la "
                "información que recibe sobre su rendimiento en el "
                "trabajo, el reconocimiento, el sentido de pertenencia y "
                "la estabilidad que le ofrece su trabajo."
            ),
            "applies_to": "large",
            "questions": _likert_block("g3", GUIA_III_MAIN[46:56], 47),
        },
        {
            "key": "g3-main-12",
            "description": (
                "Las preguntas siguientes están relacionadas con actos de "
                "violencia laboral (malos tratos, acoso, hostigamiento, "
                "acoso psicológico)."
            ),
            "applies_to": "large",
            "questions": _likert_block("g3", GUIA_III_MAIN[56:64], 57),
        },
        {
            "key": "g3-clientes-gate",
            "applies_to": "large",
            "questions": [_boolean(g3_clientes_gate_code, GATE_CLIENTES)],
        },
        {
            "key": "g3-clientes-followup",
            "description": (
                "Las preguntas siguientes están relacionadas con la "
                "atención a clientes y usuarios."
            ),
            "applies_to": "large",
            "visible_when": {"question": g3_clientes_gate_code, "equals": True},
            "questions": [
                _likert(f"g3-{65 + i}", text)
                for i, text in enumerate(GUIA_III_CLIENTES)
            ],
            "_gate_followups": (
                g3_clientes_gate_code,
                [f"g3-{65 + i}" for i in range(len(GUIA_III_CLIENTES))],
            ),
        },
        {
            "key": "g3-jefe-gate",
            "applies_to": "large",
            "questions": [_boolean(g3_jefe_gate_code, GATE_JEFE)],
        },
        {
            "key": "g3-jefe-followup",
            "description": (
                "Las preguntas siguientes están relacionadas con las "
                "actitudes de las personas que supervisa."
            ),
            "applies_to": "large",
            "visible_when": {"question": g3_jefe_gate_code, "equals": True},
            "questions": [
                _likert(f"g3-{69 + i}", text)
                for i, text in enumerate(GUIA_III_JEFE)
            ],
            "_gate_followups": (
                g3_jefe_gate_code,
                [f"g3-{69 + i}" for i in range(len(GUIA_III_JEFE))],
            ),
        },
    ]
