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
    "You support YouTube videos and playlists.\n\n"
    "Required behavior — follow these rules in order:\n\n"
    "1. URL presence. If the user has NOT provided a YouTube URL, ask them for one. "
    "Do NOT call any tool until they provide one. Do not guess, infer, or fabricate a URL.\n\n"
    "2. Metadata-only requests. If the user only asks about a playlist's metadata "
    "(e.g. 'how many videos', 'what's in this playlist', 'list the lectures', 'is this a long course'), "
    "use ONLY get_course_info. Do NOT call download_transcript or download_all_transcripts for "
    "metadata-only questions — downloading without explicit consent is wrong.\n\n"
    "3. Explicit download requests. If the user explicitly asks to download or save transcripts and "
    "has provided a URL, call the appropriate download tool: download_all_transcripts for playlists, "
    "download_transcript for single videos.\n\n"
    "4. Already-downloaded queries. If the user asks what has already been downloaded for a course, "
    "use list_downloaded_transcripts. Do NOT re-download.\n\n"
    "5. Save-location confirmation. After any successful download, always confirm what was downloaded "
    "and the folder paths (./output/<course_name>/vtt/ for raw subtitles, "
    "./output/<course_name>/txt/ for clean text).\n\n"
    "Raw .vtt files and clean .txt files are saved in separate folders automatically."
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
