"""Role-specific interview preparation built from the job analysis and the user's own data."""

from dataclasses import dataclass, field

from app.ai import skills as taxonomy
from app.schemas.ai import Importance, InterviewPrep, JobAnalysis, MatchResult, PrepQuestion, UpcomingInterview

# Core questions for each kind of role.
FAMILY_QUESTIONS: dict[str, list[tuple[str, str]]] = {
    "backend": [
        (
            "Design a URL shortener (or a rate limiter). Walk through the API, data model and how it scales.",
            "Clarify requirements first, then API → data model → bottlenecks → trade-offs.",
        ),
        (
            "How do you make an API endpoint idempotent, and why does it matter?",
            "Mention retries, idempotency keys and unique constraints.",
        ),
        (
            "A query that was fast is now slow in production. How do you investigate?",
            "EXPLAIN ANALYZE, indexes, N+1 queries, locks, recent data growth.",
        ),
        (
            "How do you handle database schema changes without downtime?",
            "Expand/contract migrations, backfills, backwards-compatible deploys.",
        ),
    ],
    "frontend": [
        (
            "How do you keep a large React app fast?",
            "Measure first (profiler, Web Vitals), then memoisation, code splitting, virtualisation.",
        ),
        (
            "How do you manage server state vs. client state?",
            "Contrast a query cache (e.g. TanStack Query) with local UI state.",
        ),
        (
            "How do you make a custom component accessible?",
            "Semantic HTML first, keyboard support, focus management, ARIA only when needed.",
        ),
        (
            "Walk through what happens between typing a URL and seeing the page.",
            "DNS, TLS, HTTP, parsing, critical rendering path, hydration.",
        ),
    ],
    "fullstack": [
        (
            "Design a feature end to end: data model, API, UI and tests.",
            "Show you can make trade-offs across layers and keep the contract typed.",
        ),
        (
            "How do you keep the frontend and backend in sync when the API changes?",
            "Generated types from OpenAPI, versioning, contract tests in CI.",
        ),
        (
            "Where do you validate data, and why there?",
            "Both: the client for UX, the server (and database constraints) for correctness.",
        ),
        (
            "How do you debug an issue that only happens in production?",
            "Logs, metrics, tracing, reproducing with production-like data, feature flags.",
        ),
    ],
    "data": [
        (
            "Design a daily pipeline that loads events into a warehouse. How do you make it reliable?",
            "Idempotent loads, partitioning, late data, backfills, data quality checks.",
        ),
        ("How do you model data for analytics?", "Facts and dimensions, slowly changing dimensions, grain."),
        (
            "A dashboard number looks wrong. How do you trace it?",
            "Lineage, compare at each step, check joins and duplicates.",
        ),
        ("Batch or streaming: how do you choose?", "Latency needs, cost, complexity, correctness guarantees."),
    ],
    "ml": [
        (
            "Take a model from notebook to production. What changes?",
            "Reproducibility, feature pipelines, serving, monitoring, retraining.",
        ),
        (
            "How do you evaluate a model beyond accuracy?",
            "Baselines, the right metric for the cost of errors, slices, calibration.",
        ),
        (
            "How would you detect and handle data drift?",
            "Monitor input and prediction distributions; alerting and retraining policy.",
        ),
        (
            "When would you not use machine learning?",
            "When rules work, data is scarce or explainability requirements are strict.",
        ),
    ],
    "devops": [
        (
            "Walk through your ideal CI/CD pipeline for a web service.",
            "Build once, test, scan, deploy progressively, roll back automatically.",
        ),
        (
            "A service is down at 3 a.m. What do you do?",
            "Mitigate first, communicate, then root cause and a blameless post-mortem.",
        ),
        (
            "How do you manage infrastructure changes safely?",
            "Infrastructure as code, reviews, plans, small changes, drift detection.",
        ),
        (
            "What do you monitor for a web service, and what do you alert on?",
            "Golden signals / SLOs; alert on symptoms users feel, not every metric.",
        ),
    ],
    "mobile": [
        (
            "How do you handle offline use and syncing?",
            "Local storage, conflict resolution, background sync, optimistic UI.",
        ),
        (
            "How do you keep an app fast and battery-friendly?",
            "Profiling, lazy loading, image handling, avoiding unnecessary work.",
        ),
        (
            "How do you release safely to app stores?",
            "Staged rollouts, feature flags, crash monitoring, forced-update strategy.",
        ),
    ],
    "qa": [
        (
            "How do you decide what to automate?",
            "Risk and frequency; the testing pyramid; keep end-to-end tests few and stable.",
        ),
        ("A test is flaky. What do you do?", "Find the cause (timing, shared state, data); never just add retries."),
        ("How do you test an API?", "Contract, validation, auth, error cases, idempotency, performance."),
    ],
    "security": [
        (
            "Walk through the OWASP Top 10 risks most relevant to a web API.",
            "Broken access control, injection, auth failures; show concrete mitigations.",
        ),
        (
            "How would you threat-model a new feature?",
            "Assets, entry points, trust boundaries, STRIDE, prioritised mitigations.",
        ),
        (
            "How should passwords and secrets be stored?",
            "Slow salted hashes (Argon2/bcrypt), a secrets manager, rotation, no secrets in Git.",
        ),
    ],
    "general": [
        (
            "Tell me about the most complex system you have worked on.",
            "Explain the architecture, your part in it, and one hard trade-off.",
        ),
        (
            "How do you make sure your code is correct and maintainable?",
            "Tests, reviews, small changes, clear naming, documentation.",
        ),
        (
            "Describe a technical decision you would make differently today.",
            "Show reflection: what you learned and how you decide now.",
        ),
    ],
}

