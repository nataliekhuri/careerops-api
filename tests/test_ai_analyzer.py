"""The built-in analyzer: skill extraction, matching, CV review and interview prep (no database)."""

import pytest

from app.ai import skills as taxonomy
from app.ai.analyzer import CandidateProfile, analyze_job, match, review_cv
from app.ai.interview_prep import PrepContext, build_prep
from app.schemas.ai import Importance, Priority

BACKEND_JOB = """Senior Backend Engineer (Python)

About us
We build payment software. Our designers love React.

What you'll do:
- Design and build REST APIs with FastAPI and PostgreSQL
- Run services on AWS with Docker and Kubernetes

Requirements:
- 5+ years of experience with Python
- Strong SQL and data modeling skills
- Experience with CI/CD (GitHub Actions)
- Excellent communication in English

Nice to have:
- Kafka or RabbitMQ
- Terraform

We offer: remote-first work, a hybrid option in Berlin and a Java-free stack.
"""


def names(found) -> set[str]:
    return set(found)


# ---------------------------------------------------------------- skill extraction


@pytest.mark.parametrize(
    ("text", "expected", "not_expected"),
    [
        ("We use JavaScript and TypeScript", {"JavaScript", "TypeScript"}, {"Java"}),
        ("Java 21 and Spring Boot", {"Java", "Spring Boot"}, {"JavaScript"}),
        ("NoSQL stores and PostgreSQL", {"NoSQL", "PostgreSQL"}, {"SQL"}),
        ("C++ and C# experience", {"C++", "C#"}, set()),
        ("ASP.NET Core services", {".NET"}, set()),
        ("Backend in Go and Python", {"Go", "Python"}, set()),
        ("We go to conferences. Go ahead and apply!", set(), {"Go"}),
        ("Golang microservices", {"Go", "Microservices"}, set()),
        ("React Native apps", {"React Native"}, {"React"}),
        ("Able to react quickly to incidents", set(), {"React"}),
        ("k8s and helm charts", {"Kubernetes"}, set()),
        ("Node.js with Express.js", {"Node.js", "Express"}, set()),
        ("HTML5, CSS3 and Tailwind", {"HTML", "CSS", "Tailwind CSS"}, set()),
        ("Experience with CI/CD pipelines", {"CI/CD"}, set()),
        ("RESTful APIs and GraphQL", {"REST APIs", "GraphQL"}, set()),
        ("Get some rest after a release", set(), {"REST APIs"}),
        ("Postgres or MySQL", {"PostgreSQL", "MySQL"}, set()),
    ],
)
def test_skill_extraction_keeps_look_alikes_apart(text, expected, not_expected):
    found = names(taxonomy.find_skills(text))

    assert expected <= found
    assert not (not_expected & found)


def test_mentions_are_counted():
    assert taxonomy.find_skills("Python, python and PYTHON")["Python"] == 3


@pytest.mark.parametrize(
    ("raw", "canonical"),
    [
        ("postgres", "PostgreSQL"),
        ("K8S", "Kubernetes"),
        ("node.js", "Node.js"),
        ("c#", "C#"),
        ("Ruby on Rails", "Rails"),
    ],
)
def test_user_entered_skills_map_to_canonical_names(raw, canonical):
    assert taxonomy.canonical_skill(raw) == canonical


def test_unknown_skills_are_not_guessed():
    assert taxonomy.canonical_skill("Underwater basket weaving") is None
    assert taxonomy.canonical_skill("   ") is None


def test_implied_and_related_skills():
    assert taxonomy.implied_by({"FastAPI"}) == {"Python": "FastAPI", "REST APIs": "FastAPI"}
    assert taxonomy.related_to("PostgreSQL", {"MySQL"}) == "MySQL"
    assert taxonomy.related_to("PostgreSQL", {"Python"}) is None


# ---------------------------------------------------------------- job analysis


def test_job_analysis_separates_required_from_nice_to_have():
    job = analyze_job(BACKEND_JOB, "Senior Backend Engineer (Python)")

    for skill in ("Python", "FastAPI", "PostgreSQL", "AWS", "Docker", "Kubernetes", "SQL", "CI/CD", "GitHub Actions"):
        assert skill in job.required_skills, skill
    assert {"Kafka", "RabbitMQ", "Terraform"} <= set(job.nice_to_have_skills)
    # "About us" and "We offer" are not requirements.
    assert "React" not in job.required_skills + job.nice_to_have_skills
    assert "Java" not in job.required_skills + job.nice_to_have_skills


