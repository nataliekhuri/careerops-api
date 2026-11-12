"""Sanity checks for the deployment files, so mistakes are caught in CI before Render sees them."""

import re
from pathlib import Path

import yaml

from app.main import app

ROOT = Path(__file__).resolve().parent.parent
BLUEPRINT = yaml.safe_load((ROOT / "render.yaml").read_text(encoding="utf-8"))
SERVICE = next(s for s in BLUEPRINT["services"] if s["name"] == "careerops-api")
DATABASE = next(d for d in BLUEPRINT["databases"] if d["name"] == "careerops-db")
ENV = {e["key"]: e for e in SERVICE["envVars"]}


def test_only_free_plans_are_used():
    assert SERVICE["plan"] == "free"
    assert DATABASE["plan"] == "free"


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
    for key, var in ENV.items():
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
