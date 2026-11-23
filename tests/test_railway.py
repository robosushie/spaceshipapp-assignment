import pytest

from scripts.railway.bootstrap import (
    POSTGRES_DATABASE_URL,
    api_variables,
    edges,
    matching_projects,
    missing_postgres_variables,
    needs_postgres_deploy,
    require_secrets,
)
from scripts.railway.release import should_seed


def test_seed_runs_only_for_an_empty_book() -> None:
    assert should_seed(0)
    assert not should_seed(400)


def test_postgres_variables_keep_an_existing_password() -> None:
    existing = {
        "POSTGRES_USER": "spaceship",
        "POSTGRES_PASSWORD": "already-set",
        "POSTGRES_DB": "spaceship",
        "DATABASE_URL": POSTGRES_DATABASE_URL,
    }
    assert "POSTGRES_PASSWORD" not in missing_postgres_variables(existing)


def test_postgres_variables_fill_a_new_database() -> None:
    updates = missing_postgres_variables({})
    assert updates["POSTGRES_USER"] == "spaceship"
    assert updates["POSTGRES_DB"] == "spaceship"
    assert updates["DATABASE_URL"] == POSTGRES_DATABASE_URL
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