def test_job_analysis_details():
    job = analyze_job(BACKEND_JOB, "Senior Backend Engineer (Python)")

    assert job.role_family == "backend"
    assert job.seniority == "Senior"
    assert job.min_years_experience == 5
    assert job.work_modes == ["remote", "hybrid"]
    assert job.warnings == []
    assert "5+ years" in job.summary
    # Required hard skills come first; every skill has the line it was found on.
    assert job.skills[0].importance == Importance.REQUIRED
    fastapi = next(s for s in job.skills if s.name == "FastAPI")
    assert "FastAPI" in fastapi.evidence


def test_line_level_markers_make_a_skill_optional():
    job = analyze_job("We need Python and Django. Experience with Docker is a plus.")

    assert "Python" in job.required_skills
    assert "Docker" in job.nice_to_have_skills


def test_skill_required_anywhere_is_required():
    job = analyze_job("Requirements:\n- Python\nNice to have:\n- Python 3.12 typing tricks")

    assert job.required_skills == ["Python"]


@pytest.mark.parametrize(
    ("title", "family", "seniority"),
    [
        ("Junior Frontend Developer", "frontend", "Junior"),
        ("Staff Data Engineer", "data", "Staff / Principal"),
        ("Site Reliability Engineer", "devops", "Not specified"),
        ("Full-stack Engineer", "fullstack", "Not specified"),
        ("ML Engineer", "ml", "Not specified"),
        ("Engineering Manager, Platform", "devops", "Lead"),
    ],
)
def test_role_family_and_seniority_from_title(title, family, seniority):
    job = analyze_job("Build great software with a great team.", title)

    assert (job.role_family, job.seniority) == (family, seniority)


def test_short_or_empty_descriptions_warn():
    job = analyze_job("Developer wanted.")

    assert job.skills == []
    assert len(job.warnings) == 2


def test_years_take_the_highest_requirement():
    job = analyze_job("3+ years of Python experience and 5-7 years of overall experience.")

    assert job.min_years_experience == 5


# ---------------------------------------------------------------- matching


def strong_profile(**overrides) -> CandidateProfile:
    fields = {
        "skills": ["Python", "FastAPI", "PostgreSQL", "AWS", "Docker", "Kubernetes", "GitHub Actions", "Data modeling"],
        "years_experience": 6,
        "cv_text": "Excellent communication in English. Kafka, RabbitMQ and Terraform in production.",
    }
    return CandidateProfile(**{**fields, **overrides})


def test_perfect_profile_scores_100():
    result = match(strong_profile(), analyze_job(BACKEND_JOB, "Senior Backend Engineer (Python)"))

    assert result.score == 100
    assert result.level == "Strong match"
    assert result.missing == []
    assert [c.name for c in result.components] == ["Skills", "Experience"]


def test_score_breakdown_is_explainable():
    profile = CandidateProfile(skills=["Python", "FastAPI", "MySQL", "Docker"], years_experience=3)
    result = match(profile, analyze_job(BACKEND_JOB, "Senior Backend Engineer (Python)"))

    assert 0 < result.score < 75
    skills, experience = result.components
    assert (skills.weight, experience.weight) == (85, 15)
    assert experience.score == 60.0  # 3 of 5 years
    assert result.score == round((skills.score * 85 + experience.score * 15) / 100)
    # MySQL gives half credit for PostgreSQL, Docker for Kubernetes.
    partial = {p.name: p for p in result.partial}
    assert partial["PostgreSQL"].credit == 0.5 and "MySQL" in partial["PostgreSQL"].reason
    assert "Kubernetes" in partial
    # REST APIs is implied by FastAPI; SQL by MySQL.
    matched = {m.name: m for m in result.matched}
    assert matched["REST APIs"].reason == "Implied by FastAPI"
    assert matched["SQL"].reason == "Implied by MySQL"
    assert "AWS" in {m.name for m in result.missing}
    assert any("AWS" in line for line in result.explanation)
    assert any("AWS" in tip for tip in result.recommendations)


def test_more_matching_skills_never_lower_the_score():
    job = analyze_job(BACKEND_JOB, "Senior Backend Engineer (Python)")
    base = CandidateProfile(skills=["Python"])
    more = CandidateProfile(skills=["Python", "Docker", "AWS"])

    assert match(more, job).score > match(base, job).score


def test_skills_from_the_cv_count_too():
    job = analyze_job("Requirements: Python, Docker")
    result = match(CandidateProfile(cv_text="I built Docker images for Python services"), job)

    assert result.score == 100
    assert {m.reason for m in result.matched} == {"In your CV"}


def test_experience_is_left_out_when_unknown():
    job = analyze_job("Requirements: 5+ years of experience with Python")
    result = match(CandidateProfile(skills=["Python"]), job)

    assert [c.name for c in result.components] == ["Skills"]
    assert result.components[0].weight == 100
    assert any("years of experience" in tip for tip in result.recommendations)


