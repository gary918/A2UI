import json
import logging
from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_response import LlmResponse
from google.genai import types

logger = logging.getLogger(__name__)


def _wrap_a2ui_part(a2ui_message: dict) -> types.Part:
  """Wrap a single A2UI message for rendering in adk web."""
  datapart_json = json.dumps({
      "kind": "data",
      "metadata": {"mimeType": "application/json+a2ui"},
      "data": a2ui_message,
  })
  blob_data = (
      b"<a2a_datapart_json>"
      + datapart_json.encode("utf-8")
      + b"</a2a_datapart_json>"
  )
  return types.Part(
      inline_data=types.Blob(
          data=blob_data,
          mime_type="text/plain",
      )
  )


def a2ui_callback(
    callback_context: CallbackContext,
    llm_response: LlmResponse,
) -> LlmResponse | None:
  """Convert A2UI JSON in text output to rendered components for adk web."""
  new_parts = []
  has_a2ui = False

  # 1. Check for STAGED A2UI payload in session state (Preferred Pattern)
  state = callback_context.state
  if state.get("pending_a2ui_payload") is not None:
    payload = state["pending_a2ui_payload"]
    state["pending_a2ui_payload"] = None
    logger.info("Found staged A2UI payload in state. Appending to response.")
    has_a2ui = True

    # If there are existing text parts from the LLM, keep them
    if llm_response.content and llm_response.content.parts:
      for part in llm_response.content.parts:
        if part.text:
          new_parts.append(part)

    # Wrap messages from staged payload
    if isinstance(payload, dict) and "a2ui_messages" in payload:
      messages = payload["a2ui_messages"]
    elif isinstance(payload, list):
      messages = payload
    else:
      messages = [payload] if payload else []

    for msg in messages:
      new_parts.append(_wrap_a2ui_part(msg))

    return LlmResponse(
        content=types.Content(role="model", parts=new_parts),
        custom_metadata={"a2a:response": "true"},
    )

  # 2. Fallback: Parse A2UI JSON from LLM text output (Legacy Pattern)
  if not llm_response.content or not llm_response.content.parts:
    return None

  for part in llm_response.content.parts:
    if not part.text:
      new_parts.append(part)
      continue

    text = part.text
    text_part = ""
    json_string_cleaned = ""

    if "---a2ui_JSON---" in text:
      has_a2ui = True
      text_part, json_string = text.split("---a2ui_JSON---", 1)
      json_string_cleaned = (
          json_string.strip().lstrip("```json").rstrip("```").strip()
      )
      logger.debug(
          f"[Fallback] Found delimiter. text_part='{text_part}',"
          f" json_string_cleaned='{json_string_cleaned}'"
      )
    else:
      # Try to see if the whole text is JSON
      cleaned = text.strip().lstrip("```json").rstrip("```").strip()
      if (cleaned.startswith("{") and cleaned.endswith("}")) or (
          cleaned.startswith("[") and cleaned.endswith("]")
      ):
        try:
          parsed = json.loads(cleaned)
          a2ui_keys = {
              "beginRendering",
              "surfaceUpdate",
              "dataModelUpdate",
              "deleteSurface",
          }
          if isinstance(parsed, dict) and (
              "a2ui_messages" in parsed or any(k in parsed for k in a2ui_keys)
          ):
            has_a2ui = True
            json_string_cleaned = cleaned
            logger.debug(
                "[Fallback] No delimiter, but text is valid A2UI dict. Parsing"
                " whole text."
            )
          elif isinstance(parsed, list) and any(
              isinstance(msg, dict) and any(k in msg for k in a2ui_keys)
              for msg in parsed
          ):
            has_a2ui = True
            json_string_cleaned = cleaned
            logger.debug(
                "[Fallback] No delimiter, but text is valid A2UI list. Parsing"
                " whole text."
            )
        except Exception as e:
          logger.debug(
              f"[Fallback] Text looks like JSON but failed to parse/verify: {e}"
          )

    if has_a2ui:
      if text_part.strip():
        new_parts.append(types.Part(text=text_part.strip()))

      try:
        ui_data = json.loads(json_string_cleaned)
        if isinstance(ui_data, list):
          messages = ui_data
        elif isinstance(ui_data, dict) and "a2ui_messages" in ui_data:
          messages = ui_data["a2ui_messages"]
        else:
          messages = [ui_data] if ui_data else []

        for msg in messages:
          new_parts.append(_wrap_a2ui_part(msg))
      except Exception as e:
        logger.error(
            "[Fallback] Failed to parse A2UI JSON in callback: %s. Raw JSON"
            " string was: '%s'",
            e,
            json_string_cleaned,
        )
        new_parts.append(part)
    else:
      new_parts.append(part)

  if has_a2ui:
    return LlmResponse(
        content=types.Content(role="model", parts=new_parts),
        custom_metadata={"a2a:response": "true"},
    )

  return None
