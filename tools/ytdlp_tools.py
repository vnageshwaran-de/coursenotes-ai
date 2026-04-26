import subprocess
import json
import os
import re
from config import OUTPUT_DIR, COOKIE_BROWSER, UDEMY_USERNAME, UDEMY_PASSWORD
from tools.vtt_to_text import convert_vtt_to_txt, convert_all_vtt_in_folder


def extract_course_name(course_url: str) -> str:
    """
    Auto-derive a folder-safe course name from a supported URL.

    Supported patterns:
      Udemy:    https://www.udemy.com/course/python-bootcamp/     -> python-bootcamp
      YouTube playlist: https://youtube.com/playlist?list=PLxxx  -> playlist-PLxxx
      YouTube video:    https://youtube.com/watch?v=abc123        -> video-abc123
      YouTube channel:  https://youtube.com/@channelname          -> channelname
      Fallback: sanitized URL slug
    """
    # Udemy
    m = re.search(r"udemy\.com/course/([^/?#]+)", course_url)
    if m:
        return m.group(1).strip("/")

    # YouTube playlist
    m = re.search(r"[?&]list=([^&]+)", course_url)
    if m and "youtube.com" in course_url:
        return f"playlist-{m.group(1)}"

    # YouTube video
    m = re.search(r"[?&]v=([^&]+)", course_url)
    if m and "youtube.com" in course_url:
        return f"video-{m.group(1)}"

    # YouTube short URL (youtu.be/ID)
    m = re.search(r"youtu\.be/([^/?#]+)", course_url)
    if m:
        return f"video-{m.group(1)}"

    # YouTube channel handle (@name)
    m = re.search(r"youtube\.com/@([^/?#]+)", course_url)
    if m:
        return m.group(1)

    # Fallback: sanitize URL into a safe string
    return re.sub(r"[^\w\-]", "_", course_url)[-50:]


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


def download_transcript(lecture_url: str, course_name: str = None) -> dict:
    """
    Download subtitle for a single lecture.
    Saves .vtt to output/<course_name>/vtt/
    Converts and saves .txt to output/<course_name>/txt/
    course_name is auto-derived from the URL if not provided.
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
    Download transcripts for all lectures in a course.
    Saves .vtt files to output/<course_name>/vtt/
    Converts and saves clean .txt files to output/<course_name>/txt/
    course_name is auto-derived from the URL if not provided.
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
