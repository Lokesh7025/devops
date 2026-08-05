"""Phase 3b - create freestyle project #2 and inspect its SCM controls."""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cdp import Browser

SHOTS = r"C:\Users\lokes\jenkins-lab\screenshots"
JENKINS = "http://localhost:8080"
JOB = "02-freestyle-github-snake-game"

b = Browser(attach=True)
try:
    b.goto(f"{JENKINS}/view/all/newJob", wait_ms=1500)
    b.fill("#name", JOB)
    b.click("input[name=mode][value='hudson.model.FreeStyleProject']")
    time.sleep(1)
    print("[15] New Item - freestyle project #2")
    b.shot(os.path.join(SHOTS, "15-new-item-freestyle-github.png"))

    b.click("#ok-button")
    b.wait_for("location.href.includes('/configure')", timeout=120, poll=1)
    b.wait_ready()
    time.sleep(3)
    print("at:", b.url())

    print("---- SCM radios ----")
    print(b.eval(b._js(
        "return __all('input[type=radio]').map(e=>'name='+(e.name||'-')+' value='"
        "+(e.value||'-')+' checked='+e.checked+' label='"
        "+JSON.stringify(((e.closest('.jenkins-radio')||e.parentElement||{}).innerText||'')"
        ".trim().slice(0,40))).join(String.fromCharCode(10));")))
finally:
    b.close(keep_browser=True)
