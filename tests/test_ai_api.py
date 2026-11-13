"""AI assistant API: career profile, job sources, user isolation, validation and real-data use."""

from datetime import UTC, datetime, timedelta

import pytest

from app.ai.providers import BuiltinAssistant, get_assistant
from app.core.config import Settings
from app.main import app

JOB = """Backend Engineer
Requirements:
- 3+ years of experience with Python and FastAPI
- PostgreSQL and Docker
Nice to have:
- Kubernetes
"""

PROFILE = {
    "headline": "Backend developer",
    "target_role": "Backend Engineer",
    "years_experience": 3,
    "skills": ["Python", "fastapi", "postgres", "Docker", "Basket weaving"],
    "cv_text": "Experience\n- Built FastAPI services",
}


def create_application(client, **fields):
    body = {"company": "Acme", "position": "Backend Engineer", "location": "Remote", **fields}
    response = client.post("/applications", json=body)
    assert response.status_code == 200, response.text
    return response.json()["application"]


ENDPOINTS = [
    ("post", "/ai/job-analysis", {"job_description": JOB}),
    ("post", "/ai/match", {"job_description": JOB}),
    ("post", "/ai/cv-review", {}),
    ("post", "/ai/interview-prep", {"job_description": JOB}),
    ("get", "/ai/skill-insights", None),
    ("get", "/ai/provider", None),
    ("get", "/users/me/career-profile", None),
    ("put", "/users/me/career-profile", PROFILE),
]


@pytest.mark.parametrize(("method", "path", "body"), ENDPOINTS)
def test_every_endpoint_requires_sign_in(anon_client, method, path, body):
    response = getattr(anon_client, method)(path, **({"json": body} if body is not None else {}))

    assert response.status_code == 401


# ---------------------------------------------------------------- career profile


def test_profile_is_empty_until_saved(client):
    body = client.get("/users/me/career-profile").json()

    assert body["skills"] == [] and body["cv_text"] == "" and body["years_experience"] is None
    assert body["updated_at"] is None


def test_save_and_replace_profile(client):
    saved = client.put("/users/me/career-profile", json=PROFILE)

    assert saved.status_code == 200
    body = saved.json()
    assert body["skills"] == PROFILE["skills"]
    assert set(body["recognized_skills"]) == {"Python", "FastAPI", "PostgreSQL", "Docker"}
    assert body["unrecognized_skills"] == ["Basket weaving"]
    assert body["updated_at"] is not None

    replaced = client.put("/users/me/career-profile", json={"skills": ["Go"]}).json()
    assert replaced["skills"] == ["Go"]
    assert replaced["headline"] == "" and replaced["cv_text"] == ""
    assert client.get("/users/me/career-profile").json()["skills"] == ["Go"]


def test_duplicate_skills_are_dropped(client):
    body = client.put("/users/me/career-profile", json={"skills": ["Python", " python ", "PYTHON", "SQL"]}).json()

    assert body["skills"] == ["Python", "SQL"]


@pytest.mark.parametrize(
    "patch",
    [
        {"years_experience": -1},
        {"years_experience": 61},
        {"skills": [""]},
        {"skills": ["x" * 61]},
        {"skills": [f"skill {i}" for i in range(101)]},
        {"cv_text": "x" * 30_001},
        {"headline": "x" * 256},
        {"unknown": 1},
    ],
)
def test_profile_validation(client, patch):
    assert client.put("/users/me/career-profile", json={**PROFILE, **patch}).status_code == 422


def test_profiles_are_private(make_user, make_client):
    ann, bob = make_client(make_user()), make_client(make_user())
    ann.put("/users/me/career-profile", json=PROFILE)

    assert bob.get("/users/me/career-profile").json()["skills"] == []


def test_deleting_the_account_deletes_the_profile(client, db_session):
    from app.models.career_profile import CareerProfile

    client.put("/users/me/career-profile", json=PROFILE)
    user_id = client.user.id
    assert client.request("DELETE", "/users/me", json={"password": "test-password-123"}).status_code == 204

    assert db_session.get(CareerProfile, user_id) is None


# ---------------------------------------------------------------- job descriptions on applications


def test_applications_store_job_descriptions(client):
    application = create_application(client, job_description=f"  {JOB}  ")

    assert application["job_description"] == JOB.strip()
    patched = client.patch(f"/applications/{application['id']}", json={"job_description": "Python only"}).json()
    assert patched["job_description"] == "Python only"
    assert create_application(client)["job_description"] == ""


