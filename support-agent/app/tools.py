"""Tools for the multiagent systems support agent.

Two independent pieces, both used from app/agent.py:
  - validate_tool_params: a `before_tool_callback` security guardrail,
    wired onto the agents whose tools reach outside the org (web search,
    MCP knowledge base).
  - find_similar_bugs: the plain Python function behind the `query_bq`
    workflow node — a BigQuery vector search over past incident
    post-mortems.
"""

import os

import dotenv
from google import genai
from google.adk.tools import BaseTool
from google.adk.tools import ToolContext
from google.cloud import bigquery


LOCATION = os.environ["GOOGLE_CLOUD_LOCATION"]

# --- Callback Tool Guardrail for Security ---
async def validate_tool_params(
    tool: BaseTool,
    args: dict,
    tool_context: ToolContext,
) -> dict | None:
  """Callback hook that acts as a security guardrail before any tool executes.

  Blocks queries that might contain sensitive developer secrets or credentials.

  Wiring: bound via `before_tool_callback=validate_tool_params` on any
  Agent whose tools can send data outside the org — see web_search_agent
  and mcp_kb_agent in agent.py. Deliberately NOT bound on
  search_vais_agent, which only queries the internal datastore and has
  nothing to leak outward.

  What it actually checks: `str(args).lower()` serializes the *entire*
  arguments dict (values included, not just keys) into one string before
  the substring check runs — so it does catch a keyword buried inside a
  query string, not just a literal dict key named e.g. "password".

  KNOWN LIMITATION (confirmed in practice, left unresolved on purpose):
  this only sees the arguments as generated for *this* tool call. In this
  workflow, `coordinator` reformulates the user's raw incident report
  into `triage_summary` first, and the calling agent (web_search_agent /
  mcp_kb_agent) can reformulate it again when deciding what to actually
  search for. Either rewrite can legitimately drop a trigger keyword with
  no intent to evade the filter — so a query containing e.g.
  "client_secret" is not guaranteed to still say so by the time it
  reaches here. Treat this as a best-effort net, not a hard guarantee; a
  stricter implementation would also need to check the original user
  input before any agent gets a chance to rephrase it.

  Args:
    tool: The tool instance being called.
    args: The arguments passed to the tool.
    tool_context: The context for the tool execution.

  Returns:
    A dict containing an error response if blocked, otherwise None.
  """
  tool_name = tool.name
  args_str = str(args).lower()

  sensitive_keywords = [
      "private_key",
      "aws_key",
      "gcp_key",
      "token",
      "client_secret",
      "password",
  ]

  if any(kw in args_str for kw in sensitive_keywords):
    print(
        "\n[SECURITY GUARDRAIL] Blocked tool call to"
        f" '{tool_name}' containing sensitive terms."
    )
    return {
        "error": (
            "Tool call blocked: Query parameters contain sensitive keywords"
            " (credentials, keys, or secrets)."
        )
    }
  return None


def find_similar_bugs(triage_summary: str) -> str:
  """Performs a semantic search in the BigQuery bug database to find bugs.

  Called from the `query_bq` workflow node in agent.py — a plain function
  node, not an LLM agent, since this retrieval is fully deterministic and
  doesn't need a model decision to run.

  Flow: embed the query with `text-embedding-004`, then run a BigQuery
  `VECTOR_SEARCH` against a table whose rows already have their
  description pre-embedded into a `description_embedding` column,
  returning the top-3 closest matches by cosine distance.

  Args:
    triage_summary: The description of the new bug to search for.

  Returns:
    A formatted string of the top 3 most similar bugs found, or a message
    if no similar bugs are found.
  """
  dotenv.load_dotenv()

  project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "whistle-flow-demo")
  dataset = os.environ.get("BIGQUERY_DATASET", "ops_intelligence")
  table = os.environ.get("BIGQUERY_TABLE", "incident_post_mortems")

  print(
      "TOOL: Received search query for BigQuery vector search:"
      f" '{triage_summary}'"
  )

  try:
    client = genai.Client(
        vertexai=True,
        project=project_id,
        location=LOCATION
    )

    response = client.models.embed_content(
        model="text-embedding-004",
        contents=triage_summary
    )

    query_embedding = response.embeddings[0].values
  except Exception as e:
    # Degrade gracefully instead of raising: a transient embedding-service
    # outage shouldn't crash the whole graph — the other branches
    # (internal Agent Search, web, MCP) can still produce a usable answer
    # even if this one can't.
    return (
        "[System Notice: The Text Embedding Service is temporarily unavailable."
        " Unable to calculate query embeddings. Please proceed using other"
        " available documentation channels only.]"
    )

  # VECTOR_SEARCH does the nearest-neighbor lookup natively in BigQuery;
  # the query embedding is passed as a query parameter (not interpolated
  # into the SQL string) to avoid building a huge literal array inline.
  sql_query = f"""
  SELECT
    base.title,
    base.description,
    distance
  FROM
    VECTOR_SEARCH(
      TABLE `{project_id}.{dataset}.{table}`,
      'description_embedding',
      (SELECT @query_embedding AS embedding),
      top_k => 3,
      distance_type => 'COSINE'
    )
  """

  # Initialize BigQuery client
  bq_client = bigquery.Client(project=project_id)
  job_config = bigquery.QueryJobConfig(
      query_parameters=[
          bigquery.ArrayQueryParameter(
              "query_embedding", "FLOAT64", query_embedding
          ),
      ]
  )

  try:
    query_job = bq_client.query(sql_query, job_config=job_config)
    results = query_job.result()
  except Exception as e:
    # Same graceful-degradation reasoning as the embedding call above.
    return (
        "[System Notice: The BigQuery similar bugs search database is"
        " temporarily offline or inaccessible. Please proceed using other"
        " available documentation channels only.]"
    )

  if results.total_rows == 0:
    return "No similar bugs were found in the database."

  response_parts = ["Found similar bugs:\n"]
  for i, row in enumerate(results):
    response_parts.append(
        f"{i+1}. Title: {row.title}\n"
        f"   Description: {row.description}\n"
        f"   (Similarity Score/Distance: {row.distance:.4f})\n"
    )

  return "\n".join(response_parts)