SKILL_QUESTIONS: dict[str, tuple[str, str]] = {
    "Python": (
        "What happens when you use a mutable default argument in Python?",
        "Defaults are evaluated once; use None and create the object inside.",
    ),
    "FastAPI": (
        "How do dependencies work in FastAPI, and how do you use them for auth?",
        "Dependency injection, overriding them in tests, per-request sessions.",
    ),
    "Django": (
        "How do you find and fix N+1 queries in Django?",
        "select_related / prefetch_related, query logging, assertNumQueries.",
    ),
    "Flask": (
        "How would you structure a growing Flask application?",
        "Blueprints, application factory, configuration per environment.",
    ),
    "SQL": (
        "Explain the difference between INNER, LEFT and anti joins, with an example.",
        "Write the query; mention NULL handling.",
    ),
    "PostgreSQL": (
        "How do indexes work in PostgreSQL, and when would an index not be used?",
        "B-tree basics, selectivity, functions on columns, EXPLAIN.",
    ),
    "MySQL": ("How do transactions and isolation levels work in MySQL (InnoDB)?", "Read phenomena, locking, MVCC."),
    "Redis": (
        "What would you use Redis for, and what are the risks?",
        "Caching, rate limiting, queues; eviction, persistence, cache invalidation.",
    ),
    "MongoDB": (
        "How do you model one-to-many relationships in MongoDB?",
        "Embed vs. reference, based on access patterns and document growth.",
    ),
    "Docker": (
        "How do you make a Docker image small and secure?",
        "Multi-stage builds, slim base images, non-root user, .dockerignore.",
    ),
    "Kubernetes": (
        "What is the difference between a Deployment, a Service and an Ingress?",
        "Explain how traffic reaches a pod and how rollouts work.",
    ),
    "AWS": (
        "Which AWS services would you use to run a web API, and why?",
        "Compute choice (ECS/Lambda), RDS, load balancer, IAM least privilege.",
    ),
    "Azure": (
        "How would you deploy and secure a web API on Azure?",
        "App Service or AKS, managed identities, Key Vault.",
    ),
    "GCP": ("How would you deploy a containerised service on Google Cloud?", "Cloud Run vs. GKE, Cloud SQL, IAM."),
    "Terraform": (
        "How do you manage Terraform state in a team?",
        "Remote state, locking, workspaces or separate stacks, plan in CI.",
    ),
    "CI/CD": (
        "What should run in CI before code can be merged?",
        "Lint, type check, tests, build, security scans; fast feedback.",
    ),
    "React": (
        "When does a React component re-render, and how do you avoid unnecessary renders?",
        "State/props/context changes; memo, useMemo, splitting components.",
    ),
    "TypeScript": (
        "How do you type an API response safely?",
        "Generated types or runtime validation (e.g. Zod) at the boundary.",
    ),
    "JavaScript": (
        "Explain the event loop, promises and async/await.",
        "Call stack, task and microtask queues, error handling.",
    ),
    "Node.js": (
        "How do you avoid blocking the Node.js event loop?",
        "Async I/O, worker threads for CPU work, streaming.",
    ),
    "Java": (
        "How does garbage collection work in the JVM, and when does it hurt?",
        "Generations, pause times, tuning basics.",
    ),
    "Spring Boot": (
        "How do you manage transactions in Spring Boot?",
        "@Transactional, propagation, pitfalls with self-invocation.",
    ),
    "Go": (
        "How do goroutines and channels work, and how do you avoid leaks?",
        "Context cancellation, closing channels, WaitGroups.",
    ),
    "Kafka": (
        "How does Kafka guarantee ordering, and how do consumers scale?",
        "Partitions, keys, consumer groups, offsets, at-least-once.",
    ),
    "Microservices": (
        "When would you not split a system into microservices?",
        "Team size, operational cost, distributed transactions.",
    ),
    "REST APIs": (
        "How do you design pagination and errors for a REST API?",
        "Limit/offset vs. cursor, consistent error format, status codes.",
    ),
    "GraphQL": (
        "What problems does GraphQL solve, and what new ones does it create?",
        "Over/under-fetching vs. caching, N+1, query cost limits.",
    ),
    "Testing": (
        "How do you decide what to unit test vs. integration test?",
        "Business rules in unit tests; real database and HTTP in integration tests.",
    ),
    "System design": (
        "How would you scale a read-heavy service to 10x traffic?",
        "Caching, read replicas, CDN, measure before optimising.",
    ),
    "Machine learning": (
        "How do you prevent data leakage when training a model?",
        "Split before preprocessing, time-based splits, careful feature design.",
    ),
    "LLMs": (
        "How would you reduce hallucinations in an LLM feature?",
        "Retrieval with sources, constrained output, evaluation sets, fallbacks.",
    ),
    "Spark": (
        "Why can a Spark job be slow, and how do you fix it?",
        "Shuffles, skew, partition sizes, caching, broadcast joins.",
    ),
    "Airflow": (
        "How do you make Airflow tasks idempotent and safe to retry?",
        "Deterministic outputs per run date, upserts, no hidden state.",
    ),
    "Agile": (
        "How do you handle scope changes in the middle of a sprint?",
        "Make the trade-off visible; agree with the product owner what moves out.",
    ),
    "Application security": (
        "How do you protect an API against broken access control?",
        "Check ownership on every request; return 404 for others' records.",
    ),
    "Observability": (
        "What would you log, measure and trace in a new service?",
        "Structured logs, RED/USE metrics, trace IDs across services.",
    ),
    "CSS": (
        "How do you build layouts that work on every screen size?",
        "Flexbox/grid, mobile-first, fluid sizes, testing on real devices.",
    ),
    "Accessibility": (
        "How do you test a page for accessibility?",
        "Keyboard-only use, a screen reader, automated checks, colour contrast.",
    ),
}

