"""Phase 5 - capture a build while it is actually executing.

Triggers build #2 of the GitHub job and screenshots the streaming console output
and the busy executor before the build finishes.
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cdp import Browser

SHOTS = r"C:\Users\lokes\jenkins-lab\screenshots"
JENKINS = "http://localhost:8080"
JOB2 = "02-freestyle-github-snake-game"
N = 2

b = Browser(attach=True)
try:
    b.goto(f"{JENKINS}/job/{JOB2}/", wait_ms=1500)
    b.click(f"a[href$='/job/{JOB2}/build?delay=0sec']")
    print("triggered build #%d" % N)

    # jump straight onto the streaming console page
    for _ in range(40):
        b.goto(f"{JENKINS}/job/{JOB2}/{N}/console", wait_ms=600)
        if "Started by user" in b.frame_text():
            break
        time.sleep(0.5)

    time.sleep(6)   # let Maven get going so the log has substance
    state = b.eval(f"fetch('/job/{JOB2}/{N}/api/json').then(r=>r.ok?r.json():null)"
                   ".then(j=>j?(j.building?'building':(j.result||'done')):'none').catch(e=>'err')")
    print("state while capturing console:", state)
    print("[23] Console output while the build is running")
    b.shot(os.path.join(SHOTS, "23-job2-build-in-progress.png"), full_page=False)

    # dashboard: executor busy, progress bar in the build queue
    b.goto(f"{JENKINS}/", wait_ms=1200)
    state = b.eval(f"fetch('/job/{JOB2}/{N}/api/json').then(r=>r.ok?r.json():null)"
                   ".then(j=>j?(j.building?'building':(j.result||'done')):'none').catch(e=>'err')")
    print("state while capturing dashboard:", state)
    print("[24] Dashboard with the build executor busy")
    b.shot(os.path.join(SHOTS, "24-build-executor-running.png"), full_page=False)

    # let it finish
    for _ in range(200):
        state = b.eval(f"fetch('/job/{JOB2}/{N}/api/json').then(r=>r.ok?r.json():null)"
                       ".then(j=>j?(j.building?'building':(j.result||'done')):'none').catch(e=>'err')")
        if state not in ("building", "none", "err"):
            break
        time.sleep(3)
    print("build #%d result: %s" % (N, state))
finally:
    b.close(keep_browser=True)
