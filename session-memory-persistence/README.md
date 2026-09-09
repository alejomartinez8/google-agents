# session-memory-persistence — Gemini Cloud Tutor

`gemini_cloud_tutor`, an ADK agent that teaches Google Cloud concepts and looks up per-service region availability with a tool, used as the vehicle to test **4 `SessionService` implementations** (conversation history) and **2 `MemoryService` implementations** (cross-session long-term memory) against the same FastAPI + SSE streaming server.

Based on the lab "Building an ADK Agent with Session and Memory Services" (`raw/Google AI Labs/Lab - Build long-term persistence with memories - ...md` in the [llm-wiki](https://github.com/alejomartinez8/llm-wiki) vault), part of course 3 ("Craft ADK Agents with Persistent Memories") of the [Build and Deploy Agents with Agent Development Kit (ADK)](https://partner.skills.google/paths/4144) path.

## Architecture

```mermaid
flowchart LR
    client[client.html<br/>chat UI] -->|SSE /chat| server

    subgraph server["sessions_server.py / memory_server.py"]
        runner[ADK Runner] --> agent[gemini_cloud_tutor<br/>LlmAgent]
    end

    agent -.tool.-> avail[check_gcp_service_availability]
    agent -.tool.-> loadmem[load_memory<br/>memory_server only]

    runner --> sess{SessionService}
    sess -->|in_memory| mem1[InMemorySessionService]
    sess -->|vertex| mem2[VertexAiSessionService<br/>Agent Runtime]
    sess -->|db| mem3[DatabaseSessionService<br/>Postgres]

    runner --> memsvc{MemoryService}
    memsvc -->|in_memory| mm1[InMemoryMemoryService]
    memsvc -->|vertex| mm2[VertexAiMemoryBankService<br/>Agent Platform Memory Bank]
```

Two servers share the same agent pattern, switched via `.env`:
- **`sessions_server.py`** (`agent_sessions.py`) — conversation history only, no cross-session memory. Swaps `SessionService` implementation based on `SESSION_SERVICE_PROVIDER`: `in_memory` (default), `vertex` (Agent Runtime-backed, survives server restarts), or `db` (Postgres via `DatabaseSessionService`).
- **`memory_server.py`** (`agent_memory.py`) — adds the `load_memory` ADK tool and writes each finished session to the memory service (`memory_service.add_session_to_memory(...)`) so a *different* session can recall e.g. a user's preferred answer format. Swaps `MemoryService` via `MEMORY_SERVICE_PROVIDER`: `in_memory` or `vertex` (`VertexAiMemoryBankService`, backed by Agent Platform Memory Bank).

## Real run results (documented live, 2026-09-07)

All 7 tasks — the 4 `SessionService` backends and 2 `MemoryService` backends — were run and confirmed live in the original Qwiklabs Cloud Shell environment. That environment expired before the code could be copied out; **the code in this folder is a faithful reconstruction** from the lab manual's exact `STUDENT TASK` snippets (see `sessions_server.py` / `memory_server.py`) applied to the public base repo ([`GoogleCloudPlatform/specialized-training-content`](https://github.com/GoogleCloudPlatform/specialized-training-content), `courses/build_production_ready_agents/ch2_lab`) — the findings below are from the actual live run, not from re-reading the manual:

- **`load_memory` worked on the first try** (Task 5, `InMemoryMemoryService`, same process, new session): it retrieved the tutoring-format preference saved in an earlier session — worth noting since the manual explicitly warns tool invocation is non-deterministic and may need a retry.
- **Parallel tool calls**: the model called `load_memory` and `check_gcp_service_availability` in the same turn, without waiting on one before requesting the other.
- **Live recovery from a tool error**: `check_gcp_service_availability("Virtual Private Cloud")` returned `"Service not found"` with a list of valid service names; the model retried on the *next* turn with `"Compute Engine"` (from that same list) instead of giving up.
- **Memory survived a full server restart** (Task 6, `VertexAiMemoryBankService`): after `CTRL+C` + relaunching `memory_server.py`, the tutoring-format preference was still recalled on prompt "Please teach me about Colab Enterprise" — the concrete proof that `VertexAiMemoryBankService` (persisted in Agent Platform Memory Bank) survives process restarts where `InMemoryMemoryService` (in-process RAM) would not. Same parallel-tool-call and graceful-retry pattern repeated here (`"Colab Enterprise"` not recognized → retried with `"Vertex AI"`).
- **Task 7 (optional), `DatabaseSessionService` + Postgres: completed.** Real trap hit along the way — see Notes below.

## Setup

```bash
cd session-memory-persistence
uv venv
source .venv/bin/activate  # every new terminal tab needs this — see Notes
uv pip install -r requirements.txt
cp .env.example .env
```

### `in_memory` (default, no extra setup)

```bash
python sessions_server.py    # session history only
# or
python memory_server.py      # + cross-session memory (load_memory tool)
```

Open the URL it prints, click **Open Client Application**, and chat. Restarting the server (`CTRL+C` then rerun) loses all state with `in_memory` — that's the point of the next two backends.

### `vertex` (Agent Runtime-backed sessions / Agent Platform Memory Bank)

```bash
cd scripts && uv pip install google-cloud-aiplatform==1.139.0 google-adk==1.26.0
export GOOGLE_CLOUD_PROJECT=<your-project-id>
python setup_agentruntime.py   # prints the fully-qualified Agent Runtime resource name
```

Set in `.env`: `SESSION_SERVICE_PROVIDER=vertex` and/or `MEMORY_SERVICE_PROVIDER=vertex`, and `REASONING_ENGINE_APP_NAME=<name printed above>`. Then run either server as above — expect extra latency on the first call while the connection warms up.

### `db` (Postgres via `DatabaseSessionService`)

```bash
cd postgres && docker build -t my-postgres . && docker run -d --name postgres-container -p 5432:5432 -e POSTGRES_PASSWORD=-pass my-postgres
uv pip install "sqlalchemy[asyncio]"   # NOT in requirements.txt — see Notes
```

Set `SESSION_SERVICE_PROVIDER=db` in `.env`, then `python sessions_server.py`. Inspect state directly with `psql postgresql://adk:-pass@localhost:5432/adk_sessions` (`\dt` lists the `sessions`/`events` tables ADK created).

## Notes

- **Real trap: `ModuleNotFoundError: No module named 'sqlalchemy'` despite installing it.** Running `uv pip install "sqlalchemy[asyncio]"` in a **new** Cloud Shell tab (the one you open to launch the Postgres container) and then `python sessions_server.py` in that same tab fails, because that tab never ran `source .venv/bin/activate` — each new Cloud Shell tab starts a fresh, unactivated shell. The traceback points to `/usr/local/lib/python3.12/dist-packages/...` (system Python) instead of `.venv/lib/...`, confirming `uv pip install` resolved against the wrong environment. **Fix:** always run `source .venv/bin/activate` in a new tab before installing/running — the `(.venv)` prefix in the prompt is the visual tell that it's active.
- **`requirements.txt` doesn't include `sqlalchemy`** — it's only needed for the optional Task 7 (`db` provider), installed separately as shown above.
- This won't run out of the box without your own GCP project with Vertex AI enabled (for the `vertex` providers) — the `in_memory` providers work locally with no cloud dependency beyond the Gemini model call itself.
- `client.html` / `client_server.py` are a minimal reference chat UI shipped with the lab (session/event inspector panel included) — not meant as a production frontend.

## Related

- [`seo_skills_agent`](../seo_skills_agent/) — same course (Craft ADK Agents with Persistent Memories), the Skills/`SkillToolset` half of the curriculum (GENAI154) instead of the Sessions/Memory half.
