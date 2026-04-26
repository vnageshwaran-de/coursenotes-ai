from agent.agent import run_agent
from rich.console import Console
from rich.prompt import Prompt

console = Console()


def main():
    console.print("\n[bold magenta]🎓 Udemy Transcript Agent[/bold magenta]")
    console.print("[dim]Powered by yt-dlp + Gemini 2.0 Flash[/dim]\n")

    while True:
        user_input = Prompt.ask("[bold white]You[/bold white]")
        if user_input.lower() in ["exit", "quit", "q"]:
            console.print("[dim]Goodbye![/dim]")
            break
        run_agent(user_input)


if __name__ == "__main__":
    main()
