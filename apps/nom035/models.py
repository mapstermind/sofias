from django.db import models

from apps.nom035 import constants as c


class NDR(models.TextChoices):
    NULO = c.NDR_NULO, "Nulo"
    BAJO = c.NDR_BAJO, "Bajo"
    MEDIO = c.NDR_MEDIO, "Medio"
    ALTO = c.NDR_ALTO, "Alto"
    MUY_ALTO = c.NDR_MUY_ALTO, "Muy alto"


class GroupLevel(models.TextChoices):
    # NOM-035 defines NDR thresholds only at dominio/categoría/final. Dimensión is
    # stored score-only (no NDR) so the per-employee panel can show it.
    CATEGORIA = c.LEVEL_CATEGORIA, "Categoría"
    DOMINIO = c.LEVEL_DOMINIO, "Dominio"
    DIMENSION = c.LEVEL_DIMENSION, "Dimensión"


class SubmissionScore(models.Model):
    submission = models.OneToOneField(
        "responses.SurveySubmission",
        on_delete=models.CASCADE,
        related_name="nom035_score",
        verbose_name="envío",
    )
    final_score = models.IntegerField("puntaje final", default=0)
    final_ndr = models.CharField(
        "nivel de riesgo final", max_length=10, choices=NDR.choices, default=NDR.NULO
    )
    # Official Guía I clinical-referral outcome (binary); see scoring.guia1_positive.
    guia1_positive = models.BooleanField("positivo en Guía I", default=False)
    computed_at = models.DateTimeField("fecha de cálculo", auto_now=True)

    class Meta:
        verbose_name = "valoración"
        verbose_name_plural = "valoraciones"

    def __str__(self):
        return f"Valoración({self.submission_id}={self.final_ndr})"


class GroupScore(models.Model):
    submission_score = models.ForeignKey(
        SubmissionScore,
        on_delete=models.CASCADE,
        related_name="groups",
        verbose_name="valoración",
    )
    level = models.CharField("nivel", max_length=12, choices=GroupLevel.choices)
    key = models.CharField("clave", max_length=64)
    score = models.IntegerField("puntaje", default=0)
    ndr = models.CharField(
        "nivel de riesgo",
        max_length=10,
        choices=NDR.choices,
        default=NDR.NULO,
        blank=True,
    )

    class Meta:
        verbose_name = "puntaje por grupo"
        verbose_name_plural = "puntajes por grupo"
        unique_together = ("submission_score", "level", "key")
        indexes = [
            models.Index(fields=["submission_score", "level"]),
            models.Index(fields=["level", "ndr"]),
        ]

    def __str__(self):
        return f"{self.level}:{self.key}={self.ndr}"
