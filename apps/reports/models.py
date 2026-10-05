from django.conf import settings
from django.db import models


class Report(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Borrador"
        PUBLISHED = "published", "Publicado"

    assignment = models.OneToOneField(
        "surveys.SurveyAssignment",
        on_delete=models.CASCADE,
        related_name="report",
        verbose_name="asignación",
    )
    status = models.CharField(
        "estado", max_length=10, choices=Status.choices, default=Status.DRAFT
    )
    snapshot = models.JSONField("datos publicados", null=True, blank=True)
    published_at = models.DateTimeField("fecha de publicación", null=True, blank=True)
    published_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        verbose_name="publicado por",
    )
    issued_in = models.CharField("lugar de emisión", max_length=120, blank=True)
    activities_summary = models.TextField("principales actividades", blank=True)
    headcount_in_person = models.PositiveIntegerField(
        "personal presencial", null=True, blank=True
    )
    headcount_home_office = models.PositiveIntegerField(
        "personal en home office", null=True, blank=True
    )
    headcount_hybrid = models.PositiveIntegerField(
        "personal híbrido", null=True, blank=True
    )
    evaluator_name = models.CharField(
        "responsable de la evaluación", max_length=200, blank=True
    )
    evaluator_license = models.CharField(
        "cédula profesional", max_length=40, blank=True
    )
    additional_recommendations = models.TextField(
        "recomendaciones adicionales", blank=True
    )
    conclusions = models.TextField("conclusiones", blank=True)
    created_at = models.DateTimeField("fecha de alta", auto_now_add=True)
    updated_at = models.DateTimeField("última actualización", auto_now=True)

    class Meta:
        verbose_name = "reporte"
        verbose_name_plural = "reportes"

    def __str__(self):
        return f"Reporte de {self.assignment}"

    @property
    def headcount_total(self):
        counts = [
            n
            for n in (
                self.headcount_in_person,
                self.headcount_home_office,
                self.headcount_hybrid,
            )
            if n is not None
        ]
        return sum(counts) if counts else None


class ReportSignatory(models.Model):
    report = models.ForeignKey(
        Report,
        on_delete=models.CASCADE,
        related_name="signatories",
        verbose_name="reporte",
    )
    title = models.CharField("cargo", max_length=200)
    name = models.CharField("nombre", max_length=200)
    order = models.PositiveSmallIntegerField("orden", default=0)

    class Meta:
        verbose_name = "responsable de la empresa"
        verbose_name_plural = "responsables de la empresa"
        ordering = ("order", "pk")

    def __str__(self):
        return f"{self.title}: {self.name}"
