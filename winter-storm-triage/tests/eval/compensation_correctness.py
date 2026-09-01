"""Deterministic check for `compensation_correctness` (see eval_config.yaml).

Verifies the agent's actual `issue_disruption_compensation` tool call (if any)
against the expected amount/shipping upgrade encoded in the case's `reference`
text. Money math shouldn't be graded by an LLM judge alone.
"""

import re

SHIPPING_OPTIONS = ["Next-Day Air", "3-Day Select", "Priority Shipping"]


def _reference_text(instance):
    try:
        return instance["reference"]["response"]["parts"][0]["text"]
    except (KeyError, IndexError, TypeError):
        return ""


def _compensation_calls(instance):
    calls = []
    for turn in (instance.get("agent_data") or {}).get("turns", []):
        for event in turn.get("events", []):
            for part in (event.get("content") or {}).get("parts", []):
                fc = part.get("function_call")
                if fc and fc.get("name") == "issue_disruption_compensation":
                    calls.append(fc.get("args") or {})
    return calls


def evaluate(instance):
    ref_text = _reference_text(instance)
    calls = _compensation_calls(instance)

    if "no compensation" in ref_text.lower():
        if not calls:
            return {"score": 1, "explanation": "No compensation issued, as expected."}
        return {
            "score": 0,
            "explanation": f"Compensation was issued despite the order not qualifying: {calls}",
        }

    if not calls:
        return {"score": 0, "explanation": "Agent never called issue_disruption_compensation."}
    if len(calls) > 1:
        return {"score": 0, "explanation": f"Agent issued compensation more than once: {calls}"}

    call = calls[0]
    expected_amount_match = re.search(r"\$(\d+)", ref_text)
    expected_amount = expected_amount_match.group(1) if expected_amount_match else None
    actual_amount = re.sub(r"[^0-9]", "", str(call.get("compensation_amount", "")))

    expected_shipping = next(
        (s for s in SHIPPING_OPTIONS if s.lower() in ref_text.lower()), None
    )
    actual_shipping = str(call.get("shipping_upgrade", ""))

    amount_ok = expected_amount is not None and actual_amount == expected_amount
    shipping_ok = expected_shipping is not None and expected_shipping.lower() in actual_shipping.lower()

    if amount_ok and shipping_ok:
        return {"score": 1, "explanation": f"Correct compensation issued: {call}"}

    return {
        "score": 0,
        "explanation": (
            f"Compensation mismatch. Expected ${expected_amount} / {expected_shipping}, "
            f"got {call.get('compensation_amount')} / {call.get('shipping_upgrade')}."
        ),
    }
