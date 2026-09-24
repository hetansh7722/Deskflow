"""
Handles LLM calls and tool execution for DeskFlow.
"""

import json
import os
import time
import httpx
from tools import TOOL_SCHEMAS, dispatch_tool
import logger

MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

SYSTEM_PROMPT = """\
You are DeskFlow, the IT helpdesk assistant for DeskFlow Technologies.

Areas you cover:
- Software access requests and entitlement checks
- Password resets
- VPN and network troubleshooting
- Creating and checking IT support tickets
- Hardware problems
- Other general IT questions

Follow these rules:
1. Scope: Stay on IT support. For HR, payroll, or unrelated topics, decline \
politely and point the employee to the right team.
2. Act only on requests: Call a tool only when the employee asks for an action or \
for information. Acknowledgements such as "thanks", "ok", "great" or "bye" get a \
short friendly reply, with no tool calls and no repeated actions.
3. Ticket details: Never create a ticket without a clear description of the problem. \
If it is missing, ask the employee to briefly describe the issue first.
4. Multi-step requests: For "get me access if I don't have it", check the \
entitlement first, then raise a ticket only if it is needed.
5. Ticket confirmation: After creating a ticket, tell the employee its ID and the \
expected response time.
6. Errors: If a tool fails, explain plainly what went wrong and what to try next.
7. Style: Short, clear and friendly. Avoid technical jargon.
8. Privacy: Only share data belonging to the employee you are chatting with. \
If asked about someone else's tickets, entitlements or profile, decline and say \
that information is confidential.
9. Unclear input: If a message looks like random characters or gibberish, do not \
call tools. Ask the employee to describe their IT issue.\
"""


def _call_groq(messages: list, api_key: str) -> dict:
    """Call Groq API with automatic retry on rate limit."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": MODEL,
        "messages": messages,
        "tools": TOOL_SCHEMAS,
        "tool_choice": "auto",
        "temperature": 0.2,
    }
    for attempt in range(4):
        with httpx.Client(timeout=60) as client:
            resp = client.post(GROQ_API_URL, headers=headers, json=payload)
            if resp.status_code == 429:
                wait = 20 * (attempt + 1)
                logger.log(f"[Agent] Rate limited, waiting {wait}s before retry {attempt+1}/4...")
                time.sleep(wait)
                continue
            resp.raise_for_status()
            return resp.json()
    raise RuntimeError("Rate limit exceeded after retries. Please wait a minute and try again.")


def run_agent(
    user_message: str,
    conversation_history: list,
    employee_id: str = "EMP001",
) -> dict:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY environment variable is not set.")

    augmented_message = f"[Employee ID: {employee_id}]\n{user_message}"

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(conversation_history)
    messages.append({"role": "user", "content": augmented_message})

    trace = []
    MAX_ITERATIONS = 10

    for iteration in range(1, MAX_ITERATIONS + 1):
        logger.log(f"[Agent] Iteration {iteration} - calling Groq API")

        data = _call_groq(messages, api_key)

        choice = data["choices"][0]
        finish_reason = choice["finish_reason"]
        assistant_msg = choice["message"]
        tool_calls = assistant_msg.get("tool_calls") or []

        step = {"iteration": iteration, "finish_reason": finish_reason, "tool_calls": []}

        msg_dict = {"role": "assistant", "content": assistant_msg.get("content") or ""}
        if tool_calls:
            msg_dict["tool_calls"] = tool_calls
        messages.append(msg_dict)

        if not tool_calls or finish_reason == "stop":
            trace.append(step)
            logger.log(f"[Agent] Done after {iteration} iteration(s)")
            return {
                "response": assistant_msg.get("content") or "(No response generated)",
                "trace": trace,
            }

        for tc in tool_calls:
            tool_name = tc["function"]["name"]
            try:
                arguments = json.loads(tc["function"]["arguments"])
            except (json.JSONDecodeError, KeyError):
                arguments = {}

            logger.log(f"[Tool ->] {tool_name}({json.dumps(arguments)})")
            result_str = dispatch_tool(tool_name, arguments)
            result_obj = json.loads(result_str)
            logger.log(f"[Tool <-] {tool_name} -> {result_str[:200]}")

            step["tool_calls"].append({
                "tool": tool_name,
                "arguments": arguments,
                "result": result_obj,
            })

            messages.append({
                "role": "tool",
                "tool_call_id": tc["id"],
                "name": tool_name,
                "content": result_str,
            })

        trace.append(step)

    logger.log("[Agent] Max iterations reached", level="warning")
    return {
        "response": (
            "I've run into an issue processing your request. "
            "Please try rephrasing, or contact helpdesk@deskflow.in directly."
        ),
        "trace": trace,
    }