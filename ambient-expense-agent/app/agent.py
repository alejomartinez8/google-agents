# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
import json
import re
import uuid
from typing import Any

from google.adk.agents import LlmAgent
from google.adk.apps import App
from google.adk.events.event import Event
from google.adk.events.event_actions import EventActions
from google.adk.models import Gemini
from google.adk.workflow import Workflow
from google.genai import types
from pydantic import BaseModel, Field

MODEL = "gemini-3.6-flash"

# Deterministic Policy Constants
AUTO_APPROVE_THRESHOLD = 100.0
ALLOWED_CATEGORIES = {"meals", "travel", "office_supplies", "software", "training"}
PROHIBITED_CATEGORIES = {"gambling", "crypto", "alcohol", "firearms", "personal"}
SSN_PATTERN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
AMOUNT_PATTERN = re.compile(r"\$?(\d+(?:\.\d{1,2})?)")


class ExpenseReport(BaseModel):
    amount: float = Field(..., description="Total expense amount in USD")
    submitter: str = Field(..., description="Email address of the submitter")
    category: str = Field(..., description="Expense category")
    description: str = Field(
        ..., description="Expense description or business justification"
    )
    date: str = Field(..., description="Transaction date (YYYY-MM-DD)")


class LLMReviewOutput(BaseModel):
    summary: str = Field(
        ..., description="Summary of the high-value expense evaluation"
    )
    risk_assessment: str = Field(
        ..., description="Risk assessment of the business justification"
    )
    recommended_action: str = Field(
        ..., description="Recommended action for the human manager"
    )


def _new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8].upper()}"


def _utc_now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _extract_raw_text(node_input: Any) -> str:
    """Safely extracts raw text from strings, dicts, or ADK Content objects."""
    if isinstance(node_input, str):
        return node_input.strip()
    if hasattr(node_input, "parts") and node_input.parts:
        texts = [
            getattr(p, "text", "") for p in node_input.parts if getattr(p, "text", "")
        ]
        return "".join(texts).strip()
    if hasattr(node_input, "text") and node_input.text:
        return str(node_input.text).strip()
    return str(node_input).strip()


def sanitize_and_prevalidate(node_input: Any) -> Event:
    """Pre-validates expense reports, redacts PII deterministically, and routes to appropriate branch."""
    report: ExpenseReport | None = None

    # Handle direct dict or ExpenseReport instance
    if isinstance(node_input, ExpenseReport):
        report = node_input
    elif isinstance(node_input, dict):
        report = ExpenseReport(**node_input)
    else:
        raw_text = _extract_raw_text(node_input)

        # Clean markdown code blocks if present (```json ... ```)
        cleaned_text = raw_text
        if "```" in cleaned_text:
            cleaned_text = re.sub(
                r"^```(?:json)?\s*", "", cleaned_text, flags=re.MULTILINE
            )
            cleaned_text = re.sub(
                r"```\s*$", "", cleaned_text, flags=re.MULTILINE
            ).strip()

        # Attempt JSON parsing
        try:
            data = json.loads(cleaned_text)
            if isinstance(data, dict):
                report = ExpenseReport(**data)
        except (json.JSONDecodeError, TypeError, ValueError):
            pass

        # If still not parsed, parse natural language input
        if report is None:
            amt_match = AMOUNT_PATTERN.search(raw_text)
            extracted_amount = float(amt_match.group(1)) if amt_match else 50.0

            # Detect category from keywords (prohibited takes priority over allowed)
            lower_text = raw_text.lower()
            detected_category = next(
                (cat for cat in PROHIBITED_CATEGORIES if cat in lower_text), None
            )
            if detected_category is None:
                detected_category = next(
                    (cat for cat in ALLOWED_CATEGORIES if cat in lower_text), "meals"
                )

            report = ExpenseReport(
                amount=extracted_amount,
                submitter="user@company.com",
                category=detected_category,
                description=raw_text,
                date=datetime.date.today().isoformat(),
            )

    # 1. Deterministic PII Sanitization (Redact SSN before any LLM sees it)
    sanitized_description = SSN_PATTERN.sub("[REDACTED_SSN]", report.description)
    sanitized_report = ExpenseReport(
        amount=report.amount,
        submitter=report.submitter,
        category=report.category.lower().strip(),
        description=sanitized_description,
        date=report.date,
    )

    # 2. Deterministic Prohibited Categories (Bypasses LLM)
    if sanitized_report.category in PROHIBITED_CATEGORIES:
        return Event(
            output=sanitized_report.model_dump(),
            actions=EventActions(route="policy_violation"),
        )

    # 3. Deterministic Low-Value Auto-Approval (Bypasses LLM: amount < $100)
    if (
        sanitized_report.amount < AUTO_APPROVE_THRESHOLD
        and sanitized_report.category in ALLOWED_CATEGORIES
    ):
        return Event(
            output=sanitized_report.model_dump(),
            actions=EventActions(route="auto_approve"),
        )

    # 4. High-Value / Contextual Review (Routes to LLM Reviewer: amount >= $100)
    return Event(
        output=sanitized_report.model_dump(),
        actions=EventActions(route="llm_review"),
    )


