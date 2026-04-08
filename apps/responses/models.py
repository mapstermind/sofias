from django.db import models


class Submission(models.Model):
    class Status(models.TextChoices):
        IN_PROGRESS = "in_progress", "In Progress"
        COMPLETED = "completed", "Completed"

    version = models.ForeignKey(
        "surveys.SurveyVersion",
        on_delete=models.CASCADE,
        related_name="submissions",
    )
    respondent_identifier = models.CharField(max_length=255, blank=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.IN_PROGRESS
    )
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-started_at"]

    def __str__(self):
        return f"Submission {self.pk} – {self.version}"


class Answer(models.Model):
    submission = models.ForeignKey(
        Submission, on_delete=models.CASCADE, related_name="answers"
    )
    question = models.ForeignKey(
        "surveys.Question", on_delete=models.CASCADE, related_name="answers"
    )
    value = models.JSONField(
        help_text="Answer value; interpretation depends on question.question_type."
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["submission", "question"],
                name="unique_answer_per_question",
            ),
        ]

    def __str__(self):
        return f"Answer to Q{self.question_id} in Submission {self.submission_id}"
