# google-agents

Learning repo for the **Gemini Enterprise Agent Development Certified Partner Specialist** certification ([Partner Learning program](https://rsvp.withgoogle.com/events/partner-learning/cps)), earned by completing 3 learning paths — [Use Agents to Build Agents](https://partner.skills.google/paths/3476), [Build and Deploy Agents with Agent Development Kit (ADK)](https://partner.skills.google/paths/4144), and [Agent Evaluation and Hill Climbing](https://partner.skills.google/paths/4306) — each closed by its own challenge lab. No separate exam or cost beyond the labs themselves.

Each subfolder is a self-contained agent project built while working through the certification's courses and challenge labs, using [`agents-cli`](https://github.com/google/agents-cli) and the [Agent Development Kit (ADK)](https://adk.dev/) — one of them (`mcp-toolset-triage-agent`) built primarily via natural-language prompts to the [Antigravity CLI](https://antigravity.google/) instead of hand-written code. See [Projects](#projects) below, organized by path.

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

#### [seo_skills_agent](seo_skills_agent/)
Blog Writing & SEO Skill Assistant — lab **GENAI154**, "Use Skills with ADK Agents", from course 3 ("Craft ADK Agents with Persistent Memories").

- Load and register directory-based and inline ADK `Skill` definitions using `SkillToolset`.
- Define domain instructions, checklists, and style guidelines using the Agent Skills specification (`SKILL.md`).
- Expose supplementary reference files dynamically to the LLM via `load_skill_resource`.
- Utilize `skill-creator` to autonomously generate complete, spec-compliant `SKILL.md` skill definitions.

#### [session-memory-persistence](session-memory-persistence/)
Gemini Cloud Tutor — lab "Building an ADK Agent with Session and Memory Services", also from course 3 ("Craft ADK Agents with Persistent Memories").

- Instrument and debug the session lifecycle, observing how events accumulate turn by turn.
- Add session persistence by swapping `InMemorySessionService` for `VertexAiSessionService` (Agent Runtime-backed) and `DatabaseSessionService` (Postgres).
- Add cross-session memory persistence with `InMemoryMemoryService` and `VertexAiMemoryBankService` (Agent Platform Memory Bank), confirmed to survive a full server restart.
- Observe non-deterministic tool invocation, parallel tool calls, and live recovery from a tool error in an LLM agent loop.


#### [multi-agent-transfer-chain](multi-agent-transfer-chain/)
Paint Shopping Assistant — Challenge Lab **GENAI129**, "Deploy an Agent with Agent Development Kit (ADK)", closing out Path 2.

- Build an agent with ADK made up of a root agent and sub-agents.
- Enable agents with an Agent Search tool and Python functions as tools.
- Store agent output in session state and retrieve it for subsequent agent instructions.
- Deploy the agent to Agent Runtime and query it from a web app.

### Path 3 — [Agent Evaluation and Hill Climbing](https://partner.skills.google/paths/4306)

#### [evaluate-adk-agents](evaluate-adk-agents/)
Cymbal Home & Garden customer service agent + a travel concierge agent — lab **GENAI164**, "Evaluate ADK Agents on Gemini Enterprise Agent Platform", from course 2 of the path.

- Evaluate an ADK agent locally with ADK's built-in eval framework: reference metrics, an LLM judge, a custom rubric, and user simulation.
- Prove a fix works with an optimize-and-verify pass against a seeded-bug agent version.
- Evaluate an agent with Gemini Enterprise Agent Platform's managed eval tools: synthetic scenario generation, the User Simulator, custom metrics, and Automatic Loss Analysis.
- Run a fully managed evaluation job against an agent deployed to Agent Runtime.

Each project has its own `README.md` with setup, run, and deployment instructions specific to that agent.
