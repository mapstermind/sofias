from django.db import models


class Survey(models.Model):
    """
    A fixed survey instrument (e.g. NOM-035). Owns its modules directly; there is
    no reusable question library and no numbered versions. A material change to a
    published instrument is made by creating a new Survey, not by versioning.
    """

    class Status(models.TextChoices):
        DRAFT = "draft", "Borrador"
        PUBLISHED = "published", "Publicada"
        ARCHIVED = "archived", "Archivada"

    key = models.SlugField(
        "clave",
        max_length=64,
        unique=True,
        help_text="Identificador estable del instrumento, p. ej. 'nom035'.",
    )
    title = models.CharField("título", max_length=255)
    description = models.TextField("descripción", blank=True)
    status = models.CharField(
        "estado", max_length=20, choices=Status.choices, default=Status.DRAFT
    )
    headcount_threshold = models.PositiveIntegerField(
        "umbral de plantilla",
        default=50,
        help_text="Las empresas con más colaboradores que este número reciben la "
        "variante grande; las demás, la pequeña.",
    )
    created_at = models.DateTimeField("fecha de creación", auto_now_add=True)
    updated_at = models.DateTimeField("última actualización", auto_now=True)

    class Meta:
        verbose_name = "encuesta"
        verbose_name_plural = "encuestas"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class Module(models.Model):
    """
    An ordered group of questions within a survey. Modules replace the old
    Section concept and carry applicability: an `all` module is shown to every
    respondent; a `small`/`large` module is shown only to assignments whose
    variant matches.
    """

    class AppliesTo(models.TextChoices):
        ALL = "all", "Todos los participantes"
        SMALL = "small", "Variante pequeña"
        LARGE = "large", "Variante grande"

    survey = models.ForeignKey(
        Survey,
        on_delete=models.CASCADE,
        related_name="modules",
        verbose_name="encuesta",
    )
    key = models.SlugField(
        "clave",
        max_length=64,
        help_text="Identificador estable, único dentro de la encuesta. Lo "
        "referencian las reglas de visible_when (any_in_module).",
    )
    title = models.CharField(
        "título",
        max_length=255,
        blank=True,
        help_text="Encabezado divisor opcional, arriba de las preguntas del "
        "módulo. Déjalo vacío si el módulo solo presenta texto (ver descripción).",
    )
    intro = models.TextField(
        "introducción",
        blank=True,
        help_text="Encabezado opcional arriba del título o divisor, para el texto "
        "introductorio de una guía (p. ej. el nombre formal del cuestionario).",
    )
    description = models.TextField(
        "descripción",
        blank=True,
        help_text="Párrafo opcional. Se muestra como subtítulo bajo el título, o "
        "por sí solo cuando el título está vacío.",
    )
    order = models.PositiveIntegerField("orden", default=0)
    applies_to = models.CharField(
        "aplica a", max_length=10, choices=AppliesTo.choices, default=AppliesTo.ALL
    )
    visible_when = models.JSONField(
        "condición de visibilidad",
        null=True,
        blank=True,
        help_text="Regla opcional de visibilidad condicional. Vacío = siempre visible.",
    )

    class Meta:
        verbose_name = "módulo"
        verbose_name_plural = "módulos"
        ordering = ["order"]
        constraints = [
            models.UniqueConstraint(
                fields=["survey", "key"], name="unique_module_key_per_survey"
            ),
        ]

    def __str__(self):
        return f"{self.survey.key}:{self.key}"


