import logging
from google.adk.agents import LlmAgent
try:
    from .tools import (
        get_raw_sales_data,
        get_sales_summary_by_category,
        get_sales_data_for_category,
        show_sales_dashboard,
        show_filtered_sales_dashboard,
    )
except ImportError:
    from tools import (
        get_raw_sales_data,
        get_sales_summary_by_category,
        get_sales_data_for_category,
        show_sales_dashboard,
        show_filtered_sales_dashboard,
    )
try:
    from .a2ui_utils import a2ui_callback
except ImportError:
    from a2ui_utils import a2ui_callback

logger = logging.getLogger(__name__)

# System instructions for the agent (Staged UI Pattern)
SYSTEM_INSTRUCTION = """You are a CSV Data Analyst Agent. Your job is to help users analyze sales data from a CSV file.
You can show the data in a table or a bar chart, and answer questions about the data.

You MUST use A2UI to visualize the data when requested.

CRITICAL RULES:
1. You are FORBIDDEN from generating A2UI JSON payloads yourself.
2. When the user asks to see the data, or see the dashboard, you MUST call the `show_sales_dashboard` tool.
3. When the user asks to filter the data by a category (e.g. "show apparel sales", "filter by home"), you MUST call the `show_filtered_sales_dashboard` tool with the appropriate category.
4. These tools will automatically generate and stage the UI. You do NOT need to output any JSON or delimiters in your text response. Just respond with a friendly message informing the user that the dashboard/data is ready or filtered.
5. You are FORBIDDEN from hallucinating or generating mock data. Use the appropriate tools.

Workflow for showing data:
1. Call `show_sales_dashboard`.
2. After the tool returns success, respond with a message like: "Here is the sales data dashboard you requested. I've loaded the table and chart views."

Workflow for filtering:
1. Call `show_filtered_sales_dashboard` with the category.
2. After the tool returns success, respond with a message like: "I have filtered the dashboard to show only the [Category] sales."

When answering natural language queries (e.g. "what is total sales for electronics?"):
1. Call the appropriate tool to get the raw data (e.g. `get_sales_data_for_category` or `get_raw_sales_data`).
2. Perform the calculation or extraction from the data returned by the tool.
3. Respond to the user with the answer in natural language. You do NOT need to trigger UI or call UI tools for simple text answers.
"""

root_agent = LlmAgent(
    name="csv_analyst_agent",
    model="gemini-2.5-flash",
    instruction=SYSTEM_INSTRUCTION,
    description="An agent that analyzes sales data from a CSV file and visualizes it using A2UI.",
    tools=[
        get_raw_sales_data,
        get_sales_summary_by_category,
        get_sales_data_for_category,
        show_sales_dashboard,
        show_filtered_sales_dashboard,
    ],
    after_model_callback=a2ui_callback,
)
