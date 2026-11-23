import subprocess
import sys
from pathlib import Path

import pytest

from scripts.railway.bootstrap import (
    POSTGRES_DATA,
    POSTGRES_DATABASE_URL,
    RailwayError,
    api_variables,
    choose_workspace,
    edges,
    matching_projects,
    missing_postgres_variables,
    needs_postgres_deploy,
    require_secrets,
    unauthorized,
    workspace_records,
)
from scripts.railway.release import should_seed


def test_seed_runs_only_for_an_empty_book() -> None:
    assert should_seed(0)
    assert not should_seed(400)


def test_release_script_finds_the_app_package() -> None:
    root = Path(__file__).resolve().parents[1]
    script = root / "scripts" / "railway" / "release.py"
    probe = f"import runpy\nrunpy.run_path({str(script)!r}, run_name='not_main')\nimport src\n"
    completed = subprocess.run(
        [sys.executable, "-c", probe],
        cwd=script.parent,
        capture_output=True,
        text=True,
        check=False,
        env={"PATH": "/usr/bin:/bin", "PYTHONDONTWRITEBYTECODE": "1"},
    )
    assert completed.returncode == 0, completed.stderr


def test_postgres_variables_keep_an_existing_password() -> None:
    existing = {
        "POSTGRES_USER": "spaceship",
        "POSTGRES_PASSWORD": "already-set",
        "POSTGRES_DB": "spaceship",
        "DATABASE_URL": POSTGRES_DATABASE_URL,
        "PGDATA": POSTGRES_DATA,
    }
    assert "POSTGRES_PASSWORD" not in missing_postgres_variables(existing)


def test_postgres_variables_fill_a_new_database() -> None:
    updates = missing_postgres_variables({})
    assert updates["POSTGRES_USER"] == "spaceship"
    assert updates["POSTGRES_DB"] == "spaceship"
    assert updates["DATABASE_URL"] == POSTGRES_DATABASE_URL
    assert updates["PGDATA"] == POSTGRES_DATA
    assert len(updates["POSTGRES_PASSWORD"]) >= 24


def test_api_variables_skip_an_empty_optional_key() -> None:
    env = {
        "JWT_SECRET": "0123456789abcdef0123456789abcdef",
        "ANTHROPIC_API_KEY": "",
    }
    values = api_variables(env)
    assert "ANTHROPIC_API_KEY" not in values
    assert "BOOTSTRAP_ADMIN_EMAIL" not in values
    assert "BOOTSTRAP_ADMIN_PASSWORD" not in values
    assert values["DATABASE_URL"] == "${{postgres.DATABASE_URL}}"
    assert values["COOKIE_SECURE"] == "true"


def test_api_variables_include_a_present_model_key() -> None:
    env = {
        "JWT_SECRET": "0123456789abcdef0123456789abcdef",
        "ANTHROPIC_API_KEY": "sk-test",
    }
    assert api_variables(env)["ANTHROPIC_API_KEY"] == "sk-test"


def test_require_secrets_accepts_an_account_token() -> None:
    require_secrets(
        {
            "RAILWAY_API_TOKEN": "account-token",
            "JWT_SECRET": "0123456789abcdef0123456789abcdef",
        }
    )


def test_require_secrets_rejects_a_short_jwt() -> None:
    with pytest.raises(SystemExit, match="JWT_SECRET"):
        require_secrets(
            {
                "RAILWAY_TOKEN": "token",
                "JWT_SECRET": "short",
            }
        )


def test_one_visible_workspace_is_selected() -> None:
    workspaces = [{"id": "ws", "name": "My Projects"}]
    assert choose_workspace(workspaces, None) == "ws"
    assert choose_workspace(workspaces, "ws") == "ws"


def test_several_workspaces_need_an_explicit_id() -> None:
    workspaces = [{"id": "one", "name": "Personal"}, {"id": "two", "name": "Team"}]
    with pytest.raises(RailwayError, match="RAILWAY_WORKSPACE"):
        choose_workspace(workspaces, None)
    assert choose_workspace(workspaces, "two") == "two"


def test_unauthorized_matches_the_railway_error() -> None:
    assert unauthorized(RailwayError("Railway API error: Not Authorized"))
    assert not unauthorized(RailwayError("Railway API HTTP 403: error code: 1010"))


def test_workspace_records_read_the_token_payload() -> None:
    payload = {"apiToken": {"workspaces": [{"id": "ws", "name": "My Projects"}]}}
    assert workspace_records(payload) == [{"id": "ws", "name": "My Projects"}]


def test_duplicate_project_names_are_visible() -> None:
    projects = [
        {"id": "one", "name": "spaceship"},
        {"id": "two", "name": "spaceship"},
        {"id": "three", "name": "other"},
    ]
    assert len(matching_projects(projects, "spaceship")) == 2


def test_edges_read_graphql_nodes() -> None:
    payload = {"project": {"volumes": {"edges": [{"node": {"id": "vol", "name": "data"}}]}}}
    assert edges(payload, "project", "volumes", "edges") == [{"id": "vol", "name": "data"}]


def test_postgres_deploys_when_missing_or_failed() -> None:
    assert needs_postgres_deploy(None)
    assert needs_postgres_deploy("FAILED")
    assert not needs_postgres_deploy("SUCCESS")
    assert not needs_postgres_deploy("BUILDING")
