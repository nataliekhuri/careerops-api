"""The free, built-in career analyzer: deterministic rules, no network calls, no API keys.

Everything here is explainable: each skill carries the line it was found on, and each
score is broken down into weighted components.
"""

import re
from dataclasses import dataclass, field

from app.ai import skills as taxonomy
from app.schemas.ai import (
    CvCheck,
    CvReview,
    CvSuggestion,
    Importance,
    JobAnalysis,
    JobSkill,
    KeywordCoverage,
    MatchedSkill,
    MatchResult,
    Priority,
    ScoreComponent,
)


@dataclass(frozen=True)
class CandidateProfile:
    """What the analyzer knows about the user (from their career profile)."""

    skills: list[str] = field(default_factory=list)
    years_experience: int | None = None
    cv_text: str = ""
    headline: str = ""
    target_role: str = ""


# ---------------------------------------------------------------- job analysis

_HEADING_OPTIONAL = re.compile(
    r"\b(nice[\s-]to[\s-]haves?|bonus(?:\s+points)?|preferred(?:\s+qualifications)?|good\s+to\s+have|"
    r"would\s+be\s+(?:a\s+)?(?:plus|great|nice)|pluses|desirable|extra\s+credit|ideally)\b"
)
_HEADING_REQUIRED = re.compile(
    r"\b(requirements?|required|must[\s-]haves?|qualifications|what\s+you(?:'ll|\s+will)?\s+(?:bring|need|have)|"
    r"who\s+you\s+are|you\s+have|you\s+bring|we(?:'re|\s+are)\s+looking\s+for|skills|about\s+you|your\s+profile|"
    r"essentials?|responsibilities|what\s+you(?:'ll|\s+will)\s+do|your\s+role|the\s+role|tech\s+stack|our\s+stack)\b"
)
_HEADING_IGNORE = re.compile(
    r"\b(benefits|we\s+offer|perks|why\s+join|about\s+us|about\s+the\s+company|who\s+we\s+are|our\s+company|"
    r"equal\s+opportunit\w+|how\s+to\s+apply)\b"
)
_LINE_OPTIONAL = re.compile(
    r"\b(nice\s+to\s+have|(?:is|are|would\s+be)?\s*a\s+plus|bonus|preferred|ideally|desirable|"
    r"familiarity\s+with|exposure\s+to|good\s+to\s+have|not\s+required|optional)\b"
)
_YEARS = re.compile(r"(?<![\d.])(\d{1,2})\s*(?:\+|plus)?\s*(?:(?:-|–|to)\s*\d{1,2}\s*\+?\s*)?(?:years?|yrs?)\b")
_WORK_MODES = (
    ("remote", re.compile(r"\b(remote|work\s+from\s+(?:home|anywhere)|distributed\s+team)\b")),
    ("hybrid", re.compile(r"\bhybrid\b")),
    ("on-site", re.compile(r"\b(on[\s-]?site|in[\s-]office|office[\s-]based)\b")),
)

