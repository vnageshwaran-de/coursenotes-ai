import re
import os


def slugify(text: str, max_length: int = 60) -> str:
    """Convert a title into a clean file-safe slug."""
    text = text.strip()
    text = re.sub(r"[^\w\s\-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text[:max_length].strip("-")


def vtt_to_clean_text(vtt_path: str) -> str:
    """
    Convert a .vtt subtitle file to clean, readable plain text.
    - Strips timestamps, cue identifiers, and WebVTT tags
    - Removes duplicate lines (common in auto-generated captions)
    - Returns a single clean string
    """
    with open(vtt_path, "r", encoding="utf-8") as f:
        content = f.read()

    lines = content.splitlines()
    clean_lines = []
    seen = set()
    last_line = None

    for line in lines:
        # Skip WebVTT header
        if line.strip().startswith("WEBVTT"):
            continue
        # Skip blank lines
        if not line.strip():
            continue
        # Skip timestamp lines (e.g. 00:00:01.000 --> 00:00:03.000)
        if re.match(r"^\d{2}:\d{2}:\d{2}[\.,]\d{3}\s*-->\s*\d{2}:\d{2}:\d{2}[\.,]\d{3}", line):
            continue
        # Skip cue identifier lines (pure numbers)
        if re.match(r"^\d+$", line.strip()):
            continue
        # Strip inline HTML/VTT tags like <c>, <i>, <b>, <00:00:01.000>
        line = re.sub(r"<[^>]+>", "", line)
        line = line.strip()

        if not line:
            continue
        # Always skip consecutive identical lines (auto-caption artifact)
        if line == last_line:
            continue
        # Skip if already seen in current window
        if line not in seen:
            clean_lines.append(line)
            seen.add(line)
            last_line = line
        # Reset seen window at sentence endings to allow phrases to recur naturally
        if line.endswith((".", "!", "?")):
            seen.clear()

    return "\n".join(clean_lines)


def convert_vtt_to_txt(vtt_path: str, txt_folder: str) -> str:
    """
    Convert a single .vtt file to a clean .txt file saved in txt_folder.
    Returns the path of the saved .txt file.
    """
    os.makedirs(txt_folder, exist_ok=True)
    # Strip language suffix e.g. "My Video.en.vtt" -> "My Video"
    raw_name = re.sub(r"\.[a-z]{2,5}$", "", os.path.splitext(os.path.basename(vtt_path))[0])
    base_name = slugify(raw_name) + ".txt"
    txt_path = os.path.join(txt_folder, base_name)
    clean_text = vtt_to_clean_text(vtt_path)
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(clean_text)
    return txt_path


def convert_all_vtt_in_folder(vtt_folder: str, txt_folder: str) -> list:
    """
    Convert all .vtt files in vtt_folder to clean .txt files saved in txt_folder.
    Returns a list of created .txt file paths.
    """
    if not os.path.exists(vtt_folder):
        return []

    os.makedirs(txt_folder, exist_ok=True)
    converted = []
    for filename in sorted(os.listdir(vtt_folder)):
        if filename.endswith(".vtt"):
            vtt_path = os.path.join(vtt_folder, filename)
            txt_path = convert_vtt_to_txt(vtt_path, txt_folder)
            converted.append(txt_path)

    return converted
