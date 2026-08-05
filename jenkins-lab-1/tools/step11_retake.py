"""Re-capture job #2's SCM panel framed so 'Branches to build' is visible."""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cdp import Browser

SHOTS = r"C:\Users\lokes\jenkins-lab\screenshots"
JOB2 = "02-freestyle-github-snake-game"

b = Browser(attach=True)
try:
    b.goto(f"http://localhost:8080/job/{JOB2}/configure", wait_ms=3500)
    # frame on the branch field, which sits below the repository URL
    b.eval(b._js("const br=__all('input[name=\"_.name\"]').find(e=>e.value&&e.value.includes('main'));"
                 "br.scrollIntoView({block:'center'});window.scrollBy(0,-140);return br.value;"))
    time.sleep(1.5)
    print("[16] Git SCM configuration (retake)")
    b.shot(os.path.join(SHOTS, "16-job2-config-git-scm.png"), full_page=False)
finally:
    b.close(keep_browser=True)
