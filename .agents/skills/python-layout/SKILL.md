---
name: python-layout
description: "Places a Python API in the folder the folder-structure skill names. Use when the backend is FastAPI, Flask, or Django."
---

# Python layout

The `folder-structure` skill is installed on every stack and owns the tree. Read `stack.json` `choices.layout` and place FastAPI, Flask, or Django in the API root that skill names.

Create the Python project with `uv init` in that root. Do not describe a second tree in this skill, and do not list the Python project as an npm workspace member.

## Infra (only when selected)

Create `infra/` only when Docker, Kubernetes + Helm, or Postgres Docker is selected. Do not put a Dockerfile, compose file, or Helm chart inside `src/` or `apps/`.

```
infra/compose/docker-compose.yml    local Postgres; Redis only when cache is selected
infra/docker/                       one Dockerfile per service that is built
infra/helm/                         only for Kubernetes + Helm (from helm create)
  Chart.yaml
  values.yaml
  templates/                        one file per Kubernetes kind (deployment.yaml, service.yaml)
```

Helm templates use dashed names and namespaced `{{ define }}` helpers (for example `mychart.fullname`). Document every key in `values.yaml`. Compose reads a gitignored env file. Do not bake secrets into an image or a committed compose override.
