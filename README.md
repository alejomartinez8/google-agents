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

### [graph-workflow-routing](graph-workflow-routing/)
Event-driven expense approval agent — guiding project of "Accelerate Agent Development with Antigravity and Agents CLI" (part of "Use Agents to Build Agents").

- Configure `agents-cli` and its ADK 2.0 skill set to scaffold, run, and evaluate an agent locally.
- Build an event-driven (not chat-based) agent using ADK 2.0's Graph Workflow API.
- Apply conditional routing and pre-model data sanitization so only genuinely ambiguous cases reach the LLM.
- Practice the iterate-and-evaluate loop (`eval generate` / `eval grade`) against a spec-derived dataset before deploying.

### [mcp-toolset-triage-agent](mcp-toolset-triage-agent/)
Winter Storm Triage Agent — Challenge Lab **GENAI144**, "Accelerate Development with Antigravity" (part of "Use Agents to Build Agents").

- Connect an external data source to an agent workflow using an MCP server.
- Author agent skills and declarative workspace rules.
- Scaffold agent deployment boilerplate using `agents-cli`.
- Deploy the agent to Agent Runtime.

### [multi-agent-transfer-chain](multi-agent-transfer-chain/)
Paint Shopping Assistant — Challenge Lab **GENAI129**, "Deploy an Agent with Agent Development Kit (ADK)" (part of "Build and Deploy Agents with ADK").

- Build an agent with ADK made up of a root agent and sub-agents.
- Enable agents with an Agent Search tool and Python functions as tools.
- Store agent output in session state and retrieve it for subsequent agent instructions.
- Deploy the agent to Agent Runtime and query it from a web app.

### [graph-workflow-fanout](graph-workflow-fanout/)
DevSecOps Incident Triage System — lab **GENAI162**, "Build and Deploy Multi-Agent ADK Systems to Gemini Enterprise" (part of "Build and Deploy Agents with ADK").

- Configure individual ADK agents and safety callbacks.
- Retrieve toolsets dynamically using the ADK Agent Registry.
- Design database vector search function nodes.
- Orchestrate parallel task flows using graph edges and `JoinNode`s.
- Deploy the multi-agent system to Agent Runtime and register/share it in Gemini Enterprise.

### [code-execution-sandbox](code-execution-sandbox/)
Cymbal Analytics Portfolio Analyst — lab **GENAI163**, "Analyze Financial Portfolios with Gemini Enterprise Agent Platform Code Execution" (part of "Build and Deploy Agents with ADK").

- Configure and authenticate the Agent Platform SDK for Code Execution.
- Create and manage Code Execution sandboxes using the Agent Platform SDK.
- Execute multi-step Python code in a sandbox and retrieve stdout and file outputs.
- Build an ADK agent with Code Execution and interact with it via `adk web`.

Each project has its own `README.md` with setup, run, and deployment instructions specific to that agent.
