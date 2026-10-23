"""
Builds the GitHub profile README and all its SVG images.

    python generator/make.py          (run from the github-profile folder)

Needs Python 3.8+ and Pillow (pip install pillow), used only to turn the
PNG/ICO logos into small embedded PNGs.

What it writes:
    assets/t-*.svg     the tiles the README shows (header, about, cards, ...)
    README.md          the profile README that stitches the tiles together
    preview.html       open in a browser to see it on GitHub-like dark/light backgrounds

To change content, edit the CONTENT section below and rerun.
Logos are read from assets/logos/ (SVG files are inlined, PNG/ICO are embedded).

Why images and not HTML/CSS: GitHub strips all CSS, style attributes and
backgrounds from READMEs. An SVG shown through <img> keeps its own styles and
animations, but cannot load anything external, so logos are embedded and each
clickable card is a separate image wrapped in a link.
"""
import base64, html, io, os, random, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")
LOGOS = os.path.join(ASSETS, "logos")

# ----------------------------------------------------------------- CONTENT
NAME = "Ajit Kumar"
TAGLINE = "Backend engineer · Java / Spring · distributed systems"
SUBLINE = "M.Tech AI, IIT Patna · SDE I at Success Numbers"

NOW = ["SDE I at Success Numbers. I build Spring Boot services for retail",
       "returns and payments that run in hundreds of stores, and I own",
       "the Saudi and UAE tax-compliance integrations."]
BEFORE = "Research intern at TCS Research: graph attention networks for protein dynamics."
STATS = [("9.46", "CGPA", "M.Tech AI, IIT Patna"),
         ("99.3", "percentile", "GATE 2024"),
         ("67%", "lower latency", "cart retrieval at work")]

# Shown two per row, in this order. desc: 3 lines of ~58 chars max.
PROJECTS = [
    dict(slug="waas", logo="waas.svg", url="https://github.com/ajayraho/waas",
         title="WaaS", cat="Waitlist-as-a-Service · backend",
         desc=["A multi-tenant waitlist any product can plug into. People",
               "see their place update live and get a timed checkout slot;",
               "Redis Lua scripts make sure no slot is handed out twice."],
         metric="0.4 s", mlabel=["500 concurrent joins", "336 ms p99 (k6)"],
         chips=["Java", "Spring Boot", "Redis"]),
    dict(slug="saga", logo="saga-checkout.svg", url="https://github.com/ajayraho/saga-checkout",
         title="saga-checkout", cat="Distributed payment saga",
         desc=["Orchestrates a 4-step checkout across services over Kafka,",
               "with a transactional outbox, idempotent requests and",
               "automatic compensation when a step fails."],
         metric="16.3/s", mlabel=["completed sagas", "across 5 JVMs"],
         chips=["Java", "Kafka", "PostgreSQL"]),
    dict(slug="nanofuse", logo="nanofuse.svg", url="https://github.com/ajayraho/nanofuse",
         title="nanofuse", cat="Tensor graph compiler",
         desc=["Built from scratch: a lazy execution graph, an op-fusion",
               "pass, and two codegen backends, a trace-once Python JIT",
               "and multi-threaded C++ with OpenMP."],
         metric="4.31×", mlabel=["faster than NumPy", "on the C++ backend"],
         chips=["Python", "C++", "OpenMP"]),
    dict(slug="ragdrift", logo="rag-drift.svg", url="https://github.com/ajayraho/rag-drift",
         title="rag-drift", cat="Agentic AI · MLOps",
         desc=["An Airflow pipeline that keeps a LangChain agent's",
               "knowledge base fresh, and catches and repairs upstream",
               "schema drift before it reaches the agent."],
         metric="Incremental", mlabel=["re-embeds only", "what changed"],
         chips=["Airflow", "LangChain"]),
    dict(slug="oss-scout", logo="oss-scout.png", url="https://github.com/ajayraho/oss-scout",
         title="OSS Scout", cat="Web app · MCP server",
         desc=["Finds beginner-friendly GitHub issues by language, label,",
               "age, comments and assignee, with live rate-limit",
               "countdowns and a per-repo issue view."],
         metric="MCP", mlabel=["search issues straight", "from an AI chat"],
         chips=["Python", "Streamlit", "MCP"]),
    dict(slug="screenrec", logo="screenrec.ico", url="https://github.com/ajayraho/screenrec",
         title="ScreenRec", cat="Windows app · on-device AI",
         desc=["Background screen recorder that captures system audio and",
               "mic together, with global hotkeys that work inside",
               "full-screen apps and remote desktop."],
         metric="Offline", mlabel=["Whisper transcripts and", "local LLM summaries"],
         chips=["C#", ".NET 9", "FFmpeg"]),
]