def test_job_description_length_limit(client):
    response = client.post(
        "/applications",
        json={"company": "A", "position": "B", "location": "C", "job_description": "x" * 20_001},
    )

    assert response.status_code == 422


# ---------------------------------------------------------------- job sources


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"application_id": 1, "job_description": JOB},
        {"job_description": "   "},
        {"job_description": "x" * 20_001},
        {"application_id": 0},
        {"job_description": JOB, "extra": True},
    ],
)
@pytest.mark.parametrize("path", ["/ai/job-analysis", "/ai/match", "/ai/interview-prep"])
def test_job_source_validation(client, path, body):
    assert client.post(path, json=body).status_code == 422


def test_cv_review_rejects_two_job_sources(client):
    assert client.post("/ai/cv-review", json={"application_id": 1, "job_description": JOB}).status_code == 422


def test_analysis_of_pasted_text(client):
    response = client.post("/ai/job-analysis", json={"job_description": JOB, "position": "Backend Engineer"})

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Backend Engineer"
    assert {"Python", "FastAPI", "PostgreSQL", "Docker"} <= set(body["required_skills"])
    assert body["nice_to_have_skills"] == ["Kubernetes"]
    assert body["min_years_experience"] == 3


def test_analysis_of_a_saved_application(client):
    application = create_application(client, position="Platform Engineer", job_description=JOB)

    body = client.post("/ai/job-analysis", json={"application_id": application["id"]}).json()

    assert body["title"] == "Platform Engineer"
    assert "FastAPI" in body["required_skills"]
    assert not any("no job description" in w for w in body["warnings"])


def test_application_without_description_falls_back_to_notes_with_a_warning(client):
    application = create_application(client, position="Python Developer", notes="Team uses Django and Redis")

    body = client.post("/ai/job-analysis", json={"application_id": application["id"]}).json()

    assert {"Python", "Django", "Redis"} <= set(body["required_skills"])
    assert "no job description" in body["warnings"][0]


@pytest.mark.parametrize("path", ["/ai/job-analysis", "/ai/match", "/ai/interview-prep", "/ai/cv-review"])
def test_other_users_applications_look_like_missing_ones(make_user, make_client, path):
    ann, bob = make_client(make_user()), make_client(make_user())
    anns = create_application(ann, job_description=JOB)

    foreign = bob.post(path, json={"application_id": anns["id"]})
    missing = bob.post(path, json={"application_id": 999_999})

    assert foreign.status_code == missing.status_code == 422
    assert foreign.json()["detail"][0]["msg"] == missing.json()["detail"][0]["msg"] == "Application not found"
    assert foreign.json()["detail"][0]["loc"] == ["body", "application_id"]


# ---------------------------------------------------------------- match, CV review, prep


def test_match_uses_the_saved_profile(client):
    application = create_application(client, job_description=JOB)

    empty = client.post("/ai/match", json={"application_id": application["id"]}).json()
    assert empty["score"] is None

    client.put("/users/me/career-profile", json=PROFILE)
    body = client.post("/ai/match", json={"application_id": application["id"]}).json()

    assert body["level"] == "Strong match"
    assert body["score"] >= 90
    assert {c["name"] for c in body["components"]} == {"Skills", "Experience"}
    assert "Kubernetes" in {m["name"] for m in body["partial"]}  # related to Docker
    assert body["job"]["title"] == "Backend Engineer"


def test_cv_review_defaults_to_the_profile_cv(client):
    assert client.post("/ai/cv-review", json={}).json()["suggestions"][0]["title"] == "Add your CV"

    client.put("/users/me/career-profile", json=PROFILE)
    body = client.post("/ai/cv-review", json={"job_description": JOB}).json()

    assert body["word_count"] > 0
    assert body["keyword_coverage"] is not None
    # Docker and PostgreSQL are in the profile but not in the CV.
    assert any(s["title"].startswith("Mention") and "Docker" in s["title"] for s in body["suggestions"])


def test_cv_review_of_pasted_cv(client):
    body = client.post("/ai/cv-review", json={"cv_text": "Experience\n- Responsible for things"}).json()

    assert body["keyword_coverage"] is None
    assert any(s["title"] == "Replace “responsible for”" for s in body["suggestions"])


