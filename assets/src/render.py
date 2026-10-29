"""Render every brand asset in assets/src to PNG with headless Chrome.  Run from the repo root: python assets/src/render.py"""
import pathlib
from playwright.sync_api import sync_playwright

SRC = pathlib.Path(__file__).resolve().parent
OUT = SRC.parent
CHROME = "C:/Program Files/Google/Chrome/Application/chrome.exe"
JOBS = [  # (page, output, width, height, transparent)
    ("logo.html", "liensight-logo.png", 1600, 420, True),
    ("thumbnail.html", "youtube-thumbnail.png", 1280, 720, False),
    ("poster.html", "poster-hero.png", 1920, 1080, False),
    ("workflow.html", "poster-workflow-stack.png", 1920, 1080, False),
]

with sync_playwright() as p:
    b = p.chromium.launch(executable_path=CHROME, args=["--allow-file-access-from-files"])
    for page, out, w, h, clear in JOBS:
        pg = b.new_page(viewport={"width": w, "height": h}, device_scale_factor=1)
        pg.goto((SRC / page).as_uri())
        pg.evaluate("document.fonts.ready")
        pg.wait_for_timeout(300)
        pg.screenshot(path=str(OUT / out), omit_background=clear)
        print("wrote", out)
    # the mark on its own, for avatars and favicons
    pg = b.new_page(viewport={"width": 512, "height": 512})
    pg.goto((OUT / "liensight-mark.svg").as_uri())
    pg.screenshot(path=str(OUT / "liensight-mark.png"), omit_background=True)
    print("wrote liensight-mark.png")
    b.close()
