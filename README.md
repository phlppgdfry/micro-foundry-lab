# Micro Foundry Lab

[![Quality](https://github.com/phlppgdfry/micro-foundry-lab/actions/workflows/quality.yml/badge.svg)](https://github.com/phlppgdfry/micro-foundry-lab/actions/workflows/quality.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A small, production-minded learning lab for [Microsoft Foundry](https://learn.microsoft.com/azure/foundry/). Build from a first model call to a grounded document assistant—with tests, source visibility, and safe configuration from day one.

> This is intentionally a **micro** project: learn one concept at a time, keep costs controlled, and graduate components only when you understand them.

## What you will build

The final project is a minimal document-assistant API. It retrieves relevant local Markdown documents, asks a Foundry model for a grounded answer, and returns the sources it used.

```text
Question → local retrieval → Foundry model → answer + source names
```

The lab is not a production security boundary. It is a clean starting point for learning prompts, retrieval, evaluation, authentication, and observability before adding enterprise services.

## Learning path

| Lab | Focus | Outcome |
| --- | --- | --- |
| 01 | Model call | Send a prompt to a Foundry model with Entra ID authentication. |
| 02 | Structured output | Treat model output as data to validate, not blindly trust. |
| 03 | Grounding | Answer from local source documents and return citations. |
| 04 | Evaluation | Keep regression cases for useful, safe answers. |

## Prerequisites

- Python 3.11+
- An Azure subscription and a Microsoft Foundry project with a model available
- Azure CLI authenticated with `az login`

This repository follows the current Foundry projects SDK (`azure-ai-projects` 2.x). Copy the **project endpoint** from the Foundry project; it has this shape:

```text
https://<resource>.services.ai.azure.com/api/projects/<project>
```

## Quick start

```bash
git clone https://github.com/phlppgdfry/micro-foundry-lab.git
cd micro-foundry-lab
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
az login
```

Edit `.env` and add `FOUNDRY_PROJECT_ENDPOINT`. Do not commit this file.

Run the first lab:

```bash
python labs/01-chat/chat.py
```

Or start the document assistant:

```bash
uvicorn micro_foundry.main:app --reload
curl http://127.0.0.1:8000/health
curl -X POST http://127.0.0.1:8000/v1/chat \
  -H 'Content-Type: application/json' \
  -d '{"question":"How long do employees have to submit expenses?"}'
```

Interactive API documentation is available at `http://127.0.0.1:8000/docs`.

## How authentication works

The app uses `DefaultAzureCredential`, so local development uses your Azure CLI identity after `az login`. No API keys are stored in source code or required in `.env`.

For a deployed app, use a managed identity with only the least-privilege Foundry role it needs. Never place long-lived secrets in browser code or commit them to Git.

## Cost guardrails

- Start with a small model and only a few test documents.
- Create an Azure budget and cost alert before experimenting.
- Set request limits before exposing an endpoint publicly.
- Keep evaluation cases small and run them deliberately; every model call has a cost.

## Where to take it next

1. Replace transparent keyword retrieval with Azure AI Search or a vector store.
2. Add validated structured output to Lab 02.
3. Add authentication, rate limiting, telemetry, and content-safety checks before serving real users.
4. Expand `evals/` whenever a response is incorrect, unsafe, or unhelpful.

## Project standards

Run checks before contributing:

```bash
ruff check .
pytest
```

See [CONTRIBUTING.md](CONTRIBUTING.md) and [SECURITY.md](SECURITY.md). Released under the [MIT License](LICENSE).