BEHAVIORAL: dict[str, list[tuple[str, str]]] = {
    "all": [
        (
            "Tell me about a project you are proud of.",
            "Pick one with a clear result; explain your part, not just the team's.",
        ),
        (
            "Describe a time you disagreed with a teammate. What happened?",
            "Show you listened, used data, and kept the relationship.",
        ),
        (
            "Tell me about a mistake you made and what you learned.",
            "Own it, explain the fix and what you changed afterwards.",
        ),
        ("Describe a time you had to learn something quickly.", "Show your learning process and the result."),
        ("Tell me about a time you improved a process or a system.", "Before → what you did → measurable after."),
    ],
    "senior": [
        (
            "Tell me about a time you influenced a technical decision without authority.",
            "Writing proposals, prototypes, aligning stakeholders.",
        ),
        ("How have you helped other engineers grow?", "Mentoring, code reviews, pairing; give a concrete example."),
    ],
    "junior": [
        (
            "How do you ask for help when you are stuck?",
            "Show you try first, then ask with context and what you tried.",
        ),
        ("What have you built outside work or study?", "Talk about a project you can show, like a portfolio app."),
    ],
}

QUESTIONS_TO_ASK: dict[str, list[str]] = {
    "all": [
        "What does success look like in this role after 3 and 12 months?",
        "What are the biggest challenges the team is facing right now?",
        "How does the team decide what to build next?",
        "How are code reviews, testing and deployments done?",
        "What does the interview process look like from here?",
    ],
    "backend": ["How do you handle on-call and production incidents?"],
    "frontend": ["How do designers and engineers work together here?"],
    "fullstack": ["How is work split between frontend and backend?"],
    "data": ["Who consumes the data, and how is data quality measured?"],
    "ml": ["How do models get from experiment to production here?"],
    "devops": ["What does your deployment frequency and incident rate look like?"],
}

TYPE_TIPS = {
    "phone": "Phone screen: prepare a 60-second introduction and your salary range; keep notes in front of you.",
    "video": "Video call: test camera, microphone and screen sharing; use a quiet, well-lit room.",
    "technical": "Technical round: think out loud, ask clarifying questions, and test your solution with examples.",
    "behavioral": "Behavioural round: prepare 5-6 STAR stories that you can adapt to different questions.",
    "onsite": "On-site: plan the route, arrive 10 minutes early, bring a copy of your CV and questions.",
    "other": "Confirm the format and who you will meet, so you can prepare the right examples.",
}


