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

## Lab B — `Lab_B_eval_geap.ipynb`

Evaluates `travel_agent` (a travel concierge with `flight_specialist`/`hotel_specialist` sub-agents) with GEAP's managed tools: synthetic adversarial scenario generation, the User Simulator, custom metrics (one code-based efficiency metric, one LLM-judge tone metric) plus predefined multi-turn metrics, and Automatic Loss Analysis. First against the local agent, then against the same agent deployed to Agent Runtime.

*(not yet run)*

## Setup

Requires running in a Vertex AI Workbench environment with access to a GCP project (Vertex AI enabled). Each notebook installs its own dependencies in the first cell (`google-adk[eval]`, `google-cloud-aiplatform[evaluation]`, etc.) and restarts the kernel — run the cells in order, top to bottom, without skipping the restart cell.

`customer_service_agent/` and `customer_service_agent_v1/` ship their eval sets (`.evalset.json`) pre-provided by the lab — Lab A reads them but doesn't generate them; the rest of the agent code is written by the notebook itself (`%%writefile` cells).

## Related

- [`code-execution-sandbox`](../code-execution-sandbox/) — another notebook-first (`.ipynb`) project in this repo, same pattern of "Real run results" documented with genuine outputs
- [[evaluate-generative-and-agentic-systems]] / [[vocabulario-evaluacion-de-agentes]] — theory and evaluation vocabulary glossary in the `llm-wiki` vault
