"""Phase 2a - create freestyle project #1 through the New Item UI."""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cdp import Browser

SHOTS = r"C:\Users\lokes\jenkins-lab\screenshots"
JENKINS = "http://localhost:8080"
JOB = "01-freestyle-simple-commands"

b = Browser(attach=True)
try:
    b.goto(f"{JENKINS}/view/all/newJob", wait_ms=1500)
    b.fill("#name", JOB)
    b.click("input[name=mode][value='hudson.model.FreeStyleProject']")
    time.sleep(1)
    print("[10] New Item - freestyle project selected")
    b.shot(os.path.join(SHOTS, "10-new-item-freestyle-project.png"))

    b.click("#ok-button")
    b.wait_for("location.href.includes('/configure')", timeout=120, poll=1)
    b.wait_ready()
    time.sleep(3)
    print("landed on:", b.url())

    print("---- config page controls ----")
    print(b.eval(b._js(
        "return __all('button, input[type=submit], input[type=button], textarea, select, "
        "input[type=text]').slice(0,80).map(e=>e.tagName+' type='+(e.type||'-')+' name='"
        "+(e.name||'-')+' id='+(e.id||'-')+' cls='+((e.className||'-')+'').slice(0,40)"
        "+' txt='+JSON.stringify(((e.innerText||e.value||'')+'').trim().slice(0,40))"
        ").join(String.fromCharCode(10));")))
finally:
    b.close(keep_browser=True)
