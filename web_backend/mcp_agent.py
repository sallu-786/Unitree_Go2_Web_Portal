import json
import logging
from pathlib import Path

from litellm import completion
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from config import (
    LLM_MODE,
    MODELS,
    DEFAULT_MODEL,
    AZURE_API_BASE,
    AZURE_API_KEY,
    AZURE_API_VERSION,
    OLLAMA_API_BASE,
    OLLAMA_API_KEY,
    MCP_AGENT_PROMPT,

)


logger = logging.getLogger("ros_mcp.agent")


# ---------------------------------------------------------
# Configuration (model + backend resolved from config, same
# pattern as web_backend/llm_describer.py:GenerateResponse)
# ---------------------------------------------------------

_model_key = DEFAULT_MODEL[LLM_MODE]
MODEL = MODELS[LLM_MODE][_model_key]

if LLM_MODE == "azure":
    API_BASE = AZURE_API_BASE
    API_KEY = AZURE_API_KEY
    API_VERSION = AZURE_API_VERSION
else:
    API_BASE = OLLAMA_API_BASE
    API_KEY = OLLAMA_API_KEY
    API_VERSION = None  # not needed

# server.py is assumed to be in the project root:
#
# project/
# ├── server.py
# └── web_backend/
#     └── mcp_agent.py
#
SERVER_PATH = Path(__file__).resolve().parent.parent / "server.py"
SYSTEM_PROMPT = MCP_AGENT_PROMPT


# ---------------------------------------------------------
# MCP -> tool schema conversion (OpenAI/litellm tool format)
# ---------------------------------------------------------

def convert_mcp_tools(mcp_tools):

    litellm_tools = []

    for tool in mcp_tools:

        litellm_tools.append({
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description or "",
                "parameters": tool.inputSchema,
            }
        })

    return litellm_tools


# ---------------------------------------------------------
# Convert MCP result to text
# ---------------------------------------------------------

def mcp_result_to_text(result):

    if hasattr(result, "content"):

        output = []

        for item in result.content:

            if hasattr(item, "text"):
                output.append(item.text)

            else:
                output.append(str(item))

        if output:
            return "\n".join(output)

    if hasattr(result, "structuredContent"):
        return json.dumps(
            result.structuredContent,
            ensure_ascii=False
        )

    return str(result)


# ---------------------------------------------------------
# Streams one assistant turn via litellm.completion(stream=True).
#
# Yields ("thinking", delta) / ("content", delta) tuples as
# tokens arrive, and finally ("done", assistant_message) once
# the turn (including any tool_calls) is complete.
#
# assistant_message["tool_calls"] (if any) is a list of dicts:
#   {"id": str, "name": str, "arguments_str": str}
# ---------------------------------------------------------

async def stream_chat_turn(messages, tools):

    stream = completion(
        model=MODEL,
        messages=messages,
        tools=tools,
        stream=True,
        api_base=API_BASE,
        api_key=API_KEY,
        api_version=API_VERSION,
    )

    thinking_text = ""
    content_text = ""

    # tool call deltas can arrive fragmented across chunks
    # (OpenAI-style), keyed by their position in the response.
    tool_call_acc = {}

    for chunk in stream:

        delta = chunk.choices[0].delta

        reasoning = getattr(delta, "reasoning_content", None)
        if reasoning:
            thinking_text += reasoning
            yield ("thinking", reasoning)

        if getattr(delta, "content", None):
            content_text += delta.content
            yield ("content", delta.content)

        if getattr(delta, "tool_calls", None):

            for tc in delta.tool_calls:

                idx = getattr(tc, "index", 0)

                if idx not in tool_call_acc:
                    tool_call_acc[idx] = {
                        "id": None,
                        "name": "",
                        "arguments_str": "",
                    }

                if getattr(tc, "id", None):
                    tool_call_acc[idx]["id"] = tc.id

                func = getattr(tc, "function", None)

                if func is not None:

                    if getattr(func, "name", None):
                        tool_call_acc[idx]["name"] += func.name

                    if getattr(func, "arguments", None):
                        tool_call_acc[idx]["arguments_str"] += func.arguments

    tool_calls = None

    if tool_call_acc:
        tool_calls = [
            tool_call_acc[idx] for idx in sorted(tool_call_acc.keys())
        ]

    yield ("done", {
        "role": "assistant",
        "content": content_text,
        "thinking": thinking_text,
        "tool_calls": tool_calls,
    })


# ---------------------------------------------------------
# High-level streaming agent used by the Gradio chatbot.
#
# Yields dicts:
#   {"type": "thinking",    "text": ...}
#   {"type": "content",     "text": ...}
#   {"type": "tool_call",   "name": ..., "arguments": ...}
#   {"type": "tool_result", "text": ...}
# ---------------------------------------------------------

async def stream_agent(user_message):

    server_params = StdioServerParameters(
        command="python",
        args=[str(SERVER_PATH)],
        env=None,
    )

    async with stdio_client(server_params) as (read, write):

        async with ClientSession(read, write) as session:

            await session.initialize()

            tools_result = await session.list_tools()
            mcp_tools = tools_result.tools
            litellm_tools = convert_mcp_tools(mcp_tools)

            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ]

            while True:

                assistant_message = None

                async for kind, payload in stream_chat_turn(messages, litellm_tools):

                    if kind == "thinking":
                        yield {"type": "thinking", "text": payload}

                    elif kind == "content":
                        yield {"type": "content", "text": payload}

                    elif kind == "done":
                        assistant_message = payload

                tool_calls = assistant_message["tool_calls"]

                # Build the API-shaped message to keep in history.
                # (thinking is dropped here - it's UI-only, not sent back.)
                history_message = {
                    "role": "assistant",
                    "content": assistant_message["content"] or "",
                }

                if tool_calls:
                    history_message["tool_calls"] = [
                        {
                            "id": tc["id"],
                            "type": "function",
                            "function": {
                                "name": tc["name"],
                                "arguments": tc["arguments_str"],
                            },
                        }
                        for tc in tool_calls
                    ]

                messages.append(history_message)

                # No tool call -> final answer, turn is done
                if not tool_calls:
                    return

                # -------------------------------------------------
                # Execute requested MCP tools
                # -------------------------------------------------

                for tool_call in tool_calls:

                    tool_name = tool_call["name"]

                    try:
                        arguments = (
                            json.loads(tool_call["arguments_str"])
                            if tool_call["arguments_str"]
                            else {}
                        )
                    except json.JSONDecodeError as e:
                        arguments = {}
                        logger.error(
                            "Failed to parse tool arguments for %s: %s",
                            tool_name, e,
                        )

                    yield {
                        "type": "tool_call",
                        "name": tool_name,
                        "arguments": arguments,
                    }

                    try:

                        result = await session.call_tool(
                            tool_name,
                            arguments
                        )

                        result_text = mcp_result_to_text(result)

                    except Exception as e:

                        result_text = (
                            f"MCP tool execution failed: {e}"
                        )

                    yield {"type": "tool_result", "text": result_text}

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "content": result_text,
                    })