PAPERS = [("PC-GoT", ["Policy-Controlled Graph-of-Thought for", "Neuro-Symbolic Logical Reasoning"],
           "IEEE Trans. on Knowledge and Data Engineering"),
          ("CAM-GEO", ["Causal Agentic Multimodal GEO for", "E-Commerce Search Visibility"],
           "IEEE Trans. on Computational Social Systems")]
TOOLKIT = [("Backend", ["Java", "Spring Boot", "Kafka", "Redis", "PostgreSQL"]),
           ("AI / ML", ["Python", "PyTorch", "LangChain", "Airflow", "MLflow"]),
           ("Shipping", ["Docker", "Azure", "React", "TypeScript"])]

CONTACT = [("email", "Email", "ajitkumar13082024@gmail.com", "mailto:ajitkumar13082024@gmail.com"),
           ("linkedin", "LinkedIn", "in/ajayraho", "https://linkedin.com/in/ajayraho"),
           ("portfolio", "Portfolio", "portfolio-ajit.web.app", "https://portfolio-ajit.web.app/?ref=github")]

# ----------------------------------------------------------------- THEME
C = dict(sheet="#e4f5eb", bg="#f4fbf7", bd="#cfeadb", ink="#173b2e", mid="#2d6a4f",
         soft="#52796f", acc="#40916c", chip="#e1f4ea", chipt="#1f5640", body="#2f4f43")
FONT = 'font-family="Segoe UI,-apple-system,BlinkMacSystemFont,Helvetica,Arial,sans-serif"'
REDUCED = "@media (prefers-reduced-motion:reduce){*{animation:none!important}}"
SWAY = (".sway{animation:sway 5s ease-in-out infinite alternate;transform-box:fill-box;transform-origin:bottom left}"
        "@keyframes sway{from{transform:rotate(-7deg)}to{transform:rotate(9deg)}}")


def esc(s):
    return html.escape(s, quote=True)


def svg(w, h, body, style="", label="", defs=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'viewBox="0 0 {w:g} {h:g}" width="{w:g}" height="{h:g}" role="img" aria-label="{esc(label)}">'
            f'<style>{style}{REDUCED}</style>{defs}<g {FONT}>{body}</g></svg>')


def panel(w, h):
    return (f'<rect x="1.5" y="1.5" width="{w-3}" height="{h-3}" rx="22" '
            f'fill="{C["bg"]}" stroke="{C["bd"]}" stroke-width="2"/>')


def sprig(x, y, s=0.55):
    return (f'<g transform="translate({x},{y}) scale({-s},{s})"><g class="sway">'
            f'<path d="M0,0 C6,-22 4,-44 14,-64" stroke="{C["acc"]}" stroke-width="2.4" fill="none" stroke-linecap="round"/>'
            f'<path d="M5,-20 C-10,-26 -14,-38 -12,-44 C-2,-40 4,-30 5,-20Z" fill="#74c69d"/>'
            f'<path d="M8,-36 C22,-42 28,-54 26,-60 C14,-58 8,-48 8,-36Z" fill="#52b788"/>'
            f'<path d="M14,-64 C6,-74 8,-84 12,-88 C18,-80 18,-72 14,-64Z" fill="#95d5b2"/></g></g>')


def chip_w(t, size):
    return int(len(t) * size * 0.6) + 24


