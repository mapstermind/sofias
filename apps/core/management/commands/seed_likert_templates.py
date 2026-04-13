from django.core.management.base import BaseCommand

from apps.surveys.models import QuestionTemplate

LIKERT_STATEMENTS = [
    "El espacio donde trabajo me permite realizar mis actividades de manera segura e higiénica.",
    "Mi trabajo me exige hacer mucho esfuerzo físico.",
    "Me preocupa sufrir un accidente en mi trabajo.",
    "Considero que en mi trabajo se aplican las normas de seguridad y salud en el trabajo.",
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
    "Considero que el tiempo dedicado al trabajo perjudica mis actividades familiares o personales.",
    "Debo atender asuntos de trabajo cuando estoy en casa.",
    "Pienso en mis actividades familiares o personales cuando estoy en el trabajo.",
    "Pienso que mis responsabilidades familiares afectan mi trabajo.",
    "Mi trabajo me permite desarrollar nuevas habilidades.",
    "En mi trabajo puedo aspirar a un mejor puesto.",
    "Durante mi jornada de trabajo puedo tomar pausas cuando las necesito.",
    "Puedo decidir cuánto trabajo realizo durante la jornada laboral.",
    "Puedo decidir la velocidad a la que realizo mis actividades en el trabajo.",
    "Puedo cambiar el orden de las actividades que realizo en mi trabajo.",
    "Los cambios que se presentan en mi trabajo dificultan mi labor.",
    "Cuando se presentan cambios en mi trabajo se tienen en cuenta mis ideas o aportaciones.",
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
    "Cuando realizamos trabajo en equipo los compañeros colaboran.",
    "Mis compañeros de trabajo me ayudan cuando tengo dificultades.",
    "Me informan sobre lo que hago bien en mi trabajo.",
    "La forma en que evalúan mi trabajo me ayuda a mejorar mi desempeño.",
    "En mi centro de trabajo me pagan a tiempo mi salario.",
    "El pago que recibo corresponde al trabajo que realizo.",
    "Si obtengo los resultados esperados en mi trabajo me recompensan o reconocen.",
    "Las personas que hacen bien el trabajo pueden crecer laboralmente.",
    "Considero que mi trabajo es estable.",
    "En mi trabajo existe una alta rotación de personal.",
    "Siento orgullo de laborar en este centro de trabajo.",
    "Me siento comprometido con mi trabajo.",
    "En mi trabajo puedo expresarme libremente sin interrupciones.",
    "Recibo críticas constantes a mi persona y/o trabajo.",
    "Recibo burlas, calumnias, difamaciones, humillaciones o ridiculizaciones en el trabajo.",
    "Se ignora mi presencia o se me excluye de reuniones y de la toma de decisiones.",
    "Se manipulan las situaciones de trabajo para hacerme parecer un mal trabajador.",
    "Se ignoran mis logros laborales y se atribuyen a otros trabajadores.",
    "Me bloquean o impiden las oportunidades de ascenso o mejora en mi trabajo.",
    "He presenciado actos de violencia en mi centro de trabajo.",
    "Atiendo clientes o usuarios muy enojados.",
    "Mi trabajo me exige atender personas muy necesitadas de ayuda o enfermas.",
    "Para hacer mi trabajo debo expresar sentimientos distintos a los que siento.",
    "Mi trabajo me exige atender situaciones de violencia.",
    "En mi trabajo comunican tarde los asuntos relevantes.",
    "En mi trabajo dificultan el logro de los resultados esperados.",
    "En mi trabajo cooperan poco cuando se necesita.",
    "En mi trabajo ignoran las sugerencias para mejorar.",
]


class Command(BaseCommand):
    help = "Seed the question template library with 72 Likert-scale statements"

    def add_arguments(self, parser):
        parser.add_argument(
            "--skip-existing",
            action="store_true",
            default=True,
            help="Skip statements that already exist (default: True)",
        )

    def handle(self, *args, **options):
        created_count = 0
        skipped_count = 0

        for text in LIKERT_STATEMENTS:
            _, created = QuestionTemplate.objects.get_or_create(
                text=text,
                question_type=QuestionTemplate.QuestionType.LIKERT,
            )
            if created:
                created_count += 1
            else:
                skipped_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Done. Created: {created_count}, Skipped (already existed): {skipped_count}."
            )
        )
