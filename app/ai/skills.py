"""Skill taxonomy and extraction for the built-in analyzer.

Each skill has a canonical name, a category and regular-expression aliases that are
matched against lower-cased text with "word" boundaries that also treat '+', '#' and
digits as part of a word. This keeps look-alikes apart: Java is not found in
"JavaScript", SQL is not found in "NoSQL" or "PostgreSQL", C is never guessed from
"C++" or "C#".
"""

import re
from dataclasses import dataclass
from functools import cache

# Categories, in display order.
LANGUAGES = "Languages"
FRAMEWORKS = "Frameworks & libraries"
DATABASES = "Databases"
CLOUD = "Cloud & DevOps"
DATA_AI = "Data & AI"
PRACTICES = "Practices"
SOFT = "Soft skills"
SPOKEN = "Spoken languages"

CATEGORY_ORDER = (LANGUAGES, FRAMEWORKS, DATABASES, CLOUD, DATA_AI, PRACTICES, SOFT, SPOKEN)


@dataclass(frozen=True)
class Skill:
    name: str
    category: str
    patterns: tuple[str, ...]
    # Patterns matched against the original text, case-sensitively (for short,
    # ambiguous names such as the Go language).
    exact_patterns: tuple[str, ...] = ()

    @property
    def soft(self) -> bool:
        return self.category in (SOFT, SPOKEN)


def _s(name: str, category: str, *patterns: str, exact: tuple[str, ...] = ()) -> Skill:
    return Skill(name, category, patterns or (re.escape(name.lower()),), exact)


