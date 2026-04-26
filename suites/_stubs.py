"""Deterministic stand-ins for the four yt-dlp-backed tools.

The real `tools/ytdlp_tools.py` functions shell out to `yt-dlp`, which
requires network, browser cookies, and writes files to disk. None of that is
desirable in a CI regression suite — we want the *agent's routing decisions*
to be the variable, not the upstream YouTube state.

Each stub returns a shape-compatible dict so the agent's response-handling
logic is exercised normally. The LLM sees the stub output via the
``role="tool"`` message and produces its final response from there.
"""

from __future__ import annotations

from typing import Any


def stub_get_course_info(course_url: str) -> dict[str, Any]:
    """Mimics yt-dlp's --dump-single-json --flat-playlist output."""
    return {
        "_type": "playlist",
        "id": "PLstub",
        "title": "Stubbed Playlist",
        "entries": [
            {"id": "vid_001", "title": "01 - Introduction"},
            {"id": "vid_002", "title": "02 - Getting Started"},
            {"id": "vid_003", "title": "03 - Advanced Topics"},
        ],
    }


def stub_download_all_transcripts(
    course_url: str, course_name: str | None = None
) -> dict[str, Any]:
    """Mimics a successful playlist transcript download."""
    name = course_name or "stubbed-playlist"
    return {
        "success": True,
        "course_name": name,
        "vtt_folder": f"./output/{name}/vtt",
        "txt_folder": f"./output/{name}/txt",
        "txt_files_created": 3,
        "txt_files": [
            "1 - Introduction.txt",
            "2 - Getting Started.txt",
            "3 - Advanced Topics.txt",
        ],
        "stdout": "[stub] downloaded 3/3",
        "stderr": "",
    }


def stub_download_transcript(
    lecture_url: str, course_name: str | None = None
) -> dict[str, Any]:
    """Mimics a successful single-video transcript download."""
    name = course_name or "stubbed-video"
    return {
        "success": True,
        "course_name": name,
        "vtt_folder": f"./output/{name}/vtt",
        "txt_folder": f"./output/{name}/txt",
        "txt_files_created": 1,
        "txt_files": ["Stubbed Lecture Title.txt"],
        "stdout": "[stub] downloaded 1/1",
        "stderr": "",
    }


def stub_list_downloaded_transcripts(course_name: str) -> list[str]:
    """Mimics tools.ytdlp_tools.list_downloaded_transcripts."""
    if "missing" in (course_name or "").lower():
        return []
    return [
        "1 - Introduction.txt",
        "2 - Getting Started.txt",
        "3 - Advanced Topics.txt",
    ]


# Same keys as ``agent.agent.TOOL_MAP`` so swapping is one assignment.
STUB_TOOL_MAP = {
    "get_course_info": stub_get_course_info,
    "download_all_transcripts": stub_download_all_transcripts,
    "download_transcript": stub_download_transcript,
    "list_downloaded_transcripts": stub_list_downloaded_transcripts,
}
