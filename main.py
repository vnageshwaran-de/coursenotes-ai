import sys
from agent.agent import run_agent
from rich.console import Console
from rich.prompt import Prompt

console = Console()

BANNER = "\n[bold magenta]🎓 coursenotes-ai[/bold magenta]"
SUBTEXT = "[dim]Powered by yt-dlp + your choice of LLM (Groq, Gemini, Ollama, OpenRouter)[/dim]\n"


def main():
    console.print(BANNER)
    console.print(SUBTEXT)

    # One-shot mode: python3 main.py <url>
    if len(sys.argv) > 1:
        url = " ".join(sys.argv[1:])
        run_agent(url)
        return

    # Interactive mode: keep prompting until exit
    console.print("[dim]Supported: Udemy course URL or YouTube video/playlist URL[/dim]")
    console.print("[dim]Type 'exit' to quit.\n[/dim]")
    while True:
        user_input = Prompt.ask("[bold white]Enter URL[/bold white]")
        if user_input.lower() in ["exit", "quit", "q"]:
            console.print("[dim]Goodbye![/dim]")
            break
        run_agent(user_input)


if __name__ == "__main__":
    main()
