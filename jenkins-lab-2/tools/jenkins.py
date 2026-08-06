"""Shared helper: get a CDP handle on a signed-in Jenkins session.

Restarting the controller invalidates the old session cookie, and this lab
never stores the admin password anywhere. So when the browser lands on the
sign-in page we hand control back to the user: a visible Edge window opens on
the Jenkins login form, they authenticate, and the scripts carry on against the
same profile. Nothing here reads or writes a credential.
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

JENKINS = "http://localhost:8080"
PORT = 9222
PROFILE = r"C:\Users\lokes\jenkins-lab\edge-cdp-profile"
SHOTS = r"C:\Users\lokes\jenkins-lab\screenshots-lab2"
WAIT_MINUTES = 15


def _alive(port):
    try:
        requests.get(f"http://127.0.0.1:{port}/json/version", timeout=2)
        return True
    except Exception:
        return False


def _close_browser(port):
    """Shuts the instance down through CDP so the profile lock is released.

    Killing msedge.exe by name is not an option - a different Edge window on a
    different profile is holding the user's Azure portal session.
    """
    if not _alive(port):
        return
    try:
        url = requests.get(f"http://127.0.0.1:{port}/json/version",
                           timeout=5).json()["webSocketDebuggerUrl"]
        ws = connect(url, open_timeout=10)
        ws.send(json.dumps({"id": 1, "method": "Browser.close"}))
        time.sleep(1)
        ws.close()
    except Exception:
        pass
    for _ in range(30):
        if not _alive(port):
            return
        time.sleep(0.5)


def _launch_visible(url):
    subprocess.Popen([
        EDGE, f"--remote-debugging-port={PORT}", f"--user-data-dir={PROFILE}",
        "--window-size=1600,1000", "--no-first-run", "--no-default-browser-check",
        url,
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(60):
        if _alive(PORT):
            return
        time.sleep(0.5)
    raise RuntimeError("Edge did not expose a DevTools endpoint")


def logged_in(b):
    b.goto(JENKINS + "/", wait_ms=1500)
    return "/login" not in (b.url() or "")


def connect_jenkins(interactive=True):
    """Returns a Browser attached to a signed-in Jenkins session."""
    if _alive(PORT):
        b = Browser(attach=True, port=PORT)
        if logged_in(b):
            return b
        b.close(keep_browser=True)
        if not interactive:
            raise RuntimeError("Jenkins session expired")
        _close_browser(PORT)

    _launch_visible(JENKINS + "/login")
    print("=" * 70)
    print(" An Edge window has opened on the Jenkins sign-in page.")
    print(" Sign in there yourself - this script never sees your password.")
    print(f" It will keep checking for up to {WAIT_MINUTES} minutes.")
    print("=" * 70, flush=True)

    b = Browser(attach=True, port=PORT)
    deadline = time.time() + WAIT_MINUTES * 60
    while time.time() < deadline:
        if logged_in(b):
            print("signed in to Jenkins", flush=True)
            return b
        time.sleep(5)
    raise TimeoutError("Jenkins sign-in did not complete")


def _crumb_js():
    """Jenkins requires a CSRF crumb on every POST."""
    return """
      const __crumb = async () => {
        const r = await fetch('/crumbIssuer/api/json', {credentials:'same-origin'});
        const j = await r.json();
        return {[j.crumbRequestField]: j.crumb};
      };
    """


def post_form(b, path, fields, timeout=180):
    """POSTs a form from inside the signed-in page, so cookies and CSRF just work."""
    body = json.dumps(fields)
    return b.eval(f"""(async () => {{
      {_crumb_js()}
      const h = await __crumb();
      const p = new URLSearchParams({body});
      const r = await fetch({json.dumps(path)}, {{
        method:'POST', credentials:'same-origin',
        headers: Object.assign({{'Content-Type':'application/x-www-form-urlencoded'}}, h),
        body: p.toString()}});
      return r.status + ' ' + (await r.text()).slice(0, 400);
    }})()""", timeout=timeout)


def groovy(b, script, timeout=300):
    """Runs a script through the Jenkins script console and returns its output.

    Used for the two things that are a poor fit for form-driving: installing a
    plugin and creating the SSH credential. Putting a private key through a
    browser form would mean the automation handling the key material; this way
    it is read from disk by Jenkins itself.
    """
    out = post_form(b, "/scriptText", {"script": script}, timeout=timeout)
    return out


def shot(b, name, label, full_page=True, max_height=3600):
    print(f"[{name[:2]}] {label}", flush=True)
    return b.shot(os.path.join(SHOTS, name), full_page=full_page,
                  max_height=max_height)


if __name__ == "__main__":
    b = connect_jenkins()
    try:
        print("url  :", b.url())
        print("title:", b.eval("document.title"))
    finally:
        b.close(keep_browser=True)
