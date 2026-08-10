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
        "can_manage_surveys",
        "can_view_dashboard",
        "can_view_insights",
        "can_take_assigned_surveys",
        "can_manage_employees",
        "can_view_submissions",
    ]
    perms = {p.codename: p for p in Permission.objects.filter(codename__in=codenames)}

    group_perms = {
        "Admins": [
            "can_manage_surveys",
            "can_view_dashboard",
            "can_view_insights",
            "can_manage_employees",
            "can_view_submissions",
        ],
        "Principal Exec": [
            "can_view_dashboard",
            "can_view_insights",
            "can_manage_employees",
            "can_take_assigned_surveys",
        ],
        "Secondary Exec": [
            "can_view_dashboard",
            "can_manage_employees",
            "can_take_assigned_surveys",
        ],
        "Employees": ["can_take_assigned_surveys"],
    }
    groups = {}
    for name, cnames in group_perms.items():
        g, _ = Group.objects.get_or_create(name=name)
        g.permissions.set([perms[c] for c in cnames if c in perms])
        groups[name] = g
    return groups


# ── Admin ─────────────────────────────────────────────────────────────────────


@pytest.fixture
def staff_client(client, make_user):
    """A test client logged in as a superuser, for exercising admin screens."""
    staff = make_user(
        email="admin-staff@example.com",
        password="Pass12345!",
        is_staff=True,
        is_superuser=True,
    )
    client.force_login(staff)
    return client


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

    def factory(
        email="emp@example.com",
        company=None,
        position="Analyst",
        area=None,
        location=None,
        is_activated=True,
        **kwargs,
    ):
        # area/location/is_activated are explicit params, not **kwargs — they
        # must not fall through to make_user, which would pass them to the User
        # constructor.
        #
        # is_activated defaults True: an unactivated profile is bounced to the
        # activation flow by RequireProfileActivationMiddleware, so a test that
        # wants to exercise any other view needs an activated user. Tests about
        # activation itself pass is_activated=False.
        user = make_user(email=email, **kwargs)
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.position = position
        profile.company = company
        profile.area = area
        profile.location = location
        profile.is_activated = is_activated
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


@pytest.fixture
def company(make_company):
    """One company, shared by fixtures that have to agree on tenancy.

    Views scope assignment lookups to the caller's own company, so a test whose
    respondent and assignment come from two separate `make_company()` calls gets
    a 404 rather than the page it meant to exercise.
    """
    return make_company()


@pytest.fixture
def make_area(db):
    """Returns a callable: make_area(company, name="...") → CompanyArea."""
    from apps.accounts.models import CompanyArea

    def factory(company, name="Sistemas", **kwargs):
        return CompanyArea.objects.create(company=company, name=name, **kwargs)

    return factory


@pytest.fixture
def make_location(db):
    """Returns a callable: make_location(company, name="...") → CompanyLocation."""
    from apps.accounts.models import CompanyLocation

    def factory(company, name="Matriz", **kwargs):
        return CompanyLocation.objects.create(company=company, name=name, **kwargs)

    return factory


# ── Survey fixture chain ──────────────────────────────────────────────────────


@pytest.fixture
def survey(db):
    from apps.surveys.models import Survey

    return Survey.objects.create(
        key="test-survey",
        title="Wellbeing Survey",
        status=Survey.Status.PUBLISHED,
    )


@pytest.fixture
def survey_module(db, survey):
    """A single `all`-variant module within the survey."""
    from apps.surveys.models import Module

    return Module.objects.create(
        survey=survey,
        key="m1",
        title="General",
        applies_to=Module.AppliesTo.ALL,
        order=0,
    )


@pytest.fixture
def survey_with_questions(db, survey, survey_module):
    """
    Returns {"survey": survey, "module": module, "questions": [...]}.
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
            module=survey_module,
            code=f"q{order + 1}",
            question_type=qtype,
            text=text,
            order=order,
        )
        if qtype in ("single_choice", "multiple_choice"):
            Choice.objects.create(question=q, label="Option A", value="a", order=0)
            Choice.objects.create(question=q, label="Option B", value="b", order=1)
        questions.append(q)
    return {"survey": survey, "module": survey_module, "questions": questions}


@pytest.fixture
def active_assignment(db, company, survey):
    """An ACTIVE SurveyAssignment linking the shared company to the survey."""
    from apps.surveys.models import SurveyAssignment

    return SurveyAssignment.objects.create(
        company=company,
        survey=survey,
        variant=SurveyAssignment.Variant.SMALL,
        status=SurveyAssignment.Status.ACTIVE,
    )