@dataclass
class PrepContext:
    job: JobAnalysis
    company: str | None = None
    company_industry: str = ""
    company_website: str = ""
    company_notes: str = ""
    match: MatchResult | None = None
    upcoming: list[UpcomingInterview] = field(default_factory=list)


def build_prep(context: PrepContext) -> InterviewPrep:
    job = context.job
    family = job.role_family if job.role_family in FAMILY_QUESTIONS else "general"

    focus = [s.name for s in job.skills if s.importance == Importance.REQUIRED and not taxonomy.BY_NAME[s.name].soft]
    focus = (focus or [s.name for s in job.skills if not taxonomy.BY_NAME[s.name].soft])[:8]

    technical = [
        PrepQuestion(question=q, topic=f"{family.capitalize()} fundamentals", tip=t)
        for q, t in FAMILY_QUESTIONS[family]
    ]
    for name in focus:
        if name in SKILL_QUESTIONS:
            question, tip = SKILL_QUESTIONS[name]
        else:
            question, tip = (
                f"Tell me about a project where you used {name}. What would you do differently?",
                "Be specific: the problem, your decisions and the measurable result.",
            )
        technical.append(PrepQuestion(question=question, topic=name, tip=tip))

    seniority_key = (
        "senior"
        if job.seniority in ("Senior", "Lead", "Staff / Principal")
        else ("junior" if job.seniority in ("Junior", "Intern") else None)
    )
    behavioral_source = BEHAVIORAL["all"] + (BEHAVIORAL[seniority_key] if seniority_key else [])
    behavioral = [PrepQuestion(question=q, topic="Behavioural (STAR)", tip=t) for q, t in behavioral_source]
    soft = [s.name for s in job.skills if taxonomy.BY_NAME[s.name].category == taxonomy.SOFT][:3]
    for name in soft:
        behavioral.append(
            PrepQuestion(
                question=f"The job mentions {name.lower()}. Give an example where it made a difference.",
                topic=name,
                tip="Use the STAR format: Situation, Task, Action, Result.",
            )
        )

    gaps: list[PrepQuestion] = []
    if context.match is not None and context.match.score is not None:
        for item in context.match.missing:
            if item.importance == Importance.REQUIRED and not taxonomy.BY_NAME[item.name].soft:
                gaps.append(
                    PrepQuestion(
                        question=f"You have not listed {item.name}. How would you get productive with it quickly?",
                        topic=item.name,
                        tip="Be honest; connect it to something similar you know "
                        "and describe a concrete learning plan.",
                    )
                )
        gaps = gaps[:4]  # leave room for related skills
        for item in context.match.partial[:2]:
            related = item.reason.split(": ")[-1]
            gaps.append(
                PrepQuestion(
                    question=f"The role uses {item.name}; you know {related}. What carries over and what is different?",
                    topic=item.name,
                    tip="Show you understand the concepts, not just the tool.",
                )
            )

    ask = QUESTIONS_TO_ASK["all"] + QUESTIONS_TO_ASK.get(family, [])
    company = context.company
    research = [
        f"Read {company}'s website{f' ({context.company_website})' if context.company_website else ''}: "
        "product, customers, business model."
        if company
        else "Read the company's website: product, customers and business model.",
        "Look up the interviewers on LinkedIn and the team's engineering blog or GitHub.",
        "Check recent news, funding and job postings to understand where the company is heading.",
        f"Prepare why you want this role{f' at {company}' if company else ''} in two or three sentences.",
    ]
    if context.company_industry:
        research.insert(1, f"Learn the basics of the {context.company_industry} industry and its main competitors.")
    if context.company_notes:
        research.append(f"Your notes on {company or 'the company'}: {context.company_notes[:200]}")

    tips = [
        "Prepare a 2-minute story of your background that ends with why this role fits.",
        f"Revise the focus skills: {', '.join(focus[:5])}."
        if focus
        else "Revise the core skills from the job description.",
    ]
    seen_types = []
    for interview in context.upcoming:
        if interview.interview_type.value not in seen_types:
            seen_types.append(interview.interview_type.value)
            tips.append(TYPE_TIPS[interview.interview_type.value])
    if job.min_years_experience:
        tips.append(f"Have examples ready that show {job.min_years_experience}+ years of relevant experience.")

    return InterviewPrep(
        title=job.title,
        company=company,
        role_family=family,
        seniority=job.seniority,
        focus_skills=focus,
        technical_questions=technical,
        behavioral_questions=behavioral,
        gap_questions=gaps[:6],
        questions_to_ask=ask,
        company_research=research,
        tips=tips,
        upcoming_interviews=context.upcoming,
    )
