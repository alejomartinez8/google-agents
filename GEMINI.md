---
trigger: always_on
always_on: true
---

# google-agents Workspace Rules & Best Practices

This document defines the rules, standards, and development guidelines for all agent-based projects in this workspace. These rules are configured as **always_on** and must be strictly followed by all development agents and contributors.

---

## 1. General Python Standards

1. **Python Docstrings**: Every new Python file must start with a clean module-level docstring at the top of the file explaining its purpose, features, and usage.
2. **Strict Type Hinting**: All function and method declarations should include explicit type annotations for parameters and return values to guarantee robust type-checking and runtime predictability.
3. **No Hardcoded Credentials**: Never hardcode API keys, service accounts, or database passwords. Use environment variables resolved via Python's `os` and `dotenv` modules, with placeholder templates provided in `.env.example`.

---

## 2. Agent Development Kit (ADK) Standards

1. **Local MCP Toolset Integration**:
   - Always run local MCP servers via `sys.executable` (using `McpToolset` and `StdioConnectionParams`) rather than relying on global `python3` commands. This ensures tools are executed inside the correct virtual environment.
   - Use relative pathing (`os.path.join(os.path.dirname(__file__), "your_mcp_server.py")`) to locate tool files, ensuring the deployment works seamlessly across local machines, Docker containers, and Cloud Run/Agent Runtime environments.
2. **Model Selection & Location Rules**:
   - Standardize model selection to the current Google GenAI enterprise recommendation (e.g., `gemini-3.5-flash` or `gemini-1.5-pro` as appropriate).
   - Ensure the Google Cloud Location configuration (`GOOGLE_CLOUD_LOCATION` / `us` or `us-west1`) is loaded correctly from `.env` or system environment configurations.
3. **Agent Orchestration**:
   - Prefer single-responsibility agents. For complex agents, delegate specialized subtasks to subagents rather than building bloated prompt-heavy single agents.

---

## 3. Project Organization & Modular Structure

1. **Modular Services**: Keep business logic separated from the API layer. Define agent-specific logic in `app/agent.py` and API endpoints in `app/fast_api_app.py`.
2. **Testing Coverage**:
   - Maintain unit tests in the `tests/unit/` folder.
   - Maintain integration and E2E tests in `tests/integration/` (such as testing local API servers and mock MCP interfaces).
3. **Clean Dependencies**: Always maintain a clean `pyproject.toml` using `uv` to handle dependencies, resolving with locked states (`uv.lock`).

---

## 4. Platform Deployment Rules

1. **Container Portability**:
   - Ensure the `Dockerfile` is always clean, multi-stage where possible, and copies the source files properly into `/code/app/`.
   - Never bundle local `.venv/` folders or local credential files into the final Docker image.
2. **Agent Runtime Compatability**:
   - Avoid executing blocking synchronous sub-processes. When integrating third-party tools or shell scripts, run them using async primitives or native python wrappers to prevent blocking the FastAPI server event loop.
