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
import os
import sys
from zoneinfo import ZoneInfo

from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import types
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters


MODEL = "gemini-3.5-flash"


def get_weather(query: str) -> str:
    """Simulates a web search. Use it get information on weather.

    Args:
        query: A string containing the location to get weather information for.

    Returns:
        A string with the simulated weather information for the queried location.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        return "It's 60 degrees and foggy."
    return "It's 90 degrees and sunny."


def get_current_time(query: str) -> str:
    """Simulates getting the current time for a city.

    Args:
        city: The name of the city to get the current time for.

    Returns:
        A string with the current time information.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        tz_identifier = "America/Los_Angeles"
    else:
        return f"Sorry, I don't have timezone information for query: {query}."

    tz = ZoneInfo(tz_identifier)
    now = datetime.datetime.now(tz)
    return f"The current time for query {query} is {now.strftime('%Y-%m-%d %H:%M:%S %Z%z')}"


# Define the MCP toolset for Cymbal Logistics
mcp_toolset = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command=sys.executable,
            args=[os.path.join(os.path.dirname(__file__), "cymbal_direct_mcp.py")],
        )
    )
)


root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=(
        "You are a winter storm triage agent. You help resolve customer shipping delays "
        "due to severe winter storms. Follow these procedures:\n"
        "1. Verify the order and customer loyalty details using get_order_status and get_customer_loyalty_info.\n"
        "2. Determine the compensation and shipping upgrade based on the customer's loyalty tier:\n"
        "   - Platinum: $100 credit, Next-Day Air shipping upgrade\n"
        "   - Gold: $50 credit, Next-Day Air shipping upgrade\n"
        "   - Silver: $25 credit, 3-Day Select shipping upgrade\n"
        "   - Member: $10 credit, Priority Shipping upgrade\n"
        "3. Call issue_disruption_compensation to apply the compensation.\n"
        "4. Write an empathetic response to the customer detailing the resolution."
    ),
    tools=[get_weather, get_current_time, mcp_toolset],
)

app = App(
    root_agent=root_agent,
    name="app",
)