def test_interview_prep_uses_company_and_upcoming_interviews(client, make_user, make_client):
    company = client.post(
        "/companies", json={"name": "Northwind", "industry": "Developer tools", "notes": "Loves Postgres"}
    ).json()
    application = create_application(client, company="Northwind", company_id=company["id"], job_description=JOB)
    soon = (datetime.now(UTC) + timedelta(days=2)).isoformat()
    past = (datetime.now(UTC) - timedelta(days=2)).isoformat()
    for when, kind in [(soon, "technical"), (past, "phone")]:
        response = client.post(
            "/interviews", json={"application_id": application["id"], "scheduled_at": when, "interview_type": kind}
        )
        assert response.status_code == 201, response.text

    body = client.post("/ai/interview-prep", json={"application_id": application["id"]}).json()

    assert body["company"] == "Northwind"
    assert [i["interview_type"] for i in body["upcoming_interviews"]] == ["technical"]
    assert any("Technical round" in tip for tip in body["tips"])
    assert any("Developer tools" in item for item in body["company_research"])
    assert any("Loves Postgres" in item for item in body["company_research"])
    assert {"Python", "FastAPI"} <= {q["topic"] for q in body["technical_questions"]}


def test_interview_prep_for_pasted_text(client):
    body = client.post("/ai/interview-prep", json={"job_description": JOB}).json()

    assert body["company"] is None
    assert body["upcoming_interviews"] == []
    assert body["gap_questions"] == []  # no profile yet


# ---------------------------------------------------------------- skill insights


def test_skill_insights_count_demand_across_applications(client):
    create_application(client, job_description="Requirements: Python, Docker")
    create_application(client, job_description="Requirements: Python, Kubernetes. Nice to have: Go")
    create_application(client)  # no description: not analysed
    client.put("/users/me/career-profile", json={"skills": ["Python", "Kubernetes"]})

    body = client.get("/ai/skill-insights").json()

    assert body["analyzed_applications"] == 2
    assert body["total_applications"] == 3
    skills = {s["name"]: s for s in body["skills"]}
    assert skills["Python"]["applications"] == 2 and skills["Python"]["have"]
    assert skills["Docker"]["have"]  # implied by Kubernetes
    assert "Go" not in skills  # only nice-to-have
    assert body["skills"][0]["name"] == "Python"
    assert body["coverage_percent"] == 100
    assert body["top_missing"] == []


def test_skill_insights_are_per_user(make_user, make_client):
    ann, bob = make_client(make_user()), make_client(make_user())
    create_application(ann, job_description="Requirements: Python")

    body = bob.get("/ai/skill-insights").json()

    assert body == {
        "analyzed_applications": 0,
        "total_applications": 0,
        "coverage_percent": None,
        "skills": [],
        "top_missing": [],
    }


def test_skill_insights_show_gaps(client):
    create_application(client, job_description="Requirements: Python, AWS")
    create_application(client, job_description="Requirements: AWS, Terraform")
    client.put("/users/me/career-profile", json={"skills": ["Python"]})

    body = client.get("/ai/skill-insights").json()

    assert body["top_missing"] == ["AWS", "Terraform"]
    assert body["coverage_percent"] == 25  # 1 of 4 requests


# ---------------------------------------------------------------- provider


def test_default_provider_is_free_and_local(client):
    assert client.get("/ai/provider").json() == {
        "name": "builtin",
        "external": False,
        "cost": "free",
        "description": "Built-in rule-based analyzer. Runs on this server; your data is not sent anywhere.",
    }


def test_the_provider_can_be_swapped(client):
    class FakeAssistant(BuiltinAssistant):
        name = "fake"

    app.dependency_overrides[get_assistant] = FakeAssistant
    try:
        assert client.get("/ai/provider").json()["name"] == "fake"
    finally:
        del app.dependency_overrides[get_assistant]


@pytest.mark.parametrize("value", ["openai", "anthropic", ""])
def test_only_the_builtin_provider_can_be_configured(value):
    with pytest.raises(ValueError, match="ai_provider"):
        Settings(DB_PASSWORD="x", AI_PROVIDER=value)


def test_builtin_is_the_default_provider():
    assert Settings(DB_PASSWORD="x").ai_provider == "builtin"
