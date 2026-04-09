from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.responses.models import Answer, Submission
from apps.surveys.models import Question, Survey


def survey_detail(request, survey_id):
    survey = get_object_or_404(Survey, id=survey_id, status=Survey.Status.PUBLISHED)
    version = survey.versions.order_by("-version_number").first()

    sections = list(
        version.sections.prefetch_related("questions__choices").order_by("order")
    )
    unsectioned = list(
        version.questions.filter(section__isnull=True)
        .prefetch_related("choices")
        .order_by("order")
    )

    # errors keyed by question.id (int) so templates can do `question.id in errors`
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
            submission = Submission.objects.create(
                version=version,
                status=Submission.Status.COMPLETED,
                completed_at=timezone.now(),
            )
            for question_id, val in answer_values.items():
                Answer.objects.create(
                    submission=submission,
                    question_id=question_id,
                    value=val,
                )
            return redirect("surveys:survey_submitted", survey_id=survey_id)

    return render(request, "surveys/survey_detail.html", {
        "survey": survey,
        "version": version,
        "sections": sections,
        "unsectioned": unsectioned,
        "errors": errors,
    })


def survey_submitted(request, survey_id):
    survey = get_object_or_404(Survey, id=survey_id, status=Survey.Status.PUBLISHED)
    return render(request, "surveys/survey_submitted.html", {"survey": survey})
