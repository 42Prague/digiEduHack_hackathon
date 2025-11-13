from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from .azure_client import client
from .settings import settings
from .schemas import AnalysisRequest, AnalysisResponse, Step, PlotSpec
from . import tools as tool_impl
from . import session_store


SYSTEM_PROMPT = """
You are an analysis agent for an educational impact intelligence platform.

You receive:
- natural language questions from analysts,
- and you can call tools to inspect which data files exist, find relevant files for a query,
  and filter data by time intervals.

Your job is to:
1. Understand the user's question.
2. Decide which tools to call (if any) to gather the right context.
3. Synthesize a short, decision-focused answer for non-technical stakeholders.
4. If the user explicitly asks for a plot/graph/visualization, also propose a minimal plot
   specification that the frontend can use to render a chart.

IMPORTANT CONSTRAINTS:
- Never assume you see raw student-level data; tools only expose high-level summaries.
- Keep answers concise and focused on insights, not technical details.

FINAL OUTPUT FORMAT (VERY IMPORTANT):
Your FINAL message (after using tools) MUST be a single valid JSON object, with no extra text,
no markdown, and no comments, using this exact schema:

{
  "answer": "<short natural-language answer>",
  "plot": {
    "title": "string or null",
    "x_axis": "string or null",
    "y_axis": "string or null",
    "series": "string or null",
    "description": "string or null"
  } or null
}

If no plot is needed, set "plot": null.
Do NOT include any other top-level keys and do NOT wrap JSON in backticks.
"""


# Tool schemas for Azure Responses API function calling
TOOLS: List[Dict[str, Any]] = [
    {
        "type": "function",
        "name": "load_files",
        "description": (
            "Return a list of available data files and their summaries. "
            "Use this to understand what data exists across regions."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 50,
                    "description": "Maximum number of files to return.",
                }
            },
            "required": [],
        },
    },
    {
        "type": "function",
        "name": "find_relevant_files",
        "description": (
            "Given a natural language query, return the most relevant files "
            "based on semantic similarity of their summaries."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The user's question or a refined search query.",
                },
                "top_k": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 20,
                    "default": 5,
                    "description": "How many files to return at most.",
                },
            },
            "required": ["query"],
        },
    },
    {
        "type": "function",
        "name": "temporal_search",
        "description": (
            "Filter data by a date interval, e.g., a specific school year or "
            "the first six months after a region joins the network."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "start_date": {
                    "type": "string",
                    "description": "Start date (inclusive) in ISO format YYYY-MM-DD.",
                },
                "end_date": {
                    "type": "string",
                    "description": "End date (inclusive) in ISO format YYYY-MM-DD.",
                },
            },
            "required": ["start_date", "end_date"],
        },
    },
]

TOOL_EXECUTORS = {
    "load_files": tool_impl.load_files,
    "find_relevant_files": tool_impl.find_relevant_files,
    "temporal_search": tool_impl.temporal_search,
}


def _summarize_tool_output(name: str, result: Any) -> str:
    """
    Short textual summary for the 'steps' trace.
    """
    try:
        if isinstance(result, dict) and "files" in result:
            files = result.get("files") or []
            file_names = [f.get("name") or f.get("id") for f in files][:3]
            return f"{name} returned {len(files)} files: {', '.join(file_names)}..."
        return f"{name} returned: {str(result)[:200]}"
    except Exception:
        return f"{name} executed."


def _history_to_inputs(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    inputs: List[Dict[str, Any]] = []
    for msg in messages:
        role = msg.get("role")
        content = msg.get("content")
        if not content:
            continue
        if role == "user":
            inputs.append(
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": str(content)},
                    ],
                }
            )
        elif role == "assistant":
            inputs.append(
                {
                    "role": "assistant",
                    "content": [
                        {"type": "output_text", "text": str(content)},
                    ],
                }
            )
    return inputs


def _append_session_message(
    session_id: str,
    role: str,
    content: str,
    *,
    message_type: Optional[str] = None,
    tool_name: Optional[str] = None,
) -> None:
    session_store.append_message(
        session_id,
        {
            "role": role,
            "content": content,
            "type": message_type,
            "tool_name": tool_name,
        },
    )


def _collect_response_messages(response: Any) -> List[str]:
    texts: List[str] = []
    for out in getattr(response, "output", []) or []:
        if getattr(out, "type", None) == "message":
            for piece in getattr(out, "content", []) or []:
                text = getattr(piece, "text", None)
                if text:
                    texts.append(text)
    return texts