ROLE_FAMILIES: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("ml", re.compile(r"\b(machine\s+learning|ml|ai|data\s+scientist|mlops|llm)\b")),
    (
        "data",
        re.compile(r"\b(data\s+(?:engineer|analyst|platform)|analytics\s+engineer|bi\s+(?:developer|engineer)|etl)\b"),
    ),
    ("devops", re.compile(r"\b(devops|sre|site\s+reliability|platform|infrastructure|cloud\s+engineer|devsecops)\b")),
    ("security", re.compile(r"\b(security|appsec|penetration)\b")),
    ("fullstack", re.compile(r"\b(full[\s-]?stack)\b")),
    ("frontend", re.compile(r"\b(front[\s-]?end|ui\s+(?:engineer|developer)|react\s+developer|web\s+developer)\b")),
    ("mobile", re.compile(r"\b(mobile|ios|android|flutter|react\s+native)\b")),
    ("qa", re.compile(r"\b(qa|quality\s+assurance|test\s+(?:engineer|automation)|sdet)\b")),
    (
        "backend",
        re.compile(
            r"\b(back[\s-]?end|api|server[\s-]side|python\s+(?:developer|engineer)|java\s+developer|software\s+engineer)\b"
        ),
    ),
)
FAMILY_LABELS = {
    "backend": "backend",
    "frontend": "frontend",
    "fullstack": "full-stack",
    "data": "data engineering",
    "ml": "machine learning",
    "devops": "DevOps / platform",
    "mobile": "mobile",
    "qa": "QA / test",
    "security": "security",
    "general": "software",
}
# Skill categories that suggest a role family when the title does not.
_FAMILY_BY_SKILLS = {
    "frontend": {"React", "Vue", "Angular", "Svelte", "CSS", "HTML", "Next.js", "Tailwind CSS", "Accessibility"},
    "backend": {"FastAPI", "Django", "Flask", "Spring Boot", "Node.js", "REST APIs", "PostgreSQL", "Microservices"},
    "data": {"Spark", "Airflow", "dbt", "ETL", "Snowflake", "BigQuery"},
    "ml": {"Machine learning", "PyTorch", "TensorFlow", "scikit-learn", "LLMs", "NLP"},
    "devops": {"Kubernetes", "Terraform", "Infrastructure as code", "CI/CD", "Observability"},
    "mobile": {"Swift", "React Native", "Flutter", "Kotlin"},
}

_SENIORITY_TITLE = (
    ("Intern", re.compile(r"\b(intern(?:ship)?|working\s+student|werkstudent)\b")),
    ("Junior", re.compile(r"\b(junior|jr\.?|graduate|entry[\s-]level|trainee)\b")),
    ("Staff / Principal", re.compile(r"\b(staff|principal|distinguished)\b")),
    ("Lead", re.compile(r"\b(lead|head\s+of|engineering\s+manager|tech\s+lead)\b")),
    ("Senior", re.compile(r"\b(senior|sr\.?)\b")),
    ("Mid-level", re.compile(r"\b(mid[\s-]?level|intermediate|medior)\b")),
)


def _lines(text: str) -> list[str]:
    parts = re.split(r"[\r\n]+|(?<=[.!?;])\s+(?=[A-Z•\-*])|\s+[•·▪‣]\s+", text)
    return [line.strip(" \t•·▪‣*-–—") for line in parts if line.strip(" \t•·▪‣*-–—")]


def _is_heading(line: str) -> bool:
    lower = line.lower()
    return (
        len(line) <= 70
        and (line.endswith(":") or not re.search(r"[.!?,;]", line))
        and bool(_HEADING_OPTIONAL.search(lower) or _HEADING_REQUIRED.search(lower) or _HEADING_IGNORE.search(lower))
    )


def _section_of(line: str, current: str) -> str:
    lower = line.lower()
    if _HEADING_OPTIONAL.search(lower):
        return "optional"
    if _HEADING_IGNORE.search(lower):
        return "ignore"
    if _HEADING_REQUIRED.search(lower):
        return "required"
    return current


def _snippet(line: str, limit: int = 160) -> str:
    return line if len(line) <= limit else line[: limit - 1].rstrip() + "…"


def detect_role_family(title: str, found_skills: set[str]) -> str:
    lower = title.lower()
    for family, pattern in ROLE_FAMILIES:
        if pattern.search(lower):
            return family
    scores = {family: len(found_skills & names) for family, names in _FAMILY_BY_SKILLS.items()}
    frontend, backend = scores["frontend"], scores["backend"]
    if frontend >= 2 and backend >= 2:
        return "fullstack"
    best = max(scores, key=lambda family: scores[family])
    return best if scores[best] >= 2 else "general"


def _seniority(title: str, text: str, years: int | None) -> str:
    for label, pattern in _SENIORITY_TITLE:
        if pattern.search(title.lower()):
            return label
    if years is not None:
        if years <= 1:
            return "Junior"
        if years <= 4:
            return "Mid-level"
        if years <= 7:
            return "Senior"
        return "Staff / Principal"
    for label, pattern in _SENIORITY_TITLE:
        if label in ("Junior", "Senior") and pattern.search(text.lower()):
            return label
    return "Not specified"


