"""DevSecOps Incident Triage System — multi-agent support agent.

Given a raw incident report, this workflow fans out to three parallel
knowledge sources — a BigQuery vector search over past incidents, an
internal Agent Search (Vertex AI Search) datastore of runbooks, and
external developer documentation via MCP + Google Search — then
synthesizes a single recommendation that always prioritizes internal
knowledge over external. See the graph diagram in README.md.

Origin: Google Cloud Skills lab GENAI162 ("Build and Deploy Multi-Agent
ADK Systems to Gemini Enterprise"), course 1 of the "Build and Deploy
Agents with Agent Development Kit (ADK)" path.
"""

import os
from typing import Any
import dotenv
from google.adk import Agent
from google.adk import Context
from google.adk import Workflow
from google.adk.apps import App
from google.adk.events.event import Event
from google.adk.integrations.agent_registry import AgentRegistry
from google.adk.tools import VertexAiSearchTool
from google.adk.tools.google_search_tool import GoogleSearchTool
from google.adk.workflow import JoinNode, node

from .tools import find_similar_bugs, validate_tool_params


dotenv.load_dotenv()

# --- Config & Registry Initialization ---
# All of these are required — see .env.example. They're read via
# os.environ[...] (not .get(...)) so a missing var fails fast at import
# time, instead of failing silently later inside a tool call.
MODEL = os.environ["MODEL"]
MCP_SERVER_NAME = os.environ["MCP_SERVER_NAME"]
PROJECT_ID = os.environ["GOOGLE_CLOUD_PROJECT"]
LOCATION = os.environ["GOOGLE_CLOUD_LOCATION"]

DATASTORE_LOCATION = os.environ["DATASTORE_LOCATION"]

MCP_SERVER_LOCATION = os.environ["MCP_SERVER_LOCATION"]
DATASTORE_ID = os.environ["DATASTORE_ID"]

# Verification Guard: Prevent API import crashes due to unconfigured MCP settings
if not MCP_SERVER_NAME or "your-mcp" in MCP_SERVER_NAME.lower() or MCP_SERVER_NAME == "None":
    raise ValueError(
        "\n"
        "========================================================================\n"
        "[ERROR] MCP_SERVER_NAME is not configured inside support_agent/.env!\n"
        "Please retrieve your MCP server name from the Active Registry console and\n"
        "update MCP_SERVER_NAME=agentregistry-... in your environment configuration.\n"
        "========================================================================"
    )

# Agent Registry is where MCP servers get registered for a GCP project.
# `registry.get_mcp_toolset(...)` below resolves the server's exposed
# tools through it.
registry = AgentRegistry(project_id=PROJECT_ID, location=MCP_SERVER_LOCATION)


# --- Root Coordinator Agent ---
# Entry point of the graph. Its only job is to turn a raw, possibly messy
# incident report into a normalized `clean_query` string that every other
# agent downstream references via `{clean_query}` — ADK's session-state
# templating: `{key}` inside an instruction string is substituted with
# the state value stored under that key before the prompt reaches the
# model, with no manual wiring required.
#
# NOTE: this agent's output is an intermediate step, not the workflow's
# final answer. If you're inspecting a trace and see a response shaped
# like "Main Error/Exception... Focused Search Query...", that's this
# node talking, not a failure and not synthesis_agent's final
# recommendation — keep following the graph.
coordinator = Agent(
    name="coordinator",
    model=MODEL,
    instruction="""
    You are a DevSecOps incident coordinator.
    Analyze the user's reported incident query and extract:
    1. The main error message or exception name.
    2. Key stack trace lines if present.
    3. The affected programming language or framework.

    Provide a clean, focused search query containing these key terms.
    """,
    output_key="clean_query",
)


# --- Internal Knowledge Nodes ---

# A workflow node doesn't have to be an LLM agent. `@node` wraps a plain,
# deterministic Python function so it can sit in the graph next to agents,
# mixing code and model calls freely. Its output is saved to session
# state automatically under the node's `name` — that's how
# `{query_bq_node}` becomes available to internal_analyst's instruction
# below, with no extra plumbing.
@node(name="query_bq_node")
def query_bq(ctx: Context, node_input: Any) -> Event:
    """Runs semantic BQ vector search to find similar past incident reports."""
    result = find_similar_bugs(str(node_input))
    return Event(state={"query_bq_node": result}, output=result)