def test_empty_profile_gets_no_score():
    result = match(CandidateProfile(), analyze_job(BACKEND_JOB))

    assert result.score is None
    assert "Career profile" in result.explanation[0]


def test_job_without_known_skills_gets_no_score():
    result = match(CandidateProfile(skills=["Python"]), analyze_job("Great team, great snacks."))

    assert result.score is None


def test_unrecognised_profile_skills_are_reported_not_scored():
    result = match(CandidateProfile(skills=["Python", "Quantum knitting"]), analyze_job("Requirements: Python"))

    assert result.score == 100
    assert any("Quantum knitting" in line for line in result.explanation)


# ---------------------------------------------------------------- CV review

GOOD_CV = (
    """Summary
Backend engineer with 5 years of Python experience. https://github.com/example

Experience
- Built a FastAPI service handling 2M requests per day on AWS
- Reduced API latency by 40% by adding PostgreSQL indexes
- Migrated 12 services to Docker and Kubernetes
- Automated deployments with GitHub Actions, cutting release time from 2 hours to 10 minutes

Skills
Python, FastAPI, PostgreSQL, SQL, Docker, Kubernetes, AWS, data modeling

Education
BSc Computer Science
"""
    + "Delivered reliable software for payment teams across Europe. " * 30
)


def test_good_cv_passes_the_checks():
    review = review_cv(GOOD_CV, analyze_job(BACKEND_JOB))

    failed = [c.name for c in review.checks if not c.passed]
    assert failed == []
    assert review.score == 100
    assert review.keyword_coverage.percent == 100
    assert {"Summary", "Experience", "Skills", "Education"} <= set(review.sections_found)


def test_weak_cv_gets_specific_suggestions():
    cv = """Experience
- Responsible for the billing API
- Worked on various projects
- I helped with my team's deployments and I did my best
"""
    review = review_cv(cv)

    titles = [s.title for s in review.suggestions]
    assert "Quantify your achievements" in titles
    assert "Replace “responsible for”" in titles
    assert "Drop “I” and “my”" in titles
    assert "Add more detail" in titles
    assert review.suggestions[0].priority == Priority.HIGH  # sorted by priority
    weak = next(s for s in review.suggestions if s.title.startswith("Replace"))
    assert "billing API" in weak.example


def test_cv_tailoring_separates_mentionable_skills_from_real_gaps():
    profile = CandidateProfile(skills=["Python", "Docker", "Kubernetes"])
    review = review_cv(
        "Experience\n- Built Python services", analyze_job("Requirements: Python, Docker, Kubernetes, Go"), profile
    )

    assert review.keyword_coverage.missing == ["Docker", "Go", "Kubernetes"]
    mention = next(s for s in review.suggestions if s.category == "Tailoring" and s.title.startswith("Mention"))
    assert mention.title == "Mention Docker, Kubernetes"
    gap = next(s for s in review.suggestions if s.title.startswith("Address the gap"))
    assert gap.title == "Address the gap: Go"


def test_empty_cv_asks_for_one():
    review = review_cv("   ")

    assert review.score is None
    assert review.suggestions[0].title == "Add your CV"


# ---------------------------------------------------------------- interview prep


def test_interview_prep_is_role_and_skill_specific():
    job = analyze_job(BACKEND_JOB, "Senior Backend Engineer (Python)")
    profile = CandidateProfile(skills=["Python", "FastAPI", "MySQL"], years_experience=6)
    prep = build_prep(
        PrepContext(job=job, company="Blue Harbor", company_industry="Fintech", match=match(profile, job))
    )

    topics = {q.topic for q in prep.technical_questions}
    assert "Backend fundamentals" in topics
    assert {"Python", "FastAPI", "Docker"} <= topics
    assert any("influenced a technical decision" in q.question for q in prep.behavioral_questions)  # senior role
    gap_topics = {q.topic for q in prep.gap_questions}
    assert "AWS" in gap_topics  # missing
    assert "PostgreSQL" in gap_topics  # related (MySQL)
    assert any("Blue Harbor" in item for item in prep.company_research)
    assert any("Fintech" in item for item in prep.company_research)
    assert any("on-call" in q for q in prep.questions_to_ask)


def test_interview_prep_without_profile_has_no_gap_questions():
    job = analyze_job("Requirements: React, TypeScript, accessibility", "Junior Frontend Developer")
    prep = build_prep(PrepContext(job=job))

    assert prep.role_family == "frontend"
    assert prep.gap_questions == []
    assert any("ask for help" in q.question for q in prep.behavioral_questions)  # junior role