def chips(x, y, items, size=13, gap=8, maxw=None):
    out, cx, cy = "", x, y
    for t in items:
        w = chip_w(t, size)
        if maxw and cx + w > x + maxw:
            cx, cy = x, cy + size + 20
        out += (f'<rect x="{cx}" y="{cy}" width="{w}" height="{size+14}" rx="{(size+14)/2}" fill="{C["chip"]}"/>'
                f'<text x="{cx+w/2}" y="{cy+size+3}" font-size="{size}" fill="{C["chipt"]}" '
                f'text-anchor="middle" font-weight="600">{esc(t)}</text>')
        cx += w + gap
    return out


def text_w(s, size):
    """Rough rendered width, good enough to place text after a big number."""
    return sum(0.74 if c.isupper() else 0.32 if c in " ./" else 0.6 for c in s) * size


# ----------------------------------------------------------------- LOGOS
def logo(name, x, y, size):
    path = os.path.join(LOGOS, name)
    if name.endswith(".svg"):
        s = open(path, encoding="utf-8").read()
        vb = re.search(r'viewBox="([^"]+)"', s).group(1)
        inner = re.sub(r"^.*?<svg[^>]*>", "", s, flags=re.S).rsplit("</svg>", 1)[0]
        inner = re.sub(r"<title>.*?</title>|<metadata>.*?</metadata>", "", inner, flags=re.S)
        return f'<svg x="{x}" y="{y}" width="{size}" height="{size}" viewBox="{vb}">{inner}</svg>'
    from PIL import Image  # PNG / ICO -> 128px PNG, base64-embedded
    im = Image.open(path)
    if name.endswith(".ico"):
        im.size = max(im.info["sizes"])
    buf = io.BytesIO()
    im.convert("RGBA").resize((128, 128), Image.LANCZOS).save(buf, "PNG")
    b = base64.b64encode(buf.getvalue()).decode()
    return (f'<image x="{x}" y="{y}" width="{size}" height="{size}" '
            f'href="data:image/png;base64,{b}" xlink:href="data:image/png;base64,{b}"/>')


# ----------------------------------------------------------------- SCENE (header / footer)
SCENE_STYLE = """
.cloud{animation:drift linear infinite}
@keyframes drift{from{transform:translateX(-260px)}to{transform:translateX(1460px)}}
.fall{animation:fall linear infinite}
@keyframes fall{from{transform:translateY(-30px)}to{transform:translateY(350px)}}
.leaf{animation:leaf ease-in-out infinite;transform-box:fill-box;transform-origin:center}
@keyframes leaf{0%,100%{transform:translateX(0) rotate(-25deg)}50%{transform:translateX(34px) rotate(35deg)}}
.blade{animation:bend ease-in-out infinite alternate;transform-box:fill-box;transform-origin:bottom center}
@keyframes bend{from{transform:rotate(-6deg)}to{transform:rotate(7deg)}}
.sun{animation:glow 6s ease-in-out infinite alternate}
@keyframes glow{from{opacity:.55}to{opacity:.9}}
.rise{animation:rise 1.2s ease-out both}.rise2{animation:rise 1.2s .25s ease-out both}
@keyframes rise{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:none}}
"""


def blades(rng, y0, n, color, h, W=1200):
    out = ""
    for _ in range(n):
        x = rng.uniform(0, W); hh = rng.uniform(h * .6, h); lean = rng.uniform(-6, 6)
        d = rng.uniform(2.5, 4.5); dl = rng.uniform(0, 4)
        out += (f'<path class="blade" style="animation-duration:{d:.2f}s;animation-delay:-{dl:.2f}s" '
                f'd="M{x:.1f},{y0} q{lean/2:.1f},-{hh/2:.1f} {lean:.1f},-{hh:.1f} q-1,{hh/2:.1f} 3,{hh:.1f}Z" fill="{color}"/>')
    return out


