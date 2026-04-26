"""Eval-mode wrapper around coursenotes-ai's agentic loop.

This module re-implements ``agent.agent.run_agent`` with two changes:

1. The OpenAI-compatible client is wrapped in
   ``agentprdiff.adapters.openai.instrument_client`` so every
   ``client.chat.completions.create`` call is recorded onto a ``Trace``.
2. The tool dispatch dict is replaced with deterministic stubs (see
   ``suites._stubs``) so the suite never touches yt-dlp / YouTube / the
   filesystem.

Production behavior is unchanged — ``agent/agent.py`` is not modified, not
imported's, internals are not monkey-patched globally. The suite only swaps
what runs *inside* the wrapper.

Returns ``(final_text, Trace)`` so agentprdiff's runner can pull baselines.
"""

from __future__ import annotations

import json
import time
from typing import Any

from agentprdiff import Trace
from agentprdiff.adapters.openai import instrument_client, instrument_tools

# Reuse the production constants — TOOLS spec, system prompt, LLM client
# factory. We do NOT reuse run_agent itself; we re-implement the loop here so
# we have explicit control over the patched client and the stubbed tool map.
from agent.agent import SYSTEM_PROMPT, _call_llm
from agent.llm_provider import get_client, get_model
from config import LLM_PROVIDER

from ._stubs import STUB_TOOL_MAP


# Keep the loop bounded so a runaway model can't burn through the free tier.
MAX_ITERATIONS = 8


def coursenotes_eval_agent(user_prompt: str) -> tuple[str, Trace]:
    """The agent under test for agentprdiff.

    Mirrors ``agent.agent.run_agent`` step-for-step but yields a recorded
    Trace alongside the final text.
    """
    client = get_client()
    model = get_model()

    # Pre-create the trace so we can stamp metadata before running.
    trace = Trace(suite_name="", case_name="", input=user_prompt)
    trace.metadata.update(
        {
            "provider": LLM_PROVIDER,
            "model": model,
            "max_iterations": MAX_ITERATIONS,
        }
    )

    final_text = ""

    with instrument_client(client, trace=trace) as t:
        tools = instrument_tools(STUB_TOOL_MAP, t)

        messages: list[Any] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]

        for _ in range(MAX_ITERATIONS):
            response = _call_llm(client, model, messages)
            msg = response.choices[0].message

            # No tool calls → final answer.
            if not msg.tool_calls:
                final_text = msg.content or ""
                break

            # Append the assistant turn (carries tool_calls metadata).
            messages.append(msg)

            for tool_call in msg.tool_calls:
                fn_name = tool_call.function.name
                try:
                    fn_args = json.loads(tool_call.function.arguments or "{}")
                except json.JSONDecodeError:
                    fn_args = {}

                if fn_name not in tools:
                    fn_result = {"error": f"unknown tool {fn_name!r}"}
                else:
                    try:
                        fn_result = tools[fn_name](**fn_args)
                    except TypeError as exc:
                        # Bad argument shape — record and let the model
                        # recover or terminate.
                        fn_result = {"error": str(exc)}

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(fn_result),
                    }
                )

            # Brief courtesy delay so the free-tier rate limit isn't tripped
            # back-to-back. Cheap and keeps the recorded latency realistic.
            time.sleep(0.1)
        else:
            final_text = "[agent: hit MAX_ITERATIONS without producing a final answer]"

    return final_text, trace
