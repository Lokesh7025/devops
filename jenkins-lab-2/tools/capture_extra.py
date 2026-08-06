"""Small top-ups: the dashboard, and a retake of the Nodes page.

The Nodes page was first captured seconds after the agent connected, before
Jenkins had polled it for architecture and disk space, so every column read
N/A. Retaking it once the monitors have run gives a page that actually shows
the agent reporting as a Linux machine.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jenkins as J

PAGES = [
    ("/", "09-jenkins-dashboard.png",
     "The Jenkins dashboard, signed in"),
    ("/computer/", "13-jenkins-nodes.png",
     "The Nodes page: the built-in Windows node plus the Linux Azure agent"),
]


def main():
    b = J.connect_jenkins()
    try:
        for path, name, label in PAGES:
            b.goto(J.JENKINS + path, wait_ms=4000)
            J.shot(b, name, label)
    finally:
        b.close(keep_browser=True)


if __name__ == "__main__":
    main()
