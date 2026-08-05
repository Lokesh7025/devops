"""
Minimal Chrome DevTools Protocol driver.

Drives an Edge/Chrome instance launched with --remote-debugging-port and saves
real PNG screenshots. Uses only packages already present on this machine
(websockets, requests) -- no Selenium/Playwright install required.
"""
import base64
import json
import os
import subprocess
import time

import requests
from websockets.sync.client import connect

EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"


class Browser:
    def __init__(self, port=9222, profile=r"C:\Users\lokes\jenkins-lab\edge-cdp-profile",
                 width=1500, height=1000, headless=True, attach=False):
        self.port = port
        self.width, self.height = width, height
        self._msg_id = 0
        self.proc = None

        # Reuse a browser this lab already left running, so the logged-in Jenkins
        # session survives between phase scripts.
        if attach and self._endpoint(port):
            self._open(port)
            return

        args = [
            EDGE,
            f"--remote-debugging-port={port}",
            f"--user-data-dir={profile}",
            f"--window-size={width},{height}",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-gpu",
            "--hide-scrollbars",
            "--disable-features=Translate,msEdgeIdentityFeature,EdgeCollections",
            "about:blank",
        ]
        if headless:
            args.insert(1, "--headless=new")
        self.proc = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        ws_url = None
        for _ in range(60):
            ws_url = self._endpoint(port)
            if ws_url:
                break
            time.sleep(0.5)
        if not ws_url:
            raise RuntimeError("could not reach the DevTools endpoint")
        self._open(port, ws_url)

    @staticmethod
    def _endpoint(port):
        """Picks a real content page, never an edge://... dialog target."""
        try:
            pages = [t for t in requests.get(f"http://127.0.0.1:{port}/json/list", timeout=2).json()
                     if t.get("type") == "page"]
        except Exception:
            return None
        for t in pages:
            if t.get("url", "").startswith(("http://", "https://")):
                return t["webSocketDebuggerUrl"]
        for t in pages:
            if not t.get("url", "").startswith("edge://"):
                return t["webSocketDebuggerUrl"]
        return pages[0]["webSocketDebuggerUrl"] if pages else None

    def _open(self, port, ws_url=None):
        ws_url = ws_url or self._endpoint(port)
        self.ws = connect(ws_url, max_size=200 * 1024 * 1024, open_timeout=30)
        self.send("Page.enable")
        self.send("Runtime.enable")
        self.send("Network.enable")

    # -- protocol plumbing ---------------------------------------------------
    def send(self, method, params=None, timeout=60):
        self._msg_id += 1
        mid = self._msg_id
        self.ws.send(json.dumps({"id": mid, "method": method, "params": params or {}}))
        deadline = time.time() + timeout
        while time.time() < deadline:
            msg = json.loads(self.ws.recv(timeout=max(1, deadline - time.time())))
            if msg.get("id") == mid:
                if "error" in msg:
                    raise RuntimeError(f"{method} failed: {msg['error']}")
                return msg.get("result", {})
        raise TimeoutError(f"{method} timed out")

    def eval(self, expr, timeout=60):
        r = self.send("Runtime.evaluate",
                      {"expression": expr, "returnByValue": True, "awaitPromise": True},
                      timeout=timeout)
        if r.get("exceptionDetails"):
            raise RuntimeError(f"JS error: {r['exceptionDetails'].get('text')} :: {expr[:120]}")
        return r.get("result", {}).get("value")

    # -- navigation ----------------------------------------------------------
    def goto(self, url, wait_ms=1200):
        self.send("Page.navigate", {"url": url}, timeout=90)
        self.wait_ready()
        time.sleep(wait_ms / 1000)

    def wait_ready(self, timeout=60):
        end = time.time() + timeout
        while time.time() < end:
            try:
                if self.eval("document.readyState") == "complete":
                    return
            except Exception:
                pass
            time.sleep(0.3)
        raise TimeoutError("page did not finish loading")

    def wait_for(self, js_predicate, timeout=90, poll=0.5):
        """Waits until a JS expression returns truthy."""
        end = time.time() + timeout
        last = None
        while time.time() < end:
            try:
                last = self.eval(js_predicate)
                if last:
                    return last
            except Exception as e:
                last = str(e)
            time.sleep(poll)
        raise TimeoutError(f"wait_for timed out: {js_predicate[:150]} (last={last!r})")

    # -- same-origin frame traversal -----------------------------------------
    # The Jenkins setup wizard renders each panel inside an <iframe>, so the
    # heading and the form fields live in a different document from the footer
    # buttons. Everything is same-origin, so we can walk into the frames.
    _DOCS_JS = """
const __collect=(d)=>{let o=[d];
  for(const f of d.querySelectorAll('iframe,frame')){
    try{ if(f.contentDocument) o=o.concat(__collect(f.contentDocument)); }catch(e){}
  } return o;};
const __docs=__collect(document);
const __all=(sel)=>__docs.flatMap(d=>[...d.querySelectorAll(sel)]);
const __txt=()=>__docs.map(d=>(d.body?d.body.innerText:'')).join('\\n');
"""

    def _js(self, body):
        return f"(()=>{{{self._DOCS_JS}\n{body}}})()"

    def frame_text(self):
        """Visible text of the page *and* every same-origin frame in it."""
        return self.eval(self._js("return __txt();"))

    # -- interaction ---------------------------------------------------------
    def click(self, selector):
        ok = self.eval(self._js(
            f"const e=__all({json.dumps(selector)})[0];"
            f"if(!e)return false;e.scrollIntoView({{block:'center'}});e.click();return true;"))
        if not ok:
            raise RuntimeError(f"no element matching {selector!r} to click")

    CLICKABLE = "button, input[type=submit], input[type=button], a, div.install-recommended, [role=button]"

    def click_text(self, text, selector=None):
        """Clicks the first clickable element whose label contains `text`.

        Jenkins mixes <button>Continue</button> with <input type=submit value="Continue">,
        so the label is taken from textContent *or* value.
        """
        sel = selector or self.CLICKABLE
        ok = self.eval(self._js(
            f"const t={json.dumps(text)}.toLowerCase();"
            f"const e=__all({json.dumps(sel)}).find(x=>"
            f"((x.textContent||'')+' '+(x.value||'')).toLowerCase().includes(t));"
            f"if(!e)return false;e.scrollIntoView({{block:'center'}});e.click();return true;"))
        if not ok:
            raise RuntimeError(f"no clickable element labelled {text!r}")

    def fill(self, selector, value):
        ok = self.eval(self._js(
            f"const e=__all({json.dumps(selector)})[0];if(!e)return false;"
            f"e.focus();e.value={json.dumps(value)};"
            f"e.dispatchEvent(new Event('input',{{bubbles:true}}));"
            f"e.dispatchEvent(new Event('change',{{bubbles:true}}));return true;"))
        if not ok:
            raise RuntimeError(f"no element matching {selector!r} to fill")

    def exists(self, selector):
        return bool(self.eval(self._js(f"return __all({json.dumps(selector)}).length>0;")))

    def text(self):
        return self.eval("document.body.innerText")

    def url(self):
        return self.eval("location.href")

    # -- capture -------------------------------------------------------------
    def shot(self, path, full_page=True, max_height=4000):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        params = {"format": "png"}
        if full_page:
            m = self.send("Page.getLayoutMetrics")
            css = m.get("cssContentSize") or m["contentSize"]
            h = min(int(css["height"]) + 2, max_height)
            w = max(int(css["width"]), self.width)
            params["clip"] = {"x": 0, "y": 0, "width": w, "height": h, "scale": 1}
            params["captureBeyondViewport"] = True
        data = self.send("Page.captureScreenshot", params, timeout=120)["data"]
        with open(path, "wb") as f:
            f.write(base64.b64decode(data))
        print(f"  saved {os.path.basename(path)}")
        return path

    def close(self, keep_browser=False):
        """keep_browser=True leaves Edge running so a later script can attach()
        and continue with the same authenticated Jenkins session."""
        try:
            self.ws.close()
        except Exception:
            pass
        if keep_browser or self.proc is None:
            return
        try:
            self.proc.terminate()
        except Exception:
            pass
