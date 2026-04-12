from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.responses.models import Answer, SurveySubmission
from apps.surveys.models import Question, SurveyAssignment


def _get_existing_answers(submission):
    if submission is None:
        return {}
    return {a.question_id: a.value for a in submission.answers.all()}


def survey_detail(request, assignment_id):
    assignment = get_object_or_404(
        SurveyAssignment, id=assignment_id, status=SurveyAssignment.Status.ACTIVE
    )
    version = assignment.version
    template = version.template

    sections = list(
        version.sections.prefetch_related("questions__choices").order_by("order")
    )
    unsectioned = list(
        version.questions.filter(section__isnull=True)
        .prefetch_related("choices")
        .order_by("order")
    )

    existing_submission = None
    existing_answers = {}
    if request.user.is_authenticated:
        existing_submission = (
            SurveySubmission.objects.filter(assignment=assignment, user=request.user)
            .prefetch_related("answers")
            .first()
        )
        existing_answers = _get_existing_answers(existing_submission)

    errors = {}

    if request.method == "POST":
        all_questions = []
        for section in sections:
            all_questions.extend(section.questions.order_by("order"))
        all_questions.extend(unsectioned)

        answer_values = {}
        for q in all_questions:
            form_key = f"question_{q.id}"
            qt = q.question_type

            if qt == Question.QuestionType.MULTIPLE_CHOICE:
                value = request.POST.getlist(form_key) or []
            elif qt == Question.QuestionType.BOOLEAN:
                raw = request.POST.get(form_key, "")
                if raw == "true":
                    value = True
                elif raw == "false":
                    value = False
                else:
                    value = None
            elif qt == Question.QuestionType.INTEGER:
                raw = request.POST.get(form_key, "").strip()
                if raw:
                    try:
                        value = int(raw)
                    except ValueError:
                        errors[q.id] = "Please enter a whole number."
                        continue
                else:
                    value = None
            elif qt == Question.QuestionType.DECIMAL:
                raw = request.POST.get(form_key, "").strip()
                if raw:
                    try:
                        value = float(raw)
                    except ValueError:
                        errors[q.id] = "Please enter a number."
                        continue
                else:
                    value = None
            else:
                raw = request.POST.get(form_key, "").strip()
                value = raw or None

            if q.required and value in (None, "", []):
                errors[q.id] = "This question is required."
            else:
                answer_values[q.id] = value

        if not errors:
            user = request.user if request.user.is_authenticated else None
            now = timezone.now()

            if user is not None:
                submission, _ = SurveySubmission.objects.get_or_create(
                    assignment=assignment,
                    user=user,
                    defaults={
                        "status": SurveySubmission.Status.COMPLETED,
                        "completed_at": now,
                    },
                )
                submission.status = SurveySubmission.Status.COMPLETED
                submission.completed_at = now
                submission.save(update_fields=["status", "completed_at"])
            else:
                submission = SurveySubmission.objects.create(
                    assignment=assignment,
                    user=None,
                    status=SurveySubmission.Status.COMPLETED,
                    completed_at=now,
                )

            for question_id, val in answer_values.items():
                Answer.objects.update_or_create(
                    submission=submission,
                    question_id=question_id,
                    defaults={"value": val},
                )
            return redirect("surveys:survey_submitted", assignment_id=assignment_id)

    return render(request, "surveys/survey_detail.html", {
        "assignment": assignment,
        "template": template,
        "version": version,
        "sections": sections,
        "unsectioned": unsectioned,
        "errors": errors,
        "existing_answers": existing_answers,
        "is_edit": existing_submission is not None,
    })


def survey_submitted(request, assignment_id):
    assignment = get_object_or_404(
        SurveyAssignment, id=assignment_id, status=SurveyAssignment.Status.ACTIVE
    )
    return render(request, "surveys/survey_submitted.html", {
        "assignment": assignment,
        "template": assignment.version.template,
    })
