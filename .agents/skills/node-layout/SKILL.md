---
name: node-layout
description: "Places a Node or Bun app in the folder the folder-structure skill names. Use when a JS frontend or JS API is selected."
---

# Node layout

The `folder-structure` skill is installed on every stack and owns the tree. Read `stack.json` `choices.layout` and place the JavaScript app in the folder that skill names.

Do not describe a second tree in this skill. A Python API is not an npm workspace member.

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
