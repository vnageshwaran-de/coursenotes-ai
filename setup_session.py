"""
One-time Udemy session setup.
Run this once to log in and save your session:

    python3 setup_session.py

A browser window will open. Log into Udemy normally,
then press Enter in the terminal. Session is saved to
session.json (git-ignored) and reused on every future run.
"""

from playwright.sync_api import sync_playwright
import os

SESSION_FILE = "session.json"


def setup():
    print("\n🎓 coursenotes-ai — Udemy Session Setup")
    print("=" * 45)
    print("A Firefox browser window will open.")
    print("Log into Udemy, then come back here and press Enter.\n")

    with sync_playwright() as p:
        browser = p.firefox.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        page.goto("https://www.udemy.com/join/login-popup/")

        input("✅ Once logged in, press Enter to save your session...")

        context.storage_state(path=SESSION_FILE)
        browser.close()

    print(f"\n✅ Session saved to {SESSION_FILE}")
    print("You won't need to log in again unless the session expires.\n")


if __name__ == "__main__":
    setup()