def auto_approve_node(node_input: dict[str, Any]) -> str:
    """Deterministic Auto-Approval Node (Zero LLM Tokens)."""
    approval_id = _new_id("APV")
    timestamp = _utc_now_iso()
    return json.dumps(
        {
            "status": "APPROVED",
            "approval_id": approval_id,
            "amount": node_input["amount"],
            "submitter": node_input["submitter"],
            "category": node_input["category"],
            "description": node_input["description"],
            "date": node_input["date"],
            "processed_at": timestamp,
            "message": f"✅ [AUTO-APPROVED] Expense of ${node_input['amount']:.2f} auto-approved with no LLM call required.",
        },
        indent=2,
    )


def policy_violation_node(node_input: dict[str, Any]) -> str:
    """Deterministic Policy Violation Node (Zero LLM Tokens)."""
    violation_id = _new_id("VIO")
    timestamp = _utc_now_iso()
    return json.dumps(
        {
            "status": "REJECTED_POLICY_VIOLATION",
            "violation_id": violation_id,
            "amount": node_input["amount"],
            "submitter": node_input["submitter"],
            "category": node_input["category"],
            "description": node_input["description"],
            "date": node_input["date"],
            "logged_at": timestamp,
            "message": f"❌ [POLICY VIOLATION] Prohibited category '{node_input['category']}'. Submission rejected deterministically.",
        },
        indent=2,
    )


# LLM Reviewer Agent Node for high-value expenses (>= $100)
llm_reviewer = LlmAgent(
    name="llm_expense_reviewer",
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction="""You are a senior compliance officer reviewing high-value corporate expenses ($100+).
Analyze the sanitized expense report, assess compliance with corporate policy, and provide a clear justification summary and risk assessment for the human manager approval queue.""",
    output_schema=LLMReviewOutput,
    output_key="llm_review",
)


def manager_escalation_node(node_input: Any) -> str:
    """Routes high-value expense to human manager approval queue after LLM review."""
    ticket_id = _new_id("TKT")
    timestamp = _utc_now_iso()
    review_data = node_input if isinstance(node_input, dict) else {}
    return json.dumps(
        {
            "status": "PENDING_MANAGER_REVIEW",
            "ticket_id": ticket_id,
            "queued_at": timestamp,
            "llm_evaluation": review_data,
            "message": "📋 [HUMAN APPROVAL REQUIRED] High-value expense ($100+) reviewed by LLM and successfully routed to manager queue.",
        },
        indent=2,
    )


# Graph Topology (ADK 2.0 Workflow API)
edges = [
    ("START", sanitize_and_prevalidate),
    (
        sanitize_and_prevalidate,
        {
            "auto_approve": auto_approve_node,
            "policy_violation": policy_violation_node,
            "llm_review": llm_reviewer,
        },
    ),
    (llm_reviewer, manager_escalation_node),
]

root_agent = Workflow(
    name="ambient_expense_workflow",
    description="Enterprise graph workflow for deterministic and cognitive expense processing.",
    edges=edges,
)

app = App(
    root_agent=root_agent,
    name="app",
)