SKILLS: tuple[Skill, ...] = (
    # Languages
    _s("Python", LANGUAGES, r"python[23]?"),
    _s("Java", LANGUAGES, r"java(?!\s*script)"),
    _s("Kotlin", LANGUAGES),
    _s("Scala", LANGUAGES),
    _s("JavaScript", LANGUAGES, r"javascript", r"ecmascript", r"es20\d\d", r"es6", r"js"),
    _s("TypeScript", LANGUAGES, r"typescript"),
    _s(
        "Go",
        LANGUAGES,
        r"golang",
        r"go\s*lang",
        exact=(r"(?<![\w.\-])Go(?![\w\-])(?!\s+(?:to|ahead|beyond|live|above|further|back)\b)",),
    ),
    _s("Rust", LANGUAGES),
    _s("C#", LANGUAGES, r"c#", r"c\s*sharp", r"csharp"),
    _s("C++", LANGUAGES, r"c\+\+", r"cpp"),
    _s(".NET", LANGUAGES, r"\.net(?:\s*core)?", r"dotnet", r"asp\.net(?:\s*core)?"),
    _s("PHP", LANGUAGES),
    _s("Ruby", LANGUAGES),
    _s("Swift", LANGUAGES, r"swift(?:ui)?"),
    _s("Dart", LANGUAGES),
    _s("Elixir", LANGUAGES),
    _s("Bash", LANGUAGES, r"bash", r"shell\s+scripting", r"shell\s+scripts?"),
    _s("SQL", LANGUAGES, r"sql"),
    _s("HTML", LANGUAGES, r"html5?"),
    _s("CSS", LANGUAGES, r"css3?", r"scss", r"sass"),
    # Frameworks & libraries
    _s("FastAPI", FRAMEWORKS, r"fast\s?api"),
    _s("Django", FRAMEWORKS, r"django(?:\s+rest\s+framework)?", r"drf"),
    _s("Flask", FRAMEWORKS),
    _s("SQLAlchemy", FRAMEWORKS),
    _s("Pydantic", FRAMEWORKS),
    _s("Celery", FRAMEWORKS),
    _s("Spring Boot", FRAMEWORKS, r"spring\s*boot", r"spring\s+framework", r"spring\s+mvc"),
    _s("Node.js", FRAMEWORKS, r"node\.?js", r"node(?=\s+(?:backend|developer|engineer|services?)\b)"),
    _s("Express", FRAMEWORKS, r"express\.?js"),
    _s("NestJS", FRAMEWORKS, r"nest\.?js"),
    _s("React", FRAMEWORKS, r"react(?:\.?js)?(?!\s+native)(?!\s+(?:to|quickly|fast|swiftly)\b)"),
    _s("React Native", FRAMEWORKS, r"react\s+native"),
    _s("Next.js", FRAMEWORKS, r"next\.?js"),
    _s("Redux", FRAMEWORKS),
    _s("Vue", FRAMEWORKS, r"vue(?:\.?js)?", r"nuxt(?:\.?js)?"),
    _s("Angular", FRAMEWORKS, r"angular(?:js)?"),
    _s("Svelte", FRAMEWORKS, r"svelte(?:kit)?"),
    _s("Tailwind CSS", FRAMEWORKS, r"tailwind(?:\s*css)?"),
    _s("Rails", FRAMEWORKS, r"ruby\s+on\s+rails", r"rails"),
    _s("Laravel", FRAMEWORKS),
    _s("Flutter", FRAMEWORKS),
    _s("GraphQL", FRAMEWORKS),
    _s("gRPC", FRAMEWORKS, r"grpc"),
    _s("Pandas", FRAMEWORKS),
    _s("NumPy", FRAMEWORKS, r"numpy"),
    _s("scikit-learn", FRAMEWORKS, r"scikit[\s-]?learn", r"sklearn"),
    _s("TensorFlow", FRAMEWORKS, r"tensorflow", r"keras"),
    _s("PyTorch", FRAMEWORKS, r"pytorch", r"torch"),
    _s("pytest", FRAMEWORKS),
    _s("Jest", FRAMEWORKS, r"jest", r"vitest"),
    _s("Cypress", FRAMEWORKS),
    _s("Playwright", FRAMEWORKS),
    _s("Selenium", FRAMEWORKS),
    # Databases
    _s("PostgreSQL", DATABASES, r"postgres(?:ql)?", r"psql"),
    _s("MySQL", DATABASES, r"mysql", r"mariadb"),
    _s("SQL Server", DATABASES, r"sql\s+server", r"mssql", r"t-sql"),
    _s("Oracle", DATABASES, r"oracle(?:\s+(?:database|db))?"),
    _s("SQLite", DATABASES),
    _s("MongoDB", DATABASES, r"mongo(?:db)?"),
    _s("Redis", DATABASES),
    _s("Elasticsearch", DATABASES, r"elastic\s?search", r"opensearch"),
    _s("DynamoDB", DATABASES),
    _s("Cassandra", DATABASES),
    _s("NoSQL", DATABASES, r"nosql"),
    _s("Snowflake", DATABASES),
    _s("BigQuery", DATABASES, r"big\s?query"),
    # Cloud & DevOps
    _s("AWS", CLOUD, r"aws", r"amazon\s+web\s+services"),
    _s("Azure", CLOUD, r"(?:microsoft\s+)?azure"),
    _s("GCP", CLOUD, r"gcp", r"google\s+cloud(?:\s+platform)?"),
    _s("Docker", CLOUD, r"docker(?:\s+compose)?", r"containeri[sz](?:ation|ed)"),
    _s("Kubernetes", CLOUD, r"kubernetes", r"k8s", r"helm", r"eks", r"aks", r"gke", r"openshift"),
    _s("Terraform", CLOUD),
    _s(
        "Infrastructure as code", CLOUD, r"infrastructure\s+as\s+code", r"iac", r"pulumi", r"cloudformation", r"ansible"
    ),
    _s(
        "CI/CD", CLOUD, r"ci\s*/\s*cd", r"cicd", r"continuous\s+(?:integration|delivery|deployment)", r"ci\s+pipelines?"
    ),
    _s("GitHub Actions", CLOUD, r"github\s+actions"),
    _s("GitLab CI", CLOUD, r"gitlab(?:\s+ci)?"),
    _s("Jenkins", CLOUD),
    _s("Linux", CLOUD, r"linux", r"unix"),
    _s("Git", CLOUD, r"git"),
    _s("Serverless", CLOUD, r"serverless", r"aws\s+lambda", r"lambda\s+functions?", r"cloud\s+functions?"),
    _s(
        "Observability",
        CLOUD,
        r"observability",
        r"monitoring",
        r"prometheus",
        r"grafana",
        r"datadog",
        r"opentelemetry",
        r"new\s+relic",
        r"sentry",
    ),
    _s("Kafka", CLOUD, r"(?:apache\s+)?kafka"),
    _s("RabbitMQ", CLOUD, r"rabbit\s?mq"),
    _s("Nginx", CLOUD),
    # Data & AI
    _s("Machine learning", DATA_AI, r"machine\s+learning", r"ml", r"deep\s+learning"),
    _s(
        "LLMs",
        DATA_AI,
        r"llms?",
        r"large\s+language\s+models?",
        r"generative\s+ai",
        r"gen\s?ai",
        r"prompt\s+engineering",
        r"rag",
    ),
    _s("NLP", DATA_AI, r"nlp", r"natural\s+language\s+processing"),
    _s("Data analysis", DATA_AI, r"data\s+analy(?:sis|tics)", r"analytics"),
    _s("Statistics", DATA_AI, r"statistics", r"statistical"),
    _s("ETL", DATA_AI, r"etl", r"elt", r"data\s+pipelines?"),
    _s("Spark", DATA_AI, r"(?:apache\s+)?spark", r"pyspark", r"databricks"),
    _s("Airflow", DATA_AI, r"(?:apache\s+)?airflow"),
    _s("dbt", DATA_AI),
    _s("Tableau", DATA_AI),
    _s("Power BI", DATA_AI, r"power\s?bi"),
    # Practices
    _s(
        "REST APIs",
        PRACTICES,
        r"rest(?:ful)?\s+(?:apis?|services?|endpoints?|interfaces?)",
        r"restful",
        r"rest(?=\s*/\s*graphql)",
    ),
    _s("API design", PRACTICES, r"api\s+design", r"designing\s+apis", r"openapi", r"swagger"),
    _s("Microservices", PRACTICES, r"micro-?services?"),
    _s(
        "System design",
        PRACTICES,
        r"system\s+design",
        r"software\s+architecture",
        r"scalab(?:le|ility)",
        r"high[\s-]availability",
    ),
    _s("Distributed systems", PRACTICES, r"distributed\s+systems?"),
    _s(
        "Testing",
        PRACTICES,
        r"(?:unit|integration|end-to-end|e2e|automated)\s+test(?:s|ing)?",
        r"test\s+automation",
        r"tdd",
        r"test-driven",
        r"testing",
    ),
    _s(
        "Application security",
        PRACTICES,
        r"(?:application|web|software)\s+security",
        r"owasp",
        r"oauth\s?2?",
        r"secure\s+coding",
        r"authentication",
    ),
    _s(
        "Performance optimization",
        PRACTICES,
        r"performance\s+(?:tuning|optimi[sz]ation)",
        r"optimi[sz]e\s+performance",
        r"profiling",
    ),
    _s("Data modeling", PRACTICES, r"data\s+model(?:l)?ing", r"database\s+design", r"schema\s+design"),
    _s("Accessibility", PRACTICES, r"accessibility", r"a11y", r"wcag"),
    _s("Responsive design", PRACTICES, r"responsive\s+(?:design|web|ui|layouts?)", r"mobile[\s-]first"),
    _s("Agile", PRACTICES, r"agile", r"scrum", r"kanban"),
    _s("Code review", PRACTICES, r"code\s+reviews?"),
    # Soft skills
    _s("Communication", SOFT, r"communication", r"communicat(?:e|or|ing)"),
    _s("Teamwork", SOFT, r"team\s?work", r"team\s+player", r"collaborat(?:e|ion|ive|ing)"),
    _s("Leadership", SOFT, r"leadership", r"lead(?:ing)?\s+(?:a\s+)?teams?", r"mentor(?:ing|ship)?", r"coaching"),
    _s("Problem solving", SOFT, r"problem[\s-]solv(?:ing|er)", r"analytical\s+(?:skills|thinking|mind)"),
    _s("Ownership", SOFT, r"ownership", r"self[\s-]starter", r"proactive", r"autonomous(?:ly)?"),
    _s("Stakeholder management", SOFT, r"stakeholders?"),
    # Spoken languages
    _s("English", SPOKEN),
    _s("German", SPOKEN, r"german", r"deutsch"),
    _s("French", SPOKEN),
    _s("Spanish", SPOKEN),
    _s("Dutch", SPOKEN),
)

