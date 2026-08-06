"""Open a signed-in Azure portal window and capture pages from it.

The Azure portal cannot be reached headlessly - it needs an interactive
Microsoft sign-in. So this opens a VISIBLE Edge window on a dedicated profile
for the user to authenticate themselves (the script never handles credentials),
then drives capture from a background tab so the sign-in window is never
disturbed.

Run directly to do the sign-in and capture the "before provisioning" pages;
import `attach()` from later scripts to reuse the same authenticated session.
"""
import json
import os
import subprocess
import sys
import time

import requests
from websockets.sync.client import connect

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from cdp import Browser, EDGE

SHOTS = r"C:\Users\lokes\jenkins-lab\screenshots-lab2"
PORT = 9224
PROFILE = r"C:\Users\lokes\jenkins-lab\edge-azure-profile"
PORTAL = "https://portal.azure.com/#home"
WAIT_MINUTES = 15


def browser_ws(port):
    return requests.get(f"http://127.0.0.1:{port}/json/version",
                        timeout=5).json()["webSocketDebuggerUrl"]


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


def launch():
    """Opens the visible sign-in window if the profile is not already running."""
    try:
        requests.get(f"http://127.0.0.1:{PORT}/json/version", timeout=2)
        return False                     # already up, reuse it
    except Exception:
        pass
    subprocess.Popen([
        EDGE, f"--remote-debugging-port={PORT}", f"--user-data-dir={PROFILE}",
        "--window-size=1600,1000", "--no-first-run", "--no-default-browser-check",
        PORTAL,
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(60):
        try:
            requests.get(f"http://127.0.0.1:{PORT}/json/version", timeout=2)
            return True
        except Exception:
            time.sleep(0.5)
    raise RuntimeError("Edge did not expose a DevTools endpoint")


def goto_soft(b, url, wait_ms=6000):
    """Navigate without insisting on readyState=complete.

    The portal is a single-page app that keeps long-poll connections open, so
    it can sit at readyState 'interactive' indefinitely. Waiting for 'complete'
    is the wrong signal here - what matters is whether the DOM we want exists.
    """
    try:
        b.goto(url, wait_ms=wait_ms)
    except TimeoutError:
        time.sleep(wait_ms / 1000)


def signed_in(b):
    """The portal keeps us on portal.azure.com only once authentication holds."""
    url = b.eval("location.href") or ""
    if "portal.azure.com" not in url:
        return False
    return bool(b.eval(
        "!!document.querySelector('#mectrl_headerPicture, "
        "[data-testid=\"user-menu\"], .fxs-avatarmenu-tenant, #fxs-avatarmenu-button')"))


def attach(wait=True):
    """Returns a Browser bound to a background tab of the signed-in window."""
    launch()
    b = Browser(attach=True, port=PORT, ws_url=make_background_tab(PORT))
    if not wait:
        return b
    deadline = time.time() + WAIT_MINUTES * 60
    while time.time() < deadline:
        goto_soft(b, PORTAL)
        if signed_in(b):
            time.sleep(5)            # let the dashboard tiles settle
            return b
        time.sleep(10)
    b.close(keep_browser=True)
    raise TimeoutError("portal sign-in did not complete")


def capture(b, url, name, label, wait_ms=12000, scroll_top=True):
    goto_soft(b, url, wait_ms)
    if scroll_top:
        b.eval("window.scrollTo(0,0); 1")
        time.sleep(1.5)
    print(f"[{name[:2]}] {label}", flush=True)
    return b.shot(os.path.join(SHOTS, name), full_page=False)


if __name__ == "__main__":
    fresh = launch()
    if fresh:
        print("=" * 70)
        print(" An Edge window has opened at the Azure portal.")
        print(" Sign in there yourself with lokeshselvam7025@gmail.com.")
        print(" This script never sees your credentials.")
        print(f" It will keep checking for up to {WAIT_MINUTES} minutes.")
        print("=" * 70, flush=True)

    b = attach()
    print("signed in - portal reachable", flush=True)
    try:
        capture(b, PORTAL,
                "01-azure-portal-home.png",
                "Azure portal home, signed in as the lab account")
        capture(b, "https://portal.azure.com/#view/Microsoft_Azure_Billing/"
                   "SubscriptionsBladeV2",
                "02-azure-subscription.png",
                "The active subscription the lab bills against")
    finally:
        b.close(keep_browser=True)
