# `adk web` / `adk run` discover an agent by importing this package and
# looking for a module-level `root_agent` — this re-export is what makes
# that discovery work; agent.py itself is never imported directly by ADK.
from . import agent