BY_NAME: dict[str, Skill] = {skill.name: skill for skill in SKILLS}
_BY_LOWER: dict[str, Skill] = {skill.name.lower(): skill for skill in SKILLS}

# Knowing the key implies knowing each value (full credit).
IMPLIES: dict[str, tuple[str, ...]] = {
    "PostgreSQL": ("SQL",),
    "MySQL": ("SQL",),
    "SQL Server": ("SQL",),
    "Oracle": ("SQL",),
    "SQLite": ("SQL",),
    "SQLAlchemy": ("Python", "SQL"),
    "FastAPI": ("Python", "REST APIs"),
    "Django": ("Python",),
    "Flask": ("Python",),
    "Pydantic": ("Python",),
    "Celery": ("Python",),
    "Pandas": ("Python",),
    "NumPy": ("Python",),
    "scikit-learn": ("Python", "Machine learning"),
    "PyTorch": ("Machine learning",),
    "TensorFlow": ("Machine learning",),
    "pytest": ("Testing", "Python"),
    "Jest": ("Testing", "JavaScript"),
    "Cypress": ("Testing",),
    "Playwright": ("Testing",),
    "Selenium": ("Testing",),
    "TypeScript": ("JavaScript",),
    "React": ("JavaScript",),
    "Next.js": ("React", "JavaScript"),
    "Redux": ("React", "JavaScript"),
    "React Native": ("React", "JavaScript"),
    "Vue": ("JavaScript",),
    "Angular": ("TypeScript", "JavaScript"),
    "Svelte": ("JavaScript",),
    "Node.js": ("JavaScript",),
    "Express": ("Node.js", "JavaScript"),
    "NestJS": ("Node.js", "TypeScript", "JavaScript"),
    "Spring Boot": ("Java",),
    "Rails": ("Ruby",),
    "Laravel": ("PHP",),
    "Flutter": ("Dart",),
    "Kubernetes": ("Docker",),
    "GitHub Actions": ("CI/CD", "Git"),
    "GitLab CI": ("CI/CD", "Git"),
    "Jenkins": ("CI/CD",),
    "Terraform": ("Infrastructure as code",),
    "Spark": ("ETL",),
    "Airflow": ("ETL",),
    "dbt": ("SQL", "ETL"),
    "Tailwind CSS": ("CSS",),
    "Microservices": ("Distributed systems",),
}

