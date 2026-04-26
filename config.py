import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = "gemini-2.0-flash"

OUTPUT_DIR = os.getenv("OUTPUT_DIR", "./output")
COOKIE_BROWSER = os.getenv("COOKIE_BROWSER", "chrome")

UDEMY_USERNAME = os.getenv("UDEMY_USERNAME")
UDEMY_PASSWORD = os.getenv("UDEMY_PASSWORD")
