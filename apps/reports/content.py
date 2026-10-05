"""Fixed report content: consultancy text shared by every report.

Transcribed from the report template in docs/internal/report-references/. The
recommendations matrix is consultancy content, not part of the norm; the norm's
own action criteria live in apps/nom035 (`action_text`).
"""

from apps.nom035 import _nom035_scoring as cfg
from apps.nom035 import constants as c

# Filled with `.format(company=...)` at render time.
CONFIDENTIALITY_NOTICE = (
    "Los contenidos, recomendaciones y formato de la información han sido "
    "desarrollados por {company} de forma exclusiva para sus clientes y no podrán "
    "transferirse a terceros sin previo aviso de la empresa. Lo anterior no "
    "aplica para entidades gubernamentales, entidades que integran a la "
    "organización contratante o holding internacional de la misma.\n"
    "\n"
    "La información presentada se desarrolló de acuerdo con los procedimientos y "
    "análisis estadísticos especificados por la STPS en la NOM-035-STPS-2018 "
    "publicado en el Diario Oficial de la Federación el 23 de octubre de 2018."
)

OBJECTIVE_PLACEHOLDER = (
    "Texto del objetivo pendiente de definir por la persona responsable de la "
    "evaluación."
)

# {dominio_key: {ndr_level: recommendation}}, one row of the template's table.
RECOMMENDATIONS = {
    cfg.DOM_CONDICIONES: {
        c.NDR_MEDIO: (
            "Actualizar y difundir políticas y procedimientos de seguridad e "
            "higiene; mantener equipos e instalaciones; checklists de "
            "ergonomía; Definir responsables y frecuencia de inspecciones."
        ),
        c.NDR_ALTO: (
            "Capacitar a equipos en cultura preventiva, pausas activas y "
            "reporte de incidentes; reuniones para priorizar correcciones y "
            "comunicar riesgos."
        ),
        c.NDR_MUY_ALTO: (
            "Valorar afectaciones a la salud por condiciones "
            "inseguras/insalubres y canalizar a medicina/psicología; ajustar "
            "temporalmente tareas o puestos."
        ),
    },
    cfg.DOM_CARGA: {
        c.NDR_MEDIO: (
            "Planificar y equilibrar cargas (metas realistas, calendarizar "
            "picos, rotación de tareas); instructivos que definan tiempos y "
            "responsables; monitorear horas extra."
        ),
        c.NDR_ALTO: (
            "Talleres de administración del tiempo, priorización y "
            "productividad saludable; reuniones para redistribuir carga y "
            "establecer pausas. Hacer pausas durante el día para pausas activas"
        ),
        c.NDR_MUY_ALTO: (
            "Atención clínica/psicológica ante síntomas de agotamiento; ajustes "
            "temporales de carga/horario; seguimiento individual."
        ),
    },
    cfg.DOM_CONTROL: {
        c.NDR_MEDIO: (
            "Involucrar a colaboradores en decisiones de organización del "
            "trabajo; ampliar márgenes de autonomía donde el proceso lo "
            "permita; Programas de desarrollo de competencias."
        ),
        c.NDR_ALTO: (
            "Capacitaciones en liderazgo compartido, comunicación asertiva y "
            "autogestión; sesiones de mejora continua por equipos."
        ),
        c.NDR_MUY_ALTO: (
            "Evaluar impacto del bajo control en salud y desempeño; "
            "coaching/terapia breve; ajustes temporales de responsabilidades."
        ),
    },
    cfg.DOM_JORNADA: {
        c.NDR_MEDIO: (
            "Alinear horarios a LFT; política de desconexión; calendarizar "
            "pausas; controlar y justificar horas extra; plan de cobertura de "
            "ausencias para evitar jornadas extendidas."
        ),
        c.NDR_ALTO: (
            "Sensibilización grupal sobre gestión del tiempo; esquemas "
            "flexibles o híbridos acordados con equipos; revisión periódica de "
            "cargas por campaña. Realizar bloqueos en el calendario para "
            "concentrarse y no tener juntas o descansar unos minutos."
        ),
        c.NDR_MUY_ALTO: (
            "Valoración médica/psicológica cuando existan signos de afectación; "
            "ajustes de jornada o reubicación temporal."
        ),
    },
    cfg.DOM_INTERFERENCIA: {
        c.NDR_MEDIO: (
            "Políticas para evitar contacto fuera de horario; permisos ante "
            "emergencias familiares; integración de acciones family-friendly "
            "(p. ej., salas de lactancia); Promover políticas de conciliación "
            "trabajo-familia (definición de horarios, límites de jornada, "
            "permisos por emergencia familiar)."
        ),
        c.NDR_ALTO: (
            "Talleres para manejo de límites saludables y corresponsabilidad; "
            "actividades de integración familiar; acuerdos de equipos sobre "
            "horarios y canales."
        ),
        c.NDR_MUY_ALTO: (
            "Apoyo psicológico individual o familiar cuando haya conflicto "
            "severo trabajo-familia; Ajustes temporales de horario o "
            "flexibilidad de horario."
        ),
    },
    cfg.DOM_LIDERAZGO: {
        c.NDR_MEDIO: (
            "Definir responsabilidades claras, evaluación y reconocimiento del "
            "desempeño; lineamientos de trato digno y no discriminación; "
            "establecer canales formales de comunicación jefe-equipo. "
            "Establecer mecanismos formales de comunicación entre supervisores "
            "y trabajadores (reuniones, buzones, comunicados) y difundir "
            "instrucciones claras ante problemas laborales."
        ),
        c.NDR_ALTO: (
            "Capacitación a mandos en liderazgo positivo, manejo de conflictos, "
            "comunicación y establecimiento de prioridades; feedback 360°."
        ),
        c.NDR_MUY_ALTO: (
            "Intervenciones individuales para líderes o colaboradores con "
            "indicadores de afectación; coaching/terapia y planes de mejora en "
            "liderazgo y comunicación."
        ),
    },
    cfg.DOM_RELACIONES: {
        c.NDR_MEDIO: (
            "Mecanismos para fomentar comunicación transversal (reuniones, "
            "minutas, buzón); reglas de convivencia y respeto; protocolos para "
            "atender problemas operativos. Diseñar y aplicar programas de "
            "capacitación para gerentes y supervisores en prevención de "
            "factores psicosociales y promoción del entorno favorable."
        ),
        c.NDR_ALTO: (
            "Dinámicas de equipo, mediación y manejo de conflictos; círculos de "
            "calidad y seguimiento semestral de clima; Sesiones grupales de "
            "liderazgo consciente, inteligencia emocional y bienestar "
            "organizacional. Realizar juntas caminando en lugar de estar "
            "sentados todo el día promueve la integración y despeja la mente."
        ),
        c.NDR_MUY_ALTO: (
            "Atención psicológica puntual a casos con afectación; acuerdos de "
            "convivencia personalizados y seguimiento; Asesoría o "
            "acompañamiento individual a líderes con equipos en crisis o alta "
            "rotación."
        ),
    },
    cfg.DOM_VIOLENCIA: {
        c.NDR_MEDIO: (
            "Política y protocolo de prevención y atención de violencia "
            "laboral; canales de denuncia; difusión de cero tolerancia; "
            "responsable y procedimiento de seguimiento. Difundir políticas de "
            "cero tolerancia a la violencia laboral, establecer procedimientos "
            "de actuación y responsables de seguimiento."
        ),
        c.NDR_ALTO: (
            "Capacitaciones de sensibilización a todo el personal (Talleres de "
            "sensibilización sobre violencia laboral, equidad, respeto y "
            "cultura de paz laboral) simulacros de actuación; comités de "
            "atención y sesiones extraordinarias ante eventos."
        ),
        c.NDR_MUY_ALTO: (
            "Atención clínica/terapéutica a personas afectadas; protección y "
            "medidas de no repetición; reubicación temporal o medidas de "
            "protección si procede."
        ),
    },
    cfg.DOM_RECONOCIMIENTO: {
        c.NDR_MEDIO: (
            "Implementar mecanismos formales y transparentes de reconocimiento "
            "(criterios, periodicidad, difusión); vincular con desarrollo y "
            "planes de carrera; Realizar detección de necesidades de "
            "capacitación (DNC) al menos cada dos años y vincularla con el "
            "programa de formación."
        ),
        c.NDR_ALTO: (
            "Programas grupales de reconocimiento entre pares; ceremonias y "
            "comunicación interna de logros; talleres de metas y feedback; "
            "Promover la participación de los trabajadores en identificación de "
            "sus necesidades de capacitación y cursos relacionados con sus "
            "funciones."
        ),
        c.NDR_MUY_ALTO: (
            "Acompañamiento individual para casos de desmotivación con "
            "afectación a la salud; Planes de desarrollo personalizados; Apoyo "
            "individual para trabajadores con bajo desempeño o dificultades de "
            "adaptación mediante tutorías o coaching."
        ),
    },
    cfg.DOM_PERTENENCIA: {
        c.NDR_MEDIO: (
            "Manual y rituales de bienvenida; campañas de orgullo corporativo; "
            "actividades de integración; comunicar cambios organizacionales con "
            "oportunidad; Fomentar la colaboración y el apoyo mutuo entre "
            "trabajadores, supervisores y gerentes mediante políticas y "
            "prácticas organizacionales."
        ),
        c.NDR_ALTO: (
            "Eventos y dinámicas de pertenencia por equipos; "
            "mentorías/apadrinamiento; voluntariado corporativo; Reuniones "
            "semestrales o anuales de seguimiento y promoción de ayuda mutua y "
            "actividades culturales o deportivas."
        ),
        c.NDR_MUY_ALTO: (
            "Intervenciones individuales ante señales de aislamiento o "
            "ansiedad; canalización y planes de reintegración."
        ),
    },
}

