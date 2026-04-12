from django.db import models


class QuestionTemplate(models.Model):
    """
    A reusable question in the library. Company-agnostic.

    Use stamp_into() to copy this template into a specific SurveyVersion,
    which creates an independent Question (and its Choices) owned by that version.
    """

    class QuestionType(models.TextChoices):
        SHORT_TEXT = "short_text", "Short Text"
        LONG_TEXT = "long_text", "Long Text"
        INTEGER = "integer", "Integer"
        DECIMAL = "decimal", "Decimal"
        DATE = "date", "Date"
        SINGLE_CHOICE = "single_choice", "Single Choice"
        MULTIPLE_CHOICE = "multiple_choice", "Multiple Choice"
        BOOLEAN = "boolean", "Boolean"
        RATING = "rating", "Rating"

    question_type = models.CharField(max_length=20, choices=QuestionType.choices)
    text = models.TextField()
    config = models.JSONField(
        default=dict,
        blank=True,
        help_text="Flexible config: min, max, placeholder, help_text, validation_rules, etc.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.text

    def stamp_into(self, version, section=None, order=0):
        """
        Copy this template into the given SurveyVersion as an independent Question.
        Also copies all ChoiceTemplates as Choice instances.
        Returns the created Question.
        """
        question = Question.objects.create(
            version=version,
            section=section,
            source=self,
            question_type=self.question_type,
            text=self.text,
            config=self.config,
            order=order,
        )
        for choice_tmpl in self.choices.order_by("order"):
            Choice.objects.create(
                question=question,
                source=choice_tmpl,
                label=choice_tmpl.label,
                value=choice_tmpl.value,
                order=choice_tmpl.order,
            )
        return question


class ChoiceTemplate(models.Model):
    """A selectable option belonging to a QuestionTemplate."""

    question = models.ForeignKey(
        QuestionTemplate, on_delete=models.CASCADE, related_name="choices"
    )
    label = models.CharField(max_length=255)
    value = models.CharField(max_length=255)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.label


class SurveyTemplate(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"
        ARCHIVED = "archived", "Archived"

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.DRAFT
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class SurveyVersion(models.Model):
    template = models.ForeignKey(
        SurveyTemplate, on_delete=models.CASCADE, related_name="versions"
    )
    version_number = models.PositiveIntegerField()
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-version_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["template", "version_number"],
                name="unique_template_version",
            ),
        ]

    def __str__(self):
        return f"{self.template.title} v{self.version_number}"


class Section(models.Model):
    version = models.ForeignKey(
        SurveyVersion, on_delete=models.CASCADE, related_name="sections"
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.title


class Question(models.Model):
    # Alias so existing code (views, workflows) using Question.QuestionType keeps working.
    QuestionType = QuestionTemplate.QuestionType

    version = models.ForeignKey(
        SurveyVersion, on_delete=models.CASCADE, related_name="questions"
    )
    section = models.ForeignKey(
        Section,
        on_delete=models.CASCADE,
        related_name="questions",
        null=True,
        blank=True,
    )
    source = models.ForeignKey(
        QuestionTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="questions",
        help_text="Library template this question was stamped from. Null if created manually.",
    )
    question_type = models.CharField(
        max_length=20, choices=QuestionTemplate.QuestionType.choices
    )
    text = models.TextField()
    order = models.PositiveIntegerField(default=0)
    config = models.JSONField(
        default=dict,
        blank=True,
        help_text="Flexible config: min, max, placeholder, help_text, validation_rules, conditional_visibility, etc.",
    )

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.text


class Choice(models.Model):
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name="choices"
    )
    source = models.ForeignKey(
        ChoiceTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="choices",
        help_text="Library choice this was stamped from. Null if created manually.",
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

    company = models.ForeignKey(
        "accounts.Company", on_delete=models.CASCADE, related_name="survey_assignments"
    )
    version = models.ForeignKey(
        SurveyVersion, on_delete=models.CASCADE, related_name="assignments"
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.ACTIVE
    )
    due_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.company} — {self.version}"
