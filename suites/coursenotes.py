"""agentprdiff regression suite for coursenotes-ai.

Each case asserts something about *what coursenotes-ai's agent does*, not
what the model says verbatim. The deterministic graders (``tool_called``,
``tool_sequence``, ``no_tool_called``, ``contains_any``) catch routing
regressions; the ``semantic`` grader catches drift on the system-prompt
contract ("Always confirm what was downloaded and where the files were
saved.") with a fake-judge fallback so CI still works without an
``OPENAI_API_KEY`` / ``ANTHROPIC_API_KEY`` for the judge.

Run::

    agentprdiff record suites/coursenotes.py
    agentprdiff check  suites/coursenotes.py

The suite calls Groq for real; baselines reflect the model in your
``LLM_MODEL`` env var (default: ``llama-3.3-70b-versatile``). Free-tier
calls per full run: ~14–20 (avg 2–3 per case).
"""

from __future__ import annotations

# agentprdiff's loader puts the suite file's parent dir on sys.path; we also
# need the project root so `agent.agent`, `config`, and `suites.*` resolve.
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from agentprdiff import case, suite  # noqa: E402
from agentprdiff.graders import (  # noqa: E402
    contains_any,
    cost_lt_usd,
    latency_lt_ms,
    no_tool_called,
    output_length_lt,
    semantic,
    tool_called,
    tool_sequence,
)

from suites._eval_agent import coursenotes_eval_agent  # noqa: E402


coursenotes = suite(
    name="coursenotes",
    agent=coursenotes_eval_agent,
    description=(
        "Regression suite for the coursenotes-ai transcript-download agent. "
        "Pins URL→tool routing, save-location confirmation, and "
        "cost/latency budgets across model and prompt changes."
    ),
    cases=[
        # ── 1. Playlist URL must route to download_all_transcripts ────────
        case(
            name="youtube_playlist_routes_to_download_all",
            input=(
                "Download all transcripts from "
                "https://www.youtube.com/playlist?list=PLstub-eb1a-demo"
            ),
            expect=[
                tool_called("download_all_transcripts"),
                no_tool_called("download_transcript"),
                contains_any(["downloaded", "saved", "transcripts"]),
                semantic(
                    "agent confirms the playlist transcripts were downloaded "
                    "and tells the user where the files are saved"
                ),
                latency_lt_ms(30_000),
                cost_lt_usd(0.005),
            ],
        ),
        # ── 2. Single video URL must route to download_transcript ─────────
        case(
            name="single_video_routes_to_download_transcript",
            input="Get the transcript for https://www.youtube.com/watch?v=abc12345",
            expect=[
                tool_called("download_transcript"),
                no_tool_called("download_all_transcripts"),
                contains_any(["transcript", "downloaded", "saved"]),
                latency_lt_ms(30_000),
                cost_lt_usd(0.005),
            ],
        ),
        # ── 3. Metadata-only query must use get_course_info, NOT download ─
        case(
            name="metadata_query_uses_get_course_info_only",
            input=(
                "How many videos are in this playlist? "
                "https://www.youtube.com/playlist?list=PLstub-info-only"
            ),
            expect=[
                tool_called("get_course_info"),
                no_tool_called("download_all_transcripts"),
                no_tool_called("download_transcript"),
                contains_any(["3", "three", "videos", "lectures"]),
                latency_lt_ms(30_000),
                cost_lt_usd(0.005),
            ],
        ),
        # ── 4. List query must NOT redownload ─────────────────────────────
        case(
            name="list_query_doesnt_redownload",
            input="What did I already download for course 'stubbed-playlist'?",
            expect=[
                tool_called("list_downloaded_transcripts"),
                no_tool_called("download_all_transcripts"),
                no_tool_called("download_transcript"),
                latency_lt_ms(30_000),
                cost_lt_usd(0.005),
            ],
        ),
        # ── 5. Missing URL must ask, not act ──────────────────────────────
        case(
            name="missing_url_asks_for_one",
            input="Can you download my course please?",
            expect=[
                no_tool_called("download_all_transcripts"),
                no_tool_called("download_transcript"),
                contains_any(["URL", "url", "link", "address"]),
                output_length_lt(800),
                latency_lt_ms(15_000),
                cost_lt_usd(0.003),
            ],
        ),
        # ── 6. Tool-sequence pin: full happy path is one call ─────────────
        case(
            name="happy_path_tool_sequence_is_single_download",
            input=(
                "Download all transcripts from "
                "https://www.youtube.com/playlist?list=PLstub-sequence"
            ),
            expect=[
                tool_sequence(["download_all_transcripts"], strict=True),
                semantic("agent reports the download succeeded"),
                latency_lt_ms(30_000),
                cost_lt_usd(0.005),
            ],
        ),
        # ── 7. Save-location promise from the system prompt ───────────────
        case(
            name="agent_states_save_location",
            input=(
                "Download all transcripts from "
                "https://www.youtube.com/playlist?list=PLstub-savepath"
            ),
            expect=[
                tool_called("download_all_transcripts"),
                contains_any(["./output/", "output/", "vtt", "txt"]),
                semantic(
                    "agent tells the user the folder path where the .vtt or "
                    ".txt transcript files were saved"
                ),
                latency_lt_ms(30_000),
                cost_lt_usd(0.005),
            ],
        ),
    ],
)
