# Micro Foundry Lab

[![Quality](https://github.com/phlppgdfry/micro-foundry-lab/actions/workflows/quality.yml/badge.svg)](https://github.com/phlppgdfry/micro-foundry-lab/actions/workflows/quality.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

<!-- showcase:start -->
> **[▶ Live showcase](https://phlppgdfry.github.io/micro-foundry-lab/)** — screens, a recorded walkthrough and what is real versus simulated

[![Live showcase: micro-foundry-lab](site/preview.png)](https://phlppgdfry.github.io/micro-foundry-lab/)
<!-- showcase:end -->

A small, production-minded learning lab for [Microsoft Foundry](https://learn.microsoft.com/azure/foundry/). It starts with one model call and ends with a grounded document-assistant API—complete with source visibility, tests, and safe local configuration.

> **Why micro?** Learn one practical concept at a time, keep model usage controlled, and only add infrastructure once it earns its place.

<p align="center"><img src="docs/images/demo.gif" width="760" alt="Asking the documents: the answer cites employee-handbook.md#expenses, the cited section opens to show the exact text, a remote-work question cites #remote-work, and a parental-leave question is declined because no document covers it"></p>

## Try it without Azure (30 seconds)

```bash
pip install -e ".[dev]"
MICRO_FOUNDRY_PROVIDER=offline uvicorn micro_foundry.main:app --reload
# open http://127.0.0.1:8000  (Swagger stays at /docs)
```

The **offline provider** does not call any model: it answers with the source sentences that best
match the question. It is labelled as such in every response. It exists so you can see the whole
retrieval → answer → citation loop before creating Azure resources, so CI can run the evaluation
suite for free, and as a baseline: a model answer that cannot beat it is not worth its cost.
Switch to your Foundry model with `MICRO_FOUNDRY_PROVIDER=foundry` (the default).

## What you can do

- Send a first prompt to a Foundry model using your Azure identity.
- Ask questions about the Markdown documents in `data/`.
- Return the exact **section** each answer is based on (`employee-handbook.md#expenses`), with the retrieved text, so answers can be checked.
- Decline questions the documents do not cover instead of inventing an answer.
- Test the API interactively in Swagger UI or with `curl`.
- Run a regression suite (`python -m micro_foundry.evals`) before changing prompts, models, or retrieval.

## How it works

```mermaid
flowchart LR
    Q[Question] --> R[Section retrieval<br/>stop words + min score]
    R -->|no section scores high enough| N[Decline]
    R --> C[Retrieved sections<br/>as untrusted context]
    C --> M{Provider}
    M -->|foundry| F[Microsoft Foundry model<br/>Entra ID auth]
    M -->|offline| X[Extractive baseline<br/>no model]
    F --> A[Answer + section citations]
    X --> A
```

The retrieval layer is deliberately simple and transparent: keyword matching over Markdown *sections*, with stop words and a minimum score, so a citation points at a paragraph rather than a whole file. It is designed for learning the complete grounding loop before moving to Azure AI Search or a vector store.

## Learning path

| Lab | Focus | Outcome |
| --- | --- | --- |
| 01 | Model call | Send a prompt to a Foundry model with Entra ID authentication. — `labs/01-chat/chat.py` |
| 02 | Structured output | Treat model output as data to validate, not blindly trust. — `labs/02-structured-output/structured.py` (`--offline` shows a reply that *looks* right being rejected) |
| 03 | Grounding | Retrieve document sections and return citations. — the API and the page at `/` |
| 04 | Evaluation | Keep regression cases for useful, safe answers. — `python -m micro_foundry.evals` runs `labs/04-evaluation/cases.json` |

## Prerequisites

- Python 3.11+
- An Azure subscription and a Microsoft Foundry project
- A deployed model, such as `gpt-5-mini`
- Azure CLI authenticated with `az login`

This project uses the current Foundry projects SDK (`azure-ai-projects` 2.x) and `DefaultAzureCredential`. You do **not** need to put an API key in this repository.

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

In Microsoft Foundry, copy the project endpoint from **Project overview**. It has this shape:

```text
https://<resource>.services.ai.azure.com/api/projects/<project>
```

Add it to `.env` together with your model deployment name:

```dotenv
FOUNDRY_PROJECT_ENDPOINT=https://<resource>.services.ai.azure.com/api/projects/<project>
FOUNDRY_MODEL=gpt-5-mini
```

`.env` is ignored by Git. Never commit secrets, tokens, customer documents, or production connection strings.

## Run it

### Lab 01 — first model call

```bash
python labs/01-chat/chat.py
```

You should receive a short response from your Foundry model.

### Document assistant API

```bash
uvicorn micro_foundry.main:app --reload
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000) to ask questions in the browser, or [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) for the interactive API. Check the service first:

```bash
curl http://127.0.0.1:8000/health
```

Then ask a question grounded in the example documents:

```bash
curl -X POST http://127.0.0.1:8000/v1/chat \
  -H 'Content-Type: application/json' \
  -d '{"question":"How long do employees have to submit expenses?"}'
```

Expected result: an answer that mentions **30 days** and cites `employee-handbook.md#expenses`.

### Evaluate before you change anything

```bash
MICRO_FOUNDRY_PROVIDER=offline python -m micro_foundry.evals   # free baseline, also runs in CI
python -m micro_foundry.evals                                  # your Foundry model
```

```text
PASS  How long do employees have to submit expenses?
      ✓ retrieved employee-handbook.md#expenses
      ✓ answer contains “30 days”
PASS  What is the parental leave policy?
      ✓ declines instead of inventing an answer

4/4 cases passed
```

Each case can check the retrieved section, required phrases and that unsupported questions are
declined. Add a case whenever you find a bad answer; the command exits non-zero on any failure.

## API contract

| Endpoint | Purpose |
| --- | --- |
| `GET /` | A small page to ask questions and inspect the cited sections. |
| `GET /health` | Confirms that the API is running and shows the provider and model. |
| `POST /v1/chat` | Answers a question and returns the sections it used. |

Request body:

```json
{"question":"How long do employees have to submit expenses?"}
```

Response shape:

```json
{
  "answer": "...",
  "citations": [
    {
      "source": "employee-handbook.md",
      "section": "Expenses",
      "anchor": "employee-handbook.md#expenses",
      "relevance": 3,
      "excerpt": "Employees may submit reasonable business expenses within 30 days. ..."
    }
  ],
  "provider": "foundry"
}
```

## Authentication and safety

Local development uses `DefaultAzureCredential`, which normally picks up your Azure CLI identity after `az login`. For deployed applications, prefer a managed identity with only the least privilege it needs.

This is a learning project, not a complete production security boundary. Before exposing it publicly, add authentication, request limits, telemetry, content-safety checks, stricter retrieval thresholds, and a proper document store.

## Cost guardrails

- Begin with a small model and a small set of test documents.
- Create an Azure budget and a cost alert before experimenting.
- Keep the API local until authentication and rate limits are in place.
- Add evaluation cases deliberately: every model request has a cost.

## Troubleshooting

| Symptom | What to do |
| --- | --- |
| Swagger says **Failed to fetch** | Keep the `uvicorn` terminal open, then refresh `http://127.0.0.1:8000/docs`. |
| `FOUNDRY_PROJECT_ENDPOINT is not configured` | Create `.env` from `.env.example` and add your project endpoint. |
| Azure authentication fails | Run `az login`, select the subscription that owns the Foundry project, then retry. |
| Model not found | Set `FOUNDRY_MODEL` to the deployment name shown in Foundry. |

## Contributing and quality

```bash
ruff check .
pytest                                                        # 10 tests
MICRO_FOUNDRY_PROVIDER=offline python -m micro_foundry.evals  # 4/4 regression cases
```

See [CONTRIBUTING.md](CONTRIBUTING.md) and [SECURITY.md](SECURITY.md). The project is released under the [MIT License](LICENSE).

## Next improvements

- [x] Stop words, a minimum relevance threshold and section-level citations in retrieval.
- [x] Validated structured output in Lab 02.
- [x] Offline provider and an evaluation runner that runs in CI.
- [ ] Replace local keyword retrieval with Azure AI Search or a vector store, and compare on the same eval cases.
- [ ] Add authentication, rate limiting, observability, and an evaluation gate before public deployment.
