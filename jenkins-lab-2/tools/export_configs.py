"""Export the job and node config.xml so the setup is reproducible from the report."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jenkins as J

OUT = r"C:\Users\lokes\jenkins-lab\repo\jenkins-lab-2\jobs"
JOB = "snake-game-on-azure-agent"
NODE = "azure-agent-1"

ITEMS = [
    (f"/job/{JOB}/config.xml", "job-snake-game-on-azure-agent.xml"),
    (f"/computer/{NODE}/config.xml", "node-azure-agent-1.xml"),
]


def main():
    os.makedirs(OUT, exist_ok=True)
    b = J.connect_jenkins()
    try:
        for path, name in ITEMS:
            xml = b.eval(f"""(async () => {{
              const r = await fetch({path!r}, {{credentials:'same-origin'}});
              return r.ok ? await r.text() : ('ERROR ' + r.status);
            }})()""", timeout=120) or ""
            dest = os.path.join(OUT, name)
            open(dest, "w", encoding="utf-8", newline="\n").write(xml)
            print(f"  {name}: {len(xml)} bytes")
    finally:
        b.close(keep_browser=True)


if __name__ == "__main__":
    main()
