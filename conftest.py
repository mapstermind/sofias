import pytest
from django.contrib.auth.models import Group, Permission

# ── Groups ────────────────────────────────────────────────────────────────────


@pytest.fixture
def bootstrap_groups(db):
    """
    Create the four authorization groups with their permissions.
    Required by verify_otp, which calls Group.objects.get(name="Employees").
    Declare this fixture explicitly on any test that exercises that flow.
    """
    codenames = [
        "can_manage_site_configuration",
        "can_manage_users",
        "can_manage_surveys",
        "can_assign_surveys",
        "can_view_dashboard",
        "can_view_reports",
        "can_view_insights",
        "can_take_assigned_surveys",
    ]
    perms = {p.codename: p for p in Permission.objects.filter(codename__in=codenames)}

    group_perms = {
        "Admins": [
            "can_manage_site_configuration",
            "can_manage_users",
            "can_manage_surveys",
            "can_assign_surveys",
            "can_view_dashboard",
            "can_view_reports",
            "can_view_insights",
        ],
        "Principal Exec": [
            "can_view_dashboard",
            "can_view_reports",
            "can_view_insights",
        ],
        "Secondary Exec": ["can_view_dashboard", "can_view_reports"],
        "Employees": ["can_take_assigned_surveys"],
    }
    groups = {}
    for name, cnames in group_perms.items():
        g, _ = Group.objects.get_or_create(name=name)
        g.permissions.set([perms[c] for c in cnames if c in perms])
        groups[name] = g
    return groups


# ── User factories ────────────────────────────────────────────────────────────


@pytest.fixture
def make_user(db):
    """
    Returns a callable: make_user(email="...", **kwargs) → User.
    Does NOT create a UserProfile.
    """
    from apps.accounts.models import User

    def factory(email="test@example.com", password=None, **kwargs):
        username = kwargs.pop("username", email.split("@")[0])
        user = User(email=email, username=username, **kwargs)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save()
        return user

    return factory


@pytest.fixture
def make_user_with_profile(db, make_user):
    """
    Returns a callable that creates a User + UserProfile.
    Optionally links to a company.
    """
    from apps.accounts.models import UserProfile

    def factory(email="emp@example.com", company=None, position="Analyst", **kwargs):
        user = make_user(email=email, **kwargs)
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.position = position
        profile.company = company
        profile.save()
        return user

    return factory


# ── Company factory ───────────────────────────────────────────────────────────


@pytest.fixture
def make_company(db):
    """Returns a callable that creates a Company (reference_code is auto-generated)."""
    from apps.accounts.models import Company

    def factory(name="Acme Corp", legal_name="Acme Corp SA de CV", **kwargs):
        return Company.objects.create(name=name, legal_name=legal_name, **kwargs)

    return factory


# ── Survey fixture chain ──────────────────────────────────────────────────────


@pytest.fixture
def survey_template(db):
    from apps.surveys.models import SurveyTemplate

    return SurveyTemplate.objects.create(
        title="Wellbeing Survey",
        status=SurveyTemplate.Status.PUBLISHED,
    )


@pytest.fixture
def survey_version(db, survey_template):
    from apps.surveys.models import SurveyVersion

    return SurveyVersion.objects.create(template=survey_template, version_number=1)


@pytest.fixture
def survey_with_questions(db, survey_version):
    """
    Returns {"version": version, "questions": [...]}.
    One question of each of the 9 types; choice questions have 2 choices each.
    """
    from apps.surveys.models import Choice, Question

    question_specs = [
        ("text", "What is your name?"),
        ("integer", "How many years of experience?"),
        ("decimal", "Rate from 0 to 10."),
        ("date", "When did you start?"),
        ("single_choice", "Pick one color."),
        ("multiple_choice", "Pick all that apply."),
        ("boolean", "Do you agree?"),
        ("rating", "Overall satisfaction?"),
        ("likert", "How often do you feel engaged?"),
    ]
    questions = []
    for order, (qtype, text) in enumerate(question_specs):
        q = Question.objects.create(
            version=survey_version,
            question_type=qtype,
            text=text,
            order=order,
        )
        if qtype in ("single_choice", "multiple_choice"):
            Choice.objects.create(question=q, label="Option A", value="a", order=0)
            Choice.objects.create(question=q, label="Option B", value="b", order=1)
        questions.append(q)
    return {"version": survey_version, "questions": questions}


@pytest.fixture
def active_assignment(db, make_company, survey_version):
    """An ACTIVE SurveyAssignment linking a fresh company to survey_version."""
    from apps.surveys.models import SurveyAssignment

    company = make_company()
    return SurveyAssignment.objects.create(
        company=company,
        version=survey_version,
        status=SurveyAssignment.Status.ACTIVE,
    )