def _min_years(lines: list[str]) -> int | None:
    values = []
    for line in lines:
        lower = line.lower()
        if "experience" in lower or "years of" in lower:
            values += [int(match.group(1)) for match in _YEARS.finditer(lower) if 0 < int(match.group(1)) <= 20]
    return max(values) if values else None


def analyze_job(text: str, title: str = "") -> JobAnalysis:
    """Extract skills (required vs nice-to-have), seniority, experience and work mode from a job description."""
    lines = _lines(text)
    section = "required"  # with no headings, every skill counts as required
    found: dict[str, dict] = {}

    for line in lines:
        if _is_heading(line):
            section = _section_of(line, section)
            if not taxonomy.find_skills(line):
                continue
        else:
            # Inline heading: "Nice to have: Kafka, Terraform" or "We offer: ..."
            prefix, colon, rest = line.partition(":")
            if colon and rest.strip() and _is_heading(prefix + ":"):
                section = _section_of(prefix, section)
                line = rest.strip()
        if section == "ignore":
            continue
        optional = section == "optional" or bool(_LINE_OPTIONAL.search(line.lower()))
        for name, count in taxonomy.find_skills(line).items():
            entry = found.setdefault(name, {"mentions": 0, "required": False, "evidence": ""})
            entry["mentions"] += count
            if not optional and not entry["required"]:
                entry["required"] = True
                entry["evidence"] = _snippet(line)
            elif not entry["evidence"]:
                entry["evidence"] = _snippet(line)

    # The title names the core skills ("Python Developer") - those are required.
    for name, count in taxonomy.find_skills(title).items():
        entry = found.setdefault(name, {"mentions": 0, "required": True, "evidence": _snippet(title)})
        entry["mentions"] += count
        entry["required"] = True

    job_skills = [
        JobSkill(
            name=name,
            category=taxonomy.BY_NAME[name].category,
            importance=Importance.REQUIRED if entry["required"] else Importance.NICE_TO_HAVE,
            mentions=entry["mentions"],
            evidence=entry["evidence"],
        )
        for name, entry in found.items()
    ]
    job_skills.sort(
        key=lambda s: (s.importance != Importance.REQUIRED, taxonomy.BY_NAME[s.name].soft, -s.mentions, s.name)
    )

    years = _min_years(lines)
    family = detect_role_family(title, set(found))
    seniority = _seniority(title, text, years)
    lower = text.lower()
    modes = [mode for mode, pattern in _WORK_MODES if pattern.search(lower)]
    required = [s.name for s in job_skills if s.importance == Importance.REQUIRED]
    nice = [s.name for s in job_skills if s.importance == Importance.NICE_TO_HAVE]
    word_count = len(text.split())

    warnings = []
    if word_count < 40:
        warnings.append("The description is very short, so the analysis is less reliable. Paste the full posting.")
    if not job_skills:
        warnings.append("No known skills were found. Check that this is the full job description.")

    hard_required = [name for name in required if not taxonomy.BY_NAME[name].soft]
    role = FAMILY_LABELS[family]
    parts = [f"{seniority} {role} role" if seniority != "Not specified" else f"{role[0].upper()}{role[1:]} role"]
    if hard_required:
        parts.append(f"core skills {', '.join(hard_required[:5])}")
    if years:
        parts.append(f"{years}+ years of experience")
    if modes:
        parts.append(" / ".join(modes))

    return JobAnalysis(
        title=title or "Untitled role",
        role_family=family,
        seniority=seniority,
        min_years_experience=years,
        work_modes=modes,
        skills=job_skills,
        required_skills=required,
        nice_to_have_skills=nice,
        summary="; ".join(parts) + ".",
        word_count=word_count,
        warnings=warnings,
    )


# ---------------------------------------------------------------- matching

SKILLS_WEIGHT = 85
EXPERIENCE_WEIGHT = 15
LEVELS = ((75, "Strong match"), (55, "Good match"), (35, "Partial match"), (0, "Low match"))


@dataclass
class _Known:
    """The user's skills: canonical name -> where we know it from."""

    sources: dict[str, str]
    custom: list[str]

    @property
    def names(self) -> set[str]:
        return set(self.sources)