# `bypass_multi_tools_limit=True` is required here: by default, Agent
# Platform won't let a search-grounding tool (VertexAiSearchTool,
# GoogleSearchTool) share an agent with other tool types. Since this
# agent only ever carries the one search tool, the flag alone is enough —
# no isolation trick needed. Contrast with mixing a search tool alongside
# non-search tools on the *same* agent, where the fix instead is to wrap
# the search tool as its own `AgentTool()` (see adk_challenge_lab/ in
# this repo for that pattern).
vais_tool = VertexAiSearchTool(
    data_store_id=(
        f"projects/{PROJECT_ID}/locations/{DATASTORE_LOCATION}/collections/"
        f"default_collection/dataStores/{DATASTORE_ID}"
    ),
    bypass_multi_tools_limit=True,
)


# Queries the internal Agent Search datastore (runbooks, indexed as
# unstructured PDFs). No `before_tool_callback` here on purpose: this
# search never leaves the org's own datastore, so there's nothing to
# guard against leaking outward — contrast with web_search_agent and
# mcp_kb_agent below, which do carry the callback.
search_vais_agent = Agent(
    name="search_vais_agent",
    model=MODEL,
    instruction="""
    You are the Internal Documentation Searcher.
    Search the internal documentation using your Vertex AI Search tool for details matching the incident query: {clean_query}

    Output a clear list of matching pages, errors, or troubleshooting procedures you find.
    """,
    tools=[vais_tool],
    output_key="vais_search_data",
)


# --- Internal Analyst Agent ---
# Cross-references two different kinds of internal knowledge in a single
# prompt, via two different state-templating sources:
#   {query_bq_node}    -> structured data ("what happened before, and how
#                         was it fixed"), sourced from the @node's name.
#   {vais_search_data} -> unstructured data ("what does the runbook say
#                         to do"), sourced from search_vais_agent's
#                         explicit `output_key`.
# Putting both in the same instruction forces the model to synthesize
# across sources rather than answer from just one.
internal_analyst = Agent(
    name="internal_analyst",
    model=MODEL,
    instruction="""
    You are the Internal Knowledge Analyst.
    Analyze the provided internal BigQuery bug logs:

    {query_bq_node}

    And Vertex AI Search documentation:

    {vais_search_data}

    Summarize:
    1. Have we seen this issue internally? If so, what was the resolution?
    2. Do our internal manuals and runbooks provide standard operating procedures for this?

    Be factual and precise. Do not hallucinate any information not present in the sources.
    """,
    output_key="internal_response",
)


# --- External Web Search Agent ---

# Same bypass reasoning as vais_tool above, this time for Google Search.
google_search = GoogleSearchTool(bypass_multi_tools_limit=True)


# Queries the public web. Carries `before_tool_callback=validate_tool_params`
# because the search text (built from {clean_query}, which traces back to
# the user's original report) could contain secrets pasted in by accident
# — this callback is the last checkpoint before that text leaves the org
# via an external search call.
#
# KNOWN LIMITATION (confirmed in practice, see tools.py for detail): the
# callback only inspects the *tool call arguments* as actually generated
# at this point, not the raw user input further upstream. The model can
# legitimately rephrase the query on its way here and drop the trigger
# keyword without meaning to, silently slipping past the filter. Treat
# this as a best-effort net, not an airtight guardrail.
web_search_agent = Agent(
    name="web_search_agent",
    model=MODEL,
    instruction="""
    You are the Web Search Agent.
    Your task is to search public developer sources (e.g. GitHub issues, StackOverflow, official documentation) using Google Search.
    Search for details about the following incident query: {clean_query}

    Provide a clear summary of public patched workarounds or documentation.
    """,
    tools=[google_search],
    before_tool_callback=validate_tool_params,
    output_key="external_web_search_response",
)


# --- External MCP Knowledge Base Agent ---
# The MCP toolset exposes its functions with the server as a namespace
# prefix, e.g. `developerknowledge_googleapis_com_search_documents` — not
# a bare `search_documents`. If the agent instruction doesn't name a tool
# explicitly (as here), the model may guess a shorter, plausible-looking
# name and fail with `ValueError: Tool '<name>' not found` (this happened
# in practice with this exact agent). If you hit that error, either name
# the tool explicitly in the instruction or inspect the registry's
# exposed tool names and adjust.
developer_kb_mcp = registry.get_mcp_toolset(
    f"projects/{PROJECT_ID}/locations/{MCP_SERVER_LOCATION}/mcpServers/{MCP_SERVER_NAME}"
)

