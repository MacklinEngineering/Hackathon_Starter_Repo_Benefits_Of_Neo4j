"""One agent loop, two tool sets.

Both agents use the same model, the same system prompt, the same tool-call
limit and the same Neo4j database. The only difference is the tool list.
"""

import os
import time

import anthropic
from dotenv import load_dotenv

from tools import TOOLS

load_dotenv()

MODEL = os.getenv("CLAUDE_MODEL", "claude-opus-5")
MAX_TOOL_CALLS = int(os.getenv("MAX_TOOL_CALLS", "6"))

VECTOR_ONLY = ["search_documents"]
GRAPH_AND_VECTOR = ["search_documents", "get_schema", "read_cypher"]

DEMO_QUESTIONS = [
    "Draft a short check-in email to our main contact at Globex about the export issue.",
    "How much ARR is exposed to the CSV export timeout bug, and which customers are affected?",
    "Which customers renew this year before a fix ships for a bug they reported?",
]

SYSTEM_PROMPT = f"""You are the customer success assistant at Acme Analytics, a B2B analytics \
software company. Today is Tuesday, September 29, 2026.

Answer questions about Acme's customers using your tools, and base your answer only on what \
the tools return. You can make at most {MAX_TOOL_CALLS} tool calls, so plan them.

Churn risk signals: a renewal date in the next 90 days (a renewal that is already signed \
doesn't count), unresolved high-severity support tickets, the customer's primary contact \
leaving recently, and negative sentiment in recent notes.

Keep answers under 200 words. Lead with the answer, then the evidence behind each fact: the \
chain of connections for graph results (for example, customer → OPENED → ticket → REPORTS → \
issue) and the document ID for search results. If you couldn't verify something, say so."""


def run_agent(question: str, tool_names: list[str], on_step=None) -> dict:
    """Run the agent until it answers. Returns the answer and every tool call it made."""
    client = anthropic.Anthropic()
    tools = [TOOLS[name]["definition"] for name in tool_names]
    messages = [{"role": "user", "content": question}]
    steps = []
    started = time.time()

    while True:
        out_of_calls = len(steps) >= MAX_TOOL_CALLS
        response = client.beta.messages.create(
            model=MODEL,
            max_tokens=16000,
            system=SYSTEM_PROMPT,
            tools=tools,
            tool_choice={"type": "none"} if out_of_calls else {"type": "auto"},
            messages=messages,
            # If a request is declined by a safety classifier, retry it on
            # Anthropic's recommended fallback model instead of failing.
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
        )
        if response.stop_reason != "tool_use":
            break

        messages.append({"role": "assistant", "content": response.content})
        results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            if len(steps) >= MAX_TOOL_CALLS:
                output, is_error = "Tool call limit reached. Answer with what you have.", True
            else:
                try:
                    if block.name not in tool_names:  # Only run the tools this agent was given.
                        raise ValueError(f"{block.name} isn't one of your tools")
                    output, is_error = TOOLS[block.name]["function"](**block.input), False
                except Exception as e:  # Show the error to Claude so it can fix its query.
                    output, is_error = f"Error: {e}", True
                step = {"tool": block.name, "input": block.input, "output": output, "error": is_error}
                steps.append(step)
                if on_step:
                    on_step(step)
            results.append({"type": "tool_result", "tool_use_id": block.id,
                            "content": output, "is_error": is_error})
        messages.append({"role": "user", "content": results})

    if response.stop_reason == "refusal":
        answer = "The request was declined."
    else:
        answer = "".join(block.text for block in response.content if block.type == "text")
    if not answer.strip():  # Rare, but say so rather than show an empty answer.
        answer = f"_No answer returned (stop reason: {response.stop_reason})._"
    return {"answer": answer, "steps": steps, "seconds": round(time.time() - started, 1)}