def known_skills(profile: CandidateProfile) -> _Known:
    sources: dict[str, str] = {}
    custom: list[str] = []
    for raw in profile.skills:
        name = taxonomy.canonical_skill(raw)
        if name:
            sources.setdefault(name, "profile")
        elif raw.strip():
            custom.append(raw.strip())
    for name in taxonomy.find_skills(profile.cv_text):
        sources.setdefault(name, "cv")
    return _Known(sources, custom)


def _weight(skill: str, importance: Importance) -> float:
    base = 2.0 if importance == Importance.REQUIRED else 1.0
    return base * (0.5 if taxonomy.BY_NAME[skill].soft else 1.0)


def match(profile: CandidateProfile, job: JobAnalysis) -> MatchResult:
    """Score how well the profile fits the job, with the reasons behind the number."""
    known = known_skills(profile)
    have = known.names
    implied = taxonomy.implied_by(have)

    matched: list[MatchedSkill] = []
    partial: list[MatchedSkill] = []
    missing: list[MatchedSkill] = []
    earned = total = 0.0

    for skill in job.skills:
        weight = _weight(skill.name, skill.importance)
        total += weight
        if skill.name in have:
            where = "your career profile" if known.sources[skill.name] == "profile" else "your CV"
            item = MatchedSkill(**_base(skill), credit=1.0, reason=f"In {where}")
            matched.append(item)
        elif skill.name in implied:
            item = MatchedSkill(**_base(skill), credit=1.0, reason=f"Implied by {implied[skill.name]}")
            matched.append(item)
        elif related := taxonomy.related_to(skill.name, have | set(implied)):
            item = MatchedSkill(**_base(skill), credit=0.5, reason=f"Related experience: {related}")
            partial.append(item)
        else:
            item = MatchedSkill(**_base(skill), credit=0.0, reason="Not in your profile or CV")
            missing.append(item)
        earned += weight * item.credit

    if not have and not known.custom:
        return _no_score(job, "Add your skills or CV in Settings → Career profile to get a match score.")
    if not job.skills:
        return _no_score(job, "No known skills were found in this job description, so it cannot be scored.")

    skills_score = 100 * earned / total
    components = [
        ScoreComponent(
            name="Skills",
            weight=SKILLS_WEIGHT,
            score=round(skills_score, 1),
            detail=f"{len(matched)} matched, {len(partial)} related, {len(missing)} missing "
            "(required skills count double, soft skills half)",
        )
    ]
    if job.min_years_experience and profile.years_experience is not None:
        experience_score = min(1.0, profile.years_experience / job.min_years_experience) * 100
        components.append(
            ScoreComponent(
                name="Experience",
                weight=EXPERIENCE_WEIGHT,
                score=round(experience_score, 1),
                detail=f"You have {profile.years_experience} years; the job asks for {job.min_years_experience}+",
            )
        )
        score = (skills_score * SKILLS_WEIGHT + experience_score * EXPERIENCE_WEIGHT) / 100
    else:
        components[0].weight = 100
        score = skills_score
    final = round(score)

    required_total = [s for s in job.skills if s.importance == Importance.REQUIRED]
    required_have = [s for s in matched if s.importance == Importance.REQUIRED]
    missing_required = [s.name for s in missing if s.importance == Importance.REQUIRED]
    explanation = [f"You cover {len(required_have)} of {len(required_total)} required skills."]
    if missing_required:
        explanation.append(f"Missing required: {', '.join(missing_required[:6])}.")
    if partial:
        explanation.append(
            "Related experience counts half: "
            + "; ".join(f"{p.name} ← {p.reason.split(': ')[1]}" for p in partial[:4])
            + "."
        )
    nice_have = [s.name for s in matched if s.importance == Importance.NICE_TO_HAVE]
    if nice_have:
        explanation.append(f"Nice-to-have skills you bring: {', '.join(nice_have[:5])}.")
    if len(components) == 2:
        explanation.append(components[1].detail + ".")
    elif job.min_years_experience:
        explanation.append(
            f"The job asks for {job.min_years_experience}+ years; "
            "add your years of experience to include it in the score."
        )
    if known.custom:
        explanation.append(f"Not scored (not in the skill list yet): {', '.join(known.custom[:5])}.")

    return MatchResult(
        score=final,
        level=next(label for threshold, label in LEVELS if final >= threshold),
        components=components,
        matched=matched,
        partial=partial,
        missing=missing,
        explanation=explanation,
        recommendations=_recommendations(profile, known, job, missing, partial),
        job=job,
    )


