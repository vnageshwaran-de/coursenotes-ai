# agentprdiff suite for coursenotes-ai

This folder pins coursenotes-ai's agent behavior — URL→tool routing, save-location confirmation, cost/latency budgets — using [`agentprdiff`](https://github.com/vnageshwaran-de/agentprdiff). When a model upgrade, prompt change, or provider swap silently changes how the agent behaves, the suite catches it on the PR before merge.

## What it tests

Seven cases, all running the real production loop in `agent/agent.py` with two changes scoped to the suite:

1. The OpenAI-compatible client is wrapped in `agentprdiff.adapters.openai.instrument_client`, so every `chat.completions.create` invocation is recorded onto a `Trace`.
2. The four `yt-dlp`-backed tools are replaced with deterministic stubs (`suites/_stubs.py`) that return shape-compatible dicts. The LLM still makes a real routing decision, but no actual download happens, no browser cookies are needed, and no files are written.

The suite **calls the real LLM** (Groq by default, configurable via `LLM_PROVIDER` / `LLM_API_KEY` / `LLM_MODEL`). That's the whole point — we want behavioral baselines that reflect *this model on this prompt*. When you upgrade Groq's underlying Llama version, the diff against the recorded baseline tells you which cases changed and why.

## Setup

```bash
cd /path/to/coursenotes-ai
python -m venv .venv && source .venv/bin/activate

# coursenotes-ai itself
pip install -r requirements.txt

# agentprdiff (currently from local checkout — feat/sdk-adapters branch)
pip install -e ../agentprdiff

# Configure Groq key (free tier is fine — full suite costs <$0.05)
cp .env.example .env
# Edit .env: LLM_API_KEY=gsk_...
```

## Recording a baseline

Run this once on a known-good main:

```bash
agentprdiff init
agentprdiff record suites/coursenotes.py
```

The recorder produces `.agentprdiff/baselines/coursenotes/<case>.json`. Commit those files — reviewers see them in pull requests.

## Checking on every PR

```bash
agentprdiff check suites/coursenotes.py
```

Exits 0 if every case still passes its assertions and the trace doesn't regress vs the baseline. Exits 1 with a human-readable diff otherwise — assertion flips, cost/latency deltas, tool-sequence changes, and a unified diff of the agent's output.

When behavior intentionally changes, re-record:

```bash
agentprdiff record suites/coursenotes.py
git add .agentprdiff/baselines
# explain the change in your PR description
```

## CI

A GitHub Actions workflow at `.github/workflows/agentprdiff.yml` runs `check` on PRs that touch the agent or the suite. It needs `GROQ_API_KEY` (or `LLM_API_KEY`) as a repository secret because the suite hits Groq for real.

If you want an offline-only PR check (no API calls), swap `_eval_agent.py`'s `get_client()` for a stub LLM client. The fake-LLM mode is on the roadmap as a `suites/coursenotes_offline.py` companion suite.

## Why these specific cases

| # | Case | What it pins |
|---|------|--------------|
| 1 | `youtube_playlist_routes_to_download_all` | Playlist URLs go to `download_all_transcripts` and not `download_transcript` |
| 2 | `single_video_routes_to_download_transcript` | Single-video URLs go to `download_transcript` and not `download_all_transcripts` |
| 3 | `metadata_query_uses_get_course_info_only` | "How many videos" doesn't trigger downloads |
| 4 | `list_query_doesnt_redownload` | "What did I already download" calls `list_downloaded_transcripts` only |
| 5 | `missing_url_asks_for_one` | Underspecified requests are met with a clarifying question, not action |
| 6 | `happy_path_tool_sequence_is_single_download` | Strict tool-sequence: the happy path is exactly one tool call |
| 7 | `agent_states_save_location` | The system prompt's "always confirm where files were saved" promise holds |

Each download case has a `cost_lt_usd(0.005)` and `latency_lt_ms(30000)` budget so a degenerate retry loop or a much pricier model is caught. Adjust the budgets to your own tolerances.