# (term, definition), in the template's order.
GLOSSARY = (
    (
        "Acontecimiento traumático severo",
        "Aquel experimentado durante o con motivo del trabajo que se caracteriza por "
        "la ocurrencia de la muerte o que representa un peligro real para la "
        "integridad física de una o varias personas y que puede generar trastorno de "
        "estrés postraumático para quien lo sufre o lo presencia. Algunos ejemplos "
        "son: explosiones, derrumbes, incendios de gran magnitud; accidentes graves "
        "o mortales, asaltos con violencia, secuestros y homicidios, entre otros.",
    ),
    (
        "Apoyo social",
        "Las acciones para mejorar las relaciones sociales en el trabajo en las que "
        "se promueve el apoyo mutuo en la solución de problemas de trabajo entre "
        "trabajadores, superiores y/o subordinados. Algunos ejemplos de medidas para "
        "constituir un apoyo social práctico y oportuno en el lugar de trabajo son: "
        "afianzar la relación supervisores-trabajadores; propiciar la ayuda mutua "
        "entre los trabajadores; fomentar las actividades culturales y del deporte, "
        "y proporcionar ayuda directa cuando sea necesario, entre otros.",
    ),
    (
        "Autoridad laboral",
        "Las unidades administrativas competentes de la Secretaría que realizan "
        "funciones de inspección y vigilancia en materia de seguridad y salud en el "
        "trabajo, y las correspondientes de las entidades federativas, que actúen en "
        "auxilio de aquéllas.",
    ),
    (
        "Centro de trabajo",
        "El lugar o lugares, tales como edificios, locales, instalaciones y áreas, "
        "donde se realicen actividades de explotación, aprovechamiento, producción, "
        "comercialización, transporte y almacenamiento o prestación de servicios, en "
        "los que laboren personas que estén sujetas a una relación de trabajo.",
    ),
    (
        "Diagnóstico de seguridad y salud en el trabajo",
        "La identificación de las condiciones inseguras o peligrosas; de los agentes "
        "físicos, químicos o biológicos o de los factores de riesgo ergonómico o "
        "psicosocial capaces de modificar las condiciones del ambiente laboral; de "
        "los peligros circundantes al centro de trabajo, así como de los "
        "requerimientos normativos en materia de seguridad y salud en el trabajo que "
        "resulten aplicables.",
    ),
    (
        "Entorno Organizacional Favorable",
        "Aquel en el que se promueve el sentido de pertenencia de los trabajadores a "
        "la empresa; la formación para la adecuada realización de las tareas "
        "encomendadas; la definición precisa de responsabilidades para los "
        "trabajadores del centro de trabajo; la participación proactiva y "
        "comunicación entre trabajadores; la distribución adecuada de cargas de "
        "trabajo, con jornadas de trabajo regulares conforme a la Ley Federal del "
        "Trabajo, y la evaluación y el reconocimiento del desempeño.",
    ),
    (
        "Factores de Riesgo Psicosocial",
        "Aquellos que pueden provocar trastornos de ansiedad, no orgánicos del ciclo "
        "sueño-vigilia y de estrés grave y de adaptación, derivado de la naturaleza "
        "de las funciones del puesto de trabajo, el tipo de jornada de trabajo y la "
        "exposición a acontecimientos traumáticos severos o a actos de violencia "
        "laboral al trabajador, por el trabajo desarrollado.\n"
        "Comprenden las condiciones peligrosas e inseguras en el ambiente de "
        "trabajo; las cargas de trabajo cuando exceden la capacidad del trabajador; "
        "la falta de control sobre el trabajo (posibilidad de influir en la "
        "organización y desarrollo del trabajo cuando el proceso lo permite); las "
        "jornadas de trabajo superiores a las previstas en la Ley Federal del "
        "Trabajo, rotación de turnos que incluyan turno nocturno y turno nocturno "
        "sin períodos de recuperación y descanso; interferencia en la relación "
        "trabajo-familia, y el liderazgo negativo y las relaciones negativas en el "
        "trabajo.",
    ),
    (
        "Medidas de prevención y acciones de control",
        "Aquellas acciones que se adoptan para prevenir y/o mitigar a los factores "
        "de riesgo psicosocial y, en su caso, para eliminar las prácticas opuestas "
        "al entorno organizacional favorable y los actos de violencia laboral, así "
        "como las acciones implementadas para darles seguimiento.",
    ),
    (
        "Política de prevención de riesgos psicosociales",
        "La declaración de principios y compromisos que establece el patrón para "
        "prevenir los factores de riesgo psicosocial y la violencia laboral, y para "
        "la promoción de un entorno organizacional favorable, con el objeto de "
        "desarrollar una cultura en la que se procure el trabajo digno o decente, y "
        "la mejora continua de las condiciones de trabajo.",
    ),
    (
        "Trabajador",
        "La persona física que presta a otra, física o moral, un trabajo personal "
        "subordinado.",
    ),
    (
        "Trabajo",
        "Toda actividad humana, intelectual o material, independientemente del grado "
        "de preparación técnica requerido por cada profesión u oficio.",
    ),
    (
        "Violencia laboral",
        "Aquellos actos de hostigamiento, acoso o malos tratos en contra del "
        "trabajador, que pueden dañar su integridad o salud.",
    ),
)