def _base(skill) -> dict:
    return {"name": skill.name, "category": skill.category, "importance": skill.importance}


def _no_score(job: JobAnalysis, reason: str) -> MatchResult:
    return MatchResult(
        score=None,
        level="Not enough information",
        components=[],
        matched=[],
        partial=[],
        missing=[],
        explanation=[reason],
        recommendations=[reason],
        job=job,
    )


def _recommendations(profile, known: _Known, job: JobAnalysis, missing, partial) -> list[str]:
    tips: list[str] = []
    cv_skills = set(taxonomy.find_skills(profile.cv_text))
    in_profile_not_cv = [
        s.name
        for s in job.skills
        if s.importance == Importance.REQUIRED
        and not taxonomy.BY_NAME[s.name].soft
        and known.sources.get(s.name) == "profile"
        and s.name not in cv_skills
    ]
    if profile.cv_text and in_profile_not_cv:
        tips.append(
            f"Mention {', '.join(in_profile_not_cv[:4])} in your CV: the job requires "
            f"{'them' if len(in_profile_not_cv) > 1 else 'it'} and your profile lists "
            f"{'them' if len(in_profile_not_cv) > 1 else 'it'}, but your CV does not."
        )
    hard_missing = [
        s.name for s in missing if s.importance == Importance.REQUIRED and not taxonomy.BY_NAME[s.name].soft
    ]
    if hard_missing:
        tips.append(
            f"Close the biggest gap first: {hard_missing[0]}. A small project or course you can talk about helps."
        )
        if len(hard_missing) > 1:
            tips.append(f"Be ready to explain how you would ramp up on {', '.join(hard_missing[1:4])}.")
    for item in partial[:2]:
        tips.append(f"Frame your {item.reason.split(': ')[1]} experience as transferable to {item.name}.")
    if not profile.cv_text:
        tips.append("Add your CV to your career profile so skills in it are counted too.")
    if job.min_years_experience and profile.years_experience is None:
        tips.append("Add your years of experience to your career profile.")
    if not tips:
        tips.append("Your skills line up well: tailor your CV summary to this role and apply.")
    return tips


# ---------------------------------------------------------------- CV review

_SECTIONS = {
    "Summary": re.compile(r"^\s*(summary|profile|about\s+me|professional\s+summary|objective)\b", re.I | re.M),
    "Experience": re.compile(
        r"^\s*(experience|work\s+experience|employment|professional\s+experience|work\s+history)\b", re.I | re.M
    ),
    "Skills": re.compile(
        r"^\s*(skills|technical\s+skills|tech\s+stack|technologies|core\s+competencies)\b", re.I | re.M
    ),
    "Education": re.compile(r"^\s*(education|academic|qualifications|degrees?)\b", re.I | re.M),
    "Projects": re.compile(r"^\s*(projects|personal\s+projects|portfolio|side\s+projects)\b", re.I | re.M),
}
_BULLET = re.compile(r"^\s*(?:[-•*▪‣–]|\d+[.)])\s+(.+)$", re.M)
_WEAK_PHRASES = (
    "responsible for",
    "worked on",
    "helped with",
    "helped to",
    "duties included",
    "involved in",
    "tasked with",
    "participated in",
    "assisted with",
    "was part of",
)
_ACTION_VERBS = frozenset(
    re.findall(
        r"\w+",
        """
        achieved automated built cut championed collaborated created decreased delivered deployed designed
        developed drove eliminated enabled engineered established expanded implemented improved increased
        introduced launched led maintained managed mentored migrated modernised modernized optimised
        optimized owned planned prototyped reduced refactored replaced resolved restructured saved scaled
        secured shipped simplified spearheaded streamlined tested trained transformed upgraded wrote
        analysed analyzed architected coordinated integrated monitored configured debugged documented
        accelerated
        """,
    )
)
_METRIC = re.compile(r"\d|%|€|\$|£|\bx\d|\bdouble|\btriple|\bhalf\b")
_LINK = re.compile(r"(github\.com|gitlab\.com|linkedin\.com|https?://)", re.I)


