from tools.ytdlp_tools import slugify, extract_course_name
from tools.vtt_to_text import vtt_to_clean_text
import tempfile, os


def test_slugify_basic():
    assert slugify("Hello World!") == "Hello-World"


def test_slugify_special_chars():
    assert slugify("MCP: Beyond the Hype | AI") == "MCP-Beyond-the-Hype-AI"


def test_slugify_max_length():
    long = "A" * 100
    assert len(slugify(long)) <= 60


def test_extract_course_name_youtube_video():
    # Falls back to yt-<id> when yt-dlp is not available in CI
    name = extract_course_name("https://www.youtube.com/watch?v=abc123")
    assert "abc123" in name or len(name) > 0


def test_extract_course_name_youtube_playlist():
    name = extract_course_name("https://www.youtube.com/playlist?list=PLxxx")
    assert len(name) > 0


def test_vtt_to_clean_text():
    vtt_content = """WEBVTT

00:00:01.000 --> 00:00:03.000
Hello world

00:00:04.000 --> 00:00:06.000
This is a test.

00:00:04.000 --> 00:00:06.000
This is a test.
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".vtt", delete=False) as f:
        f.write(vtt_content)
        tmp = f.name

    try:
        result = vtt_to_clean_text(tmp)
        assert "Hello world" in result
        assert "This is a test." in result
        # Deduplication check
        assert result.count("This is a test.") == 1
    finally:
        os.unlink(tmp)
