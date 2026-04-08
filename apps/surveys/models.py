from django.db import models


class Survey(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"
        CLOSED = "closed", "Closed"

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
    survey = models.ForeignKey(
        Survey, on_delete=models.CASCADE, related_name="versions"
    )
    version_number = models.PositiveIntegerField()
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-version_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["survey", "version_number"],
                name="unique_survey_version",
            ),
        ]

    def __str__(self):
        return f"{self.survey.title} v{self.version_number}"


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
    question_type = models.CharField(max_length=20, choices=QuestionType.choices)
    text = models.TextField()
    required = models.BooleanField(default=True)
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
    label = models.CharField(max_length=255)
    value = models.CharField(max_length=255)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.label