# Skills in the same group are related: knowing one gives half credit for another.
RELATED_GROUPS: tuple[frozenset[str], ...] = tuple(
    frozenset(group)
    for group in (
        {"PostgreSQL", "MySQL", "SQL Server", "Oracle", "SQLite"},
        {"MongoDB", "DynamoDB", "Cassandra", "NoSQL", "Redis"},
        {"Snowflake", "BigQuery"},
        {"AWS", "Azure", "GCP"},
        {"React", "Vue", "Angular", "Svelte"},
        {"FastAPI", "Django", "Flask"},
        {"Spring Boot", ".NET", "Express", "NestJS", "Rails", "Laravel"},
        {"Java", "Kotlin", "Scala", "C#"},
        {"JavaScript", "TypeScript"},
        {"GitHub Actions", "GitLab CI", "Jenkins", "CI/CD"},
        {"Kafka", "RabbitMQ", "Celery"},
        {"TensorFlow", "PyTorch", "scikit-learn"},
        {"Terraform", "Infrastructure as code"},
        {"Jest", "pytest"},
        {"Cypress", "Playwright", "Selenium"},
        {"Tableau", "Power BI"},
        {"React Native", "Flutter", "Swift"},
        {"Spark", "Airflow", "dbt", "ETL"},
        {"Docker", "Kubernetes", "Serverless"},
        {"Machine learning", "NLP", "LLMs"},
    )
)

_BOUNDARY_BEFORE = r"(?<![a-z0-9+#])"
_BOUNDARY_AFTER = r"(?![a-z0-9+#])"


@cache
def _compiled() -> tuple[tuple[Skill, re.Pattern[str], re.Pattern[str] | None], ...]:
    compiled = []
    for skill in SKILLS:
        lower = re.compile(_BOUNDARY_BEFORE + "(?:" + "|".join(skill.patterns) + ")" + _BOUNDARY_AFTER)
        exact = re.compile("|".join(skill.exact_patterns)) if skill.exact_patterns else None
        compiled.append((skill, lower, exact))
    return tuple(compiled)


def find_skills(text: str) -> dict[str, int]:
    """Return {canonical skill name: number of mentions} found in the text."""
    if not text:
        return {}
    lower = text.lower()
    found: dict[str, int] = {}
    for skill, pattern, exact in _compiled():
        count = len(pattern.findall(lower))
        if exact is not None:
            count += len(exact.findall(text))
        if count:
            found[skill.name] = count
    return found


def canonical_skill(value: str) -> str | None:
    """Map one user-entered skill ("postgres", "k8s", "Node") to its canonical name, if known."""
    cleaned = value.strip()
    if not cleaned:
        return None
    direct = _BY_LOWER.get(cleaned.lower())
    if direct is not None:
        return direct.name
    found = set(find_skills(cleaned))
    if len(found) == 1:
        return found.pop()
    # "Ruby on Rails" finds Ruby and Rails; Rails implies Ruby, so it is the answer.
    for name in sorted(found):
        if found - {name} <= set(IMPLIES.get(name, ())):
            return name
    return None


def implied_by(have: set[str]) -> dict[str, str]:
    """Skills implied by the ones a person has: {implied skill: the skill that implies it}."""
    implied: dict[str, str] = {}
    for skill in sorted(have):
        for target in IMPLIES.get(skill, ()):
            if target not in have:
                implied.setdefault(target, skill)
    return implied


def related_to(skill: str, have: set[str]) -> str | None:
    """A skill the person has that is related to `skill` (half credit), if any."""
    for group in RELATED_GROUPS:
        if skill in group:
            for other in sorted(group - {skill}):
                if other in have:
                    return other
    return None
