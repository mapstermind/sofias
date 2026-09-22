"""Results data for the NOM-035 results page.

One assignment at a time, narrowed by a validated filter (see
apps/core/results_query.py), returned as frozen dataclasses. The small-group
rule is applied here, not in templates: a suppressed result carries no numbers.
See docs/platform/nom-035-results-dashboard.md.
"""

from dataclasses import dataclass

from django.db.models import Count, Max, Min, Q
from django.utils import timezone

from apps.surveys.models import SurveyAssignment

NOM035_SURVEY_KEY = "nom035"

_MONTHS = (
    "ene",
    "feb",
    "mar",
    "abr",
    "may",
    "jun",
    "jul",
    "ago",
    "sep",
    "oct",
    "nov",
    "dic",
)


def _short(day, *, year=True) -> str:
    text = f"{day.day} {_MONTHS[day.month - 1]}"
    return f"{text} {day.year}" if year else text


def assignment_label(variant_label, first, last, created) -> str:
    if first is None:
        return f"{variant_label} · creada {_short(created)} · sin respuestas"
    if first == last:
        span = _short(first)
    elif first.year == last.year:
        span = f"{_short(first, year=False)} – {_short(last)}"
    else:
        span = f"{_short(first)} – {_short(last)}"
    return f"{variant_label} · aplicada {span}"


@dataclass(frozen=True)
class AssignmentOption:
    assignment: SurveyAssignment
    label: str
    scored_count: int


def _local_date(moment):
    return timezone.localtime(moment).date() if moment is not None else None


def assignment_options(company) -> list[AssignmentOption]:
    scored = Q(submissions__nom035_score__isnull=False)
    rows = (
        SurveyAssignment.objects.filter(company=company, survey__key=NOM035_SURVEY_KEY)
        .select_related("company")
        .annotate(
            first_answer=Min("submissions__completed_at", filter=scored),
            last_answer=Max("submissions__completed_at", filter=scored),
            scored_count=Count("submissions__nom035_score"),
        )
        .order_by("-created_at", "-pk")
    )
    return [
        AssignmentOption(
            assignment=a,
            label=assignment_label(
                a.get_variant_display(),
                _local_date(a.first_answer),
                _local_date(a.last_answer),
                _local_date(a.created_at),
            ),
            scored_count=a.scored_count,
        )
        for a in rows
    ]


def select_assignment(options, requested_pk):
    if not options:
        return None
    for option in options:
        if option.assignment.pk == requested_pk:
            return option
    return next((o for o in options if o.scored_count), options[0])
