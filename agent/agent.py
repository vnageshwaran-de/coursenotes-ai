import google.generativeai as genai
from config import GEMINI_API_KEY, GEMINI_MODEL
from tools.ytdlp_tools import (
    get_course_info,
    download_transcript,
    download_all_transcripts,
    list_downloaded_transcripts
)
from rich.console import Console

console = Console()

genai.configure(api_key=GEMINI_API_KEY)

# --- Tool definitions for Gemini function calling ---

tools = [
    {
        "function_declarations": [
            {
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
            },
            {
                "name": "download_all_transcripts",
                "description": "Download transcripts for all videos in a Udemy course or YouTube playlist. The output folder name is auto-derived from the URL — no need to provide course_name.",
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
            },
            {
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
            },
            {
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
        ]
    }
]

TOOL_MAP = {
    "get_course_info": get_course_info,
    "download_all_transcripts": download_all_transcripts,
    "download_transcript": download_transcript,
    "list_downloaded_transcripts": list_downloaded_transcripts,
}


def run_agent(user_prompt: str):
    """Run the coursenotes-ai transcript agent with a user prompt."""
    model = genai.GenerativeModel(
        model_name=GEMINI_MODEL,
        tools=tools,
        system_instruction=(
            "You are coursenotes-ai, a transcript downloader agent. "
            "You support Udemy courses and YouTube videos or playlists. "
            "When given a URL, detect the platform (Udemy or YouTube), "
            "use the available tools to fetch course info and download transcripts for all lectures. "
            "Raw .vtt files and clean .txt files are saved in separate folders automatically. "
            "Always confirm what was downloaded, the platform detected, and where the files were saved."
        )
    )

    chat = model.start_chat(enable_automatic_function_calling=False)
    console.print(f"\n[bold cyan]Agent:[/bold cyan] Processing your request...\n")

    response = chat.send_message(user_prompt)

    # Agentic loop
    while True:
        if response.candidates[0].content.parts[0].function_call.name:
            fn_call = response.candidates[0].content.parts[0].function_call
            fn_name = fn_call.name
            fn_args = dict(fn_call.args)

            console.print(f"[bold yellow]Tool call:[/bold yellow] {fn_name}({fn_args})")

            fn_result = TOOL_MAP[fn_name](**fn_args)

            console.print(f"[bold green]Tool result:[/bold green] {fn_result}\n")

            response = chat.send_message(
                genai.protos.Content(
                    parts=[genai.protos.Part(
                        function_response=genai.protos.FunctionResponse(
                            name=fn_name,
                            response={"result": str(fn_result)}
                        )
                    )]
                )
            )
        else:
            # Final text response
            final = response.text
            console.print(f"\n[bold cyan]Agent:[/bold cyan] {final}")
            return final
