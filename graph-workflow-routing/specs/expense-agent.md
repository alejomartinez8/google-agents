# Expense Agent Specification

## Feature: Expense Report Processing

### Design Rationale ("The Why")
The Ambient Expense Agent operates on a hybrid architecture designed to optimize latency, cost, and strict compliance:
1. **Deterministic Fast-Path (No LLM):** Routine low-risk tasks (e.g., standard expenses under the $100 threshold) do not require expensive LLM inference. Auto-approval happens deterministically, eliminating token costs and latency.
2. **Security & Privacy Guardrails (Pre-LLM Sanitization):** Personally Identifiable Information (PII) like Social Security Numbers (SSNs) or Credit Card numbers must never be sent to external LLMs. A deterministic redaction filter sanitizes payloads *before* any cognitive processing.
3. **Cognitive Routing & Human-in-the-Loop:** High-value or ambiguous submissions ($250+) are evaluated with LLM context and routed to human managers for final authorization.

---

## Scenarios (BDD Specifications)

```gherkin
Feature: Expense Report Processing

  Scenario: Low-value expense auto-approval
    Given an expense report with amount: 45
    When the agent processes the report
    Then it auto-approves with no LLM call

  Scenario: High-value expense with PII in the description
    Given an expense report with amount: 250 and an SSN in the description
    When the agent processes the report
    Then it redacts the SSN before the LLM reviewer sees it
    And it routes to human approval after the LLM review
```

---

## Technical Specifications

### 1. Routing Rules & Thresholds
- **Low-Value Auto-Approval (`amount < 100`):**
  - Executed deterministically without invoking the LLM.
  - Returns `APPROVED` status with generated `approval_id`.
- **High-Value Escalation (`amount >= 100`):**
  - Sanitized through the PII filter.
  - Evaluated by the LLM reviewer.
  - Routed to human manager approval queue (`PENDING_MANAGER_REVIEW`).

### 2. Security & Compliance Pipeline
- **PII Redactor:** Regex/pattern matching to detect and mask SSNs (`\b\d{3}-\d{2}-\d{4}\b` -> `[REDACTED_SSN]`) before any LLM API request.
- **Deterministic Pre-checks:** Schema verification, duplicate check, and prohibited category blacklist.

### 3. Tool Contracts & State Transitions

```
[Expense Payload]
       │
       ▼
[Deterministic PII Redaction & Pre-validation]
       │
       ├──── (amount < 100 & valid) ─────────► [AUTO_APPROVED] (No LLM Call)
       │
       └──── (amount >= 100) ────────────────► [LLM Reviewer] ──► [PENDING_MANAGER_APPROVAL]
```
