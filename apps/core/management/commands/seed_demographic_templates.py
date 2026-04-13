from django.core.management.base import BaseCommand

from apps.surveys.models import ChoiceTemplate, QuestionTemplate

QUESTIONS = [
    {
        "text": "Género.",
        "question_type": QuestionTemplate.QuestionType.SINGLE_CHOICE,
        "choices": ["Hombre", "Mujer", "Otro", "Prefiero no responder"],
    },
    {
        "text": "Edad.",
        "question_type": QuestionTemplate.QuestionType.INTEGER,
        "choices": [],
    },
    {
        "text": "Segmento.",
        "question_type": QuestionTemplate.QuestionType.SINGLE_CHOICE,
        "choices": [
            "Accounting Operations and Reporting - Finance",
            "Archivo y Mensajería",
            "BDMC",
            "Client Revenue - Finance",
            "Compliance",
            "Employment Compensation",
            "Global Mobility",
            "International Commercial",
            "IP-Tech",
            "IT Systems",
            "Knowledge Management",
            "Litigation",
            "Office Managers",
            "Procurement to Pay (P2P) - Finance",
            "Recepción",
            "Recruitment",
            "Secretarial",
            "Social Responsibility",
            "Talent Management",
            "Tax",
            "Transactional",
            "Otro",
        ],
    },
    {
        "text": "Línea de trabajo.",
        "question_type": QuestionTemplate.QuestionType.SINGLE_CHOICE,
        "choices": [
            "Analista / Auxiliar",
            "Archivista / Mensajero",
            "Asistente Secretarial",
            "Associate - Junior",
            "Associate - Mid-Level",
            "Associate - Senior",
            "Coordinador / Coordinador Sr. / Supervisor / Executive",
            "Counsel",
            "Director",
            "Gerente / Gerente Sr. / Senior Executive",
            "Knowledge Attorney / Research Librarian / Translator",
            "Law Clerk (Half time / Full time)",
            "National Partner",
            "Principal",
            "Recepcionista",
            "Specialist / Paralegal / Support Specialist",
            "Otro",
        ],
    },
]


class Command(BaseCommand):
    help = "Seed the question template library with demographic questions"

    def handle(self, *args, **options):
        created_count = 0
        skipped_count = 0

        for q in QUESTIONS:
            template, created = QuestionTemplate.objects.get_or_create(
                text=q["text"],
                question_type=q["question_type"],
            )

            if created:
                created_count += 1
                for order, label in enumerate(q["choices"]):
                    ChoiceTemplate.objects.create(
                        question=template,
                        label=label,
                        value=label,
                        order=order,
                    )
            else:
                skipped_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Done. Created: {created_count}, Skipped (already existed): {skipped_count}."
            )
        )
