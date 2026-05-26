import json
import os
from typing import Optional
import urllib.parse
import pandas as pd
from google.adk.tools.tool_context import ToolContext

# The CSV file is in the parent directory of the agent folder
CSV_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "sample_data.csv",
)


def get_raw_sales_data(tool_context: ToolContext) -> dict:
  """Reads and returns all raw sales data from the CSV file.

  Useful for answering questions about the data.
  """
  if not os.path.exists(CSV_PATH):
    return {"error": f"CSV file not found at {CSV_PATH}"}
  try:
    df = pd.read_csv(CSV_PATH)
    return {"data": df.to_dict(orient="records")}
  except Exception as e:
    return {"error": str(e)}


def get_sales_summary_by_category(tool_context: ToolContext) -> dict:
  """Groups sales data by category and returns the total sales for each category."""
  if not os.path.exists(CSV_PATH):
    return {"error": f"CSV file not found at {CSV_PATH}"}
  try:
    df = pd.read_csv(CSV_PATH)
    grouped = df.groupby("Category")["Sales"].sum().reset_index()
    return {"data": grouped.to_dict(orient="records")}
  except Exception as e:
    return {"error": str(e)}


def get_sales_data_for_category(category: str, tool_context: ToolContext) -> dict:
  """Filters sales data for a specific category."""
  if not os.path.exists(CSV_PATH):
    return {"error": f"CSV file not found at {CSV_PATH}"}
  try:
    df = pd.read_csv(CSV_PATH)
    filtered = df[df["Category"].str.lower() == category.lower()]
    return {"data": filtered.to_dict(orient="records")}
  except Exception as e:
    return {"error": str(e)}


def _generate_chart_url(df: pd.DataFrame) -> str:
  """Generates a QuickChart URL for sales by category."""
  grouped = df.groupby("Category")["Sales"].sum().reset_index()
  if grouped.empty:
    chart_config = {
        "type": "horizontalBar",
        "data": {"labels": ["No Data"], "datasets": [{"data": [0]}]},
    }
  else:
    categories = grouped["Category"].tolist()
    sales = grouped["Sales"].tolist()
    chart_config = {
        "type": "horizontalBar",
        "data": {
            "labels": categories,
            "datasets": [
                {
                    "label": "Sales",
                    "data": [int(s) for s in sales],
                    "backgroundColor": "rgba(77, 137, 249, 0.5)",
                    "borderColor": "rgb(77, 137, 249)",
                    "borderWidth": 1,
                }
            ],
        },
        "options": {
            "title": {
                "display": True,
                "text": "Sales by Category",
                "fontSize": 36,
            },
            "scales": {
                "xAxes": [{"ticks": {"beginAtZero": True, "fontSize": 24}}],
                "yAxes": [{"ticks": {"fontSize": 24}}],
            },
            "plugins": {
                "datalabels": {
                    "anchor": "end",
                    "align": "right",
                    "font": {"size": 24, "weight": "bold"},
                }
            },
        },
    }

  config_str = json.dumps(chart_config)
  encoded_config = urllib.parse.quote(config_str)
  return f"https://quickchart.io/chart?c={encoded_config}&width=1800&height=900"


