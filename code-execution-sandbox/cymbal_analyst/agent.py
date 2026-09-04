"""Cymbal Analytics portfolio analyst — an ADK agent wired to a pre-existing
Code Execution sandbox.

Unlike a typical ADK agent that gets its tools handed to it as plain
functions, this one gets a `code_executor`: instead of calling a fixed set
of tools, the LLM writes arbitrary Python on the fly and the executor runs
it inside a secure, isolated sandbox (no outbound network, no host access)
that was already created and populated with data by `ap_sandbox.ipynb`
(Tasks 1-4). This agent doesn't create the sandbox or load any data itself —
it just reuses the one referenced by SANDBOX_RESOURCE_NAME, so it inherits
whatever state (e.g. the `df` DataFrame) that sandbox already has in memory.
"""

import os

from google.genai import types
from google.adk.agents import LlmAgent
from google.adk.models import Gemini
from google.adk.code_executors.agent_engine_sandbox_code_executor import (
    AgentEngineSandboxCodeExecutor,
)

# Model calls occasionally return a transient/malformed response (the lab
# manual itself calls out UNEXPECTED_TOOL_CALL as a known possibility) —
# retry with a short backoff instead of letting one bad turn kill the
# session. Not present in the lab's base version of this file.
RETRY_OPTIONS = types.HttpRetryOptions(initial_delay=1, max_delay=3, attempts=30)

# The sandbox is created once by the notebook (Task 2) and its resource name
# is appended to .env from there — this agent only ever *joins* an existing
# sandbox, it never creates one. Fail fast and explain why, rather than
# letting AgentEngineSandboxCodeExecutor fail later with a less obvious error
# if this is missing.
sandbox_resource_name = os.environ.get("SANDBOX_RESOURCE_NAME")
assert sandbox_resource_name, (
    "SANDBOX_RESOURCE_NAME is not set. "
    "Complete Task 2: 'Add the sandbox resource name to .env' before running adk web."
)

root_agent = LlmAgent(
    model=Gemini(model=os.getenv("MODEL"), retry_options=RETRY_OPTIONS),
    name="cymbal_analyst",
    description="Financial analyst agent for Cymbal Analytics",
    # "MUST write ... in a Python code block" is what actually triggers
    # code_executor: ADK routes fenced Python blocks in the model's response
    # to the executor and feeds the result back, rather than the model
    # calling a declared tool by name. The instruction also tells the model
    # about `df` up front (name, index, columns) since the model has no
    # other way to discover what's already loaded in the sandbox — it can't
    # inspect the sandbox's state except by running code against it.
    instruction="""You are a financial analyst at Cymbal Analytics.
    When asked to analyze data, create charts or visualizations, or perform calculations, you MUST write clean Python code in a Python code block.
    The sandbox environment already has portfolio price data pre-loaded as a pandas DataFrame named df. The DataFrame index is dates. Columns are stock tickers ('GOOGL', 'MSFT', 'AMZN') with daily closing prices.
    Always use df directly for portfolio computations without recreating it.
    Always interpret the code execution output for the user after showing the numbers.""",
    # This is what turns a normal LlmAgent into a code-executing one: ADK
    # intercepts fenced code blocks in the model's output and runs them
    # through this executor instead of just returning them as text. Points
    # at the sandbox created by the notebook, not a new one — see the
    # sandbox_resource_name check above. For agents that need declared
    # *tools* alongside search grounding instead, see the multi-tools-limit
    # workaround documented in ../paint-shopping-assistant/README.md.
    code_executor=AgentEngineSandboxCodeExecutor(
        sandbox_resource_name=sandbox_resource_name,
    ),
)
