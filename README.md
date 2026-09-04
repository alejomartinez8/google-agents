# google-agents

Learning repo for the **Gemini Enterprise Agent Development Certified Partner Specialist** certification ([Partner Learning program](https://rsvp.withgoogle.com/events/partner-learning/cps)), covering both the [**"Use Agents to Build Agents"**](https://partner.skills.google/paths/3476) and [**"Build and Deploy Agents with Agent Development Kit (ADK)"**](https://partner.skills.google/paths/4144) paths.

Each subfolder is a self-contained agent project built while working through the path's labs and challenges, using the [Antigravity IDE](https://antigravity.google/), [`agents-cli`](https://github.com/google/agents-cli), and the [Agent Development Kit (ADK)](https://adk.dev/).

## Path coverage

- Agent development and architecture
- Protocol integration (MCP, A2A, A2UI)
- Agent evaluation techniques
- Deployment readiness
- Gemini Enterprise app integration

## Projects

### [ambient-expense-agent](ambient-expense-agent/)
Event-driven expense approval agent built with ADK 2.0's Graph Workflow API — it doesn't chat, it processes a report and returns a decision.

- **Conditional routing, not fan-out**: exactly one of three branches runs per report (`EventActions(route=...)`), the other two never execute.
- Two branches are **zero-token** — deterministic Python for policy violations and auto-approvals; only genuinely ambiguous cases reach the LLM.
- Deterministically **redacts anything that looks like an SSN** before it ever reaches the model, on every branch.
- Self-contained — no external database or datastore to provision.

### [winter-storm-triage](winter-storm-triage/)
Single ADK agent that triages storm-delayed orders: looks up the order, checks loyalty tier via a mock logistics MCP server, and issues a tier-based compensation.

- **Simplest architecture in the repo** — one `Agent`, no sub-agents, no graph.
- MCP server runs as a **local stdio subprocess**, physically bundled inside the deployed package (contrast with `support-agent`'s networked MCP server).
- Built almost entirely by **prompting the Antigravity CLI (`agy`) in natural language** rather than hand-writing code — that's the actual skill the lab tests.
- Real deployed resource ID and the lab's own grading artifacts (`summary_task*.md`) kept as a genuine record of what got produced.

### [paint-shopping-assistant](paint-shopping-assistant/)
Multi-agent ADK assistant for a paint department: product search, room/color picks, coverage calculation, pricing.

- Central lab bug: **a search tool can't share an agent with non-search tools**, not even via a sub-agent — fixed by isolating the search agent behind its own `AgentTool`.
- Transfer chain: `paint_agent` → `room_planner_agent` → `coverage_calculator_agent`, each handling one step of the conversation.
- Grounded in a real product datasheet via **Agent Search** (`VertexAiSearchTool`).
- Ships with a Chainlit frontend (needs pointing at your own deployed agent — the checked-in one is stale/destroyed).

### [support-agent](support-agent/)
DevSecOps Incident Triage System — ADK 2.0 Graph Workflow that searches three sources in parallel and synthesizes one recommendation.

- **Fans out to 3 concurrent branches** (BigQuery vector search, internal Agent Search, external MCP + Google Search), synchronized by a `JoinNode` before synthesis.
- Explicit grounding rule: **internal knowledge always wins over external**, enforced in the synthesis prompt.
- Hits the same search-tool restriction as `paint-shopping-assistant`, solved differently — `bypass_multi_tools_limit=True` instead of an `AgentTool` wrapper — worth comparing both.
- Deployed to Agent Runtime **and** registered in Gemini Enterprise as two separate steps (with a real region-mismatch gotcha documented).

### [code-execution-sandbox](code-execution-sandbox/)
Cymbal Analytics Portfolio Analyst — demonstrates Agent Platform's **Code Execution** sandbox (isolated, no outbound network, state persists across calls).

- The **same sandbox is driven two ways**: hand-written Python via direct SDK calls first, then an ADK agent that autonomously generates and runs its own code against it.
- Portfolio risk metrics (return, volatility, Sharpe ratio) computed manually and **independently reproduced by the agent** against the same in-memory data, to cross-check.
- Real quirks found along the way: a region mismatch between `.env` and where the sandbox actually runs, a duplicate `.env` key left by the notebook, and retry handling added beyond the lab's base code.

Each project has its own `README.md` with setup, run, and deployment instructions specific to that agent.
