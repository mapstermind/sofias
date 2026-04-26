from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.responses.models import Answer, SurveySubmission
from apps.surveys.models import Question, SurveyAssignment


def _get_existing_answers(submission):
    if submission is None:
        return {}
    return {a.question_id: a.value for a in submission.answers.all()}


def survey_detail(request, assignment_id):
    assignment = get_object_or_404(SurveyAssignment, id=assignment_id)

    if assignment.status == SurveyAssignment.Status.CLOSED:
        return redirect("core:home")

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
        if existing_submission and existing_submission.status == SurveySubmission.Status.COMPLETED:
            return redirect("core:home")
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
            elif qt == Question.QuestionType.LIKERT:
                raw = request.POST.get(form_key, "").strip()
                if raw:
                    try:
                        value = int(raw)
                    except ValueError:
                        errors[q.id] = "Please select a valid option."
                        continue
                else:
                    value = None
            else:
                raw = request.POST.get(form_key, "").strip()
                value = raw or None

            answer_values[q.id] = value

        if not errors:
            user = request.user if request.user.is_authenticated else None
            now = timezone.now()
            all_answered = all(val is not None for val in answer_values.values())
            new_status = (
                SurveySubmission.Status.COMPLETED
                if all_answered
                else SurveySubmission.Status.IN_PROGRESS
            )

            if user is not None:
                submission, _ = SurveySubmission.objects.get_or_create(
                    assignment=assignment,
                    user=user,
                    defaults={"status": new_status},
                )
                submission.status = new_status
                submission.completed_at = now if all_answered else None
                submission.save(update_fields=["status", "completed_at"])
            else:
                submission = SurveySubmission.objects.create(
                    assignment=assignment,
                    user=None,
                    status=new_status,
                    completed_at=now if all_answered else None,
                )

            for question_id, val in answer_values.items():
                if val is None:
                    Answer.objects.filter(
                        submission=submission, question_id=question_id
                    ).delete()
                else:
                    Answer.objects.update_or_create(
                        submission=submission,
                        question_id=question_id,
                        defaults={"value": val},
                    )

            if all_answered:
                return redirect("surveys:survey_submitted", assignment_id=assignment_id)
            return redirect(f"{request.path}?saved=1")

    all_q_ids = list(version.questions.values_list("id", flat=True))
    total_questions = len(all_q_ids)
    answered_count = sum(
        1 for qid in all_q_ids if existing_answers.get(qid) not in (None, "", [])
    )

    return render(
        request,
        "surveys/survey_detail.html",
        {
            "assignment": assignment,
            "template": template,
            "version": version,
            "sections": sections,
            "unsectioned": unsectioned,
            "errors": errors,
            "existing_answers": existing_answers,
            "is_edit": existing_submission is not None,
            "total_questions": total_questions,
            "answered_count": answered_count,
        },
    )


@require_POST
def autosave_survey(request, assignment_id):
    """AJAX endpoint — saves a single changed field without altering submission status."""
    if not request.user.is_authenticated:
        return JsonResponse({"ok": False, "error": "unauthenticated"}, status=401)

    assignment = get_object_or_404(SurveyAssignment, id=assignment_id)
    if assignment.status == SurveyAssignment.Status.CLOSED:
        return JsonResponse({"ok": False, "error": "closed"}, status=403)

    question_ids = []
    for key in request.POST:
        if key.startswith("question_"):
            try:
                question_ids.append(int(key[len("question_") :]))
            except ValueError:
                pass

    if not question_ids:
        return JsonResponse({"ok": True})

    questions = {q.id: q for q in Question.objects.filter(id__in=question_ids)}

    answer_values = {}
    for qid in question_ids:
        q = questions.get(qid)
        if q is None:
            continue
        form_key = f"question_{qid}"
        qt = q.question_type

        if qt == Question.QuestionType.MULTIPLE_CHOICE:
            vals = request.POST.getlist(form_key)
            value = vals if vals else None
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
            try:
                value = int(raw) if raw else None
            except ValueError:
                continue
        elif qt == Question.QuestionType.DECIMAL:
            raw = request.POST.get(form_key, "").strip()
            try:
                value = float(raw) if raw else None
            except ValueError:
                continue
        elif qt == Question.QuestionType.LIKERT:
            raw = request.POST.get(form_key, "").strip()
            try:
                value = int(raw) if raw else None
            except ValueError:
                continue
        else:
            raw = request.POST.get(form_key, "").strip()
            value = raw or None

        answer_values[qid] = value

    submission, _ = SurveySubmission.objects.get_or_create(
        assignment=assignment,
        user=request.user,
        defaults={"status": SurveySubmission.Status.IN_PROGRESS},
    )

    for question_id, val in answer_values.items():
        if val is None:
            Answer.objects.filter(
                submission=submission, question_id=question_id
            ).delete()
        else:
            Answer.objects.update_or_create(
                submission=submission,
                question_id=question_id,
                defaults={"value": val},
            )

    return JsonResponse({"ok": True})


def survey_submitted(request, assignment_id):
    assignment = get_object_or_404(SurveyAssignment, id=assignment_id)
    return render(
        request,
        "surveys/survey_submitted.html",
        {
            "assignment": assignment,
            "template": assignment.version.template,
        },
    )