def header():
    rng = random.Random(7)
    W, H = 1200, 320
    leaves = ""
    for _ in range(11):
        x = rng.randint(60, 1150); dur = rng.uniform(10, 17); delay = rng.uniform(0, 17)
        sc = rng.uniform(.7, 1.25); col = rng.choice(["#40916c", "#52b788", "#74c69d", "#2d6a4f", "#95d5b2"])
        sw = rng.uniform(3.5, 5.5)
        leaves += (f'<g transform="translate({x},0)"><g class="fall" style="animation-duration:{dur:.2f}s;animation-delay:-{delay:.2f}s">'
                   f'<g class="leaf" style="animation-duration:{sw:.2f}s"><g transform="scale({sc:.2f})">'
                   f'<path d="M0,-13 C9,-8 9,8 0,13 C-9,8 -9,-8 0,-13Z" fill="{col}"/>'
                   f'<path d="M0,-11 L0,11" stroke="#1b4332" stroke-opacity=".35" stroke-width="1"/></g></g></g></g>')

    def cloud(y, s, dur, delay, op):
        return (f'<g class="cloud" style="animation-duration:{dur}s;animation-delay:-{delay}s">'
                f'<g transform="translate(0,{y}) scale({s})" fill="#fff" opacity="{op}">'
                f'<ellipse cx="60" cy="30" rx="60" ry="18"/><circle cx="40" cy="20" r="20"/>'
                f'<circle cx="72" cy="12" r="26"/><circle cx="100" cy="24" r="16"/></g></g>')
    clouds = cloud(38, 1.1, 95, 10, .95) + cloud(80, .7, 70, 45, .85) + cloud(20, .55, 120, 80, .8) + cloud(110, .9, 85, 62, .9)
    defs = ('<defs><linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#c7ecfb"/>'
            '<stop offset=".65" stop-color="#e6f8f1"/><stop offset="1" stop-color="#f1fbf5"/></linearGradient>'
            '<radialGradient id="sun"><stop offset="0" stop-color="#fff9d6"/><stop offset=".35" stop-color="#fff3b8" stop-opacity=".8"/>'
            '<stop offset="1" stop-color="#fff3b8" stop-opacity="0"/></radialGradient>'
            '<clipPath id="r"><path d="M0,18 A18,18 0 0 1 18,0 H1182 A18,18 0 0 1 1200,18 V320 H0Z"/></clipPath></defs>')
    body = (f'<g clip-path="url(#r)"><rect width="{W}" height="{H}" fill="url(#sky)"/>'
            f'<circle class="sun" cx="1040" cy="70" r="120" fill="url(#sun)"/><circle cx="1040" cy="70" r="30" fill="#fff6c4"/>'
            f'{clouds}'
            f'<path d="M0,235 C180,190 330,215 480,228 C650,242 760,188 940,196 C1060,201 1140,222 1200,214 L1200,320 L0,320Z" fill="#b7e4c7"/>'
            f'<path d="M0,262 C150,236 300,250 430,258 C600,268 720,232 880,240 C1010,246 1110,262 1200,252 L1200,320 L0,320Z" fill="#95d5b2"/>'
            f'{leaves}'
            f'<text class="rise" x="64" y="118" font-size="58" font-weight="700" fill="#1b4332" letter-spacing="-1">{esc(NAME)}</text>'
            f'<text class="rise2" x="66" y="160" font-size="21" fill="#2d6a4f">{esc(TAGLINE)}</text>'
            f'<text class="rise2" x="66" y="190" font-size="17" fill="#40916c">{esc(SUBLINE)}</text>'
            f'<path d="M0,290 C200,272 380,282 560,286 C760,291 900,274 1060,278 C1130,280 1170,286 1200,284 L1200,320 L0,320Z" fill="#74c69d"/>'
            f'{blades(rng, 292, 70, "#52b788", 22)}'
            f'<path d="M0,306 C260,298 520,304 760,302 C960,300 1100,306 1200,304 L1200,320 L0,320Z" fill="#52b788"/>'
            f'{blades(rng, 310, 60, "#40916c", 16)}</g>')
    return svg(W, H, body, SCENE_STYLE, f"{NAME}: {TAGLINE}. {SUBLINE}", defs)


