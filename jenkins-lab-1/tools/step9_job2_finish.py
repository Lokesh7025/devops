"""Phase 3d - finish job #2's configuration, screenshot it, save, build, capture output."""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cdp import Browser

SHOTS = r"C:\Users\lokes\jenkins-lab\screenshots"
JENKINS = "http://localhost:8080"
JOB = "02-freestyle-github-snake-game"
MAVEN_NAME = "Maven-3.9.16"
GOALS = "clean package"
ARTIFACTS = "target/*.jar"


def wait_build(b, job, number, timeout=1800):
    end = time.time() + timeout
    while time.time() < end:
        state = b.eval(
            f"fetch('/job/{job}/{number}/api/json').then(r=>r.ok?r.json():null)"
            ".then(j=>j?(j.building?'building':(j.result||'done')):'none').catch(e=>'err')",
            timeout=30)
        if state not in ("building", "none", "err"):
            return state
        time.sleep(4)
    raise TimeoutError(f"build {job} #{number} did not finish")


b = Browser(attach=True)
try:
    # the post-build dropdown was left open by the previous phase
    b.click_text("Archive the artifacts", selector=".jenkins-dropdown__item")
    time.sleep(2.5)
    b.fill("input[name='_.artifacts']", ARTIFACTS)

    # Maven installation + goals
    print("maven select ->", b.eval(b._js(
        "const s=__all('select[name=\"maven.name\"]')[0];"
        f"const o=[...s.options].find(x=>x.text.includes({MAVEN_NAME!r}));"
        "if(!o)return 'option not found: '+[...s.options].map(x=>x.text).join(',');"
        "s.value=o.value;s.dispatchEvent(new Event('change',{bubbles:true}));return s.value;")))
    b.fill("input[name='_.targets']", GOALS)
    time.sleep(1)

    # -- screenshots of the finished configuration ---------------------------
    b.eval(b._js("__all('input[name=\"_.url\"]').find(e=>e.offsetParent!==null)"
                 ".scrollIntoView({block:'center'});return 1;"))
    time.sleep(1.5)
    print("[16] Git SCM configuration")
    b.shot(os.path.join(SHOTS, "16-job2-config-git-scm.png"), full_page=False)

    b.eval(b._js("__all('input[name=\"_.targets\"]')[0].scrollIntoView({block:'center'});return 1;"))
    time.sleep(1.5)
    print("[17] Maven build step + archive artifacts")
    b.shot(os.path.join(SHOTS, "17-job2-config-maven-step.png"), full_page=False)

    # -- save ----------------------------------------------------------------
    b.click("button[name=Submit]")
    b.wait_for(f"location.href.includes('/job/{JOB}/') && !location.href.includes('configure')",
               timeout=180, poll=1)
    b.wait_ready()
    time.sleep(2)
    print("saved ->", b.url())

    # -- build ---------------------------------------------------------------
    b.click(f"a[href$='/job/{JOB}/build?delay=0sec']")
    print("Build Now clicked; waiting (first build downloads Maven dependencies)...")
    result = wait_build(b, JOB, 1)
    print("build #1 result:", result)

    b.goto(f"{JENKINS}/job/{JOB}/", wait_ms=3000)
    print("[18] Job page")
    b.shot(os.path.join(SHOTS, "18-job2-project-page.png"))

    b.goto(f"{JENKINS}/job/{JOB}/1/console", wait_ms=3000)
    print("[19] Console output")
    b.shot(os.path.join(SHOTS, "19-job2-console-output.png"))
    txt = b.frame_text()
    print("---- console head ----");  print(txt[:1600])
    print("---- console tail ----");  print(txt[-1800:])
finally:
    b.close(keep_browser=True)
