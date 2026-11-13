"""AI provider interface.

The API talks to a `CareerAssistant`, never to a specific service. Today the only
provider is the free built-in analyzer, which runs locally with no API key and no
network access.

Adding a hosted AI service later (see README "AI providers"):

1. Implement the `CareerAssistant` protocol in a new module. Read its API key from an
   environment variable (never from code or Git), set `external = True`, and keep the
   built-in analyzer as a fallback when the service fails or times out.
2. Register it in `PROVIDERS` and allow its name in `Settings.ai_provider`.
3. It stays off unless `AI_PROVIDER` is set to its name. Enabling a paid provider must
   be an explicit, approved decision: it sends user data to a third party and costs money.
"""

from functools import cache
from typing import Protocol

from app.ai import analyzer
from app.ai.interview_prep import PrepContext, build_prep
from app.core.config import get_settings
from app.schemas.ai import CvReview, InterviewPrep, JobAnalysis, MatchResult, ProviderInfo


class CareerAssistant(Protocol):
    """What every AI provider must implement."""

    name: str
    external: bool

    def info(self) -> ProviderInfo: ...

    def analyze_job(self, text: str, title: str = "") -> JobAnalysis: ...

    def match(self, profile: analyzer.CandidateProfile, job: JobAnalysis) -> MatchResult: ...

    def review_cv(
        self, cv_text: str, job: JobAnalysis | None, profile: analyzer.CandidateProfile | None
    ) -> CvReview: ...

    def interview_prep(self, context: PrepContext) -> InterviewPrep: ...


class BuiltinAssistant:
    """Free rule-based analyzer: deterministic, private (nothing leaves the server), no API key."""

    name = "builtin"
    external = False

    def info(self) -> ProviderInfo:
        return ProviderInfo(
            name=self.name,
            external=self.external,
            cost="free",
            description="Built-in rule-based analyzer. Runs on this server; your data is not sent anywhere.",
        )

    def analyze_job(self, text: str, title: str = "") -> JobAnalysis:
        return analyzer.analyze_job(text, title)

    def match(self, profile: analyzer.CandidateProfile, job: JobAnalysis) -> MatchResult:
        return analyzer.match(profile, job)

    def review_cv(self, cv_text: str, job: JobAnalysis | None, profile: analyzer.CandidateProfile | None) -> CvReview:
        return analyzer.review_cv(cv_text, job, profile)

    def interview_prep(self, context: PrepContext) -> InterviewPrep:
        return build_prep(context)


PROVIDERS: dict[str, type[CareerAssistant]] = {"builtin": BuiltinAssistant}


@cache
def _provider(name: str) -> CareerAssistant:
    return PROVIDERS[name]()


def get_assistant() -> CareerAssistant:
    """FastAPI dependency: the configured provider (override it in tests)."""
    return _provider(get_settings().ai_provider)