def footer():
    rng = random.Random(11)
    defs = '<defs><clipPath id="b"><path d="M0,0 H1200 V92 A18,18 0 0 1 1182,110 H18 A18,18 0 0 1 0,92Z"/></clipPath></defs>'
    body = (f'<g clip-path="url(#b)"><rect width="1200" height="110" fill="{C["sheet"]}"/><g transform="translate(0,20)">'
            f'<path d="M0,52 C200,36 400,48 600,50 C800,52 1000,38 1200,46 L1200,90 L0,90Z" fill="#b7e4c7"/>'
            f'{blades(rng, 60, 60, "#74c69d", 20)}'
            f'<path d="M0,66 C260,58 520,64 760,62 C960,60 1100,66 1200,64 L1200,90 L0,90Z" fill="#74c69d"/>'
            f'{blades(rng, 74, 70, "#52b788", 16)}'
            f'<path d="M0,78 C300,74 600,80 900,77 C1050,76 1150,79 1200,78 L1200,90 L0,90Z" fill="#52b788"/></g></g>')
    return svg(1200, 110, body, SCENE_STYLE, "", defs)


# ----------------------------------------------------------------- COMPONENTS (natural size)
def card(p):
    W, H = 600, 300
    b = panel(W, H)
    b += f'<rect x="30" y="30" width="72" height="72" rx="18" fill="#ffffff" stroke="{C["bd"]}" stroke-width="1.5"/>'
    b += logo(p["logo"], 38, 38, 56)
    b += f'<text x="122" y="62" font-size="27" font-weight="700" fill="{C["ink"]}">{esc(p["title"])}</text>'
    b += f'<text x="123" y="90" font-size="15" fill="{C["soft"]}">{esc(p["cat"])}</text>'
    b += f'<text x="556" y="62" font-size="22" fill="{C["acc"]}" text-anchor="end">↗</text>'
    for i, line in enumerate(p["desc"]):
        b += f'<text x="32" y="{140+i*24}" font-size="16" fill="{C["body"]}">{esc(line)}</text>'
    b += f'<line x1="32" y1="216" x2="568" y2="216" stroke="{C["bd"]}" stroke-width="1.5"/>'
    mf = 36 if len(p["metric"]) <= 6 else 26
    b += f'<text x="32" y="262" font-size="{mf}" font-weight="800" fill="{C["mid"]}" letter-spacing="-.5">{esc(p["metric"])}</text>'
    mx = int(text_w(p["metric"], mf)) + 48
    for i, line in enumerate(p["mlabel"]):
        b += f'<text x="{mx}" y="{246+i*19}" font-size="14" fill="{C["soft"]}">{esc(line)}</text>'
    cw = sum(chip_w(t, 12) for t in p["chips"]) + 8 * (len(p["chips"]) - 1)
    b += chips(568 - cw, 239, p["chips"], size=12)
    return svg(W, H, b, label=f'{p["title"]}: ' + " ".join(p["desc"]))


def about():
    W, H = 1200, 250
    b = panel(W, H)
    b += f'<text x="44" y="62" font-size="14" font-weight="700" fill="{C["acc"]}" letter-spacing="2">NOW</text>'
    for i, line in enumerate(NOW):
        b += f'<text x="44" y="{94+i*28}" font-size="19" fill="{C["ink"]}">{esc(line)}</text>'
    b += f'<text x="44" y="196" font-size="14" font-weight="700" fill="{C["acc"]}" letter-spacing="2">BEFORE</text>'
    b += f'<text x="44" y="224" font-size="17" fill="{C["body"]}">{esc(BEFORE)}</text>'
    for i, (n, u, s) in enumerate(STATS):
        y = 34 + i * 62
        b += (f'<rect x="806" y="{y}" width="350" height="52" rx="14" fill="#ffffff" stroke="{C["bd"]}" stroke-width="1.5"/>'
              f'<text x="826" y="{y+36}" font-size="28" font-weight="800" fill="{C["mid"]}">{esc(n)}</text>'
              f'<text x="914" y="{y+23}" font-size="14" font-weight="700" fill="{C["ink"]}">{esc(u)}</text>'
              f'<text x="914" y="{y+41}" font-size="13" fill="{C["soft"]}">{esc(s)}</text>')
    return svg(W, H, b, label=" ".join(NOW) + " " + BEFORE)


