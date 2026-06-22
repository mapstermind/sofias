from django.db import models

from apps.nom035 import constants as c


class NDR(models.TextChoices):
    NULO = c.NDR_NULO, "Nulo"
    BAJO = c.NDR_BAJO, "Bajo"
    MEDIO = c.NDR_MEDIO, "Medio"
    ALTO = c.NDR_ALTO, "Alto"
    MUY_ALTO = c.NDR_MUY_ALTO, "Muy alto"


class Severity(models.TextChoices):
    NONE = c.SEV_NONE, "Ninguna"
    LOW = c.SEV_LOW, "Baja"
    MED = c.SEV_MED, "Media"
    HIGH = c.SEV_HIGH, "Alta"


class GroupLevel(models.TextChoices):
    CATEGORIA = c.LEVEL_CATEGORIA, "Categoría"
    DOMINIO = c.LEVEL_DOMINIO, "Dominio"
    DIMENSION = c.LEVEL_DIMENSION, "Dimensión"


class SubmissionScore(models.Model):
    submission = models.OneToOneField(
        "responses.SurveySubmission",
        on_delete=models.CASCADE,
        related_name="nom035_score",
    )
    final_score = models.IntegerField(default=0)
    final_ndr = models.CharField(max_length=10, choices=NDR.choices, default=NDR.NULO)
    guia1_event = models.BooleanField(default=False)
    guia1_followup_count = models.IntegerField(default=0)
    guia1_severity = models.CharField(
        max_length=10, choices=Severity.choices, default=Severity.NONE
    )
    computed_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Score({self.submission_id}={self.final_ndr})"


class GroupScore(models.Model):
    submission_score = models.ForeignKey(
        SubmissionScore, on_delete=models.CASCADE, related_name="groups"
    )
    level = models.CharField(max_length=12, choices=GroupLevel.choices)
    key = models.CharField(max_length=64)
    score = models.IntegerField(default=0)
    ndr = models.CharField(max_length=10, choices=NDR.choices, default=NDR.NULO)

    class Meta:
        unique_together = ("submission_score", "level", "key")
        indexes = [
            models.Index(fields=["submission_score", "level"]),
            models.Index(fields=["level", "ndr"]),
        ]

    def __str__(self):
        return f"{self.level}:{self.key}={self.ndr}"
