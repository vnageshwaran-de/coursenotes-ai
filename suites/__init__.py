"""agentprdiff regression suites for coursenotes-ai.

The suite hits a real LLM provider (Groq by default) so the recorded baselines
capture actual model routing decisions. The yt-dlp side-effecting tools are
replaced with deterministic stubs so the suite is repeatable, doesn't touch
YouTube, and doesn't litter the filesystem.

Run::

    cd coursenotes-ai
    source .venv/bin/activate
    pip install -e ../agentprdiff       # if not already installed
    agentprdiff init
    agentprdiff record suites/coursenotes.py     # first time
    agentprdiff check  suites/coursenotes.py     # in CI; exit 1 on regression

Costs a handful of free-tier Groq calls per run.
"""