class Question(models.Model):
    class QuestionType(models.TextChoices):
        TEXT = "text", "Texto"
        INTEGER = "integer", "Número entero"
        DECIMAL = "decimal", "Número decimal"
        DATE = "date", "Fecha"
        SINGLE_CHOICE = "single_choice", "Opción única"
        MULTIPLE_CHOICE = "multiple_choice", "Opción múltiple"
        BOOLEAN = "boolean", "Sí / No"
        RATING = "rating", "Calificación"
        LIKERT = "likert", "Escala Likert"

    module = models.ForeignKey(
        Module,
        on_delete=models.CASCADE,
        related_name="questions",
        verbose_name="módulo",
    )
    # Denormalized from module.survey so `code` can be unique per survey at the
    # database level. Kept in sync by save().
    survey = models.ForeignKey(
        Survey,
        on_delete=models.CASCADE,
        related_name="questions",
        editable=False,
        verbose_name="encuesta",
    )
    code = models.SlugField(
        "código",
        max_length=64,
        help_text="Identificador estable dentro de la encuesta, p. ej. 'g3-29'. Es "
        "la llave de integración que consume el motor de valoración.",
    )
    question_type = models.CharField(
        "tipo de pregunta", max_length=20, choices=QuestionType.choices
    )
    text = models.TextField("texto")
    order = models.PositiveIntegerField("orden", default=0)
    config = models.JSONField(
        "configuración",
        default=dict,
        blank=True,
        help_text="Configuración flexible por tipo: min, max, placeholder, labels, etc.",
    )
    visible_when = models.JSONField(
        "condición de visibilidad",
        null=True,
        blank=True,
        help_text="Regla opcional de visibilidad condicional. Vacío = siempre visible.",
    )

    class Meta:
        verbose_name = "pregunta"
        verbose_name_plural = "preguntas"
        ordering = ["order"]
        constraints = [
            models.UniqueConstraint(
                fields=["survey", "code"], name="unique_question_code_per_survey"
            ),
        ]

    def save(self, *args, **kwargs):
        # Keep the denormalized survey consistent with the owning module.
        if self.module_id:
            self.survey_id = self.module.survey_id
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.code}: {self.text[:50]}"


class Choice(models.Model):
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="choices",
        verbose_name="pregunta",
    )
    label = models.CharField("etiqueta", max_length=255)
    value = models.CharField("valor", max_length=255)
    order = models.PositiveIntegerField("orden", default=0)

    class Meta:
        verbose_name = "opción"
        verbose_name_plural = "opciones"
        ordering = ["order"]

    def __str__(self):
        return self.label


class SurveyAssignment(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Activa"
        CLOSED = "closed", "Cerrada"

    class Variant(models.TextChoices):
        SMALL = "small", "Guía II"
        LARGE = "large", "Guía III"

    company = models.ForeignKey(
        "accounts.Company",
        on_delete=models.CASCADE,
        related_name="survey_assignments",
        verbose_name="empresa",
    )
    survey = models.ForeignKey(
        Survey,
        on_delete=models.CASCADE,
        related_name="assignments",
        verbose_name="encuesta",
    )
    variant = models.CharField(
        "variante",
        max_length=10,
        choices=Variant.choices,
        help_text="Se fija al crear la asignación; no cambia si cambia la plantilla.",
    )
    status = models.CharField(
        "estado", max_length=20, choices=Status.choices, default=Status.ACTIVE
    )
    due_date = models.DateField("fecha límite", null=True, blank=True)
    created_at = models.DateTimeField("fecha de creación", auto_now_add=True)

    class Meta:
        verbose_name = "asignación de encuesta"
        verbose_name_plural = "asignaciones de encuesta"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.company} — {self.survey} ({self.variant})"

    @staticmethod
    def resolve_default_variant(company, survey):
        """
        Suggested variant from company headcount vs survey.headcount_threshold.
        Headcount strictly greater than the threshold => large, else small.
        Pure helper; the caller stores the (possibly overridden) result.
        """
        headcount = company.members.count()
        if headcount > survey.headcount_threshold:
            return SurveyAssignment.Variant.LARGE
        return SurveyAssignment.Variant.SMALL

    def modules_for_variant(self):
        """Modules presented for this assignment: `all` plus the variant's."""
        return self.survey.modules.filter(
            models.Q(applies_to=Module.AppliesTo.ALL)
            | models.Q(applies_to=self.variant)
        ).order_by("order")
