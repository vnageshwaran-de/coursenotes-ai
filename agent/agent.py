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
                "description": "Fetch course metadata and list of lectures from a Udemy course URL.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "course_url": {
                            "type": "string",
                            "description": "The full Udemy course URL"
                        }
                    },
                    "required": ["course_url"]
                }
            },
            {
                "name": "download_all_transcripts",
                "description": "Download transcripts for all lectures in a Udemy course.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "course_url": {
                            "type": "string",
                            "description": "The full Udemy course URL"
                        },
                        "course_name": {
                            "type": "string",
                            "description": "A short name/slug to use as the output folder name"
                        }
                    },
                    "required": ["course_url", "course_name"]
                }
            },
            {
                "name": "download_transcript",
                "description": "Download transcript for a single Udemy lecture.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "lecture_url": {
                            "type": "string",
                            "description": "The URL of the individual lecture"
                        },
                        "output_path": {
                            "type": "string",
                            "description": "Local folder path to save the transcript"
                        }
                    },
                    "required": ["lecture_url", "output_path"]
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
    """Run the Udemy transcript agent with a user prompt."""
    model = genai.GenerativeModel(
        model_name=GEMINI_MODEL,
        tools=tools,
        system_instruction=(
            "You are a helpful Udemy transcript downloader agent. "
            "When given a Udemy course URL, use the available tools to fetch course info "
            "and download transcripts for all lectures. "
            "Always confirm what was downloaded and where the files were saved."
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
