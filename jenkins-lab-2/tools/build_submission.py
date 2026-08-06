"""Assemble the Jenkins Lab 2 submission package.

Same shape as the Lab 1 packager: a numbered folder tree plus one self-contained
HTML report, so a marker opens a single file and scrolls the whole lab with the
screenshots rendered inline rather than opening PNGs one at a time.
"""
import os
import re
import shutil

import markdown

SRC = r"C:\Users\lokes\jenkins-lab\repo\jenkins-lab-2"
CODE = r"C:\Users\lokes\jenkins-lab\repo"
OUT = r"C:\Users\lokes\jenkins-lab\submission\Jenkins-Lab-2-Lokesh-Selvam"

DIRS = {
    "screenshots": "01-Screenshots",
    "infra":       "03-Azure-Infrastructure",
    "jobs":        "04-Jenkins-Job-Configs",
    "logs":        "05-Build-Logs",
    "tools":       "06-Automation-Scripts",
}

TREE = """Jenkins-Lab-2-Lokesh-Selvam/
├── Jenkins-Lab-2-Report.html   <-- START HERE (the full report, screenshots inline)
├── README.md                   the same report in Markdown
├── 01-Screenshots/             screenshots, numbered in execution order
├── 02-Project-Code/            the Maven project plus the Jenkinsfile
├── 03-Azure-Infrastructure/    provisioning script and cloud-init
├── 04-Jenkins-Job-Configs/     exported config.xml for the job and the node
├── 05-Build-Logs/              full console logs
└── 06-Automation-Scripts/      scripts used to drive and capture the lab"""

TITLE = "Jenkins Lab 2 &mdash; Lokesh Selvam"
SUBTITLE = ("<b>Lokesh Selvam</b> &nbsp;&middot;&nbsp; Build a project on an Azure VM "
            "agent node &nbsp;&middot;&nbsp; Jenkins 2.568.1 LTS")

# ---------------------------------------------------------------- copy tree
if os.path.exists(OUT):
    shutil.rmtree(OUT)
os.makedirs(OUT)

for src_name, dst_name in DIRS.items():
    src = os.path.join(SRC, src_name)
    if os.path.isdir(src):
        shutil.copytree(src, os.path.join(OUT, dst_name))
    else:
        os.makedirs(os.path.join(OUT, dst_name), exist_ok=True)

code = os.path.join(OUT, "02-Project-Code")
os.makedirs(code, exist_ok=True)
for f in ("pom.xml", "Jenkinsfile"):
    shutil.copy2(os.path.join(CODE, f), code)
shutil.copytree(os.path.join(CODE, "src"), os.path.join(code, "src"))

# ------------------------------------------------------- rewrite the report
md = open(os.path.join(SRC, "README.md"), encoding="utf-8").read()
for src_name, dst_name in DIRS.items():
    md = md.replace(f"({src_name}/", f"({dst_name}/")
    md = md.replace(f"`{src_name}/", f"`{dst_name}/")
md = re.sub(r"jenkins-lab-2/\n(?:[├└│].*\n?)+", TREE + "\n", md)

open(os.path.join(OUT, "README.md"), "w", encoding="utf-8").write(md)

# ------------------------------------------------- captions for the gallery
captions = {}
for num, fname, cap in re.findall(
        r"\|\s*(\d+)\s*\|\s*\[`([^`]+\.png)`\]\([^)]+\)\s*\|\s*(.+?)\s*\|", md):
    captions[fname] = (int(num), cap)

shot_dir = os.path.join(OUT, "01-Screenshots")
shots = sorted(os.listdir(shot_dir)) if os.path.isdir(shot_dir) else []
gallery = ['<h2 id="gallery">Screenshot gallery</h2>',
           f'<p class="muted">All {len(shots)} screenshots in the order they were taken.</p>']
for f in shots:
    num, cap = captions.get(f, (0, ""))
    cap = re.sub(r"[*`]", "", cap)
    gallery.append(
        f'<figure id="shot-{f[:2]}">'
        f'<img src="01-Screenshots/{f}" alt="{f}" loading="lazy">'
        f'<figcaption><b>{f}</b>{" &mdash; " + cap if cap else ""}</figcaption></figure>')

