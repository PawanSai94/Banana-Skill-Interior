# Builds kitchen-plan.html: python3 build_page.py kitchen-plan.html page_template.html
import html, re, sys
from pathlib import Path
F = Path("/home/user/Banana-Skill-Interior/floorplans")
out = Path(sys.argv[1])

def inline(t):
    t = html.escape(t, quote=False)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", t)
    return t

def md_sections(md):
    secs, cur = [], None
    lines = md.splitlines()
    i = 0
    while i < len(lines):
        ln = lines[i]
        if ln.startswith("# "):
            i += 1; continue
        if ln.startswith("## "):
            cur = {"title": ln[3:].strip(), "body": []}; secs.append(cur); i += 1; continue
        if cur is None:
            i += 1; continue
        if ln.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-{3,}:?", c) for c in cells):
                    rows.append(cells)
                i += 1
            head, body = rows[0], rows[1:]
            t = ['<div class="tbl"><table><thead><tr>'] + [f"<th>{inline(c)}</th>" for c in head] + ["</tr></thead><tbody>"]
            for r in body:
                cls = ' class="total"' if r[0].startswith("**") else ""
                t.append(f"<tr{cls}>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>")
            t.append("</tbody></table></div>")
            cur["body"].append("".join(t)); continue
        if re.match(r"\d+\. ", ln):
            items = []
            while i < len(lines) and re.match(r"\d+\. ", lines[i]):
                items.append(re.sub(r"^\d+\. ", "", lines[i])); i += 1
            cur["body"].append("<ol>" + "".join(f"<li>{inline(x)}</li>" for x in items) + "</ol>"); continue
        if ln.strip():
            para = [ln.strip()]; i += 1
            while i < len(lines) and lines[i].strip() and not lines[i].startswith(("|", "## ")) and not re.match(r"\d+\. ", lines[i]):
                para.append(lines[i].strip()); i += 1
            cur["body"].append(f"<p>{inline(' '.join(para))}</p>"); continue
        i += 1
    return secs

def svg(name):
    s = (F / name).read_text()
    s = re.sub(r"^<\?xml[^>]*>\s*", "", s)
    s = re.sub(r"<!--.*?-->", "", s, flags=re.S)
    return s

secs = md_sections((F / "INVENTORY.md").read_text())
def sec_id(t): return "inv-" + re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")
inv_html = []
for sct in secs:
    num, _, name = sct["title"].partition(". ")
    if not name: num, name = "", sct["title"]
    inv_html.append(f'<section class="inv" id="{sec_id(sct["title"])}"><h3><span class="num">{inline(num)}</span>{inline(name)}</h3>{"".join(sct["body"])}</section>')

drawings = [
    ("plan", "Floor plan", "Top view, north up. Base cabinets numbered 1–9, tall cabinets 11–13, wall cabinets U1–U6 dotted blue. Scale 4 px = 1 in.", "floorplan.svg"),
    ("east", "East wall", "A → H, 177\" (14′-9″). Stovetop D–E, windows B–C and F–G (sill 46.5\"), base cabinets 1–6, wall cabinets U1–U3. Ceiling 96\".", "east_elevation.svg"),
    ("south", "South wall", "H → K, 123.5\". Sink base 8 under the 32\" window, trash 9, dishwasher, wall cabinets U2 and U4–U6. Ceiling slopes 96\" → 100\".", "south_elevation.svg"),
    ("west", "West wall", "K → R. Pantry opening, fridge alcove with cabinet 10, appliance garage 11–12 and oven/coffee/microwave stack 13 on a 9\" raised box with toe-kick drawers. Ceiling 100\".", "west_elevation.svg"),
    ("pantry", "Walk-in pantry", "About 36\" × 61\" inside. U-shaped shelving, rolling rice and atta bins, bag platform.", "pantry_layout.svg"),
]
fig = []
for did, ttl, cap, fn in drawings:
    fig.append(f'<figure class="sheet" id="{did}"><figcaption><h3>{html.escape(ttl)}</h3><p>{html.escape(cap)}</p></figcaption><div class="drawing">{svg(fn)}</div></figure>')

page = Path(sys.argv[2]).read_text()
page = page.replace("{{DRAWINGS}}", "\n".join(fig)).replace("{{INVENTORY}}", "\n".join(inv_html))
out.write_text(page)
print(len(page))