def _build_dashboard_ui(
    table_df: pd.DataFrame, full_df_for_chart: Optional[pd.DataFrame] = None
) -> dict:
  """Helper to build the A2UI components list."""
  components = []

  # Root Column
  components.append({
      "id": "root_col",
      "component": {
          "Column": {"children": {"explicitList": ["title_txt", "tabs_container"]}}
      },
  })

  # Title
  components.append({
      "id": "title_txt",
      "component": {
          "Text": {
              "text": {"literalString": "Sales Data Analysis"},
              "usageHint": "h2",
          }
      },
  })

  # Tabs
  components.append({
      "id": "tabs_container",
      "component": {
          "Tabs": {
              "tabItems": [
                  {"title": {"literalString": "Table View"}, "child": "table_card"},
                  {"title": {"literalString": "Chart View"}, "child": "chart_card"},
              ]
          }
      },
  })

  # Table Card
  components.append({
      "id": "table_card",
      "component": {"Card": {"child": "table_col"}},
  })

  # Table Column
  table_children = ["table_header_row"]
  for i in range(len(table_df)):
    table_children.append(f"table_row_{i}")

  components.append({
      "id": "table_col",
      "component": {
          "Column": {
              "children": {"explicitList": table_children},
              "alignment": "stretch",
          }
      },
  })

  # Table Header Row
  components.append({
      "id": "table_header_row",
      "component": {
          "Row": {
              "children": {
                  "explicitList": [
                      "th_category",
                      "th_month",
                      "th_sales",
                  ]
              },
              "distribution": "spaceBetween",
          }
      },
  })
  components.append({
      "id": "th_category",
      "component": {
          "Text": {
              "text": {"literalString": "Category"},
              "usageHint": "body",
          }
      },
  })
  components.append({
      "id": "th_month",
      "component": {
          "Text": {
              "text": {"literalString": "Month"},
              "usageHint": "body",
          }
      },
  })
  components.append({
      "id": "th_sales",
      "component": {
          "Text": {
              "text": {"literalString": "Sales"},
              "usageHint": "body",
          }
      },
  })

  # Table Data Rows
  for i, (_, row) in enumerate(table_df.iterrows()):
    row_id = f"table_row_{i}"
    components.append({
        "id": row_id,
        "component": {
            "Row": {
                "children": {
                    "explicitList": [
                        f"{row_id}_cat",
                        f"{row_id}_month",
                        f"{row_id}_sales",
                    ]
                },
                "distribution": "spaceBetween",
            }
        },
    })
    components.append({
        "id": f"{row_id}_cat",
        "component": {
            "Text": {
                "text": {"literalString": str(row["Category"])},
                "usageHint": "body",
            }
        },
    })
    components.append({
        "id": f"{row_id}_month",
        "component": {
            "Text": {
                "text": {"literalString": str(row["Month"])},
                "usageHint": "body",
            }
        },
    })
    components.append({
        "id": f"{row_id}_sales",
        "component": {
            "Text": {
                "text": {"literalString": f"{row['Sales']:,.0f}"},
                "usageHint": "body",
            }
        },
    })

  # Chart Card
  components.append({
      "id": "chart_card",
      "component": {"Card": {"child": "chart_col"}},
  })

  # Chart Column
  components.append({
      "id": "chart_col",
      "component": {
          "Column": {
              "children": {"explicitList": ["chart_title_txt", "chart_img"]}
          }
      },
  })

  # Chart Title
  components.append({
      "id": "chart_title_txt",
      "component": {
          "Text": {
              "text": {"literalString": "Sales by Category"},
              "usageHint": "h3",
          }
      },
  })

  # Chart Image (QuickChart API)
  chart_df = (
      full_df_for_chart if full_df_for_chart is not None else table_df
  )
  chart_url = _generate_chart_url(chart_df)
  components.append({
      "id": "chart_img",
      "component": {
          "Image": {
              "url": {"literalString": chart_url},
              "altText": {"literalString": "Sales by Category Bar Chart"},
          }
      },
  })

  return {"components": components}


# ========== STAGED UI TOOLS ==========


def show_sales_dashboard(tool_context: ToolContext) -> dict:
  """Generates and stages the complete sales dashboard UI.

  This stages the A2UI payload in the session state to be sent by the callback.
  The LLM does not need to generate the JSON.

  Returns:
      A status message.
  """
  if not os.path.exists(CSV_PATH):
    return {"error": f"CSV file not found at {CSV_PATH}"}

  try:
    df = pd.read_csv(CSV_PATH)
    ui_data = _build_dashboard_ui(df)

    # Construct A2UI payload
    payload = {
        "a2ui_messages": [
            {"beginRendering": {"surfaceId": "main", "root": "root_col"}},
            {
                "surfaceUpdate": {
                    "surfaceId": "main",
                    "components": ui_data["components"],
                }
            },
        ]
    }

    # Stage payload in session state
    tool_context.state["pending_a2ui_payload"] = payload
    return {
        "status": "success",
        "message": "Dashboard UI generated and staged. Inform the user.",
    }
  except Exception as e:
    return {"error": str(e)}


def show_filtered_sales_dashboard(
    category: str, tool_context: ToolContext
) -> dict:
  """Generates and stages the filtered sales dashboard UI.

  Args:
      category: The category to filter the table by.

  Returns:
      A status message.
  """
  if not os.path.exists(CSV_PATH):
    return {"error": f"CSV file not found at {CSV_PATH}"}

  try:
    df = pd.read_csv(CSV_PATH)
    filtered_df = df[df["Category"].str.lower() == category.lower()]
    ui_data = _build_dashboard_ui(filtered_df, full_df_for_chart=df)

    # Construct A2UI payload
    payload = {
        "a2ui_messages": [
            {"beginRendering": {"surfaceId": "main", "root": "root_col"}},
            {
                "surfaceUpdate": {
                    "surfaceId": "main",
                    "components": ui_data["components"],
                }
            },
        ]
    }

    # Stage payload in session state
    tool_context.state["pending_a2ui_payload"] = payload
    return {
        "status": "success",
        "message": f"Filtered Dashboard UI for '{category}' generated and staged. Inform the user.",
    }
  except Exception as e:
    return {"error": str(e)}
