# coursenotes-ai

Automatically download and organize course transcripts from Udemy and YouTube using yt-dlp, orchestrated by a Gemini 2.0 Flash AI agent.

> **v1.1 — Udemy + YouTube supported.** More platforms planned for future releases.

## Features

- Download transcripts from **Udemy courses** and **YouTube videos or playlists**
- Course folder auto-named from the URL — no manual input needed
- Raw `.vtt` files and clean readable `.txt` files saved in separate folders
- Uses browser cookies for auth — no passwords stored in code
- Gemini 2.0 Flash agent auto-detects the platform and orchestrates the workflow

## Output Structure

```
output/
├── python-bootcamp/              ← Udemy: auto-derived from course URL
│   ├── vtt/                      ← raw subtitle files
│   │   ├── 001 - Introduction.en.vtt
│   │   └── 002 - Getting Started.en.vtt
│   └── txt/                      ← clean readable transcripts
│       ├── 001 - Introduction.txt
│       └── 002 - Getting Started.txt
└── playlist-PLxxxxx/             ← YouTube: derived from playlist ID
    ├── vtt/
    └── txt/
```

## Requirements

- Python 3.10+
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) (`pip install yt-dlp`)
- Google Gemini API key
- Active Udemy session in your browser (Chrome, Firefox, Safari, or Edge)

## Setup

```bash
# 1. Clone the repo
git clone https://github.com/vnageshwaran-de/coursenotes-ai.git
cd coursenotes-ai

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

Then paste any supported URL when prompted:

```
# Udemy course
You: Download all transcripts from https://www.udemy.com/course/python-bootcamp/

# YouTube playlist
You: Download all transcripts from https://www.youtube.com/playlist?list=PLxxxxxxx

# Single YouTube video
You: Get the transcript for https://www.youtube.com/watch?v=abc123
```

The agent will:
1. Auto-detect the platform (Udemy or YouTube)
2. Fetch the course or playlist structure
3. Download all available transcripts into `output/<name>/vtt/`
4. Convert each to a clean, readable `.txt` file in `output/<name>/txt/`
5. Confirm what was saved and where

## Auth — Browser Cookies (Recommended)

Log into Udemy or YouTube in your browser. The agent picks up your active session automatically — no password ever touches the code.

Set `COOKIE_BROWSER=chrome` (or `firefox`, `safari`, `edge`) in your `.env`.

> **Note:** Public YouTube videos don't require auth. Browser cookies are only needed for Udemy or private/age-restricted YouTube content.

## Project Structure

```
coursenotes-ai/
├── agent/
│   └── agent.py          # Gemini 2.0 Flash agent + tool calling loop
├── tools/
│   ├── ytdlp_tools.py    # yt-dlp wrapper + course name extraction
│   └── vtt_to_text.py    # VTT → clean .txt converter
├── tests/                # Unit tests
├── output/               # Downloaded transcripts (git-ignored)
├── config.py             # Environment config
├── main.py               # CLI entry point
├── requirements.txt
└── .env.example
```

## Roadmap

- [x] Udemy transcript download
- [x] YouTube video and playlist transcript download
- [x] Clean `.txt` output with separate `vtt/` and `txt/` folders
- [x] Auto course folder naming from URL
- [ ] Coursera and LinkedIn Learning support
- [ ] Whisper fallback for courses without captions
- [ ] Markdown export for study notes

## License

MIT