# (heading, text); article 43's fractions are one per line.
LFT_ARTICLES = (
    (
        "Artículo 43",
        "Respecto de los Factores de Riesgo Psicosocial del Centro de Trabajo, los "
        "patrones deberán:\n"
        "I. Identificar y analizar los puestos de trabajo con Riesgo psicosocial por "
        "la naturaleza de sus funciones o el tipo de jornada laboral;\n"
        "II. Identificar a los trabajadores que fueron sujetos a acontecimientos "
        "traumáticos severos o a actos de Violencia Laboral, y valorarlos "
        "clínicamente;\n"
        "III. Adoptar las medidas preventivas pertinentes para mitigar los Factores "
        "de Riesgo Psicosocial;\n"
        "IV. Practicar exámenes o evaluaciones clínicas al Personal Ocupacionalmente "
        "Expuesto a Factores de Riesgo Psicosocial, según se requiera;\n"
        "V. Informar a los trabajadores sobre las posibles alteraciones a la salud "
        "por la exposición a los Factores de Riesgo Psicosocial, y\n"
        "VI. Llevar los registros sobre las medidas preventivas adoptadas y los "
        "resultados de los exámenes o evaluaciones clínicas.",
    ),
    (
        "Artículo 473",
        "Riesgos de trabajo son los accidentes y enfermedades a que están expuestos "
        "los trabajadores en ejercicio o con motivo del trabajo.",
    ),
    (
        "Artículo 474",
        "El accidente de trabajo es toda lesión orgánica o perturbación funcional, "
        "inmediata o posterior, o la muerte, producida repentinamente en ejercicio, "
        "o con motivo del trabajo, cualesquiera que sean el lugar y el tiempo en que "
        "se preste. Quedan incluidos en la definición anterior los accidentes que se "
        "produzcan al trasladarse el trabajador directamente de su domicilio al "
        "lugar del trabajo y de éste a aquél.",
    ),
    (
        "Artículo 475",
        "La enfermedad de trabajo es todo estado patológico derivado de la acción "
        "continuada de una causa que tenga su origen o motivo en el trabajo o en el "
        "medio en que el trabajador se vea obligado a prestar sus servicios.",
    ),
)
