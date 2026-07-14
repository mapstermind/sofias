from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.responses.models import Answer, SurveySubmission
from apps.surveys.models import Question, SurveyAssignment
from apps.surveys.visibility import visible_questions


def _parse_value(question, post):
    """Parse the posted value for a single question by its type.

    Returns (value, error). `error` is a message string or None. A None value
    with no error means "unanswered". Shared by survey_detail and autosave so the
    two never diverge.
    """
    form_key = f"question_{question.id}"
    qt = question.question_type

    if qt == Question.QuestionType.MULTIPLE_CHOICE:
        vals = post.getlist(form_key)
        return (vals or None), None
    if qt == Question.QuestionType.BOOLEAN:
        raw = post.get(form_key, "")
        if raw == "true":
            return True, None
        if raw == "false":
            return False, None
        return None, None
    if qt == Question.QuestionType.INTEGER:
        raw = post.get(form_key, "").strip()
        if not raw:
            return None, None
        try:
            return int(raw), None
        except ValueError:
            return None, "Please enter a whole number."
    if qt == Question.QuestionType.DECIMAL:
        raw = post.get(form_key, "").strip()
        if not raw:
            return None, None
        try:
            return float(raw), None
        except ValueError:
            return None, "Please enter a number."
    if qt == Question.QuestionType.LIKERT:
        raw = post.get(form_key, "").strip()
        if not raw:
            return None, None
        try:
            return int(raw), None
        except ValueError:
            return None, "Please select a valid option."

    raw = post.get(form_key, "").strip()
    return (raw or None), None


def _modules_with_questions(assignment):
    """Ordered modules (variant-filtered), each with prefetched questions+choices."""
    return list(assignment.modules_for_variant().prefetch_related("questions__choices"))


def _flat_questions(modules):
    out = []
    for module in modules:
        out.extend(module.questions.all())
    return out


def survey_detail(request, assignment_id):
    assignment = get_object_or_404(SurveyAssignment, id=assignment_id)

    if assignment.status == SurveyAssignment.Status.CLOSED:
        return redirect("core:home")

    survey = assignment.survey
    modules = _modules_with_questions(assignment)
    all_questions = _flat_questions(modules)

    existing_submission = None
    existing_answers = {}  # by question_id
    if request.user.is_authenticated:
        existing_submission = (
            SurveySubmission.objects.filter(assignment=assignment, user=request.user)
            .prefetch_related("answers")
            .first()
        )
        if (
            existing_submission
            and existing_submission.status == SurveySubmission.Status.COMPLETED
        ):
            return redirect("core:home")
        if existing_submission:
            existing_answers = {
                a.question_id: a.value for a in existing_submission.answers.all()
            }

    errors = {}

    if request.method == "POST":
        answer_values = {}  # question_id -> value
        for q in all_questions:
            value, error = _parse_value(q, request.POST)
            if error:
                errors[q.id] = error
                continue
            answer_values[q.id] = value

        if not errors:
            # Determine which questions are visible given the submitted answers.
            answers_by_code = {q.code: answer_values.get(q.id) for q in all_questions}
            visible = visible_questions(assignment, answers_by_code)
            visible_ids = {q.id for q in visible}

            all_answered = all(
                answer_values.get(qid) is not None for qid in visible_ids
            )

            user = request.user if request.user.is_authenticated else None
            now = timezone.now()
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

    # Progress: count visible questions answered (using stored answers).
    answers_by_code = {q.code: existing_answers.get(q.id) for q in all_questions}
    visible = visible_questions(assignment, answers_by_code)
    total_questions = len(visible)
    answered_count = sum(
        1 for q in visible if existing_answers.get(q.id) not in (None, "", [])
    )

    return render(
        request,
        "surveys/survey_detail.html",
        {
            "assignment": assignment,
            "survey": survey,
            "modules": modules,
            "errors": errors,
            "existing_answers": existing_answers,
            "is_edit": existing_submission is not None,
            "total_questions": total_questions,
            "answered_count": answered_count,
            # Nothing answered yet = first visit, so open the instructions modal.
            "show_instructions": existing_submission is None and answered_count == 0,
            "container_width": "max-w-6xl",
        },
    )


@require_POST
def autosave_survey(request, assignment_id):
    """AJAX endpoint — saves changed fields without altering submission status."""
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
        value, error = _parse_value(q, request.POST)
        if error:
            continue
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
            "survey": assignment.survey,
        },
    )
