# evaluate-adk-agents — Evaluate ADK Agents on Gemini Enterprise Agent Platform

Two notebooks that evaluate ADK agents two complementary ways: **Lab A** with ADK's own built-in evaluation framework, running entirely local in a notebook; **Lab B** with Gemini Enterprise Agent Platform's (GEAP) managed evaluation tools — user simulation, custom metrics, Automatic Loss Analysis, and a managed evaluation run against a deployed agent.

Based on lab **GENAI164** — "Evaluate ADK Agents on Gemini Enterprise Agent Platform", from course 2 ("Evaluate Agents on Gemini Enterprise Agent Platform") of the [Agent Evaluation and Hill Climbing](https://partner.skills.google/paths/4306) path.

**Environment note**: unlike the other labs in this repo, this one runs in **Vertex AI Workbench** (managed JupyterLab), not Cloud Shell — no `adk run`/`adk web`/`adk deploy` from a terminal.

## Lab A — `Lab_A_evaluate_adk_agents.ipynb` (complete)

Builds `customer_service_agent`, a customer-service agent (Cymbal Home & Garden) with 3 tools (`get_purchase_history`, `issue_refund`, `lookup_product_info`) over in-memory mock data, and evaluates it with ADK's built-in evaluation framework (`adk eval`).

### Real run results

**Reference metrics (`tool_trajectory_avg_score`, `response_match_score`) — expected outcome, called out by the notebook itself before running it:**

`tool_trajectory_avg_score` (compares which tools were called and with what arguments, exact match) passed 1.0 on both eval cases — the agent called the right tools with the right arguments. `response_match_score` (ROUGE-1, literal word overlap against the reference response) **failed** on 3 of 4 invocations (0.49–0.75 against a 0.8 threshold) — not because the agent answered wrong, but because it paraphrased ("Certainly! I can help you with that refund..." vs. the expected "I can help with that..."). ROUGE counts shared words, not meaning.

**LLM-judge metric (`final_response_match_v2`) — confirms the responses were actually correct:**

With the exact same responses ROUGE had rejected, the LLM judge (`gemini-3.5-flash`, 5 samples) scored **2/2 cases PASSED, 1.0 across all 4 invocations** — it recognizes that "I can help you with that refund request..." and "I can help with that..." ask the same thing. Confirms in practice the difference between reference metrics (fast, literal) and LLM-judge metrics (slower/billable, semantic).

**Rubric metric (`rubric_based_final_response_quality_v1`) — matched the notebook's prediction, plus a real judge misfire it didn't predict:**

As the notebook warns, `purchase_history_lookup` PASSED (1.0) but `refund_damaged_item` FAILED (0.5): `conciseness` scores 1.0 throughout, `completeness` drags the score down because its rubric text ("fully answers the customer's request, including the relevant order details") doesn't account for the agent correctly asking for the refund reason before it has order details to give.

What the notebook *doesn't* call out: `completeness` failed on **both** turns of the refund case, not just the first. On turn 2 — after the agent successfully processes the refund and reports the real order ID and amount straight from `issue_refund`'s tool response — the judge still scores completeness 0.0, reasoning that *"the order details in the final answer... are based on hallucinated parameters and cannot be verified using trusted evidence."* That's wrong: `ORD-101` and `$120.00` are exactly what the mock data and the tool response returned, not hallucinated. This looks like the judge grading that turn without the full `function_response` event in view, and jumping to "hallucination" instead of just "unverifiable from what I can see."

**Takeaway**: an LLM-judge's `rationale`/reasoning text can itself be wrong — not just its score. Read the reasoning, don't just trust a FAILED verdict at face value; a rubric worded for one exchange type can misfire on a validly-different turn shape, and the judge can misdiagnose *why* something looks unsupported.

**User simulation (`hallucinations_v1`, `safety_v1`) — dry run confirmed the simulated conversation followed the scenario exactly; the scored run surfaced a likely metric bug, not an agent problem:**

The dry run (`criteria: {}`, no metrics) produced `Overall Eval Status: NOT_EVALUATED` as expected — the User Simulator carried out the 3-turn refund scenario exactly per the `conversation_plan` (ask for customer ID → look up purchase history → request the refund with the "damaged" reason), and the agent called the right tools at the right points throughout.

The scored run (same conversation, `hallucinations_v1` + `safety_v1`) came back **`hallucinations_v1` PASSED (0.91–1.0)** but **`safety_v1` FAILED flat 0.0 on all 3 turns** — on a conversation with zero unsafe content (a greeting, an order lookup, a refund). That flat, identical-across-turns 0.0 (vs. `hallucinations_v1`'s turn-by-turn variation) was the first red flag. The stderr warning log confirmed it: ADK's `metric_evaluator_registry` logs an `[EXPERIMENTAL] <EvaluatorName>` warning the first time it instantiates each metric's evaluator class — `HallucinationsV1Evaluator` shows up in the log, **no `SafetyV1Evaluator` warning ever appears**, even though `safety_v1` was requested in `criteria`. Strong evidence the safety evaluator never actually ran a judge call in this configuration (`safety_v1` combined with `user_simulator_config`) and the framework fell back to a default fail score rather than a real verdict. Logged as an open finding, not chased further (same call as the unresolved `before_tool_callback` mystery in the GENAI162 lab) — worth retrying in isolation (`criteria` with only `safety_v1`) if this comes up again.

**Part 4 — optimize and verify (`tool_trajectory_avg_score` on `customer_service_agent` vs. a seeded-bug `customer_service_agent_v1`):**

`v1` has one weakened line in its instruction: it calls `issue_refund` immediately instead of asking for a reason first. Against the shared `cs_refund.evalset.json` trajectory (ask first, refund second), `v1` **FAILED at 0.0** — it called `issue_refund` on turn 0 with an invented `reason='Customer request'`, then had nothing left to do on turn 1 when the real reason ("damaged") arrived, since it had already acted. The current agent (`v2`) **PASSED at 1.0** on the identical eval set — it asks first, then calls `issue_refund(order_id='ORD-101', reason='damaged')` with the real reason on turn 2. One instruction paragraph, the entire difference between a 0.0 and a 1.0 trajectory score — a concrete regression check, not just "it looked fine."

## Lab B — `Lab_B_eval_geap.ipynb` (complete)

Evaluates `travel_agent` (a travel concierge with `flight_specialist`/`hotel_specialist` sub-agents) with GEAP's managed tools: synthetic adversarial scenario generation, the User Simulator, custom metrics (one code-based efficiency metric, one LLM-judge tone metric) plus predefined multi-turn metrics, and Automatic Loss Analysis. First against the local agent (Part 1), then against the same agent deployed to Agent Runtime via a single managed job (Part 2).

### Real run results

**Part 1 — local agent, 7 adversarial scenarios (unavailable cities, changing plans, invalid seat/room classes, impatient/incomplete users):**

| Metric | Mean | Pass rate |
|---|---|---|
| `multi_turn_efficiency` (custom, code-based) | 0.180 | 0% |
| `tone-check` (custom, LLM-judge) | 0.286 | 0% |
| `multi_turn_tool_use_quality_v1` (predefined) | 0.815 | 14% (1/7) |
| `multi_turn_task_success_v1` (predefined) | 0.589 | **0%** |

Matches the notebook's own prediction — low custom-metric scores (adversarial scenarios force lots of tool calls and hostile tone, both penalized by design) and a higher tool-use score (the agent handles the chaos, just inefficiently). The interesting one: `multi_turn_task_success_v1` averages 0.589 (several cases scoring 0.75–0.875) yet its **pass rate is 0%** — because several scenarios are deliberately unwinnable (booking to a city with "no availability" by design), "task success" can't be achieved no matter how well the agent behaves. A 0% pass rate here doesn't mean the agent failed badly; it means the mean score, not the pass/fail column, is the one telling the real story for this metric on this dataset.

**Automatic Loss Analysis** clustered the 6 failing `multi_turn_tool_use_quality_v1` cases into 2 named categories: **"Omission of Required Tool Call"** (6/7 items — the agent skips a prerequisite lookup and calls a dependent tool with a guessed/hallucinated parameter instead of fetching the real value first) and **"Incorrect Parameter Value"** (1/7 — right tool, right parameter name, wrong value). The dominant failure mode — skip the lookup, guess the parameter — is the same pattern as Lab A's `v1` bug (guessed `reason='Customer request'` instead of asking) — a recurring failure shape across this whole lab, not a one-off.

**Console cross-check**: Agent Platform's console (`Optimize → Evaluation`) has `Experiments` / `Metrics` / `Online monitors` tabs matching the M1 vocabulary lesson exactly — but the `Experiments` tab showed "No rows to display" for this run. The managed Eval Management Service used here is still `v1beta1`/preview; its results aren't wired into that console UI yet. Results are only visible via the SDK or the GCS `dest` bucket.

**Part 2 — managed run against the deployed agent, same 7 scenarios, one server-side job (713 seconds):**

A real GEAP bug, not an agent problem: **2 of the 7 cases silently disappeared from the results.** The poll output showed:

```
Failed to load evaluation result from GCS: ...
Error: 1 validation error for EvaluationItemResult
request.candidateResponses.0.error
  Extra inputs are not permitted [type=extra_forbidden, input_value={'code': 13, 'message': "...has no attribute 'get'"}]
```

Those 2 cases failed server-side (gRPC code 13 = INTERNAL, an `AttributeError` inside the service). When the client SDK tried to parse *that error itself* to report it, the Pydantic model validating the error payload is strict (`extra_forbidden`) and rejected an unexpected field in it — so even the failure couldn't be reported. Net effect: `eval_case_results` silently contains 5 items instead of 7, with no flag in the summary table that 2 are missing — you only notice by counting. Summary metrics below are the mean of only those 5 surviving cases (higher across the board than Part 1's 7-case numbers, plausibly because the 2 missing cases were the hardest ones):

| Metric | Mean (5/7 cases) |
|---|---|
| `multi_turn_efficiency` | 0.416 |
| `tone-check` | 0.500 |
| `multi_turn_tool_use_quality_v1` | 0.713 |
| `multi_turn_task_success_v1` | 0.650 |

**Takeaway**: three separate, independent instances of a GEAP-managed judge/scoring path silently dropping or misreporting results in this lab (the rubric "hallucinated parameters" misfire in Lab A, `safety_v1`'s never-instantiated evaluator, and this dropped-case bug) — a genuine pattern worth remembering: verify case counts and read the raw logs, don't trust a clean-looking summary table at face value.

## Setup

Requires running in a Vertex AI Workbench environment with access to a GCP project (Vertex AI enabled). Each notebook installs its own dependencies in the first cell (`google-adk[eval]`, `google-cloud-aiplatform[evaluation]`, etc.) and restarts the kernel — run the cells in order, top to bottom, without skipping the restart cell.

`customer_service_agent/` and `customer_service_agent_v1/` ship their eval sets (`.evalset.json`) pre-provided by the lab — Lab A reads them but doesn't generate them; the rest of the agent code is written by the notebook itself (`%%writefile` cells).

## Related

- [`code-execution-sandbox`](../code-execution-sandbox/) — another notebook-first (`.ipynb`) project in this repo, same pattern of "Real run results" documented with genuine outputs
- [[evaluate-generative-and-agentic-systems]] / [[vocabulario-evaluacion-de-agentes]] — theory and evaluation vocabulary glossary in the `llm-wiki` vault
