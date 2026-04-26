import subprocess
import json
import os
from config import OUTPUT_DIR, COOKIE_BROWSER, UDEMY_USERNAME, UDEMY_PASSWORD


def get_course_info(course_url: str) -> dict:
    """Fetch course metadata and lecture list using yt-dlp."""
    cmd = [
        "yt-dlp",
        "--cookies-from-browser", COOKIE_BROWSER,
        "--dump-single-json",
        "--flat-playlist",
        course_url
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return {"error": result.stderr}
    return json.loads(result.stdout)


def download_transcript(lecture_url: str, output_path: str) -> dict:
    """Download subtitles/transcript for a single lecture."""
    os.makedirs(output_path, exist_ok=True)
    cmd = [
        "yt-dlp",
        "--cookies-from-browser", COOKIE_BROWSER,
        "--write-auto-sub",
        "--write-sub",
        "--sub-lang", "en",
        "--sub-format", "vtt",
        "--skip-download",
        "--output", f"{output_path}/%(title)s.%(ext)s",
        lecture_url
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return {
        "success": result.returncode == 0,
        "stdout": result.stdout,
        "stderr": result.stderr
    }


def download_all_transcripts(course_url: str, course_name: str) -> dict:
    """Download transcripts for all lectures in a course."""
    output_path = os.path.join(OUTPUT_DIR, course_name)
    os.makedirs(output_path, exist_ok=True)
    cmd = [
        "yt-dlp",
        "--cookies-from-browser", COOKIE_BROWSER,
        "--write-auto-sub",
        "--write-sub",
        "--sub-lang", "en",
        "--sub-format", "vtt",
        "--skip-download",
        "--output", f"{output_path}/%(playlist_index)s - %(title)s.%(ext)s",
        course_url
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return {
        "success": result.returncode == 0,
        "output_path": output_path,
        "stdout": result.stdout,
        "stderr": result.stderr
    }


def list_downloaded_transcripts(course_name: str) -> list:
    """List all transcript files downloaded for a course."""
    path = os.path.join(OUTPUT_DIR, course_name)
    if not os.path.exists(path):
        return []
    return [f for f in os.listdir(path) if f.endswith(".vtt") or f.endswith(".srt")]