# the HTML page has its own cover heading, so drop the Markdown H1
md_html = re.sub(r"^#\s+Jenkins Lab 2\s*\n+", "", md, count=1)
body = markdown.markdown(md_html, extensions=["tables", "fenced_code", "toc", "sane_lists"])

HTML = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Jenkins Lab 2 &mdash; Lokesh Selvam</title>
<style>
 :root {{ --fg:#1c1e21; --muted:#606770; --line:#dfe1e5; --accent:#0b6bcb; --bg:#fff; --code:#f5f6f7; }}
 * {{ box-sizing:border-box; }}
 body {{ margin:0 auto; max-width:1000px; padding:2.5rem 1.5rem 6rem;
        font:16px/1.65 -apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
        color:var(--fg); background:var(--bg); }}
 .cover {{ border-bottom:3px solid var(--accent); margin-bottom:2.5rem; padding-bottom:1.25rem; }}
 .cover h1 {{ margin:0 0 .35rem; font-size:2.1rem; letter-spacing:-.02em; }}
 .cover .sub {{ color:var(--muted); font-size:1.02rem; }}
 h2 {{ margin-top:2.75rem; padding-bottom:.3rem; border-bottom:1px solid var(--line); font-size:1.5rem; }}
 h3 {{ margin-top:2rem; font-size:1.15rem; }}
 table {{ border-collapse:collapse; width:100%; margin:1.1rem 0; font-size:.94rem; display:block; overflow-x:auto; }}
 th,td {{ border:1px solid var(--line); padding:.5rem .7rem; text-align:left; vertical-align:top; }}
 th {{ background:#f0f2f5; font-weight:600; }}
 tr:nth-child(even) td {{ background:#fafbfc; }}
 code {{ background:var(--code); padding:.12em .38em; border-radius:4px;
         font:.88em ui-monospace,Consolas,"Courier New",monospace; }}
 pre {{ background:var(--code); border:1px solid var(--line); border-radius:6px;
        padding:.9rem 1rem; overflow-x:auto; }}
 pre code {{ background:none; padding:0; font-size:.85rem; line-height:1.5; }}
 a {{ color:var(--accent); }}
 blockquote {{ margin:1.2rem 0; padding:.6rem 1rem; border-left:4px solid var(--accent);
               background:#f4f9ff; color:var(--muted); }}
 figure {{ margin:2rem 0; }}
 figure img {{ width:100%; border:1px solid var(--line); border-radius:6px; display:block; }}
 figcaption {{ color:var(--muted); font-size:.88rem; margin-top:.5rem; }}
 .muted {{ color:var(--muted); }}
 @media print {{ body {{ max-width:none; }} figure {{ page-break-inside:avoid; }} }}
</style></head><body>
<div class="cover">
  <h1>Jenkins Lab 2</h1>
  <div class="sub">{subtitle}</div>
</div>
{body}
<hr style="margin:3.5rem 0 0; border:none; border-top:1px solid var(--line)">
{gallery}
</body></html>"""

open(os.path.join(OUT, "Jenkins-Lab-2-Report.html"), "w", encoding="utf-8").write(
    HTML.format(body=body, gallery="\n".join(gallery), subtitle=SUBTITLE))

# ------------------------------------------------------------------ summary
total = sum(os.path.getsize(os.path.join(r, f))
            for r, _, fs in os.walk(OUT) for f in fs)
print(f"built {OUT}")
print(f"  screenshots  : {len(shots)}")
print(f"  captioned    : {len(captions)}")
print(f"  total size   : {total/1024/1024:.1f} MB")
for d in sorted(os.listdir(OUT)):
    p = os.path.join(OUT, d)
    n = sum(len(fs) for _, _, fs in os.walk(p)) if os.path.isdir(p) else 1
    print(f"  {d:32} {n} file(s)")
