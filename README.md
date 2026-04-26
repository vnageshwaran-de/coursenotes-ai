# udemy-transcript-agent

Automatically download and organize Udemy course transcripts using yt-dlp, orchestrated by a Gemini 2.0 Flash AI agent.

## Features

- Download transcripts for an entire Udemy course in one command
- Uses browser cookies for auth — no passwords stored in code
- Gemini 2.0 Flash agent orchestrates the workflow and handles errors
- Outputs clean `.vtt` transcript files organized by course

## Requirements

- Python 3.10+
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) installed (`pip install yt-dlp`)
- Google Gemini API key
- Active Udemy session in your browser (Chrome/Firefox/Safari)

## Setup

```bash
# 1. Clone the repo
git clone https://github.com/vnageshwaran-de/udemy-transcript-agent.git
cd udemy-transcript-agent

# 2. Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

## Usage

```bash
python main.py
```

Then paste a Udemy course URL when prompted:

```
You: Download all transcripts from https://www.udemy.com/course/your-course-name/
```

The agent will:
1. Fetch the course structure
2. Download all available transcripts to `./output/<course-name>/`
3. Confirm what was saved

## Auth — Browser Cookies (Recommended)

Log into Udemy in your browser, then the agent uses your active session automatically.
Set `COOKIE_BROWSER=chrome` (or `firefox`, `safari`, `edge`) in your `.env`.

## Project Structure

```
udemy-transcript-agent/
├── agent/
│   └── agent.py          # Gemini 2.0 Flash agent + tool loop
├── tools/
│   └── ytdlp_tools.py    # yt-dlp wrapper functions
├── tests/                # Unit tests
├── output/               # Downloaded transcripts (git-ignored)
├── config.py             # Environment config
├── main.py               # CLI entry point
├── requirements.txt
└── .env.example
```

## License

MIT
