"""Create the Spaceship Railway project when it is missing, then leave it ready to deploy.

The script uses an account or workspace token. It does not connect the GitHub repository,
so Railway does not deploy on its own.
"""

from __future__ import annotations

import json
import os
import secrets
import time
import urllib.error
import urllib.request
from collections.abc import Mapping, Sequence
from typing import cast

ENDPOINT = "https://backboard.railway.com/graphql/v2"
USER_AGENT = "Mozilla/5.0 (compatible; spaceship-deploy/1.0)"
PROJECT_NAME = "spaceship"
ENVIRONMENT_NAME = "production"
POSTGRES_IMAGE = "postgres:17"
POSTGRES_MOUNT = "/var/lib/postgresql/data"
POSTGRES_DATA = "/var/lib/postgresql/data/pgdata"
POSTGRES_DATABASE_URL = (
    "postgresql://${{POSTGRES_USER}}:${{POSTGRES_PASSWORD}}"
    "@${{RAILWAY_PRIVATE_DOMAIN}}:5432/${{POSTGRES_DB}}"
)
API_START = "/app/scripts/railway/api-entrypoint.sh"
AGENT_START = "/app/.venv/bin/python -m src.agent.worker"
API_PORT = "8080"
API_UPSTREAM = "http://${{api.RAILWAY_PRIVATE_DOMAIN}}:${{api.PORT}}"
REDIS_IMAGE = "redis:7-alpine"
REDIS_URL = "redis://:${{REDIS_PASSWORD}}@${{RAILWAY_PRIVATE_DOMAIN}}:6379/0"
SHARED_REDIS_URL = "${{redis.REDIS_URL}}"
WEB_ORIGIN = "https://${{web.RAILWAY_PUBLIC_DOMAIN}}"
REQUIRED_SECRETS = ("JWT_SECRET",)
OPTIONAL_SECRETS = (
    "ANTHROPIC_API_KEY",
    "OPENAI_API_KEY",
    "RESEND_API_KEY",
    "RESEND_FROM",
)
TERMINAL_FAILURE = {"FAILED", "CRASHED"}
API_WATCH = [
    "src/**",
    "alembic/**",
    "scripts/bootstrap/**",
    "scripts/railway/release.py",
    "scripts/railway/api-entrypoint.sh",
    "pyproject.toml",
    "uv.lock",
    "infra/docker/api.Dockerfile",
    "infra/railway/api.toml",
]
WEB_WATCH = [
    "apps/web/**",
    "package.json",
    "pnpm-lock.yaml",
    "pnpm-workspace.yaml",
    "infra/docker/web.Dockerfile",
    "infra/docker/nginx.conf.template",
    "infra/docker/web-entrypoint.sh",
    "infra/railway/web.toml",
]


class RailwayError(RuntimeError):
    pass


def railway_token(env: Mapping[str, str]) -> str:
    return env.get("RAILWAY_API_TOKEN", "").strip() or env.get("RAILWAY_TOKEN", "").strip()


def require_secrets(env: Mapping[str, str]) -> None:
    missing = [name for name in REQUIRED_SECRETS if not env.get(name, "").strip()]
    if not railway_token(env):
        missing.insert(0, "RAILWAY_TOKEN")
    if missing:
        raise SystemExit(f"Missing Railway deploy secrets: {', '.join(missing)}")
    if len(env["JWT_SECRET"].encode("utf-8")) < 32:
        raise SystemExit("JWT_SECRET must be at least 32 bytes")


def edges(payload: Mapping[str, object], *path: str) -> list[dict[str, object]]:
    node: object = payload
    for key in path:
        if not isinstance(node, Mapping):
            return []
        node = node.get(key, {})
    if not isinstance(node, list):
        return []
    found: list[dict[str, object]] = []
    for item in node:
        if not isinstance(item, Mapping):
            continue
        entry = item.get("node", item)
        if isinstance(entry, Mapping):
            found.append(cast(dict[str, object], dict(entry)))
    return found


def named_id(items: list[dict[str, object]], name: str) -> str | None:
    for item in items:
        if item.get("name") == name and isinstance(item.get("id"), str):
            return cast(str, item["id"])
    return None


def matching_projects(
    projects: Sequence[Mapping[str, object]],
    name: str,
) -> list[Mapping[str, object]]:
    return [project for project in projects if project.get("name") == name]


