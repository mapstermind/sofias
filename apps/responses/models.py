from django.conf import settings
from django.db import models


class SurveySubmission(models.Model):
    class Status(models.TextChoices):
        IN_PROGRESS = "in_progress", "En progreso"
        COMPLETED = "completed", "Completado"

    assignment = models.ForeignKey(
        "surveys.SurveyAssignment",
        on_delete=models.CASCADE,
        related_name="submissions",
        verbose_name="asignación",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="submissions",
        verbose_name="colaborador",
    )
    status = models.CharField(
        "estado", max_length=20, choices=Status.choices, default=Status.IN_PROGRESS
    )
    started_at = models.DateTimeField("fecha de inicio", auto_now_add=True)
    completed_at = models.DateTimeField("fecha de término", null=True, blank=True)

    class Meta:
        verbose_name = "envío de encuesta"
        verbose_name_plural = "envíos de encuesta"
        ordering = ["-started_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "assignment"],
                condition=models.Q(user__isnull=False),
                name="unique_submission_per_user_assignment",
            ),
        ]

    def __str__(self):
        return f"Envío {self.pk} — {self.assignment}"


class Answer(models.Model):
    submission = models.ForeignKey(
        SurveySubmission,
        on_delete=models.CASCADE,
        related_name="answers",
        verbose_name="envío",
    )
    question = models.ForeignKey(
        "surveys.Question",
        on_delete=models.CASCADE,
        related_name="answers",
        verbose_name="pregunta",
    )
    value = models.JSONField(
        "valor",
        help_text="Valor de la respuesta; su interpretación depende del tipo de "
        "pregunta.",
    )

    class Meta:
        verbose_name = "respuesta"
        verbose_name_plural = "respuestas"
        constraints = [
            models.UniqueConstraint(
                fields=["submission", "question"],
                name="unique_answer_per_question",
            ),
        ]

    def __str__(self):
        return (
            f"Respuesta a la pregunta {self.question_id} del envío {self.submission_id}"
        )