def section_label(text):
    b = (f'<g transform="translate(14,40)"><path d="M0,0 C4,-14 16,-22 26,-22 C24,-10 14,0 0,0Z" fill="#52b788"/>'
         f'<path d="M2,-2 L20,-18" stroke="#2d6a4f" stroke-width="1.5"/></g>'
         f'<text x="52" y="44" font-size="24" font-weight="700" fill="{C["mid"]}">{esc(text)}</text>'
         f'<path d="M{60+len(text)*14},36 C{400+len(text)*6},30 800,42 1186,34" stroke="#95d5b2" '
         f'stroke-width="2.5" fill="none" stroke-linecap="round"/>')
    return svg(1200, 70, b, label=text)


def research():
    W, H = 600, 320
    b = panel(W, H) + f'<text x="32" y="56" font-size="14" font-weight="700" fill="{C["acc"]}" letter-spacing="2">PAPERS · UNDER REVIEW</text>'
    for i, (t, lines, venue) in enumerate(PAPERS):
        y = 96 + i * 110
        b += f'<rect x="32" y="{y-22}" width="6" height="96" rx="3" fill="#95d5b2"/>'
        b += f'<text x="54" y="{y}" font-size="21" font-weight="700" fill="{C["ink"]}">{esc(t)}</text>'
        for j, line in enumerate(lines):
            b += f'<text x="54" y="{y+25+j*21}" font-size="15" fill="{C["body"]}">{esc(line)}</text>'
        b += f'<text x="54" y="{y+70}" font-size="13" font-style="italic" fill="{C["soft"]}">{esc(venue)}</text>'
    b += sprig(574, 320)
    return svg(W, H, b, SWAY, "Papers under review: " + ", ".join(p[0] for p in PAPERS))


def toolkit():
    W, H = 600, 320
    b = panel(W, H) + f'<text x="32" y="56" font-size="14" font-weight="700" fill="{C["acc"]}" letter-spacing="2">WHAT I REACH FOR</text>'
    for i, (g, items) in enumerate(TOOLKIT):
        y = 96 + i * 76
        b += f'<text x="32" y="{y}" font-size="15" font-weight="700" fill="{C["ink"]}">{esc(g)}</text>'
        b += chips(32, y + 12, items, size=14, maxw=536)
    b += sprig(574, 320)
    return svg(W, H, b, SWAY, "Toolkit: " + ", ".join(t for _, it in TOOLKIT for t in it))


ICONS = {
    "email": f'<g transform="translate(38,38)" fill="none" stroke="{C["mid"]}" stroke-width="2.4" stroke-linejoin="round"><rect width="28" height="20" rx="3"/><path d="M1,2 L14,12 L27,2"/></g>',
    "linkedin": f'<g transform="translate(37,33)"><rect width="30" height="30" rx="6" fill="{C["mid"]}"/><text x="15" y="23" font-size="19" font-weight="800" fill="#fff" text-anchor="middle">in</text></g>',
    "portfolio": f'<g transform="translate(52,48)" fill="none" stroke="{C["mid"]}" stroke-width="2.2"><circle r="14"/><ellipse rx="6" ry="14"/><path d="M-14,0 H14 M-12,-7 H12 M-12,7 H12"/></g>',
}


def contact_pill(key, title, sub):
    W, H = 390, 96
    b = (panel(W, H) + f'<circle cx="52" cy="48" r="26" fill="{C["chip"]}"/>{ICONS[key]}'
         f'<text x="94" y="44" font-size="19" font-weight="700" fill="{C["ink"]}">{esc(title)}</text>'
         f'<text x="94" y="68" font-size="13.5" fill="{C["soft"]}">{esc(sub)}</text>'
         f'<text x="356" y="56" font-size="20" fill="{C["acc"]}" text-anchor="end">↗</text>')
    return svg(W, H, b, label=f"{title}: {sub}")