# Same `before_tool_callback` reasoning as web_search_agent: this query
# also leaves the org's boundary (to the MCP server), so it gets the same
# guardrail — and the same limitation applies.
mcp_kb_agent = Agent(
    name="mcp_kb_agent",
    model=MODEL,
    instruction="""
    You are the Internal Knowledge Agent.
    Your task is to query the Developer KB MCP toolset for any internal developer documentation, guidelines, runbooks, or known incident reports matching this query: {clean_query}

    Provide a clear summary of internal findings.
    """,
    tools=[developer_kb_mcp],
    before_tool_callback=validate_tool_params,
    output_key="external_mcp_kb_response",
)

# --- Join Node ---
# A synchronization barrier: waits until every incoming branch (internal
# + web + MCP) has produced output, then passes them all together to
# whatever comes next. Without it, synthesis_agent could run before the
# slower branches finish and end up missing context.
merge_join = JoinNode(name="merge")


# --- Synthesis & Grounding Agent (Rules-Enforcer) ---
# Reads all three branch outputs (merged by merge_join) and produces the
# actual final answer. The source-attribution prefix
# ("[Source: Internal Grounding]" / "[Source: External Grounding (No
# Internal Reference Found)]" / "[Source: Hybrid Grounding]") is how you
# tell, at a glance, whether the internal-knowledge-first rule actually
# kicked in for a given run.
synthesis_agent = Agent(
    name="synthesis_agent",
    model=MODEL,
    instruction="""
    You are the Lead DevSecOps Synthesis and Grounding Agent.
    You are a rules-based agent that enforces internal knowledge prioritization.
    Your goal is to provide a final resolution recommendation for the user's reported incident.

    You have access to:
    - Internal Knowledge Report: {internal_response}
    - External Web Search findings: {external_web_search_response}
    - External KB findings: {external_mcp_kb_response}

    CRITICAL GROUNDING RULES:
    1. You MUST strictly prioritize internal knowledge over external web knowledge.
    2. If a valid internal incident resolution, runbook, or bug fix is found, use it as the primary solution.
    3. Only use external knowledge if:
       - No internal matching resolution, runbook, or bug is found.
       - The internal docs explicitly refer to external procedures.
    4. If there is any conflict between internal corporate policies/runbooks and external suggestions, the internal guidelines ALWAYS win.
    5. You must explicitly state your source attribution:
       - If the solution is based solely on internal sources, start with: "[Source: Internal Grounding]"
       - If based on external sources, start with: "[Source: External Grounding (No Internal Reference Found)]"
       - If hybrid, start with: "[Source: Hybrid Grounding]"

    Provide a structured resolution report with:
    - Source Attribution
    - Summary of the Issue
    - Recommended Action Steps (clear, numbered)
    - References (internal docs, bugs, or external links)
    """
)


# --- Main Workflow Definition ---
# The graph topology (see README.md for the rendered diagram):
#   START -> coordinator
#   coordinator -> {query_bq, web_search_agent, mcp_kb_agent}   (fan-out;
#     one source node pointing at multiple targets runs them
#     concurrently by default, no extra routing tags needed)
#   query_bq -> search_vais_agent -> internal_analyst            (internal chain)
#   {internal_analyst, web_search_agent, mcp_kb_agent} -> merge_join (join)
#   merge_join -> synthesis_agent                                 (final answer)
root_agent = Workflow(
    name="devsecops_workflow",
    edges=[
        ('START', coordinator),
        (coordinator, query_bq),
        (query_bq, search_vais_agent),
        (coordinator, web_search_agent),
        (coordinator, mcp_kb_agent),
        (search_vais_agent, internal_analyst),
        (web_search_agent, merge_join),
        (mcp_kb_agent, merge_join),
        (internal_analyst, merge_join),
        (merge_join, synthesis_agent),
    ]
)

# --- App Definition ---
# `app` must stay module-level under this exact name — the ADK/agents-cli
# toolchain (playground, deploy, etc.) discovers the agent through it.
app = App(
    name="support_agent",
    root_agent=root_agent,
)
