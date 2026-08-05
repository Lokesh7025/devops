"""Phase 2b - configure freestyle project #1: description + a batch build step."""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cdp import Browser

SHOTS = r"C:\Users\lokes\jenkins-lab\screenshots"
JENKINS = "http://localhost:8080"
JOB = "01-freestyle-simple-commands"

DESCRIPTION = (
    "Lab 1, Part 1 - Freestyle project driven by simple commands.\n"
    "Runs a single 'Execute Windows batch command' build step that prints Jenkins "
    "environment variables, the date, the working directory and the Java version, "
    "then writes and reads back a file in the workspace."
)

BATCH = r"""@echo off
echo ==================================================
echo   Freestyle Project 1 - Simple Commands
echo ==================================================
echo Job name     : %JOB_NAME%
echo Build number : %BUILD_NUMBER%
echo Build tag    : %BUILD_TAG%
echo Workspace    : %WORKSPACE%
echo Executed on  : %NODE_NAME%
echo.

echo --- 1. Date and time ---
date /t
time /t
echo.

echo --- 2. Current working directory ---
cd
echo.

echo --- 3. Java version available to the build ---
java -version
echo.

echo --- 4. Write a file into the workspace, then read it back ---
echo Hello from Jenkins build #%BUILD_NUMBER% > greeting.txt
type greeting.txt
echo.

echo --- 5. Workspace contents ---
dir /b
echo.

echo Build completed successfully.
"""

b = Browser(attach=True)
try:
    b.goto(f"{JENKINS}/job/{JOB}/configure", wait_ms=3000)

    b.fill("textarea[name=description]", DESCRIPTION)

    b.click_text("Add build step", selector="button.hetero-list-add")
    time.sleep(2)

    print("---- dropdown items ----")
    print(b.eval(b._js(
        "return __all('.jenkins-dropdown__item, .yuimenuitemlabel, .bd li a, [role=menuitem]')"
        ".map(e=>e.tagName+' cls='+((e.className||'')+'').slice(0,32)+' txt='"
        "+JSON.stringify(((e.innerText||e.value||'')+'').trim().slice(0,45))"
        ").join(String.fromCharCode(10));")))

    b.click_text("Execute Windows batch command",
                 selector=".jenkins-dropdown__item, .yuimenuitemlabel, [role=menuitem], a, button")
    time.sleep(2.5)

    print("---- textareas now on page ----")
    print(b.eval(b._js(
        "return __all('textarea').map(e=>'name='+(e.name||'-')+' cls='"
        "+((e.className||'')+'').slice(0,40)).join(String.fromCharCode(10));")))

    b.fill("textarea[name=command]", BATCH)
    time.sleep(1)
    print("command field now holds",
          len(b.eval(b._js("return (__all('textarea[name=command]')[0]||{}).value||'';"))), "chars")
finally:
    b.close(keep_browser=True)
