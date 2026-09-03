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

| Project | Description |
|---------|-------------|
| [ambient-expense-agent](ambient-expense-agent/) | ReAct agent scaffolded with `agents-cli`; exposes a FastAPI backend and supports the A2A protocol. |
| [winter-storm-triage](winter-storm-triage/) | Winter Storm Triage Agent built using ADK and a FastMCP server. Resolves shipping delays and issues automated compensations based on customer loyalty tiers, deployed to Vertex AI Agent Runtime. |
| [adk_challenge_lab](adk_challenge_lab/) | Cymbal Shops Paint Shopping Assistant — root `paint_agent` uses `search_agent` as an `AgentTool` (isolated from its other tools due to Agent Platform's search-tool restriction) and transfers to `room_planner_agent` → `coverage_calculator_agent` for room sizing and pricing. Deployed to Vertex AI Agent Engine and fronted by a Chainlit UI. |
| [support-agent](support-agent/) | DevSecOps Incident Triage System — ADK 2.0 Graph Workflow that fans out to BigQuery vector search, an internal Agent Search datastore, and external web/MCP search, then synthesizes a grounding-prioritized recommendation via a `JoinNode`. Deployed to Agent Runtime and registered in Gemini Enterprise. |

Each project has its own `README.md` with setup, run, and deployment instructions specific to that agent.
