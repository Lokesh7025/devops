"""Phase 2c - screenshot job #1's configuration, save it, then run the build."""
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
    # -- configuration page, scrolled to the build step ----------------------
    b.eval(b._js("__all('textarea[name=command]')[0]"
                 ".scrollIntoView({block:'center'});return 1;"))
    time.sleep(1.5)
    print("[11] Build step configuration")
    b.shot(os.path.join(SHOTS, "11-job1-config-build-step.png"), full_page=False)

    # -- save ----------------------------------------------------------------
    b.click("button[name=Submit]")
    b.wait_for(f"location.href.includes('/job/{JOB}/') && !location.href.includes('configure')",
               timeout=120, poll=1)
    b.wait_ready()
    time.sleep(2.5)
    print("saved, now at:", b.url())
    print("[12] Job page")
    b.shot(os.path.join(SHOTS, "12-job1-project-page.png"))

    print("---- sidebar links ----")
    print(b.eval(b._js(
        "return __all('a, button').filter(e=>/build|workspace|configure/i.test(e.innerText||''))"
        ".map(e=>e.tagName+' href='+((e.getAttribute&&e.getAttribute('href'))||'-')"
        "+' cls='+((e.className||'')+'').slice(0,35)"
        "+' txt='+JSON.stringify(((e.innerText||'')+'').trim().slice(0,30))"
        ").join(String.fromCharCode(10));")))
finally:
    b.close(keep_browser=True)
