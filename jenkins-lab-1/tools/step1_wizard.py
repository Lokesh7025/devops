"""
Phase 1 - drive the Jenkins post-install setup wizard and screenshot every page.

Credentials come from the environment so no password is written into the repo:
    JENKINS_ADMIN_USER, JENKINS_ADMIN_PASS, JENKINS_ADMIN_EMAIL
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cdp import Browser

SHOTS = r"C:\Users\lokes\jenkins-lab\screenshots"
JENKINS = "http://localhost:8080"
SECRET = r"C:\Users\lokes\jenkins-lab\home\secrets\initialAdminPassword"

USER = os.environ.get("JENKINS_ADMIN_USER", "lokesh")
PASS = os.environ["JENKINS_ADMIN_PASS"]
EMAIL = os.environ.get("JENKINS_ADMIN_EMAIL", "lokeshselvam7025@gmail.com")
FULL = os.environ.get("JENKINS_ADMIN_FULLNAME", "Lokesh Selvam")

b = Browser(headless=True, attach=True)
try:
    # -- 1. Unlock Jenkins ---------------------------------------------------
    b.goto(JENKINS)
    b.wait_for("!!document.querySelector('input[type=password]')")
    print("[1] Unlock Jenkins")
    b.shot(os.path.join(SHOTS, "03-unlock-jenkins.png"))

    token = open(SECRET).read().strip()
    b.fill("input[type=password]", token)
    b.click_text("Continue")

    # -- 2. Customize Jenkins ------------------------------------------------
    b.wait_for("document.body.innerText.includes('Customize Jenkins')", timeout=120)
    time.sleep(1.5)
    print("[2] Customize Jenkins")
    b.shot(os.path.join(SHOTS, "04-customize-jenkins.png"))

    b.click_text("Install suggested plugins")

    # -- 3. Plugin installation progress ------------------------------------
    b.wait_for("document.body.innerText.includes('Getting Started')"
               " && !document.body.innerText.includes('Customize Jenkins')", timeout=120)
    time.sleep(12)          # let a few plugins land so the progress list has content
    print("[3] Installing suggested plugins")
    b.shot(os.path.join(SHOTS, "05-installing-suggested-plugins.png"))

    # -- 4. Create First Admin User -----------------------------------------
    print("    waiting for plugin installation to finish (can take a few minutes)...")
    b.wait_for("document.body.innerText.includes('Create First Admin User')"
               " || document.body.innerText.includes('Instance Configuration')", timeout=1800, poll=3)
    time.sleep(2)
    print("[4] Create First Admin User")
    b.shot(os.path.join(SHOTS, "06-create-admin-user.png"))

    b.fill("input[name=username]", USER)
    b.fill("input[name=password1]", PASS)
    b.fill("input[name=password2]", PASS)
    b.fill("input[name=fullname]", FULL)
    b.fill("input[name=email]", EMAIL)
    b.click_text("Save and Continue")

    # -- 5. Instance Configuration ------------------------------------------
    b.wait_for("document.body.innerText.includes('Instance Configuration')", timeout=180)
    time.sleep(1.5)
    print("[5] Instance Configuration")
    b.shot(os.path.join(SHOTS, "07-instance-configuration.png"))
    b.click_text("Save and Finish")

    # -- 6. Jenkins is ready -------------------------------------------------
    b.wait_for("document.body.innerText.includes('Jenkins is ready')"
               " || document.body.innerText.includes('Start using Jenkins')", timeout=300)
    time.sleep(1.5)
    print("[6] Jenkins is ready")
    b.shot(os.path.join(SHOTS, "08-jenkins-is-ready.png"))
    b.click_text("Start using Jenkins")

    # -- 7. Dashboard --------------------------------------------------------
    b.wait_for("document.body.innerText.includes('Welcome to Jenkins')"
               " || !!document.querySelector('#jenkins-head-icon, .app-page-body')", timeout=180)
    time.sleep(2)
    b.goto(JENKINS + "/")
    print("[7] Dashboard")
    b.shot(os.path.join(SHOTS, "09-dashboard-empty.png"))

    print("\nlogged in as:", b.eval(
        "(document.querySelector('.jenkins-header__auth, #header .login, a[href*=\"/user/\"]')||{}).innerText||'?'" ))
    print("URL:", b.url())
finally:
    b.close(keep_browser=True)

