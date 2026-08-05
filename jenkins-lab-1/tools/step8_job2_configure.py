"""Phase 3c - configure freestyle project #2: Git SCM + Maven goals + artifact archiving."""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cdp import Browser

SHOTS = r"C:\Users\lokes\jenkins-lab\screenshots"
JENKINS = "http://localhost:8080"
JOB = "02-freestyle-github-snake-game"
REPO = "https://github.com/Lokesh7025/devops.git"
BRANCH = "*/main"

DESCRIPTION = (
    "Lab 1, Part 2 - Freestyle project built from GitHub.\n"
    "Checks out https://github.com/Lokesh7025/devops (branch main) with the Git plugin "
    "and builds the com.snake:snake-game Maven project with 'clean package'. "
    "The shaded JAR produced in target/ is archived as a build artifact."
)

b = Browser(attach=True)
try:
    b.goto(f"{JENKINS}/job/{JOB}/configure", wait_ms=3000)
    b.fill("textarea[name=description]", DESCRIPTION)

    # -- Source Code Management: Git ----------------------------------------
    b.click("input[name=scm][value='1']")
    time.sleep(2)

    b.eval(b._js(
        "const u=__all('input[name=\"_.url\"]').find(e=>e.offsetParent!==null);"
        f"u.focus();u.value={REPO!r};"
        "u.dispatchEvent(new Event('input',{bubbles:true}));"
        "u.dispatchEvent(new Event('change',{bubbles:true}));return 1;"))
    time.sleep(2)   # let the plugin's async URL validation run

    b.eval(b._js(
        "const br=__all('input[name=\"_.name\"]').find(e=>e.value==='*/master');"
        f"br.focus();br.value={BRANCH!r};"
        "br.dispatchEvent(new Event('input',{bubbles:true}));"
        "br.dispatchEvent(new Event('change',{bubbles:true}));return 1;"))
    time.sleep(1)

    print("git url  :", b.eval(b._js(
        "const u=__all('input[name=\"_.url\"]').find(e=>e.offsetParent!==null);return u?u.value:'?';")))
    print("branch   :", b.eval(b._js(
        "const b2=__all('input[name=\"_.name\"]').filter(e=>e.offsetParent!==null)"
        ".map(e=>e.value);return JSON.stringify(b2);")))

    # -- Build step: Invoke top-level Maven targets --------------------------
    b.click_text("Add build step", selector="button.hetero-list-add")
    time.sleep(2)
    b.click_text("Invoke top-level Maven targets", selector=".jenkins-dropdown__item")
    time.sleep(2.5)

    print("---- maven step fields ----")
    print(b.eval(b._js(
        "return __all('select, input[type=text], textarea').filter(e=>e.offsetParent!==null)"
        ".map(e=>e.tagName+' name='+(e.name||'-')+' val='"
        "+JSON.stringify(((e.value||'')+'').slice(0,45))).join(String.fromCharCode(10));")))

    # -- Post-build: Archive the artifacts -----------------------------------
    b.click_text("Add post-build action", selector="button.hetero-list-add")
    time.sleep(2)
    print("---- post-build menu ----")
    print(b.eval(b._js(
        "return __all('.jenkins-dropdown__item').map(e=>JSON.stringify(e.innerText.trim()))"
        ".join(String.fromCharCode(10));")))
finally:
    b.close(keep_browser=True)
