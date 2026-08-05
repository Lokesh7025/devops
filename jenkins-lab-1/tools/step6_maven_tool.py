"""Phase 3a - register the already-installed Apache Maven 3.9.16 as a Jenkins tool.

'Install automatically' is unchecked so Jenkins uses the local Maven at
MAVEN_HOME instead of downloading its own copy.
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cdp import Browser

SHOTS = r"C:\Users\lokes\jenkins-lab\screenshots"
JENKINS = "http://localhost:8080"
MAVEN_NAME = "Maven-3.9.16"
MAVEN_HOME = r"C:\Users\lokes\tools\apache-maven-3.9.16"

# All work is scoped to the Maven repeatable-container, because the Git tool on
# the same page reuses the _.name / _.home field names.
SCOPE = ("const c=__all('button.repeatable-add').find(x=>/Add Maven/.test(x.innerText))"
         ".closest('.repeated-container');")

b = Browser(attach=True)
try:
    b.goto(f"{JENKINS}/manage/configureTools/", wait_ms=3000)
    b.click_text("Add Maven", selector="button.repeatable-add")
    time.sleep(2)

    # name
    b.eval(b._js(SCOPE + f"const n=c.querySelector('input[name=\"_.name\"]');"
                         f"n.focus();n.value={MAVEN_NAME!r};"
                         "n.dispatchEvent(new Event('input',{bubbles:true}));"
                         "n.dispatchEvent(new Event('change',{bubbles:true}));return 1;"))

    # untick 'Install automatically' so MAVEN_HOME appears
    b.eval(b._js(SCOPE + "const cb=c.querySelector('input[name=\"hudson-tools-InstallSourceProperty\"]');"
                         "if(cb.checked)cb.click();return cb.checked;"))
    time.sleep(1.5)

    home_visible = b.eval(b._js(SCOPE + "const h=c.querySelector('input[name=\"_.home\"]');"
                                        "return h.offsetParent!==null;"))
    print("MAVEN_HOME field visible:", home_visible)

    b.eval(b._js(SCOPE + f"const h=c.querySelector('input[name=\"_.home\"]');"
                         f"h.focus();h.value={MAVEN_HOME!r};"
                         "h.dispatchEvent(new Event('input',{bubbles:true}));"
                         "h.dispatchEvent(new Event('change',{bubbles:true}));"
                         "h.scrollIntoView({block:'center'});return 1;"))
    time.sleep(2)

    print("[14] Global Tool Configuration - Maven")
    b.shot(os.path.join(SHOTS, "14-global-tool-config-maven.png"), full_page=False)

    b.click("button[name=Submit]")
    time.sleep(4)
    b.wait_ready()
    print("saved ->", b.url())

    # confirm it stuck
    b.goto(f"{JENKINS}/manage/configureTools/", wait_ms=3000)
    print("persisted name/home:", b.eval(b._js(
        SCOPE + "const n=c.querySelector('input[name=\"_.name\"]'),"
                "h=c.querySelector('input[name=\"_.home\"]');"
                "return (n?n.value:'?')+' | '+(h?h.value:'?');")))
finally:
    b.close(keep_browser=True)
