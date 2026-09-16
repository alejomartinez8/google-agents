# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import datetime
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

from google.cloud import bigquery
from google.adk.agents import Agent
from google.adk.tools.bigquery import BigQueryToolset, BigQueryCredentialsConfig
from google.adk.tools.bigquery.config import BigQueryToolConfig, WriteMode
from google.adk.models import Gemini
from google.genai import types

import google.auth
from google.auth.transport.requests import Request

import google.cloud.logging

load_dotenv()
cloud_logging_client = google.cloud.logging.Client(project=os.getenv('GOOGLE_CLOUD_PROJECT'))
cloud_logging_client.setup_logging()

from .callback_logging import log_query_to_model, log_model_response

RETRY_OPTIONS = types.HttpRetryOptions(initial_delay=1, attempts=6)

# Uses externally-managed Application Default Credentials (ADC) by default.
# This decouples authentication from the agent / tool lifecycle.
# https://cloud.google.com/docs/authentication/provide-credentials-adc
application_default_credentials, _ = google.auth.default()
if not application_default_credentials.valid:
    application_default_credentials.refresh(Request())
credentials_config = BigQueryCredentialsConfig(
    credentials=application_default_credentials)

# Define a tool configuration to block any write operations
tool_config = BigQueryToolConfig(write_mode=WriteMode.ALLOWED)

# Instantiate a BigQuery toolset
bigquery_toolset = BigQueryToolset(
    credentials_config=credentials_config,
    bigquery_tool_config=tool_config
)

def _serialize_datetime_in_dict(data):
    """Recursively converts datetime objects in a dictionary or list to ISO format strings."""
    if isinstance(data, dict):
        return {k: _serialize_datetime_in_dict(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [_serialize_datetime_in_dict(elem) for elem in data]
    elif isinstance(data, (datetime.date, datetime.datetime)):
        return data.isoformat()
    return data

def read_table_all(table_name: str):
    """Reads all rows from the specified table.

    Args:
        table_name: The name of the table to read from.

    Returns:
        list of dict: A list of all row dictionaries in the table.
    """
    client = bigquery.Client(project=os.getenv('GOOGLE_CLOUD_PROJECT'))
    query = f"""
        SELECT * FROM `pool_data.{table_name}`
    """
    query_job = client.query(query)
    results = query_job.result()

    # Always returns a list (will be [] if the table is empty), which is safe to iterate
    return [_serialize_datetime_in_dict(dict(row)) for row in results]


def read_table(table_name: str, email: str):
    """Reads a single row matching the customer's email from the specified table.

    Args:
        table_name: The name of the table to read from.
        email: The customer's email address to filter by.

    Returns:
        dict: The row data if found, otherwise None.
    """
    client = bigquery.Client(project=os.getenv('GOOGLE_CLOUD_PROJECT'))
    query = f"""
        SELECT * FROM `pool_data.{table_name}`
        WHERE customer_email = @email
        LIMIT 1
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("email", "STRING", email)
        ]
    )
    query_job = client.query(query, job_config=job_config)
    results = query_job.result()

    # Safely get the first row, or None if no rows exist
    row = next(results, None)
    if row:
        return _serialize_datetime_in_dict(dict(row))
    return None


def write_to_table(table_name: str, row: dict):
    """Writes a row to the specified table, automatically formatting date fields.

    Args:
        table_name: The name of the table to write to.
        row: A dictionary representing the row data to insert.

    Returns:
        str: "Success" on success, empty string if row is empty.
    """
    if not row:
        return ""
    client = bigquery.Client(project=os.getenv('GOOGLE_CLOUD_PROJECT'))

    # We use a standard DML parameterized INSERT statement to avoid BigQuery's
    # streaming buffer limitation. This ensures that any rows written can be
    # deleted or modified immediately afterwards without causing BadRequest errors.
    columns = ", ".join(row.keys())
    param_placeholders = ", ".join(f"@{k}" for k in row.keys())

    query = f"""
        INSERT INTO `pool_data.{table_name}` ({columns})
        VALUES ({param_placeholders})
    """

    query_parameters = []
    for k, v in row.items():
        if v is None:
            param_type = "STRING"
        elif isinstance(v, bool):
            param_type = "BOOL"
        elif isinstance(v, int):
            param_type = "INT64"
        elif isinstance(v, float):
            param_type = "FLOAT64"
        elif isinstance(v, (datetime.date, datetime.datetime)):
            param_type = "DATE" if isinstance(v, datetime.date) else "DATETIME"
            v = v.isoformat()
        else:
            param_type = "STRING"

        query_parameters.append(
            bigquery.ScalarQueryParameter(k, param_type, v)
        )

    job_config = bigquery.QueryJobConfig(query_parameters=query_parameters)
    query_job = client.query(query, job_config=job_config)
    query_job.result()
    return "Success"

def delete_from_table(table_name: str, email: str):
    """Deletes rows from the specified table that match the customer's email.

    Args:
        table_name: The name of the table to delete from.
        email: The customer's email to match for deletion.

    Returns:
        str: "Success" on success.
    """
    client = bigquery.Client(project=os.getenv('GOOGLE_CLOUD_PROJECT'))
    query = f"""
        DELETE FROM `pool_data.{table_name}`
        WHERE customer_email = @email
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("email", "STRING", email)
        ]
    )
    delete_job = client.query(query, job_config=job_config)
    delete_job.result()
    return "Success"

def perform_consistent_transaction(from_table: str, to_table: str, customer_email: str):
    """
    Search for a record from from_table.
    If that record exists, write it to the to_table and delete it from the original table.

    Args:
        from_table: The table to read the record from
        to_table: The table to write the record to
        customer_email: The email of the customer to perform the transaction for

    Returns:
        Whether it could perform the transaction
    """
    # TODO: Implement this function by combining three of the functions above.
    # Make sure to consider if a row is retrieved before attempting to write it
    # to another table or remove it.

    return False

def check_transaction(from_table: str, to_table: str) -> bool:
    """
    Checks if a transition between two tables is valid.
    Args:
        from_table: The source table.
        to_table: The destination table.
    Returns:
        bool: True if the transition is valid, False otherwise.
    """
    # TODO: Implement this function by creating a data structure
    # that allows the agent to look up if a move from one table
    # to another is a valid transition.

    return False

# Agent Definition
root_agent = Agent(
    model=Gemini(model=os.getenv("MODEL"), retry_options=RETRY_OPTIONS),
    name="bigquery_agent_buggy",
    description=(
        "Agent to answer questions about BigQuery data and models and execute"
        " SQL queries."
    ),
    instruction=f"""
        You are a data science agent with access to several BigQuery tools.
        Make use of those tools to answer the user's questions.

        When querying BigQuery, always use the project
        {os.getenv('GOOGLE_CLOUD_PROJECT')} and the dataset named `pool_data`.
        Do not create new tables.
        Before deleting a record to move it, confirm it exists and can be moved.
        Before adding a record, confirm it is not already present.
        Query all available tables in the dataset, and then decide which table to use.
    """,
    before_model_callback=log_query_to_model,
    after_model_callback=log_model_response,
    tools=[bigquery_toolset],
)
