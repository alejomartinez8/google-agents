# Copyright (c) 2026 Cymbal Direct. All rights reserved.
"""Winter Storm Triage Agent for resolving package delivery disruptions using Cymbal Logistics MCP."""

import os
import sys

from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from google.genai import types
from mcp import StdioServerParameters

MODEL = "gemini-3.5-flash"

# Define the MCP toolset connected to the Cymbal Logistics FastMCP server
mcp_server_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "cymbal_direct_mcp.py")
)

cymbal_mcp_toolset = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command=sys.executable,
            args=[mcp_server_path],
        )
    )
)

INSTRUCTION = """You are the Cymbal Direct Winter Storm Triage Agent.
Your primary role is to handle customer orders that are delayed due to severe winter storms following standard operating procedures.

When a customer or order inquiry is received:
1. Verification:
   - Call get_order_status with the order_id to verify the order status and identify the customer_id.
   - Call get_customer_loyalty_info with the customer_id to determine their loyalty tier.

2. Tier Compensation Rules:
   - Platinum: $100 credit, Next-Day Air shipping upgrade
   - Gold: $50 credit, Next-Day Air shipping upgrade
   - Silver: $25 credit, 3-Day Select shipping upgrade
   - Member: $10 credit, Priority Shipping upgrade

3. Compensation Execution:
   - Call issue_disruption_compensation with the customer_id, the appropriate compensation_amount (e.g., "$50"), and shipping_upgrade (e.g., "Next-Day Air").

4. Customer Communication:
   - Draft an empathetic response acknowledging and apologizing for the delay caused by the winter storm.
   - Detail the compensation credit applied to their account and the complimentary shipping upgrade provided to expedite delivery once operations resume.
   - Offer further assistance.
"""

root_agent = Agent(
    name="winter_storm_triage_agent",
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=INSTRUCTION,
    tools=[cymbal_mcp_toolset],
)

app = App(
    root_agent=root_agent,
    name="app",
)
