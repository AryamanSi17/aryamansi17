#!/usr/bin/env python3
"""Render the README's animated SVG cards from data/contributions.json.

    python3 scripts/render_readme_cards.py           # animated
    STATIC=1 python3 scripts/render_readme_cards.py  # final frame only, for screenshots

Stdlib only. Fonts come from fonts/*.woff (subset with pyftsubset), embedded as data URIs.
"""
import base64
import datetime as dt
import json
import os
from collections import defaultdict
from xml.sax.saxutils import escape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC = os.environ.get("STATIC") == "1"

NAME = ("Aryaman", "Sinha")
TAGLINE = "AI Applications Engineer in Bengaluru"
SUB = "MERN by day, Gen AI apps by night. Always a student."

PAPER, INK, MUTED, LINE = "#FAF7F2", "#1C1B18", "#6F6A60", "#E6E0D4"
BLUE, RED, YELLOW = "#2457F5", "#E0423A", "#F2B826"


def font_css():
    out = []
    for fam, weight, fn in (("Instrument Serif", 400, "serif"), ("Geist", 400, "sans"), ("Geist", 500, "sans500")):
        with open(os.path.join(ROOT, "fonts", fn + ".woff"), "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        out.append(f"@font-face{{font-family:'{fam}';font-weight:{weight};src:url(data:font/woff;base64,{b64})}}")
    return "".join(out)


FONTS = font_css()

# One shared keyframe set. Every animated element's *natural* state is its end state and the
# keyframes start from the hidden state (fill-mode: backwards), so STATIC and reduced-motion
# just drop the animation.
KEYFRAMES = """
@keyframes rise{from{opacity:0;transform:translateY(14px)}}
@keyframes pop{from{opacity:0;transform:scale(.4)}60%{opacity:1;transform:scale(1.15)}}
@keyframes grow{from{transform:scaleY(0)}}
@keyframes swing{from{opacity:0;transform:translateY(40px) rotate(-3deg)}60%{opacity:1;transform:translateY(-6px) rotate(1deg)}}
@keyframes ring{from{opacity:.8;transform:scale(.2)}to{opacity:0;transform:scale(2.4)}}
@keyframes nudge{0%,80%,100%{transform:translate(0,0)}90%{transform:translate(3px,-3px)}}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.25}}
@keyframes fadein{from{opacity:0}}
text{font-family:'Geist',system-ui,sans-serif}
.serif{font-family:'Instrument Serif',Georgia,serif}
.a{animation-fill-mode:backwards;animation-timing-function:cubic-bezier(.2,.7,.2,1)}
.rise{animation-name:rise;animation-duration:.7s}
.pop{animation-name:pop;animation-duration:.5s}
.fade{animation-name:fadein;animation-duration:.6s}
.grow{animation-name:grow;animation-duration:.8s;transform-box:fill-box;transform-origin:bottom}
.swing{animation-name:swing;animation-duration:.9s;transform-box:fill-box;transform-origin:center bottom}
.ring{animation:ring 1.6s ease-out infinite;transform-box:fill-box;transform-origin:center}
.nudge{animation:nudge 3s ease-in-out infinite}
.dot{animation:blink 2s ease-in-out infinite}
.static{display:none}
@media(prefers-reduced-motion:reduce){*{animation:none!important}.anim{display:none}.static{display:inline}}
"""
if STATIC:
    KEYFRAMES += "*{animation:none!important}.anim{display:none}.static{display:inline}"


def svg(w, h, body, extra_css=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'font-size="14" fill="{INK}">'
            f"<style>{FONTS}{KEYFRAMES}{extra_css}</style>{body}</svg>")


def card(w, h, body, extra_css=""):
    frame = f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="14" fill="{PAPER}" stroke="{LINE}"/>'
    return svg(w, h, frame + body, extra_css)


def delay(s):
    return f'style="animation-delay:{s:.2f}s"'


def shine_gradient(gid, base, color, period=6, begin=0):
    """Gradient of `base` with a stripe of `color` that sweeps across whatever uses fill=url(#gid).
    Starts parked off the left edge, so STATIC and reduced-motion show plain `base`."""
    anim = "" if STATIC else (
        f'<animateTransform attributeName="gradientTransform" type="translate" from="-1 0" to="2 0" '
        f'dur="{period}s" begin="{begin}s" repeatCount="indefinite"/>')
    return (f'<linearGradient id="{gid}" x1="0" x2="1" y1="0" y2="0" gradientTransform="translate(-1 0)">'
            f'<stop offset="0" stop-color="{base}"/><stop offset=".45" stop-color="{base}"/>'
            f'<stop offset=".5" stop-color="{color}"/><stop offset=".55" stop-color="{base}"/>'
            f'<stop offset="1" stop-color="{base}"/>{anim}</linearGradient>')


def countup(x, y, value, begin, cls="", attrs="", frames=18, dur=0.9):
    """Text that counts up to `value` with SMIL <set> frames; the final value in a .static twin."""
    final = f'<text class="static {cls}" x="{x}" y="{y}" {attrs}>{value:,}</text>'
    if STATIC:
        return final
    step = dur / frames
    parts = []
    for i in range(frames + 1):
        v = round(value * (1 - (1 - i / frames) ** 3))  # ease-out
        last = i == frames
        parts.append(
            f'<text class="{cls}" x="{x}" y="{y}" {attrs} opacity="0">{v:,}'
            f'<set attributeName="opacity" to="1" begin="{begin + i * step:.3f}s" '
            + ('fill="freeze"' if last else f'dur="{step:.3f}s"') + "/></text>")
    return f'<g class="anim">{"".join(parts)}</g>{final}'


# ---------------------------------------------------------------- data

def load():
    with open(os.path.join(ROOT, "data", "contributions.json")) as f:
        u = json.load(f)["data"]["user"]
    cal = u["contributionsCollection"]["contributionCalendar"]
    days = [(dt.date.fromisoformat(d["date"]), d["contributionCount"])
            for w in cal["weeks"] for d in w["contributionDays"]]
    weeks = [[(dt.date.fromisoformat(d["date"]), d["contributionCount"]) for d in w["contributionDays"]]
             for w in cal["weeks"]]
    return u, cal["totalContributions"], days, weeks


def stats(days):
    active = sum(1 for _, c in days if c)
    busiest = max(days, key=lambda d: d[1])
    longest = cur = run = 0
    for _, c in days:
        run = run + 1 if c else 0
        longest = max(longest, run)
    # current streak: count back from today (or yesterday if today is empty)
    tail = [c for _, c in days]
    if tail and tail[-1] == 0:
        tail = tail[:-1]
    for c in reversed(tail):
        if not c:
            break
        cur += 1
    months = defaultdict(int)
    for d, c in days:
        months[d.strftime("%Y-%m")] += c
    keys = sorted(months)[-12:]
    return dict(active=active, busiest=busiest, longest=longest, current=cur,
                months=[(k, months[k]) for k in keys])


# ---------------------------------------------------------------- cards

def hero():
    W, H = 1200, 300
    gid = shine_gradient("shine", INK, BLUE, period=5, begin=1.5)
    first, last = NAME
    body = f"<defs>{gid}</defs>"
    body += (f'<text class="serif a rise" {delay(0.1)} x="56" y="128" font-size="104">{first}</text>'
             f'<text class="serif a rise" {delay(0.3)} x="56" y="222" font-size="104" fill="url(#shine)">{last}</text>')
    body += (f'<g class="a rise" {delay(0.6)}>'
             f'<circle class="dot" cx="62" cy="261" r="5" fill="{BLUE}"/>'
             f'<text x="78" y="266" font-size="18" fill="{MUTED}">{escape(TAGLINE)}</text></g>')
    # right column: three worlds legend
    x = 860
    for i, (label, col) in enumerate((("BUILD", BLUE), ("CREATE", RED), ("CONNECT", YELLOW))):
        y = 96 + i * 52
        body += (f'<g class="a rise" {delay(0.5 + i * 0.15)}>'
                 f'<rect x="{x}" y="{y - 14}" width="18" height="18" rx="4" fill="{col}"/>'
                 f'<text x="{x + 32}" y="{y}" font-size="16" font-weight="500" letter-spacing="2">{label}</text></g>')
    body += (f'<text class="a fade" {delay(1.0)} x="{W - 56}" y="262" font-size="15" text-anchor="end" fill="{MUTED}">{escape(SUB)}</text>')
    return card(W, H, body)


def graph(weeks, total):
    W = 1200
    cell, gap, left, top = 15, 4, 56, 64
    H = top + 7 * (cell + gap) + 46
    body = (f'<text class="a rise" x="{left}" y="38" font-size="15" font-weight="500" letter-spacing="2">CONTRIBUTIONS</text>'
            f'<text class="a rise serif" x="{W - 56}" y="42" text-anchor="end" font-size="30">{total:,} '
            f'<tspan font-size="16" font-family="Geist" fill="{MUTED}">in the last year</tspan></text>')
    peak = max((c for w in weeks for _, c in w), default=1) or 1
    shades = ["#EDE8DE", "#B9CBFB", "#7A9BF8", "#4571F6", BLUE]
    cols = len(weeks)
    span = (W - 2 * left - cell) / max(cols - 1, 1)
    seen_month = None
    for wi, w in enumerate(weeks):
        x = left + wi * span
        for d, c in w:
            if d.day <= 7 and d.strftime("%b") != seen_month:
                seen_month = d.strftime("%b")
                body += f'<text class="a fade" {delay(0.6 + wi * 0.03)} x="{x:.1f}" y="{top - 10}" font-size="11" fill="{MUTED}">{seen_month}</text>'
            y = top + d.weekday() * (cell + gap)
            lvl = 0 if c == 0 else min(4, 1 + int(3 * c / peak))
            body += (f'<rect class="a pop" style="animation-delay:{0.4 + wi * 0.03 + d.weekday() * 0.01:.2f}s;'
                     f'transform-box:fill-box;transform-origin:center" x="{x:.1f}" y="{y}" width="{cell}" height="{cell}" rx="3" fill="{shades[lvl]}"/>')
    ly = H - 18
    body += f'<text class="a fade" {delay(2.2)} x="{left}" y="{ly}" font-size="11" fill="{MUTED}">Less</text>'
    for i, s in enumerate(shades):
        body += f'<rect class="a fade" {delay(2.2)} x="{left + 36 + i * 17}" y="{ly - 10}" width="12" height="12" rx="3" fill="{s}"/>'
    body += f'<text class="a fade" {delay(2.2)} x="{left + 36 + 5 * 17 + 4}" y="{ly}" font-size="11" fill="{MUTED}">More</text>'
    return card(W, H, body)


def activity(st, total):
    W, H = 1200, 340
    left, base, bar_w, chart_w = 56, 230, 52, 760
    months = st["months"]
    peak = max(c for _, c in months) or 1
    best = max(range(len(months)), key=lambda i: months[i][1])
    body = f'<text class="a rise" x="{left}" y="38" font-size="15" font-weight="500" letter-spacing="2">BY MONTH</text>'
    step = chart_w / len(months)
    for i, (k, c) in enumerate(months):
        x = left + i * step
        h = max(4, 150 * c / peak)
        col = BLUE if i == best else "#D9D2C4"
        body += f'<rect class="a grow" {delay(2.4 + i * 0.06)} x="{x:.1f}" y="{base - h:.1f}" width="{bar_w}" height="{h:.1f}" rx="6" fill="{col}"/>'
        mon = dt.date.fromisoformat(k + "-01").strftime("%b")
        body += f'<text class="a fade" {delay(2.4 + i * 0.06)} x="{x + bar_w / 2:.1f}" y="{base + 22}" font-size="12" text-anchor="middle" fill="{MUTED}">{mon}</text>'
        if i == best:
            body += (f'<text class="a pop" style="animation-delay:3.3s;transform-box:fill-box;transform-origin:center bottom" '
                     f'x="{x + bar_w / 2:.1f}" y="{base - h - 12:.1f}" font-size="18" font-weight="500" text-anchor="middle" fill="{BLUE}">{c:,}</text>')
    # stats column
    sx = left + chart_w + 70
    rows = [("Current streak", f"{st['current']} days"), ("Longest streak", f"{st['longest']} days"),
            ("Active days", f"{st['active']} of 365"),
            ("Busiest day", f"{st['busiest'][1]} on {st['busiest'][0].strftime('%-d %b')}")]
    body += f'<line x1="{sx - 34}" y1="30" x2="{sx - 34}" y2="{H - 30}" stroke="{LINE}"/>'
    for i, (label, val) in enumerate(rows):
        y = 64 + i * 66
        body += (f'<g class="a rise" {delay(2.8 + i * 0.12)}>'
                 f'<text x="{sx}" y="{y}" font-size="12" letter-spacing="1.5" fill="{MUTED}">{label.upper()}</text>'
                 f'<text class="serif" x="{sx}" y="{y + 32}" font-size="30">{escape(val)}</text></g>')
    return card(W, H, body)


def tile(label, color, big, small, line, href_hint, begin, number=None):
    W, H = 390, 250
    gid = shine_gradient(f"sh_{label}", color, "#FFFFFF", period=7, begin=begin + 2)
    css = f'#t_{label} .shine{{fill:url(#sh_{label})}}'
    body = f"<defs>{gid}</defs>"
    body += f'<g id="t_{label}" class="a swing" {delay(begin)}>'
    body += f'<rect x="10" y="10" width="{W - 20}" height="{H - 20}" rx="16" fill="{color}"/>'
    body += (f'<circle class="ring" style="animation-delay:{begin + 0.5}s" cx="{W - 46}" cy="46" r="10" '
             f'fill="none" stroke="#fff" stroke-width="2"/>')
    tc = "#fff" if color != YELLOW else INK
    body += f'<text x="34" y="52" font-size="14" font-weight="500" letter-spacing="3" fill="{tc}" opacity=".85">{label}</text>'
    if number is not None:
        body += countup(34, 140, number, begin + 0.4, cls="serif", attrs=f'font-size="84" fill="{tc}"')
    else:
        body += f'<text class="serif" x="34" y="140" font-size="60" fill="{tc}">{escape(big)}</text>'
    body += f'<text x="34" y="176" font-size="16" fill="{tc}" opacity=".9">{escape(small)}</text>'
    body += (f'<text x="34" y="214" font-size="13" fill="{tc}" opacity=".7">{escape(line)}</text>'
             f'<text class="nudge" x="{W - 34}" y="216" font-size="22" text-anchor="end" fill="{tc}">&#8599;</text>')
    # sweep highlight over the whole tile
    body += f'<rect x="10" y="10" width="{W - 20}" height="{H - 20}" rx="16" class="shine" opacity=".35"/>'
    body += "</g>"
    return svg(W, H, body, css)


def repo_card(r, begin):
    W, H = 590, 150
    lang = r.get("primaryLanguage") or {}
    desc = (r.get("description") or "").strip()
    if len(desc) > 72:
        desc = desc[:70].rsplit(" ", 1)[0] + "…"
    body = f'<g class="a rise" {delay(begin)}>'
    body += f'<text class="serif" x="36" y="56" font-size="30">{escape(r["name"])}</text>'
    body += f'<text x="36" y="86" font-size="14" fill="{MUTED}">{escape(desc)}</text>'
    y = 120
    if lang:
        body += (f'<circle cx="42" cy="{y - 5}" r="5" fill="{lang.get("color") or MUTED}"/>'
                 f'<text x="54" y="{y}" font-size="13" fill="{MUTED}">{escape(lang["name"])}</text>')
    body += (f'<text x="{W - 36}" y="{y}" font-size="13" text-anchor="end" fill="{MUTED}">'
             f'&#9733; {r["stargazerCount"]}</text></g>')
    body += f'<text class="nudge" x="{W - 36}" y="58" font-size="20" text-anchor="end" fill="{BLUE}">&#8599;</text>'
    return card(W, H, body)


# ---------------------------------------------------------------- main

def write(name, content):
    path = os.path.join(ROOT, "cards", name)
    with open(path, "w") as f:
        f.write(content)
    print(f"{name:14} {len(content) // 1024:4} KB")


def main():
    user, total, days, weeks = load()
    st = stats(days)
    os.makedirs(os.path.join(ROOT, "cards"), exist_ok=True)
    write("hero.svg", hero())
    write("graph.svg", graph(weeks, total))
    write("activity.svg", activity(st, total))
    repos = user["repositories"]
    write("build.svg", tile("BUILD", BLUE, "", "public repos", "Projects, tools, experiments", "repos", 3.6, number=repos["totalCount"]))
    write("create.svg", tile("CREATE", RED, "@ai_aryaman", "Reels about AI tools", "The tools I actually use, daily", "ig", 3.75))
    write("connect.svg", tile("CONNECT", YELLOW, "LinkedIn", "Say hi, I reply", "Work, collabs, questions", "li", 3.9))
    featured = [r for r in repos["nodes"] if r.get("description")][:4]
    for i, r in enumerate(featured):
        write(f"repo-{i + 1}.svg", repo_card(r, 4.4 + i * 0.15))
    readme(featured)


README = """<a href="https://github.com/AryamanSi17"><img src="./cards/hero.svg" width="100%" alt="Aryaman Sinha, AI Applications Engineer in Bengaluru" /></a>

<a href="https://github.com/AryamanSi17"><img src="./cards/graph.svg" width="100%" alt="Contribution graph" /></a>
<a href="https://github.com/AryamanSi17"><img src="./cards/activity.svg" width="100%" alt="Contributions by month" /></a>

<a href="https://github.com/AryamanSi17?tab=repositories"><img src="./cards/build.svg" width="32.5%" alt="Build" /></a>
<a href="https://www.instagram.com/ai_aryaman/"><img src="./cards/create.svg" width="32.5%" alt="Create" /></a>
<a href="https://www.linkedin.com/in/aryamansi1712/"><img src="./cards/connect.svg" width="32.5%" alt="Connect" /></a>

{repos}

### Hi, I'm Aryaman Sinha

AI Applications Engineer in Bengaluru. I build open-source developer tools with **Claude Code** and Python, mostly stdlib-first CLIs that do one job well, and I post a short Reel every day about an AI tool I actually use at [@ai_aryaman](https://www.instagram.com/ai_aryaman/).

- **Build:** Claude Code skills and CLIs, Gen AI apps, MERN and Next.js products. Start with [claude-watermark-remover](https://github.com/AryamanSi17/claude-watermark-remover) or [tv-debloat](https://github.com/AryamanSi17/tv-debloat).
- **Create:** daily AI tool Reels, guides and carousels, made with [content-desk](https://github.com/AryamanSi17/content-desk).
- **Connect:** [LinkedIn](https://www.linkedin.com/in/aryamansi1712/), [X](https://twitter.com/Aryaman1702), [aryaman.club](https://aryaman.club). Open to collabs on AI tooling and developer content.

<p align="center"><sub>
<a href="https://www.instagram.com/ai_aryaman/">Instagram</a> ·
<a href="https://www.linkedin.com/in/aryamansi1712/">LinkedIn</a> ·
<a href="https://twitter.com/Aryaman1702">X</a>
&nbsp;&nbsp;&nbsp;cards redrawn daily by <a href="./scripts/render_readme_cards.py">one Python script</a>
</sub></p>
"""


def readme(featured):
    rows = "\n".join(f'<a href="{r["url"]}"><img src="./cards/repo-{i + 1}.svg" width="49%" alt="{escape(r["name"])}" /></a>'
                     for i, r in enumerate(featured))
    with open(os.path.join(ROOT, "README.md"), "w") as f:
        f.write(README.format(repos=rows))
    print("README.md")


if __name__ == "__main__":
    main()
