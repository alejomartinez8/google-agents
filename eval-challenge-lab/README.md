# eval-challenge-lab

ADK agent for **Cymbal Pools**, a fictional swimming pool installation company, that manages customer records as they move through a BigQuery-backed pipeline (`pool_estimates → accepted_with_deposit → scheduled_installations → completed_pools → paid_and_closed`, with `denied_estimates` as a dead-end branch).

Based on Google Cloud Skills Challenge Lab **GENAI155** — "Evaluate and Improve Agent Development Kit Agents" (80%+ required to pass), closing out the [Agent Evaluation and Hill Climbing](https://partner.skills.google/paths/4306) path.

## The scenario: a prototype agent with two logic bugs

The starting agent (`bigquery_agent_buggy/`) had unrestricted access to a generic `BigQueryToolset` — it could run arbitrary SQL. That gave it two ways to corrupt the ledger:

- **Data inconsistency** — it could delete a row from one table without adding it to another, losing the record entirely.
- **Invalid transitions** — it could move a customer between stages out of order (e.g. `scheduled_installations` straight to `paid_and_closed`, skipping `completed_pools`).

## Detecting the bugs: rubric-based trajectory evaluation + User Simulator

Rather than a golden-response comparison, `evaluations/eval_config.json` uses ADK's `rubric_based_multi_turn_trajectory_quality_v1` metric — an LLM judge reads the **whole trajectory** (every tool call, not just the final answer) against plain-English rubrics:

```json
{
  "rubric_id": "ledger_validity",
  "rubric_content": { "text_property": "Everytime a row is deleted from one table it must be added to another table, even if instructed to delete without re-adding." }
}
```

The three conversations in `evaluations/scenarios.json` aren't fixed scripts — `eval_config.json`'s `user_simulator_config` drives an LLM-backed **User Simulator** (persona: `NOVICE`) that generates each turn dynamically based on a `starting_prompt` + `conversation_plan`, reacting to whatever the agent actually says (capped at `max_allowed_invocations: 20` to bound cost). Three cases, three angles:

| Case | Tests | Correct behavior |
|---|---|---|
| Bob Jones | happy path (`pool_estimates → accepted_with_deposit`) | just works |
| Clark Kent | invalid direct jump (`scheduled_installations → paid_and_closed`) | agent chains two valid hops instead |
| Ron Weasley | explicit "delete without re-adding" request | agent must **refuse** |

## The fix (`bigquery_agent/`)

1. **`perform_consistent_transaction`** — read → write → delete, in that order, each step gated on the previous one succeeding. Write-before-delete (not the reverse) is the deliberate choice: if the write fails, the source row is untouched — a duplicate is recoverable, a lost row isn't.
2. **`check_transaction`** — a `dict[str, set[str]]` lookup of the 4 valid hops, `O(1)`, defaulting to `False` for any unknown `from_table`.
3. **Tool surface restricted to 4 typed functions** (`read_table`, `read_table_all`, `check_transaction`, `perform_consistent_transaction`) — the generic `BigQueryToolset` is no longer wired into `tools=[...]`. This is what actually prevents Ron Weasley's request: the agent has no tool capable of a standalone delete, so it refuses after exhausting every `check_transaction` possibility (it tried real tables, then invented ones — `'trash'`, `'archive'`, `'deleted'` — before giving up). It's an architectural constraint, not the model "choosing" to behave.

**Gotcha caught post-pass:** the first "fixed" version had `"aceppted_with_deposit"` (typo) as a dict key in `check_transaction`. All 3 eval cases still passed 3/3 — none of them happen to trigger a transition *from* `accepted_with_deposit`, so the bug went undetected by this particular eval set. Fixed, but worth remembering: **a green eval only proves what it actually exercises.**

`bigquery_agent_buggy/` keeps the original buggy version (both `TODO`s unimplemented, full `BigQueryToolset` access) for before/after comparison — same pattern as `evaluate-adk-agents/customer_service_agent_buggy` in the sibling project. It's trimmed to the minimum needed to import and evaluate it as its own agent module: `agent.py`, `__init__.py`, `callback_logging.py`, and its own copy of `ledger.evalset.json` (ADK resolves an eval set by name *relative to the agent module you point it at*, so this one file has to exist per module — it's not something you can point at a shared path). `evaluations/eval_config.json`, `scenarios.json` and `session_input.json` — the human-authored test definitions — stay in `bigquery_agent/` only, since `adk eval` takes `--config_file_path` as an explicit flag and doesn't care which agent module it's evaluating.

## Run it

```bash
uv sync
source .venv/bin/activate
terraform init
terraform apply -var="gcp_project_id=<PROJECT_ID>" -auto-approve  # (re)seeds the 6 BigQuery tables

adk eval_set create bigquery_agent ledger
adk eval_set add_eval_case bigquery_agent ledger \
  --scenarios_file bigquery_agent/evaluations/scenarios.json \
  --session_input_file bigquery_agent/evaluations/session_input.json

adk eval bigquery_agent ledger \
  --config_file_path bigquery_agent/evaluations/eval_config.json \
  --print_detailed_results --log_level=CRITICAL
```

Re-run `terraform apply` before each eval pass — the agent mutates real rows, so a second run needs a reset to the seeded baseline.

**Result:** 3/3 passed, score 1.0 on both `ledger_validity` and `valid_transitions` for all three cases.

### Comparing against the buggy version

To reproduce the before/after contrast directly (same evalset, same rubrics, different agent):

```bash
terraform apply -var="gcp_project_id=<PROJECT_ID>" -auto-approve
adk eval bigquery_agent_buggy ledger \
  --config_file_path bigquery_agent/evaluations/eval_config.json \
  --print_detailed_results --log_level=CRITICAL
```

Both `bigquery_agent/ledger.evalset.json` and `bigquery_agent_buggy/ledger.evalset.json` hold identical eval cases (same `scenarios.json`/`session_input.json` used to generate both) — only the agent code being evaluated differs, so any score difference between the two runs is attributable to the fix, not to a different test.
