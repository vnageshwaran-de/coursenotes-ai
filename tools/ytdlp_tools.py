import subprocess
import json
import os
import re
from config import OUTPUT_DIR, COOKIE_BROWSER, UDEMY_USERNAME, UDEMY_PASSWORD
from tools.vtt_to_text import convert_vtt_to_txt, convert_all_vtt_in_folder


def is_udemy_url(url: str) -> bool:
    return "udemy.com" in url


def slugify(text: str, max_length: int = 60) -> str:
    """Convert a title into a clean folder-safe slug."""
    text = text.strip()
    # Replace special characters and spaces with hyphens
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


def clean_udemy_url(url: str) -> str:
    """
    Strip lecture-specific parts from a Udemy URL.
    e.g. https://www.udemy.com/course/nvidia-nca-genl/learn/lecture/54150585#overview
      -> https://www.udemy.com/course/nvidia-nca-genl/
    """
    m = re.search(r"(https://www\.udemy\.com/course/[^/?#]+/)", url)
    if m:
        return m.group(1)
    return url


def extract_course_name(course_url: str) -> str:
    """
    Derive a meaningful folder name from the URL.
    For Udemy: uses the course slug from the URL.
    For YouTube: fetches the actual video/playlist title via yt-dlp.
    Falls back to sanitized URL if title fetch fails.
    """
    # Udemy — slug is already meaningful
    m = re.search(r"udemy\.com/course/([^/?#]+)", course_url)
    if m:
        return m.group(1).strip("/")

    # YouTube — fetch real title
    if "youtube.com" in course_url or "youtu.be" in course_url:
        title = fetch_title(course_url)
        if title:
            return slugify(title)

    # Fallback: sanitize URL into a safe string
    return re.sub(r"[^\w\-]", "_", course_url)[-50:]


def get_course_info(course_url: str) -> dict:
    """Fetch course metadata and lecture list."""
    if is_udemy_url(course_url):
        from tools.udemy_playwright import get_udemy_course_info
        return get_udemy_course_info(clean_udemy_url(course_url))

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
    Download subtitle for a single lecture.
    Saves .vtt to output/<course_name>/vtt/
    Converts and saves .txt to output/<course_name>/txt/
    course_name is auto-derived from the URL if not provided.
    """
    lecture_url = clean_udemy_url(lecture_url)
    course_name = course_name or extract_course_name(lecture_url)

    if is_udemy_url(lecture_url):
        from tools.udemy_playwright import download_udemy_transcripts
        return download_udemy_transcripts(lecture_url, course_name)
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
    Download transcripts for all lectures in a course.
    Saves .vtt files to output/<course_name>/vtt/
    Converts and saves clean .txt files to output/<course_name>/txt/
    course_name is auto-derived from the URL if not provided.
    """
    course_url = clean_udemy_url(course_url)
    course_name = course_name or extract_course_name(course_url)

    if is_udemy_url(course_url):
        from tools.udemy_playwright import download_udemy_transcripts
        return download_udemy_transcripts(course_url, course_name)
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
