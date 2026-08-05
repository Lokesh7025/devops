"""
Phase 1b - finish the setup wizard: admin user, instance URL, dashboard.

Resumes against the browser left running by step1_wizard.py. Each wizard panel
is rendered in a same-origin <iframe>, so waits key off elements found through
the frame-aware helpers rather than top-level body text.
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cdp import Browser

SHOTS = r"C:\Users\lokes\jenkins-lab\screenshots"
JENKINS = "http://localhost:8080"

USER = os.environ.get("JENKINS_ADMIN_USER", "lokesh")
PASS = os.environ["JENKINS_ADMIN_PASS"]
EMAIL = os.environ.get("JENKINS_ADMIN_EMAIL", "lokeshselvam7025@gmail.com")
FULL = os.environ.get("JENKINS_ADMIN_FULLNAME", "Lokesh Selvam")

b = Browser(attach=True)
try:
    print("at:", b.url())

    # -- 4. Create First Admin User -----------------------------------------
    b.wait_for("!!document.querySelector('.save-first-user')", timeout=1800, poll=3)
    time.sleep(2)
    print("[4] Create First Admin User")
    b.shot(os.path.join(SHOTS, "06-create-admin-user.png"))

    b.fill("input[name=username]", USER)
    b.fill("input[name=password1]", PASS)
    b.fill("input[name=password2]", PASS)
    b.fill("input[name=fullname]", FULL)
    b.fill("input[name=email]", EMAIL)
    time.sleep(0.5)
    b.click(".save-first-user")

    # -- 5. Instance Configuration ------------------------------------------
    b.wait_for("!!document.querySelector('.save-configure-instance')", timeout=300, poll=2)
    time.sleep(2)
    print("[5] Instance Configuration")
    b.shot(os.path.join(SHOTS, "07-instance-configuration.png"))
    b.click(".save-configure-instance")

    # -- 6. Jenkins is ready -------------------------------------------------
    b.wait_for("!!document.querySelector('.install-done, .save-button, .btn-primary')"
               " && /ready|start using/i.test(document.body.innerText)", timeout=300, poll=2)
    time.sleep(2)
    print("[6] Jenkins is ready")
    b.shot(os.path.join(SHOTS, "08-jenkins-is-ready.png"))
    b.click_text("Start using Jenkins")

    # -- 7. Dashboard --------------------------------------------------------
    time.sleep(4)
    b.goto(JENKINS + "/", wait_ms=2500)
    print("[7] Dashboard  ->", b.url())
    b.shot(os.path.join(SHOTS, "09-dashboard-empty.png"))
    print(b.text()[:400])
finally:
    b.close(keep_browser=True)
