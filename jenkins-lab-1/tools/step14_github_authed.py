"""Phase 6 - capture the GitHub side of the lab from a signed-in browser.

Lokesh7025/devops is private, so a signed-out browser gets "Page not found".
This opens a VISIBLE Edge window at the GitHub sign-in page for the user to
authenticate themselves - the script never handles the credentials - then polls
from a separate background tab until the repository becomes reachable and
captures the pages.
"""
import json
import os
import subprocess
import sys
import time

import requests
from websockets.sync.client import connect

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cdp import Browser, EDGE

SHOTS = r"C:\Users\lokes\jenkins-lab\screenshots"
PORT = 9223
PROFILE = r"C:\Users\lokes\jenkins-lab\edge-github-profile"
REPO = "https://github.com/Lokesh7025/devops"
WAIT_MINUTES = 15

PAGES = [
    (REPO,                                             "28-github-repo-main.png",
     "Repository on GitHub (branch main)"),
    (f"{REPO}/blob/main/pom.xml",                      "29-github-maven-pom.png",
     "The Maven project descriptor - pom.xml"),
    (f"{REPO}/tree/jenkins-lab-1/jenkins-lab-1",       "30-github-lab-branch.png",
     "The jenkins-lab-1 branch holding this lab report"),
]


def browser_ws(port):
    return requests.get(f"http://127.0.0.1:{port}/json/version", timeout=5).json()["webSocketDebuggerUrl"]


def make_background_tab(port):
    """Creates a tab that does not steal focus from the sign-in window."""
    ws = connect(browser_ws(port), open_timeout=20)
    ws.send(json.dumps({"id": 1, "method": "Target.createTarget",
                        "params": {"url": "about:blank", "background": True}}))
    tid = None
    for _ in range(20):
        msg = json.loads(ws.recv(timeout=10))
        if msg.get("id") == 1:
            tid = msg["result"]["targetId"]
            break
    ws.close()
    for t in requests.get(f"http://127.0.0.1:{port}/json/list", timeout=5).json():
        if t.get("id") == tid:
            return t["webSocketDebuggerUrl"]
    raise RuntimeError("could not find the background tab")


# -- 1. open a visible window on the GitHub sign-in page ---------------------
subprocess.Popen([
    EDGE, f"--remote-debugging-port={PORT}", f"--user-data-dir={PROFILE}",
    "--window-size=1500,1000", "--no-first-run", "--no-default-browser-check",
    "https://github.com/login",
], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

for _ in range(60):
    try:
        requests.get(f"http://127.0.0.1:{PORT}/json/version", timeout=2)
        break
    except Exception:
        time.sleep(0.5)

print("=" * 68)
print(" An Edge window has opened at the GitHub sign-in page.")
print(" Sign in there yourself. This script never sees your credentials.")
print(f" It will keep checking for up to {WAIT_MINUTES} minutes, then capture.")
print("=" * 68, flush=True)

# -- 2. poll from a background tab until the private repo resolves -----------
b = Browser(attach=True, port=PORT, ws_url=make_background_tab(PORT))
try:
    deadline = time.time() + WAIT_MINUTES * 60
    ready = False
    while time.time() < deadline:
        b.goto(REPO, wait_ms=1500)
        title = b.eval("document.title") or ""
        if "Page not found" not in title and "Sign in" not in title:
            ready = True
            print(f"signed in - repo reachable ({title})", flush=True)
            break
        time.sleep(10)

    if not ready:
        print("TIMED OUT - still not signed in, nothing captured.", flush=True)
        sys.exit(2)

    # -- 3. capture ----------------------------------------------------------
    for url, name, label in PAGES:
        b.goto(url, wait_ms=4500)
        b.eval("window.scrollTo(0,0); 1")
        time.sleep(2)
        title = b.eval("document.title")
        print(f"[{name[:2]}] {label}\n     {title}", flush=True)
        if "Page not found" in (title or ""):
            print("     !! still 404 - skipping", flush=True)
            continue
        b.shot(os.path.join(SHOTS, name), full_page=True, max_height=2800)
finally:
    b.close(keep_browser=True)
