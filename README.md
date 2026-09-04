# google-agents

Learning repo for the **Gemini Enterprise Agent Development Certified Partner Specialist** certification ([Partner Learning program](https://rsvp.withgoogle.com/events/partner-learning/cps)), covering both the [**"Use Agents to Build Agents"**](https://partner.skills.google/paths/3476) and [**"Build and Deploy Agents with Agent Development Kit (ADK)"**](https://partner.skills.google/paths/4144) paths.

Each subfolder is a self-contained agent project built while working through the path's labs and challenges, using [`agents-cli`](https://github.com/google/agents-cli) and the [Agent Development Kit (ADK)](https://adk.dev/) — one of them (`mcp-toolset-triage-agent`) built primarily via natural-language prompts to the [Antigravity CLI](https://antigravity.google/) instead of hand-written code.

## Path coverage

- Agent development and architecture
- Protocol integration (MCP, A2A, A2UI)
- Agent evaluation techniques
- Deployment readiness
- Gemini Enterprise app integration

## Projects

Organized by the 3 learning paths of the [Gemini Enterprise Agent Development Certified Partner Specialist](https://goo.gle/cps) certification, in the order each was built.

### Path 1 — [Use Agents to Build Agents](https://partner.skills.google/paths/3476)

#### [graph-workflow-routing](graph-workflow-routing/)
Event-driven expense approval agent, built during the path's opening course session — "Accelerate Agent Development with Antigravity and Agents CLI" — not a standalone lab, but the guiding project the course walks through.

- Configure `agents-cli` and its ADK 2.0 skill set to scaffold, run, and evaluate an agent locally.
- Build an event-driven (not chat-based) agent using ADK 2.0's Graph Workflow API.
- Apply conditional routing and pre-model data sanitization so only genuinely ambiguous cases reach the LLM.
- Practice the iterate-and-evaluate loop (`eval generate` / `eval grade`) against a spec-derived dataset before deploying.

#### [mcp-toolset-triage-agent](mcp-toolset-triage-agent/)
Winter Storm Triage Agent — Challenge Lab **GENAI144**, "Accelerate Development with Antigravity", closing out Path 1.

- Connect an external data source to an agent workflow using an MCP server.
- Author agent skills and declarative workspace rules.
- Scaffold agent deployment boilerplate using `agents-cli`.
- Deploy the agent to Agent Runtime.

### Path 2 — [Build and Deploy Agents with Agent Development Kit (ADK)](https://partner.skills.google/paths/4144)

#### [graph-workflow-fanout](graph-workflow-fanout/)
DevSecOps Incident Triage System — lab **GENAI162**, from course 1 ("Build Agents with the Agent Development Kit").

- Configure individual ADK agents and safety callbacks.
- Retrieve toolsets dynamically using the ADK Agent Registry.
- Design database vector search function nodes.
- Orchestrate parallel task flows using graph edges and `JoinNode`s.
- Deploy the multi-agent system to Agent Runtime and register/share it in Gemini Enterprise.

#### [code-execution-sandbox](code-execution-sandbox/)
Cymbal Analytics Portfolio Analyst — lab **GENAI163**, from course 2 ("Build Enterprise Agents with Code Execution on Gemini Enterprise Agent Platform").

- Configure and authenticate the Agent Platform SDK for Code Execution.
- Create and manage Code Execution sandboxes using the Agent Platform SDK.
- Execute multi-step Python code in a sandbox and retrieve stdout and file outputs.
- Build an ADK agent with Code Execution and interact with it via `adk web`.

*(Course 3, "Craft ADK Agents with Persistent Memories", not started yet — no project here until it's underway.)*

#### [multi-agent-transfer-chain](multi-agent-transfer-chain/)
Paint Shopping Assistant — Challenge Lab **GENAI129**, "Deploy an Agent with Agent Development Kit (ADK)", closing out Path 2.

- Build an agent with ADK made up of a root agent and sub-agents.
- Enable agents with an Agent Search tool and Python functions as tools.
- Store agent output in session state and retrieve it for subsequent agent instructions.
- Deploy the agent to Agent Runtime and query it from a web app.

### Path 3 — [Agent Evaluation and Hill Climbing](https://partner.skills.google/paths/4306)

Not started yet — covers evaluation metrics, iterative improvement ("hill climbing"), and cost optimization for agentic systems. No project here until it's underway.

Each project has its own `README.md` with setup, run, and deployment instructions specific to that agent.
