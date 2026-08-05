"""Phase 2d - re-capture job #1's build step (full script visible), run it, capture console output."""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cdp import Browser

SHOTS = r"C:\Users\lokes\jenkins-lab\screenshots"
JENKINS = "http://localhost:8080"
JOB = "01-freestyle-simple-commands"


def wait_build(b, job, number, timeout=900):
    """Polls the build's REST API through the browser's authenticated session."""
    end = time.time() + timeout
    while time.time() < end:
        state = b.eval(
            f"fetch('/job/{job}/{number}/api/json').then(r=>r.ok?r.json():null)"
            ".then(j=>j?(j.building?'building':(j.result||'done')):'none').catch(e=>'err')",
            timeout=30)
        if state not in ("building", "none", "err"):
            return state
        time.sleep(3)
    raise TimeoutError(f"build {job} #{number} did not finish")


b = Browser(attach=True)
try:
    # -- nicer capture of the build step: grow the command box ---------------
    b.goto(f"{JENKINS}/job/{JOB}/configure", wait_ms=3000)
    b.eval(b._js("const t=__all('textarea[name=command]')[0];"
                 "t.style.height='620px';t.rows=32;"
                 "t.scrollIntoView({block:'center'});return 1;"))
    time.sleep(1.5)
    print("[11] Build step configuration (full script)")
    b.shot(os.path.join(SHOTS, "11-job1-config-build-step.png"), full_page=False)

    # -- trigger the build ---------------------------------------------------
    b.goto(f"{JENKINS}/job/{JOB}/", wait_ms=2000)
    b.click(f"a[href$='/job/{JOB}/build?delay=0sec']")
    print("Build Now clicked")
    result = wait_build(b, JOB, 1)
    print("build #1 result:", result)

    # -- build page + console output ----------------------------------------
    b.goto(f"{JENKINS}/job/{JOB}/", wait_ms=3000)
    print("[12] Job page with build history")
    b.shot(os.path.join(SHOTS, "12-job1-project-page.png"))

    b.goto(f"{JENKINS}/job/{JOB}/1/console", wait_ms=3000)
    print("[13] Console output")
    b.shot(os.path.join(SHOTS, "13-job1-console-output.png"))
    print("---- console text ----")
    print(b.frame_text()[:2500])
finally:
    b.close(keep_browser=True)
