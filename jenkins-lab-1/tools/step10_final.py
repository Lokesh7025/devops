"""Phase 4 - closing evidence: console tail, archived artifact, dashboard with both jobs."""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cdp import Browser

SHOTS = r"C:\Users\lokes\jenkins-lab\screenshots"
JENKINS = "http://localhost:8080"
JOB2 = "02-freestyle-github-snake-game"

b = Browser(attach=True)
try:
    # -- tail of job 2's console: the BUILD SUCCESS block --------------------
    b.goto(f"{JENKINS}/job/{JOB2}/1/console", wait_ms=3000)
    b.eval("window.scrollTo(0, document.body.scrollHeight); 1")
    time.sleep(2)
    print("[20] Console tail - BUILD SUCCESS")
    b.shot(os.path.join(SHOTS, "20-job2-build-success.png"), full_page=False)

    # -- build page showing the archived artifact ---------------------------
    b.goto(f"{JENKINS}/job/{JOB2}/1/", wait_ms=3000)
    print("[21] Build #1 page with archived artifact")
    b.shot(os.path.join(SHOTS, "21-job2-archived-artifact.png"))
    print(b.frame_text()[:700])

    # -- dashboard with both jobs -------------------------------------------
    b.goto(f"{JENKINS}/", wait_ms=3000)
    print("[22] Dashboard with both freestyle projects")
    b.shot(os.path.join(SHOTS, "22-dashboard-both-jobs.png"))
    print("----")
    print(b.frame_text()[:700])
finally:
    b.close(keep_browser=True)
