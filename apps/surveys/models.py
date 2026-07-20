from django.db import models


class Survey(models.Model):
    """
    A fixed survey instrument (e.g. NOM-035). Owns its modules directly; there is
    no reusable question library and no numbered versions. A material change to a
    published instrument is made by creating a new Survey, not by versioning.
    """

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"
        ARCHIVED = "archived", "Archived"

    key = models.SlugField(
        max_length=64,
        unique=True,
        help_text="Stable identifier for the instrument, e.g. 'nom035'.",
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.DRAFT
    )
    headcount_threshold = models.PositiveIntegerField(
        default=50,
        help_text="Companies with headcount strictly greater than this get the "
        "'large' variant, otherwise 'small'.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
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
        ALL = "all", "All respondents"
        SMALL = "small", "Small variant"
        LARGE = "large", "Large variant"

    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name="modules")
    key = models.SlugField(
        max_length=64,
        help_text="Stable identifier, unique within the survey. Referenced by "
        "visible_when rules (any_in_module).",
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)
    applies_to = models.CharField(
        max_length=10, choices=AppliesTo.choices, default=AppliesTo.ALL
    )
    visible_when = models.JSONField(
        null=True,
        blank=True,
        help_text="Optional conditional-visibility rule. Null = always visible.",
    )

    class Meta:
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
        TEXT = "text", "Text"
        INTEGER = "integer", "Integer"
        DECIMAL = "decimal", "Decimal"
        DATE = "date", "Date"
        SINGLE_CHOICE = "single_choice", "Single Choice"
        MULTIPLE_CHOICE = "multiple_choice", "Multiple Choice"
        BOOLEAN = "boolean", "Boolean"
        RATING = "rating", "Rating"
        LIKERT = "likert", "Likert Scale"

    module = models.ForeignKey(
        Module, on_delete=models.CASCADE, related_name="questions"
    )
    # Denormalized from module.survey so `code` can be unique per survey at the
    # database level. Kept in sync by save().
    survey = models.ForeignKey(
        Survey, on_delete=models.CASCADE, related_name="questions", editable=False
    )
    code = models.SlugField(
        max_length=64,
        help_text="Stable per-survey identifier, e.g. 'g3-29'. The integration "
        "key for the future valuation engine.",
    )
    question_type = models.CharField(max_length=20, choices=QuestionType.choices)
    text = models.TextField()
    order = models.PositiveIntegerField(default=0)
    config = models.JSONField(
        default=dict,
        blank=True,
        help_text="Flexible per-type config: min, max, placeholder, labels, etc.",
    )
    visible_when = models.JSONField(
        null=True,
        blank=True,
        help_text="Optional conditional-visibility rule. Null = always visible.",
    )

    class Meta:
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
        Question, on_delete=models.CASCADE, related_name="choices"
    )
    label = models.CharField(max_length=255)
    value = models.CharField(max_length=255)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.label


class SurveyAssignment(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        CLOSED = "closed", "Closed"

    class Variant(models.TextChoices):
        SMALL = "small", "Guía II"
        LARGE = "large", "Guía III"

    company = models.ForeignKey(
        "accounts.Company",
        on_delete=models.CASCADE,
        related_name="survey_assignments",
    )
    survey = models.ForeignKey(
        Survey, on_delete=models.CASCADE, related_name="assignments"
    )
    variant = models.CharField(
        max_length=10,
        choices=Variant.choices,
        help_text="Frozen at creation; does not change if headcount changes.",
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.ACTIVE
    )
    due_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
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