def run_agent(
    request: AnalysisRequest,
    *,
    session_id: str,
    existing_messages: Optional[List[Dict[str, Any]]] = None,
) -> AnalysisResponse:
    """
    Orchestrate a multi-step Responses API interaction with tool calling.
    Returns a structured AnalysisResponse including a 'steps' execution trace.
    """
    session_store.ensure_session(session_id)
    history_messages = list(existing_messages or [])

    steps: List[Step] = []

    max_steps = request.max_steps or settings.agent_max_steps

    # Prepare conversation history for the first Responses API call.
    history_inputs = _history_to_inputs(history_messages)

    user_content = f"Language: {request.language}\n\nUser question:\n{request.query}"

    inputs: List[Dict[str, Any]] = history_inputs + [
        {
            "role": "user",
            "content": [
                {"type": "input_text", "text": user_content},
            ],
        }
    ]

    _append_session_message(
        session_id,
        "user",
        request.query,
        message_type="user_message",
    )
    previous_response_id: Optional[str] = None
    model_name = settings.azure_openai_model

    total_input_tokens = 0
    total_output_tokens = 0

    for step_index in range(max_steps):
        response = client.responses.create(
            model=model_name,
            instructions=SYSTEM_PROMPT,
            tools=TOOLS,
            input=inputs,
            previous_response_id=previous_response_id,
        )

        previous_response_id = response.id

        # Track token usage if available
        usage = getattr(response, "usage", None)
        if usage is not None:
            total_input_tokens += getattr(usage, "input_tokens", 0) or 0
            total_output_tokens += getattr(usage, "output_tokens", 0) or 0

        # Inspect outputs for tool calls vs final answer
        function_calls = []
        for output in response.output:
            if output.type == "function_call":
                function_calls.append(output)

        for text in _collect_response_messages(response):
            _append_session_message(
                session_id,
                "assistant",
                text,
                message_type="assistant_message",
            )

        # Record LLM call step (high-level, no chain-of-thought)
        steps.append(
            Step(
                type="llm_call",
                label=f"LLM call #{step_index + 1}",
                detail=(
                    "Model decided to call tools."
                    if function_calls
                    else "Model produced a final answer."
                ),
            )
        )

        # If there are no tool calls, we expect this to be the final JSON answer
        if not function_calls:
            # Prefer output_text for responses API (already concatenated) 
            final_text = getattr(response, "output_text", None)
            if not final_text:
                # Fallback: concatenate message content
                parts = []
                for out in response.output:
                    if out.type == "message":
                        for c in out.content:
                            if c.type in ("output_text", "input_text"):
                                parts.append(c.text)
                final_text = "\n".join(parts)

            # Try to parse JSON; if it fails, fall back to plain-text answer
            answer = final_text
            plot = None

            try:
                parsed = json.loads(final_text)
                answer = parsed.get("answer", final_text)
                plot_data = parsed.get("plot")
                if isinstance(plot_data, dict):
                    plot = PlotSpec(**plot_data)
            except Exception:
                # Not valid JSON; treat it as plain answer.
                pass

            steps.append(
                Step(
                    type="final",
                    label="Final answer",
                    detail="Agent returned a final answer to the user.",
                )
            )

            _append_session_message(
                session_id,
                "assistant",
                answer,
                message_type="assistant_final",
            )

            return AnalysisResponse(
                answer=answer,
                steps=steps,
                plot=plot,
                model=model_name,
                token_usage={
                    "input_tokens": total_input_tokens,
                    "output_tokens": total_output_tokens,
                    "total_tokens": total_input_tokens + total_output_tokens,
                },
                session_id=session_id,
            )
        else:
            next_inputs: List[Dict[str, Any]] = []
            for fc in function_calls:
                name = fc.name
                executor = TOOL_EXECUTORS.get(name)
                if executor is None:
                    raise ValueError(f"Unknown tool requested by model: {name}")

                # Arguments come as JSON string in fc.arguments
                raw_args = fc.arguments or "{}"
                try:
                    args = json.loads(raw_args)
                except json.JSONDecodeError:
                    args = {}
                result = executor(**args)

                _append_session_message(
                    session_id,
                    "assistant",
                    f"[Tool call] {name} args: {json.dumps(args)}",
                    message_type="tool_call",
                    tool_name=name,
                )

                steps.append(
                    Step(
                        type="tool_call",
                        label=f"Tool call: {name}",
                        detail=_summarize_tool_output(name, result),
                        tool_name=name,
                        tool_args=args,
                    )
                )

                _append_session_message(
                    session_id,
                    "tool",
                    json.dumps(result),
                    message_type="tool_result",
                    tool_name=name,
                )

                next_inputs.append(
                    {
                        "type": "function_call_output",
                        "call_id": fc.call_id,
                        "output": json.dumps(result),
                    }
                )

            # Prepare for next loop iteration
            inputs = next_inputs

    # If we exit the loop without a final answer, return a graceful fallback
    steps.append(
        Step(
            type="final",
            label="Max steps reached",
            detail=(
                "Agent reached the maximum number of steps without finalizing an answer. "
                "This usually means the question is too broad or tools misbehaved."
            ),
        )
    )

    fallback_text = "Sorry, I could not produce a confident answer within the configured step limit."
    _append_session_message(
        session_id,
        "assistant",
        fallback_text,
        message_type="assistant_final",
    )

    return AnalysisResponse(
        answer=fallback_text,
        steps=steps,
        plot=None,
        model=model_name,
        token_usage={
            "input_tokens": total_input_tokens,
            "output_tokens": total_output_tokens,
            "total_tokens": total_input_tokens + total_output_tokens,
        },
        session_id=session_id,
    )