def review_cv(cv_text: str, job: JobAnalysis | None = None, profile: CandidateProfile | None = None) -> CvReview:
    """Check a CV for structure, impact and (optionally) keywords from a job description."""
    text = cv_text.strip()
    if not text:
        return CvReview(
            score=None,
            word_count=0,
            sections_found=[],
            checks=[],
            keyword_coverage=None,
            suggestions=[
                CvSuggestion(
                    category="Getting started",
                    priority=Priority.HIGH,
                    title="Add your CV",
                    detail="Paste your CV as plain text into Settings → Career profile "
                    "(or into this form) to get a review.",
                )
            ],
        )

    words = len(text.split())
    sections = [name for name, pattern in _SECTIONS.items() if pattern.search(text)]
    bullets = [m.group(1).strip() for m in _BULLET.finditer(text)]
    statements = bullets or [line.strip() for line in text.splitlines() if len(line.strip()) > 40]
    lower = text.lower()

    checks: list[CvCheck] = []
    suggestions: list[CvSuggestion] = []

    # Length: roughly one to two pages.
    good_length = 250 <= words <= 1000
    checks.append(CvCheck(name="Length", passed=good_length, detail=f"{words} words (aim for about 250-1000)"))
    if words < 250:
        suggestions.append(
            CvSuggestion(
                category="Content",
                priority=Priority.MEDIUM,
                title="Add more detail",
                detail="Your CV is short. Describe 3-5 achievements per recent role and the technologies you used.",
            )
        )
    elif words > 1000:
        suggestions.append(
            CvSuggestion(
                category="Content",
                priority=Priority.MEDIUM,
                title="Tighten it to two pages",
                detail="Recruiters skim. Cut older or less relevant roles to one line and keep the strongest results.",
            )
        )

    # Structure.
    core_missing = [name for name in ("Experience", "Skills", "Education") if name not in sections]
    checks.append(
        CvCheck(
            name="Sections",
            passed=not core_missing,
            detail="Found: " + (", ".join(sections) if sections else "no standard headings"),
        )
    )
    if core_missing:
        suggestions.append(
            CvSuggestion(
                category="Structure",
                priority=Priority.HIGH if "Experience" in core_missing else Priority.MEDIUM,
                title=f"Add clear {', '.join(core_missing)} heading{'s' if len(core_missing) > 1 else ''}",
                detail="Standard headings help applicant tracking systems and recruiters find information quickly.",
            )
        )
    if "Summary" not in sections:
        suggestions.append(
            CvSuggestion(
                category="Structure",
                priority=Priority.LOW,
                title="Open with a short summary",
                detail="Two or three lines on who you are, your core stack and what you are looking for.",
                example="Backend engineer with 4 years of Python and PostgreSQL experience, focused on reliable APIs.",
            )
        )

    # Impact: numbers and strong verbs.
    if statements:
        with_metrics = [s for s in statements if _METRIC.search(s)]
        share = len(with_metrics) / len(statements)
        checks.append(
            CvCheck(
                name="Measurable results",
                passed=share >= 0.3,
                detail=f"{len(with_metrics)} of {len(statements)} statements include a number",
            )
        )
        if share < 0.3:
            example_line = next((s for s in statements if not _METRIC.search(s)), statements[0])
            suggestions.append(
                CvSuggestion(
                    category="Impact",
                    priority=Priority.HIGH,
                    title="Quantify your achievements",
                    detail="Add numbers: users, requests per second, time or money saved, percentages, team size.",
                    example=f"“{_snippet(example_line, 90)}” → add the result, e.g. “…, cutting response time by 40%”.",
                )
            )
        strong = [s for s in statements if s.split()[0].lower().strip(",.:;") in _ACTION_VERBS]
        verb_share = len(strong) / len(statements)
        checks.append(
            CvCheck(
                name="Action verbs",
                passed=verb_share >= 0.5,
                detail=f"{len(strong)} of {len(statements)} statements start with a strong verb",
            )
        )
        if verb_share < 0.5:
            suggestions.append(
                CvSuggestion(
                    category="Impact",
                    priority=Priority.MEDIUM,
                    title="Start statements with strong verbs",
                    detail="Lead with what you did: built, designed, migrated, reduced, automated, led.",
                )
            )

    weak = [phrase for phrase in _WEAK_PHRASES if phrase in lower]
    checks.append(
        CvCheck(
            name="Weak phrases",
            passed=not weak,
            detail="None found" if not weak else "Found: " + ", ".join(f"“{w}”" for w in weak),
        )
    )
    if weak:
        line = next(line for line in text.splitlines() if weak[0] in line.lower())
        suggestions.append(
            CvSuggestion(
                category="Wording",
                priority=Priority.MEDIUM,
                title=f"Replace “{weak[0]}”",
                detail="Passive phrases hide your contribution. Say what you did and what changed because of it.",
                example=f"“{_snippet(line.strip(' -•*'), 90)}” → “Built … which …”",
            )
        )

    first_person = len(re.findall(r"\b(i|my|me)\b", lower))
    checks.append(CvCheck(name="Concise style", passed=first_person <= 3, detail=f"{first_person} first-person words"))
    if first_person > 3:
        suggestions.append(
            CvSuggestion(
                category="Wording",
                priority=Priority.LOW,
                title="Drop “I” and “my”",
                detail="CV statements read better without first-person pronouns: “Designed…”, not “I designed…”.",
            )
        )

    has_link = bool(_LINK.search(text))
    checks.append(
        CvCheck(name="Links", passed=has_link, detail="Profile or portfolio link found" if has_link else "No links")
    )
    if not has_link:
        suggestions.append(
            CvSuggestion(
                category="Content",
                priority=Priority.LOW,
                title="Link your GitHub or portfolio",
                detail="A link to real code (like this project) lets reviewers verify your skills.",
            )
        )

    # Tailoring to the job.
    coverage = None
    if job is not None and job.skills:
        cv_skills = set(taxonomy.find_skills(text))
        cv_skills |= set(taxonomy.implied_by(cv_skills))
        wanted = [
            s.name for s in job.skills if s.importance == Importance.REQUIRED and not taxonomy.BY_NAME[s.name].soft
        ]
        wanted = wanted or [s.name for s in job.skills if not taxonomy.BY_NAME[s.name].soft]
        present = [name for name in wanted if name in cv_skills]
        absent = [name for name in wanted if name not in cv_skills]
        percent = round(100 * len(present) / len(wanted)) if wanted else 100
        coverage = KeywordCoverage(percent=percent, present=present, missing=absent)
        checks.append(
            CvCheck(
                name="Job keywords",
                passed=percent >= 70,
                detail=f"{len(present)} of {len(wanted)} required skills appear in your CV",
            )
        )
        profile_skills = known_skills(profile).names if profile else set()
        profile_skills |= set(taxonomy.implied_by(profile_skills))
        can_add = [name for name in absent if name in profile_skills]
        gaps = [name for name in absent if name not in profile_skills]
        if can_add:
            suggestions.insert(
                0,
                CvSuggestion(
                    category="Tailoring",
                    priority=Priority.HIGH,
                    title=f"Mention {', '.join(can_add[:4])}",
                    detail="The job requires these and your career profile lists them, but your CV does not. "
                    "Add them where you actually used them.",
                ),
            )
        if gaps:
            suggestions.append(
                CvSuggestion(
                    category="Tailoring",
                    priority=Priority.MEDIUM,
                    title=f"Address the gap: {', '.join(gaps[:4])}",
                    detail="Only add skills you have. If you have related experience, describe it; "
                    "otherwise prepare to discuss how you would learn them.",
                )
            )

    passed = sum(check.passed for check in checks)
    order = {Priority.HIGH: 0, Priority.MEDIUM: 1, Priority.LOW: 2}
    suggestions.sort(key=lambda s: order[s.priority])
    return CvReview(
        score=round(100 * passed / len(checks)),
        word_count=words,
        sections_found=sections,
        checks=checks,
        keyword_coverage=coverage,
        suggestions=suggestions,
    )
