"""
Udemy transcript downloader using Playwright + Udemy internal API.
Uses a saved browser session (session.json) — no passwords in code.

Run setup_session.py once before using this module.
"""

import os
import re
import json
import requests
from playwright.sync_api import sync_playwright
from tools.vtt_to_text import convert_all_vtt_in_folder
from config import OUTPUT_DIR

SESSION_FILE = "session.json"


def _check_session():
    if not os.path.exists(SESSION_FILE):
        raise FileNotFoundError(
            "session.json not found. Run 'python3 setup_session.py' first to log in."
        )


def _get_course_slug(course_url: str) -> str:
    m = re.search(r"udemy\.com/course/([^/?#]+)", course_url)
    if not m:
        raise ValueError(f"Could not extract course slug from URL: {course_url}")
    return m.group(1).strip("/")


def get_udemy_course_info(course_url: str) -> dict:
    """Fetch course title and lecture list via Udemy internal API."""
    _check_session()
    course_slug = _get_course_slug(course_url)

    with sync_playwright() as p:
        browser = p.firefox.launch(headless=True)
        context = browser.new_context(storage_state=SESSION_FILE)
        page = context.new_page()

        # Get course ID and title
        resp = page.request.get(
            f"https://www.udemy.com/api-2.0/courses/{course_slug}/"
            f"?fields[course]=id,title,num_lectures"
        )
        if resp.status != 200:
            browser.close()
            return {"error": f"HTTP {resp.status} fetching course info"}

        course_data = resp.json()
        course_id   = course_data["id"]
        course_title = course_data.get("title", course_slug)

        # Get full curriculum
        resp = page.request.get(
            f"https://www.udemy.com/api-2.0/courses/{course_id}/subscriber-curriculum-items/"
            f"?page_size=1400"
            f"&fields[lecture]=id,title,asset"
            f"&fields[asset]=id,asset_type,captions"
        )
        curriculum = resp.json()
        browser.close()

    lectures = [
        {
            "id":       item["id"],
            "title":    item.get("title", ""),
            "asset_id": item.get("asset", {}).get("id"),
        }
        for item in curriculum.get("results", [])
        if item.get("_class") == "lecture" and item.get("asset", {}).get("asset_type") == "Video"
    ]

    return {
        "course_id":    course_id,
        "course_title": course_title,
        "num_lectures": len(lectures),
        "lectures":     lectures,
    }


def download_udemy_transcripts(course_url: str, course_name: str = None) -> dict:
    """
    Download all transcripts for a Udemy course via internal API.
    Saves .vtt to output/<course_name>/vtt/
    Converts to clean .txt in output/<course_name>/txt/
    """
    _check_session()
    course_slug = _get_course_slug(course_url)
    course_name = course_name or course_slug

    vtt_folder = os.path.join(OUTPUT_DIR, course_name, "vtt")
    txt_folder = os.path.join(OUTPUT_DIR, course_name, "txt")
    os.makedirs(vtt_folder, exist_ok=True)

    with sync_playwright() as p:
        browser = p.firefox.launch(headless=True)
        context = browser.new_context(storage_state=SESSION_FILE)
        page    = context.new_page()

        # Get course ID
        resp = page.request.get(
            f"https://www.udemy.com/api-2.0/courses/{course_slug}/?fields[course]=id,title"
        )
        if resp.status != 200:
            browser.close()
            return {"success": False, "error": f"HTTP {resp.status} — session may have expired. Re-run setup_session.py"}

        course_data  = resp.json()
        course_id    = course_data["id"]
        course_title = course_data.get("title", course_slug)

        # Get curriculum
        resp = page.request.get(
            f"https://www.udemy.com/api-2.0/courses/{course_id}/subscriber-curriculum-items/"
            f"?page_size=1400"
            f"&fields[lecture]=id,title,asset"
            f"&fields[asset]=id,asset_type,captions"
        )
        curriculum = resp.json()

        lectures = [
            item for item in curriculum.get("results", [])
            if item.get("_class") == "lecture"
            and item.get("asset", {}).get("asset_type") == "Video"
        ]

        downloaded = []
        skipped    = []

        for idx, lecture in enumerate(lectures, start=1):
            title    = lecture.get("title", f"lecture-{idx}")
            asset    = lecture.get("asset", {})
            captions = asset.get("captions", [])

            # Pick English caption
            en_caption = next(
                (c for c in captions if c.get("locale_id", "").startswith("en")),
                captions[0] if captions else None
            )

            if not en_caption:
                skipped.append(title)
                continue

            caption_url = en_caption.get("url")
            if not caption_url:
                skipped.append(title)
                continue

            # Download the VTT file
            safe_title = re.sub(r"[^\w\s\-]", "", title).strip()
            vtt_filename = f"{idx:03d} - {safe_title}.vtt"
            vtt_path = os.path.join(vtt_folder, vtt_filename)

            vtt_resp = page.request.get(caption_url)
            if vtt_resp.status == 200:
                with open(vtt_path, "w", encoding="utf-8") as f:
                    f.write(vtt_resp.text())
                downloaded.append(vtt_filename)
            else:
                skipped.append(title)

        browser.close()

    # Convert all VTT to clean TXT
    txt_files = convert_all_vtt_in_folder(vtt_folder, txt_folder)

    return {
        "success":          True,
        "course_title":     course_title,
        "vtt_folder":       vtt_folder,
        "txt_folder":       txt_folder,
        "downloaded":       len(downloaded),
        "skipped":          len(skipped),
        "txt_files_created": len(txt_files),
        "txt_files":        txt_files,
    }
