from django.conf import settings
from django.db import models


class SurveySubmission(models.Model):
    class Status(models.TextChoices):
        IN_PROGRESS = "in_progress", "In Progress"
        COMPLETED = "completed", "Completed"

    assignment = models.ForeignKey(
        "surveys.SurveyAssignment",
        on_delete=models.CASCADE,
        related_name="submissions",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="submissions",
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.IN_PROGRESS
    )
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-started_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "assignment"],
                condition=models.Q(user__isnull=False),
                name="unique_submission_per_user_assignment",
            ),
        ]

    def __str__(self):
        return f"Submission {self.pk} — {self.assignment}"


class Answer(models.Model):
    submission = models.ForeignKey(
        SurveySubmission, on_delete=models.CASCADE, related_name="answers"
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