def workspace_records(payload: Mapping[str, object]) -> list[dict[str, object]]:
    token = payload.get("apiToken")
    if not isinstance(token, Mapping):
        return []
    workspaces = token.get("workspaces")
    if isinstance(workspaces, list):
        return [dict(item) for item in workspaces if isinstance(item, Mapping)]
    if isinstance(workspaces, Mapping):
        return edges({"workspaces": workspaces}, "workspaces", "edges")
    return []


def choose_workspace(workspaces: Sequence[Mapping[str, object]], requested: str | None) -> str:
    visible = [item for item in workspaces if isinstance(item.get("id"), str)]
    if requested:
        if any(item.get("id") == requested for item in visible):
            return requested
        raise RailwayError("RAILWAY_WORKSPACE is not visible to this token")
    if len(visible) == 1:
        return cast(str, visible[0]["id"])
    if not visible:
        raise RailwayError(
            "This Railway token cannot list a workspace. "
            "Create an account token at railway.com/account/tokens."
        )
    names = ", ".join(str(item.get("name") or item.get("id")) for item in visible)
    raise RailwayError(
        f"More than one Railway workspace is visible ({names}). Set RAILWAY_WORKSPACE."
    )


def missing_postgres_variables(existing: Mapping[str, str]) -> dict[str, str]:
    updates: dict[str, str] = {}
    if "POSTGRES_USER" not in existing:
        updates["POSTGRES_USER"] = "spaceship"
    if "POSTGRES_PASSWORD" not in existing:
        updates["POSTGRES_PASSWORD"] = secrets.token_hex(24)
    if "POSTGRES_DB" not in existing:
        updates["POSTGRES_DB"] = "spaceship"
    if existing.get("DATABASE_URL") != POSTGRES_DATABASE_URL:
        updates["DATABASE_URL"] = POSTGRES_DATABASE_URL
    if existing.get("PGDATA") != POSTGRES_DATA:
        updates["PGDATA"] = POSTGRES_DATA
    return updates


def missing_redis_variables(existing: Mapping[str, str]) -> dict[str, str]:
    updates: dict[str, str] = {}
    if "REDIS_PASSWORD" not in existing:
        updates["REDIS_PASSWORD"] = secrets.token_hex(24)
    if existing.get("REDIS_URL") != REDIS_URL:
        updates["REDIS_URL"] = REDIS_URL
    return updates


def redis_start_command(password: str) -> str:
    return (
        "sh -c 'exec redis-server --requirepass "
        f"{password} --bind 0.0.0.0 :: --port 6379'"
    )


def api_variables(env: Mapping[str, str]) -> dict[str, str]:
    values = {
        "DATABASE_URL": "${{postgres.DATABASE_URL}}",
        "REDIS_URL": SHARED_REDIS_URL,
        "PORT": API_PORT,
        "JWT_SECRET": env["JWT_SECRET"],
        "JWT_ISSUER": "spaceship",
        "JWT_AUDIENCE": "spaceship-web",
        "COOKIE_SECURE": "true",
        "WEB_ORIGIN": WEB_ORIGIN,
        "CORS_ORIGINS": WEB_ORIGIN,
    }
    for name in OPTIONAL_SECRETS:
        value = env.get(name, "").strip()
        if value:
            values[name] = value
    return values


def agent_variables(env: Mapping[str, str]) -> dict[str, str]:
    values = {
        "DATABASE_URL": "${{postgres.DATABASE_URL}}",
        "REDIS_URL": SHARED_REDIS_URL,
        "JWT_SECRET": env["JWT_SECRET"],
    }
    for name in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY"):
        value = env.get(name, "").strip()
        if value:
            values[name] = value
    return values


def needs_postgres_deploy(status: str | None) -> bool:
    return status is None or status in TERMINAL_FAILURE


def unauthorized(exc: RailwayError) -> bool:
    return "Not Authorized" in str(exc)


