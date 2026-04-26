from agent.llm_provider import get_client, get_model
from config import LLM_PROVIDER
from tools.ytdlp_tools import (
    get_course_info,
    download_transcript,
    download_all_transcripts,
    list_downloaded_transcripts,
)
from openai import BadRequestError
from rich.console import Console
import json
import time

# Fallback model if primary model fails tool calling
GROQ_FALLBACK_MODEL = "mixtral-8x7b-32768"

console = Console()

# --- Tool definitions (OpenAI-compatible format) ---
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_course_info",
            "description": "Fetch course metadata and list of lectures from a Udemy or YouTube URL.",
            "parameters": {
                "type": "object",
                "properties": {
                    "course_url": {
                        "type": "string",
                        "description": "The full course or playlist URL (Udemy or YouTube)"
                    }
                },
                "required": ["course_url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "download_all_transcripts",
            "description": (
                "Download transcripts for all videos in a Udemy course or YouTube playlist. "
                "The output folder name is auto-derived from the URL — no need to provide course_name."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "course_url": {
                        "type": "string",
                        "description": "The full course or playlist URL (Udemy or YouTube)"
                    },
                    "course_name": {
                        "type": "string",
                        "description": "Optional. Override the auto-derived folder name."
                    }
                },
                "required": ["course_url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "download_transcript",
            "description": "Download transcript for a single Udemy lecture or YouTube video.",
            "parameters": {
                "type": "object",
                "properties": {
                    "lecture_url": {
                        "type": "string",
                        "description": "The URL of the individual lecture or YouTube video"
                    },
                    "course_name": {
                        "type": "string",
                        "description": "Optional. Override the auto-derived folder name."
                    }
                },
                "required": ["lecture_url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_downloaded_transcripts",
            "description": "List all transcript files already downloaded for a course.",
            "parameters": {
                "type": "object",
                "properties": {
                    "course_name": {
                        "type": "string",
                        "description": "The course folder name used during download"
                    }
                },
                "required": ["course_name"]
            }
        }
    },
]

TOOL_MAP = {
    "get_course_info":           get_course_info,
    "download_all_transcripts":  download_all_transcripts,
    "download_transcript":       download_transcript,
    "list_downloaded_transcripts": list_downloaded_transcripts,
}

SYSTEM_PROMPT = (
    "You are coursenotes-ai, a YouTube transcript downloader agent. "
    "You support YouTube videos and playlists. "
    "When given a YouTube URL, use the available tools to fetch video info and download transcripts. "
    "Raw .vtt files and clean .txt files are saved in separate folders automatically. "
    "Always confirm what was downloaded and where the files were saved."
)


def _call_llm(client, model: str, messages: list) -> object:
    """Call the LLM with retry + fallback on tool_use_failed errors."""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            return client.chat.completions.create(
                model=model,
                messages=messages,
                tools=TOOLS,
                tool_choice="auto",
                parallel_tool_calls=False,
            )
        except BadRequestError as e:
            if "tool_use_failed" in str(e) and LLM_PROVIDER == "groq":
                if attempt < max_retries - 1:
                    console.print(f"[dim]Tool call malformed, retrying ({attempt + 1}/{max_retries - 1})...[/dim]")
                    time.sleep(1)
                    continue
                # All retries failed — switch to fallback model
                console.print(f"[bold red]Switching to fallback model: {GROQ_FALLBACK_MODEL}[/bold red]")
                return client.chat.completions.create(
                    model=GROQ_FALLBACK_MODEL,
                    messages=messages,
                    tools=TOOLS,
                    tool_choice="auto",
                    parallel_tool_calls=False,
                )
            raise


def run_agent(user_prompt: str):
    """Run the coursenotes-ai agent with a user prompt."""
    client = get_client()
    model  = get_model()

    console.print(f"\n[bold cyan]Agent:[/bold cyan] Using [bold]{LLM_PROVIDER}[/bold] / {model}\n")

    messages = [
        {"role": "system",  "content": SYSTEM_PROMPT},
        {"role": "user",    "content": user_prompt},
    ]

    # Agentic loop
    while True:
        response = _call_llm(client, model, messages)
        msg = response.choices[0].message

        # No tool call — final answer
        if not msg.tool_calls:
            console.print(f"\n[bold cyan]Agent:[/bold cyan] {msg.content}")
            return msg.content

        # Process tool calls
        messages.append(msg)

        for tool_call in msg.tool_calls:
            fn_name = tool_call.function.name
            fn_args = json.loads(tool_call.function.arguments)

            console.print(f"[bold yellow]Tool call:[/bold yellow] {fn_name}({fn_args})")

            fn_result = TOOL_MAP[fn_name](**fn_args)

            console.print(f"[bold green]Tool result:[/bold green] {fn_result}\n")

            messages.append({
                "role":         "tool",
                "tool_call_id": tool_call.id,
                "content":      json.dumps(fn_result),
            })
