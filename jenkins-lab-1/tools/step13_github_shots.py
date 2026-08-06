"""Phase 6 - capture the GitHub side: the repository Jenkins builds, its Maven
project descriptor, and the branch this lab report lives on."""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cdp import Browser

SHOTS = r"C:\Users\lokes\jenkins-lab\screenshots"
REPO = "https://github.com/Lokesh7025/devops"

PAGES = [
    (f"{REPO}",                      "27-github-repo-main.png",      "Repository on GitHub (branch main)"),
    (f"{REPO}/blob/main/pom.xml",    "28-github-maven-pom.png",      "The Maven project descriptor - pom.xml"),
    (f"{REPO}/tree/jenkins-lab-1/jenkins-lab-1",
                                     "29-github-lab-branch.png",     "The jenkins-lab-1 branch with the lab report"),
]

b = Browser(attach=True)
try:
    for url, name, label in PAGES:
        b.goto(url, wait_ms=4000)
        # GitHub lazy-loads; nudge it and settle
        b.eval("window.scrollTo(0,0); 1")
        time.sleep(2)
        print(f"[{name[:2]}] {label}")
        print("    title:", b.eval("document.title"))
        b.shot(os.path.join(SHOTS, name), full_page=True, max_height=2600)
finally:
    b.close(keep_browser=True)