class Railway:
    def __init__(self, token: str) -> None:
        self._token = token
        self._project_token = False

    def gql(self, query: str, variables: Mapping[str, object]) -> dict[str, object]:
        headers = {
            "Content-Type": "application/json",
            "User-Agent": USER_AGENT,
        }
        if self._project_token:
            headers["Project-Access-Token"] = self._token
        else:
            headers["Authorization"] = f"Bearer {self._token}"
        body = json.dumps({"query": query, "variables": variables}).encode()
        request = urllib.request.Request(
            ENDPOINT,
            data=body,
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                payload = json.loads(response.read().decode())
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode(errors="replace")
            raise RailwayError(f"Railway API HTTP {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise RailwayError(f"Railway API request failed: {exc.reason}") from exc
        if not isinstance(payload, dict):
            raise RailwayError("Railway API returned a response that is not an object")
        errors = payload.get("errors")
        if errors:
            raise RailwayError(f"Railway API error: {errors}")
        data = payload.get("data")
        if not isinstance(data, dict):
            raise RailwayError("Railway API returned no data")
        return cast(dict[str, object], data)

    def projects(self, workspace_id: str) -> list[dict[str, object]]:
        data = self.gql(
            """
            query workspaceProjects($workspaceId: String!) {
              projects(workspaceId: $workspaceId) {
                edges { node { id name } }
              }
            }
            """,
            {"workspaceId": workspace_id},
        )
        return edges(data, "projects", "edges")

    def workspace_id(self, requested: str | None) -> str:
        data = self.gql(
            """
            query tokenWorkspaces {
              apiToken { workspaces { id name } }
            }
            """,
            {},
        )
        return choose_workspace(workspace_records(data), requested)

    def project_token_scope(self) -> tuple[str, str | None]:
        self._project_token = True
        data = self.gql(
            """
            query projectScope {
              projectToken { projectId environmentId }
            }
            """,
            {},
        )
        node = data.get("projectToken")
        if not isinstance(node, Mapping) or not isinstance(node.get("projectId"), str):
            raise RailwayError("The Railway token is not a project token")
        environment_id = node.get("environmentId")
        if environment_id is not None and not isinstance(environment_id, str):
            raise RailwayError("The project token did not include an environment")
        return cast(str, node["projectId"]), environment_id

    def create_project(self, workspace_id: str | None) -> str:
        project_input: dict[str, object] = {"name": PROJECT_NAME}
        if workspace_id:
            project_input["workspaceId"] = workspace_id
        data = self.gql(
            """
            mutation projectCreate($input: ProjectCreateInput!) {
              projectCreate(input: $input) { id name }
            }
            """,
            {"input": project_input},
        )
        created = data.get("projectCreate")
        if not isinstance(created, Mapping) or not isinstance(created.get("id"), str):
            raise RailwayError("projectCreate returned no id")
        return cast(str, created["id"])

    def environment_id(self, project_id: str) -> str:
        data = self.gql(
            """
            query project($id: String!) {
              project(id: $id) {
                environments { edges { node { id name } } }
              }
            }
            """,
            {"id": project_id},
        )
        environments = edges(data, "project", "environments", "edges")
        found = named_id(environments, ENVIRONMENT_NAME)
        if found:
            return found
        if environments and isinstance(environments[0].get("id"), str):
            return cast(str, environments[0]["id"])
        raise RailwayError("The project has no environment")

    def services(self, project_id: str) -> list[dict[str, object]]:
        data = self.gql(
            """
            query project($id: String!) {
              project(id: $id) {
                services { edges { node { id name } } }
              }
            }
            """,
            {"id": project_id},
        )
        return edges(data, "project", "services", "edges")

    def ensure_service(
        self,
        project_id: str,
        environment_id: str,
        name: str,
        source: dict[str, str] | None,
    ) -> str:
        found = named_id(self.services(project_id), name)
        if found:
            return found
        service_input: dict[str, object] = {
            "projectId": project_id,
            "environmentId": environment_id,
            "name": name,
        }
        if source is not None:
            service_input["source"] = source
        data = self.gql(
            """
            mutation serviceCreate($input: ServiceCreateInput!) {
              serviceCreate(input: $input) { id name }
            }
            """,
            {"input": service_input},
        )
        created = data.get("serviceCreate")
        if not isinstance(created, Mapping) or not isinstance(created.get("id"), str):
            raise RailwayError(f"serviceCreate returned no id for {name}")
        return cast(str, created["id"])

    def configure(
        self,
        service_id: str,
        environment_id: str,
        settings: Mapping[str, object],
    ) -> None:
        self.gql(
            """
            mutation serviceInstanceUpdate(
              $serviceId: String!
              $environmentId: String!
              $input: ServiceInstanceUpdateInput!
            ) {
              serviceInstanceUpdate(
                serviceId: $serviceId
                environmentId: $environmentId
                input: $input
              )
            }
            """,
            {
                "serviceId": service_id,
                "environmentId": environment_id,
                "input": dict(settings),
            },
        )

    def has_volume(self, project_id: str) -> bool:
        data = self.gql(
            """
            query project($id: String!) {
              project(id: $id) {
                volumes { edges { node { id name } } }
              }
            }
            """,
            {"id": project_id},
        )
        return bool(edges(data, "project", "volumes", "edges"))

    def ensure_volume(self, project_id: str, environment_id: str, service_id: str) -> None:
        if self.has_volume(project_id):
            return
        self.gql(
            """
            mutation volumeCreate($input: VolumeCreateInput!) {
              volumeCreate(input: $input) { id }
            }
            """,
            {
                "input": {
                    "projectId": project_id,
                    "environmentId": environment_id,
                    "serviceId": service_id,
                    "mountPath": POSTGRES_MOUNT,
                }
            },
        )

    def variables(self, project_id: str, environment_id: str, service_id: str) -> dict[str, str]:
        data = self.gql(
            """
            query variables(
              $projectId: String!
              $environmentId: String!
              $serviceId: String!
              $unrendered: Boolean
            ) {
              variables(
                projectId: $projectId
                environmentId: $environmentId
                serviceId: $serviceId
                unrendered: $unrendered
              )
            }
            """,
            {
                "projectId": project_id,
                "environmentId": environment_id,
                "serviceId": service_id,
                "unrendered": True,
            },
        )
        raw = data.get("variables")
        if not isinstance(raw, Mapping):
            return {}
        return {str(key): str(value) for key, value in raw.items()}

    def upsert(
        self,
        project_id: str,
        environment_id: str,
        service_id: str,
        values: Mapping[str, str],
    ) -> None:
        if not values:
            return
        self.gql(
            """
            mutation variableCollectionUpsert($input: VariableCollectionUpsertInput!) {
              variableCollectionUpsert(input: $input)
            }
            """,
            {
                "input": {
                    "projectId": project_id,
                    "environmentId": environment_id,
                    "serviceId": service_id,
                    "variables": dict(values),
                    "skipDeploys": True,
                }
            },
        )

    def latest_status(self, environment_id: str, service_name: str) -> str | None:
        data = self.gql(
            """
            query environment($id: String!) {
              environment(id: $id) {
                serviceInstances {
                  edges {
                    node {
                      serviceName
                      latestDeployment { id status }
                    }
                  }
                }
              }
            }
            """,
            {"id": environment_id},
        )
        for instance in edges(data, "environment", "serviceInstances", "edges"):
            if instance.get("serviceName") != service_name:
                continue
            deployment = instance.get("latestDeployment")
            if isinstance(deployment, Mapping) and isinstance(deployment.get("status"), str):
                return cast(str, deployment["status"])
            return None
        return None

    def deploy(self, service_id: str, environment_id: str) -> None:
        self.gql(
            """
            mutation serviceInstanceDeployV2($serviceId: String!, $environmentId: String!) {
              serviceInstanceDeployV2(serviceId: $serviceId, environmentId: $environmentId)
            }
            """,
            {"serviceId": service_id, "environmentId": environment_id},
        )

    def domain(self, project_id: str, environment_id: str, service_id: str) -> str:
        data = self.gql(
            """
            query domains($projectId: String!, $environmentId: String!, $serviceId: String!) {
              domains(projectId: $projectId, environmentId: $environmentId, serviceId: $serviceId) {
                serviceDomains { domain }
              }
            }
            """,
            {
                "projectId": project_id,
                "environmentId": environment_id,
                "serviceId": service_id,
            },
        )
        domains = data.get("domains")
        if isinstance(domains, Mapping):
            service_domains = domains.get("serviceDomains")
            if isinstance(service_domains, list):
                for item in service_domains:
                    if isinstance(item, Mapping) and isinstance(item.get("domain"), str):
                        return cast(str, item["domain"])
        created = self.gql(
            """
            mutation serviceDomainCreate($input: ServiceDomainCreateInput!) {
              serviceDomainCreate(input: $input) { domain }
            }
            """,
            {"input": {"serviceId": service_id, "environmentId": environment_id}},
        )
        domain = created.get("serviceDomainCreate")
        if not isinstance(domain, Mapping) or not isinstance(domain.get("domain"), str):
            raise RailwayError("serviceDomainCreate returned no domain")
        return cast(str, domain["domain"])


def wait_for_service(
    railway: Railway,
    environment_id: str,
    service_id: str,
    service_name: str,
    *,
    redeploy: bool,
) -> None:
    triggered = False
    saw_progress = False
    if redeploy:
        railway.deploy(service_id, environment_id)
        triggered = True
    deadline = time.monotonic() + 300
    while time.monotonic() < deadline:
        status = railway.latest_status(environment_id, service_name)
        if status == "SUCCESS":
            return
        if status is not None and status not in TERMINAL_FAILURE:
            saw_progress = True
        if needs_postgres_deploy(status) and not triggered:
            railway.deploy(service_id, environment_id)
            triggered = True
            time.sleep(5)
            continue
        if status in TERMINAL_FAILURE and triggered and saw_progress:
            raise RailwayError(f"{service_name} deployment {status}")
        time.sleep(5)
    raise RailwayError(f"{service_name} deployment timed out")


def write_output(project_id: str, environment_id: str, domain: str) -> None:
    print(f"project_id={project_id}")
    print(f"environment_id={environment_id}")
    print(f"web_url=https://{domain}")
    output = os.environ.get("GITHUB_OUTPUT")
    if not output:
        return
    with open(output, "a", encoding="utf-8") as handle:
        handle.write(f"project_id={project_id}\n")
        handle.write(f"environment_id={environment_id}\n")
        handle.write(f"web_domain={domain}\n")


def bootstrap(env: Mapping[str, str] | None = None) -> None:
    source = os.environ if env is None else env
    require_secrets(source)
    requested_workspace = source.get("RAILWAY_WORKSPACE", "").strip() or None
    railway = Railway(railway_token(source))
    try:
        workspace = railway.workspace_id(requested_workspace)
    except RailwayError as exc:
        if not unauthorized(exc):
            raise
        project_id, token_environment = railway.project_token_scope()
        environment_id = token_environment or railway.environment_id(project_id)
    else:
        found = matching_projects(railway.projects(workspace), PROJECT_NAME)
        if len(found) > 1:
            raise RailwayError(
                "More than one Railway project is named spaceship. Set RAILWAY_WORKSPACE."
            )
        project_id = (
            cast(str, found[0]["id"])
            if found and isinstance(found[0].get("id"), str)
            else railway.create_project(workspace)
        )
        environment_id = railway.environment_id(project_id)

    postgres_id = railway.ensure_service(
        project_id,
        environment_id,
        "postgres",
        {"image": POSTGRES_IMAGE},
    )
    railway.ensure_volume(project_id, environment_id, postgres_id)
    postgres_updates = missing_postgres_variables(
        railway.variables(project_id, environment_id, postgres_id)
    )
    railway.upsert(project_id, environment_id, postgres_id, postgres_updates)
    wait_for_service(
        railway,
        environment_id,
        postgres_id,
        "postgres",
        redeploy="PGDATA" in postgres_updates,
    )

    redis_id = railway.ensure_service(
        project_id,
        environment_id,
        "redis",
        {"image": REDIS_IMAGE},
    )
    redis_existing = railway.variables(project_id, environment_id, redis_id)
    redis_updates = missing_redis_variables(redis_existing)
    railway.upsert(project_id, environment_id, redis_id, redis_updates)
    redis_password = redis_updates.get("REDIS_PASSWORD") or redis_existing.get("REDIS_PASSWORD", "")
    railway.configure(
        redis_id,
        environment_id,
        {"startCommand": redis_start_command(redis_password)},
    )
    wait_for_service(
        railway,
        environment_id,
        redis_id,
        "redis",
        redeploy="REDIS_PASSWORD" in redis_updates,
    )

    api_id = railway.ensure_service(project_id, environment_id, "api", None)
    railway.configure(
        api_id,
        environment_id,
        {
            "dockerfilePath": "infra/docker/api.Dockerfile",
            "watchPatterns": API_WATCH,
            "healthcheckPath": "/health",
            "healthcheckTimeout": 120,
            "preDeployCommand": "python scripts/railway/release.py",
            "startCommand": API_START,
        },
    )

    agent_id = railway.ensure_service(project_id, environment_id, "agent", None)
    railway.configure(
        agent_id,
        environment_id,
        {
            "dockerfilePath": "infra/docker/api.Dockerfile",
            "watchPatterns": API_WATCH,
            "startCommand": AGENT_START,
        },
    )
    railway.upsert(project_id, environment_id, agent_id, agent_variables(source))

    web_id = railway.ensure_service(project_id, environment_id, "web", None)
    railway.configure(
        web_id,
        environment_id,
        {
            "dockerfilePath": "infra/docker/web.Dockerfile",
            "watchPatterns": WEB_WATCH,
            "healthcheckPath": "/health",
            "healthcheckTimeout": 120,
        },
    )
    domain = railway.domain(project_id, environment_id, web_id)
    railway.upsert(project_id, environment_id, api_id, api_variables(source))
    railway.upsert(project_id, environment_id, web_id, {"API_UPSTREAM": API_UPSTREAM})
    write_output(project_id, environment_id, domain)


def main() -> None:
    try:
        bootstrap()
    except RailwayError as exc:
        raise SystemExit(str(exc)) from exc


if __name__ == "__main__":
    main()
