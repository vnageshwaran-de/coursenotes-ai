import subprocess
import json
import os
import re
from config import OUTPUT_DIR, COOKIE_BROWSER
from tools.vtt_to_text import convert_vtt_to_txt, convert_all_vtt_in_folder


def slugify(text: str, max_length: int = 60) -> str:
    """Convert a title into a clean folder-safe slug."""
    text = text.strip()
    text = re.sub(r"[^\w\s\-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text[:max_length].strip("-")


def fetch_title(url: str) -> str | None:
    """Fetch the video/playlist title from yt-dlp without downloading."""
    cmd = [
        "yt-dlp",
        "--cookies-from-browser", COOKIE_BROWSER,
        "--print", "%(title)s",
        "--flat-playlist",
        "--playlist-items", "1",
        url
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0 and result.stdout.strip():
        return result.stdout.strip().splitlines()[0]
    return None


def extract_course_name(url: str) -> str:
    """
    Derive a meaningful folder name from a YouTube URL.
    Fetches the actual video/playlist title via yt-dlp.
    Falls back to sanitized URL if title fetch fails.
    """
    if "youtube.com" in url or "youtu.be" in url:
        title = fetch_title(url)
        if title:
            return slugify(title)

    # Fallback: sanitize URL into a safe string
    return re.sub(r"[^\w\-]", "_", url)[-50:]


def get_course_info(course_url: str) -> dict:
    """Fetch video/playlist metadata and lecture list using yt-dlp."""
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


def download_transcript(lecture_url: str, course_name: str = None) -> dict:
    """
    Download subtitle for a single YouTube video.
    Saves .vtt to output/<course_name>/vtt/
    Converts and saves .txt to output/<course_name>/txt/
    course_name is auto-derived from the video title if not provided.
    """
    course_name = course_name or extract_course_name(lecture_url)
    vtt_folder = os.path.join(OUTPUT_DIR, course_name, "vtt")
    txt_folder = os.path.join(OUTPUT_DIR, course_name, "txt")
    os.makedirs(vtt_folder, exist_ok=True)

    cmd = [
        "yt-dlp",
        "--cookies-from-browser", COOKIE_BROWSER,
        "--write-auto-sub",
        "--write-sub",
        "--sub-lang", "en",
        "--sub-format", "vtt",
        "--skip-download",
        "--output", f"{vtt_folder}/%(title)s.%(ext)s",
        lecture_url
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)

    txt_files = []
    if result.returncode == 0:
        for filename in sorted(os.listdir(vtt_folder)):
            if filename.endswith(".vtt"):
                vtt_path = os.path.join(vtt_folder, filename)
                txt_path = convert_vtt_to_txt(vtt_path, txt_folder)
                txt_files.append(txt_path)

    return {
        "success": result.returncode == 0,
        "vtt_folder": vtt_folder,
        "txt_folder": txt_folder,
        "txt_files": txt_files,
        "stdout": result.stdout,
        "stderr": result.stderr
    }


def download_all_transcripts(course_url: str, course_name: str = None) -> dict:
    """
    Download transcripts for all videos in a YouTube playlist.
    Saves .vtt files to output/<course_name>/vtt/
    Converts and saves clean .txt files to output/<course_name>/txt/
    course_name is auto-derived from the playlist title if not provided.
    """
    course_name = course_name or extract_course_name(course_url)
    vtt_folder = os.path.join(OUTPUT_DIR, course_name, "vtt")
    txt_folder = os.path.join(OUTPUT_DIR, course_name, "txt")
    os.makedirs(vtt_folder, exist_ok=True)

    cmd = [
        "yt-dlp",
        "--cookies-from-browser", COOKIE_BROWSER,
        "--write-auto-sub",
        "--write-sub",
        "--sub-lang", "en",
        "--sub-format", "vtt",
        "--skip-download",
        "--output", f"{vtt_folder}/%(playlist_index)s - %(title)s.%(ext)s",
        course_url
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)

    txt_files = []
    if result.returncode == 0:
        txt_files = convert_all_vtt_in_folder(vtt_folder, txt_folder)

    return {
        "success": result.returncode == 0,
        "vtt_folder": vtt_folder,
        "txt_folder": txt_folder,
        "txt_files_created": len(txt_files),
        "txt_files": txt_files,
        "stdout": result.stdout,
        "stderr": result.stderr
    }


def list_downloaded_transcripts(course_name: str) -> list:
    """List all clean .txt transcript files for a course."""
    txt_folder = os.path.join(OUTPUT_DIR, course_name, "txt")
    if not os.path.exists(txt_folder):
        return []
    return sorted([f for f in os.listdir(txt_folder) if f.endswith(".txt")])
