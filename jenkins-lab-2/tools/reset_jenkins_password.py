"""Reset the Jenkins admin password.

Jenkins stores passwords as bcrypt hashes, so the old one cannot be read back -
it can only be replaced. This performs the documented recovery: stop the
controller, turn security off in config.xml, start it, set a new password
through the script console, then restore the original config and restart.

The window in which Jenkins is unsecured is a few seconds long and it is only
ever listening on localhost.
"""
import os
import re
import secrets
import shutil
import subprocess
import time

import requests

HOME = r"C:\Users\lokes\jenkins-lab\home"
CONFIG = os.path.join(HOME, "config.xml")
BACKUP = os.path.join(HOME, "config.xml.pre-reset")
START = r"C:\Users\lokes\jenkins-lab\tools\Start-Jenkins.ps1"
URL = "http://localhost:8080"
USER = "lokesh"


def jenkins_pids():
    """PIDs of java processes whose command line mentions jenkins.war."""
    out = subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         "Get-CimInstance Win32_Process -Filter \"Name='java.exe'\" | "
         "Where-Object { $_.CommandLine -like '*jenkins.war*' } | "
         "Select-Object -ExpandProperty ProcessId"],
        capture_output=True, text=True)
    return [int(x) for x in out.stdout.split() if x.strip().isdigit()]


def stop():
    pids = jenkins_pids()
    for pid in pids:
        subprocess.run(["taskkill", "/PID", str(pid), "/F", "/T"],
                       capture_output=True)
    for _ in range(60):
        if not jenkins_pids():
            break
        time.sleep(1)
    print(f"stopped jenkins (pids {pids or 'none'})", flush=True)


def start():
    subprocess.Popen(["powershell", "-NoExit", "-ExecutionPolicy", "Bypass",
                      "-File", START],
                     creationflags=subprocess.CREATE_NEW_CONSOLE)
    for _ in range(180):
        try:
            if requests.get(URL + "/login", timeout=5).status_code < 500:
                print("jenkins is up", flush=True)
                return
        except Exception:
            pass
        time.sleep(2)
    raise RuntimeError("jenkins did not come back up")


def set_security(enabled):
    """Flips <useSecurity> without round-tripping the file through a decoder
    that would mangle its UTF-8."""
    with open(CONFIG, "rb") as f:
        raw = f.read()
    new = re.sub(rb"<useSecurity>(true|false)</useSecurity>",
                 b"<useSecurity>%s</useSecurity>" % (b"true" if enabled else b"false"),
                 raw, count=1)
    with open(CONFIG, "wb") as f:
        f.write(new)


def groovy(script):
    s = requests.Session()
    crumb = {}
    try:
        j = s.get(URL + "/crumbIssuer/api/json", timeout=10).json()
        crumb = {j["crumbRequestField"]: j["crumb"]}
    except Exception:
        pass
    r = s.post(URL + "/scriptText", data={"script": script},
               headers=crumb, timeout=120)
    return r.status_code, r.text.strip()


def main():
    password = "Jenkins-" + secrets.token_urlsafe(9)

    shutil.copy2(CONFIG, BACKUP)
    print(f"backed up config.xml -> {BACKUP}", flush=True)

    stop()
    set_security(False)
    print("security disabled", flush=True)
    start()

    code, out = groovy(f"""
        def u = hudson.model.User.getById({USER!r}, false)
        if (u == null) {{ println('NO SUCH USER'); return }}
        u.addProperty(hudson.security.HudsonPrivateSecurityRealm.Details
                        .fromPlainPassword({password!r}))
        u.save()
        println('password updated for ' + u.getId())
    """)
    print(f"script console -> {code}: {out[:200]}", flush=True)
    ok = "password updated" in out

    stop()
    shutil.copy2(BACKUP, CONFIG)
    print("original config.xml restored", flush=True)
    start()

    print("=" * 60)
    print(" username :", USER)
    print(" password :", password if ok else "(RESET FAILED)")
    print("=" * 60, flush=True)
    if not ok:
        raise SystemExit("the password was not changed")


if __name__ == "__main__":
    main()