# ----------------------------------------------------------------- TILING
# Every component is placed on a slab of sheet colour, so the README images
# butt together into one continuous sheet (README uses align="top" to remove
# the gap GitHub leaves under inline images).
def tile(component, TW, x, w, pad_t=12, pad_b=12, TH=None):
    ow, oh = map(float, re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', component).group(1, 2))
    h = w * oh / ow
    TH = TH or round(h + pad_t + pad_b, 2)
    label = re.search(r'aria-label="([^"]*)"', component).group(1)
    inner = re.sub(r"^<svg[^>]*>", "", component, count=1).rsplit("</svg>", 1)[0]
    return (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'viewBox="0 0 {TW} {TH:g}" width="{TW}" height="{TH:g}" role="img" aria-label="{label}">'
            f'<rect width="{TW}" height="{TH:g}" fill="{C["sheet"]}"/>'
            f'<svg x="{x}" y="{pad_t}" width="{w}" height="{h:.2f}" viewBox="0 0 {ow:g} {oh:g}" overflow="visible">{inner}</svg></svg>')


def main():
    os.makedirs(ASSETS, exist_ok=True)
    files = {}  # name -> svg text
    rows = []   # README rows: list of (file, width%, link or None, alt)

    def add(name, content, width, link=None):
        files[name] = content
        alt = re.search(r'aria-label="([^"]*)"', content).group(1)
        rows.append((name, width, link, alt))

    FULL = 1136  # inner width of full-width components (32px sheet margin each side)
    add("t-header.svg", header(), "100%")
    add("t-about.svg", tile(about(), 1200, 32, FULL, 16, 8), "100%")
    add("t-label-work.svg", tile(section_label("Selected work"), 1200, 32, FULL, 14, 0), "100%")
    for i, p in enumerate(PROJECTS):
        left = i % 2 == 0
        add(f"t-card-{p['slug']}.svg", tile(card(p), 600, 32 if left else 12, 556), "50%", p["url"])
    add("t-label-research.svg", tile(section_label("Research and toolkit"), 1200, 32, FULL, 14, 0), "100%")
    add("t-research.svg", tile(research(), 600, 32, 556), "50%")
    add("t-toolkit.svg", tile(toolkit(), 600, 12, 556), "50%")
    add("t-label-contact.svg", tile(section_label("Get in touch"), 1200, 32, FULL, 14, 0), "100%")
    # 3 buttons: widths 396/408/396 (33%/34%/33%) so they line up exactly
    PW = 352; TH = round(PW * 96 / 390 + 12 + 14, 2)
    for (key, title, sub, link), (TW, x, pct) in zip(CONTACT, [(396, 32, "33%"), (408, 28, "34%"), (396, 12, "33%")]):
        add(f"t-contact-{key}.svg", tile(contact_pill(key, title, sub), TW, x, PW, TH=TH), pct, link)
    add("t-footer.svg", footer(), "100%")

    for name, content in files.items():
        with open(os.path.join(ASSETS, name), "w", encoding="utf-8") as f:
            f.write(content)

    # One line, no whitespace between images: a space would push the
    # second half of a row onto the next line.
    parts = []
    for name, width, link, alt in rows:
        img = f'<img src="assets/{name}" width="{width}" align="top" alt="{alt}">'
        parts.append(f'<a href="{link}">{img}</a>' if link else img)
    readme = "<div>" + "".join(parts) + "</div>\n"
    with open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8") as f:
        f.write(readme)

    css = (".markdown-body{font:16px/1.5 -apple-system,Segoe UI,sans-serif;max-width:896px;margin:32px auto}"
           ".markdown-body img{max-width:100%;box-sizing:content-box}"
           "body{margin:0;background:#0d1117}body.light{background:#fff}"
           "button{position:fixed;top:12px;right:12px}")
    with open(os.path.join(ROOT, "preview.html"), "w", encoding="utf-8") as f:
        f.write(f'<!doctype html><meta charset="utf-8"><title>Profile preview</title><style>{css}</style>'
                f'<button onclick="document.body.classList.toggle(\'light\')">Toggle light / dark</button>'
                f'<article class="markdown-body">{readme}</article>')
    print(f"Wrote {len(files)} SVGs, README.md and preview.html in {ROOT}")


if __name__ == "__main__":
    main()
