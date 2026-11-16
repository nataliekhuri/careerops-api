"""Sanity checks for the deployment files, so mistakes are caught in CI before Render sees them."""

import re
from pathlib import Path

import yaml

from app.main import app

ROOT = Path(__file__).resolve().parent.parent
BLUEPRINT = yaml.safe_load((ROOT / "render.yaml").read_text(encoding="utf-8"))
SERVICE = next(s for s in BLUEPRINT["services"] if s["name"] == "careerops-api")
WEB = next(s for s in BLUEPRINT["services"] if s["name"] == "careerops-web")
DATABASE = next(d for d in BLUEPRINT["databases"] if d["name"] == "careerops-db")
ENV = {e["key"]: e for e in SERVICE["envVars"]}
WEB_ENV = {e["key"]: e for e in WEB["envVars"]}


def test_only_free_plans_are_used():
    assert SERVICE["plan"] == "free"
    assert DATABASE["plan"] == "free"
    # Static sites have no compute plan and no region; Render rejects both fields.
    assert "plan" not in WEB
    assert "region" not in WEB


def test_web_service_builds_from_the_dockerfile():
    assert SERVICE["runtime"] == "docker"
    assert (ROOT / SERVICE["dockerfilePath"]).is_file()


def test_health_check_path_is_a_real_route():
    paths = app.openapi()["paths"]

    assert SERVICE["healthCheckPath"] == "/health/ready"
    assert "get" in paths[SERVICE["healthCheckPath"]]


def test_database_url_comes_from_the_render_database():
    assert ENV["DATABASE_URL"]["fromDatabase"] == {"name": "careerops-db", "property": "connectionString"}


def test_jwt_secret_is_generated_by_render():
    assert ENV["JWT_SECRET_KEY"] == {"key": "JWT_SECRET_KEY", "generateValue": True}


def test_migrations_run_on_start():
    assert ENV["RUN_MIGRATIONS"]["value"] == "true"


def test_no_secret_values_in_the_blueprint():
    for key, var in {**ENV, **WEB_ENV}.items():
        if re.search(r"PASSWORD|SECRET|TOKEN|KEY|DATABASE_URL", key):
            assert "value" not in var, f"{key} must come from Render, not be written in render.yaml"


def test_database_is_not_reachable_from_the_internet():
    assert DATABASE["ipAllowList"] == []


def test_deploys_wait_for_ci():
    assert SERVICE["branch"] == "main"
    assert SERVICE["autoDeployTrigger"] == "checksPass"


def test_service_and_database_share_a_region():
    assert SERVICE["region"] == DATABASE["region"]


def test_start_script_is_in_the_image_and_uses_lf_line_endings():
    script = ROOT / "scripts" / "start.sh"
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    dockerignore = (ROOT / ".dockerignore").read_text(encoding="utf-8").split()

    assert "COPY scripts ./scripts" in dockerfile
    assert 'CMD ["sh", "scripts/start.sh"]' in dockerfile
    assert "scripts" not in dockerignore
    assert b"\r" not in script.read_bytes(), "start.sh must use LF line endings to run in Linux containers"


# -------------------------------------------------------------- static frontend site


def test_web_service_builds_the_frontend():
    assert WEB["runtime"] == "static"
    assert WEB["rootDir"] == "frontend"
    assert WEB["staticPublishPath"] == "dist"
    assert "npm ci" in WEB["buildCommand"]
    assert "npm run build" in WEB["buildCommand"]
    assert (ROOT / WEB["rootDir"]).is_dir()


def test_frontend_deploys_wait_for_ci_and_skip_pr_previews():
    assert WEB["branch"] == "main"
    assert WEB["autoDeployTrigger"] == "checksPass"
    assert WEB["pullRequestPreviewsEnabled"] is False


def test_frontend_is_a_single_page_app():
    rewrite = next(r for r in WEB["routes"] if r["source"] == "/*")
    assert rewrite == {"type": "rewrite", "source": "/*", "destination": "/index.html"}


def test_frontend_points_at_the_live_api():
    assert WEB_ENV["VITE_API_URL"]["value"] == "https://careerops-api.onrender.com"
    # The API only allows that same frontend origin to call it from a browser.
    assert ENV["CORS_ORIGINS"]["value"] == "https://careerops-web.onrender.com"


def test_frontend_has_security_headers():
    headers = {h["name"]: h for h in WEB["headers"]}

    assert headers["Content-Security-Policy"]["value"].startswith("default-src 'self'")
    # The CSP's connect-src must allow calling the configured API, or XHR/fetch breaks.
    assert WEB_ENV["VITE_API_URL"]["value"] in headers["Content-Security-Policy"]["value"]
    assert headers["X-Content-Type-Options"]["value"] == "nosniff"
    assert headers["X-Frame-Options"]["value"] == "DENY"
    assert headers["Referrer-Policy"]["value"]
    assert headers["Permissions-Policy"]["value"]


def test_long_lived_cache_only_applies_to_hashed_assets():
    cache_rules = [h for h in WEB["headers"] if h["name"] == "Cache-Control"]

    assert all(h["path"] == "/assets/*" for h in cache_rules)
    assert all("immutable" in h["value"] for h in cache_rules)


