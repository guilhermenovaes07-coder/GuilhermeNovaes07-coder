import json
import math
import os
import re
import urllib.request
from datetime import date

USER = os.environ.get("GH_USER", "guilhermenovaes07-coder")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
OUT = os.environ.get("OUT_DIR", "assets")
CACHE = os.path.join(OUT, "stats.json")

G = "#00ff41"
T = "#8dffa9"
M = "#00aa2b"
CARD = "#020a04"
FONT = "font-family:'SFMono-Regular',Consolas,'Liberation Mono',Menlo,'Courier New',monospace"
PALETTE = ["#00ff41", "#00e5ff", "#8dffa9", "#00aa2b", "#7cff00", "#2bd4a0"]


def http(url, api=False):
    headers = {"User-Agent": "Mozilla/5.0"}
    if api:
        headers["Accept"] = "application/vnd.github+json"
        if TOKEN:
            headers["Authorization"] = "Bearer " + TOKEN
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=30) as r:
        return r.read().decode()


def api(path):
    return json.loads(http("https://api.github.com" + path, True))


def calendar():
    html = http(f"https://github.com/users/{USER}/contributions")
    dates = {i: d for d, i in re.findall(r'data-date="([^"]+)"[^>]*?id="([^"]+)"', html)}
    days = []
    for i, text in re.findall(r'for="(contribution-day-component-[^"]+)"[^>]*>\s*([^<]+)', html):
        m = re.match(r"(\d+) contribution", text.strip())
        if i in dates:
            days.append((dates[i], int(m.group(1)) if m else 0))
    days = sorted(set(days))
    today = date.today().isoformat()
    return [x for x in days if x[0] <= today]


def streaks(days):
    longest = run = 0
    run_start = best_start = best_end = None
    for d, c in days:
        if c > 0:
            if run == 0:
                run_start = d
            run += 1
            if run > longest:
                longest, best_start, best_end = run, run_start, d
        else:
            run = 0
    cur = 0
    seq = days[:-1] if days and days[-1][1] == 0 else days
    for d, c in reversed(seq):
        if c > 0:
            cur += 1
        else:
            break
    return cur, longest, best_start, best_end


def fetch_stats():
    repos = api(f"/users/{USER}/repos?per_page=100&type=owner")
    langs = {}
    for r in repos:
        if r.get("fork"):
            continue
        for k, v in api(f"/repos/{USER}/{r['name']}/languages").items():
            langs[k] = langs.get(k, 0) + v
    return {
        "stars": sum(r["stargazers_count"] for r in repos),
        "commits": api(f"/search/commits?q=author:{USER}&per_page=1")["total_count"],
        "prs": api(f"/search/issues?q=author:{USER}+type:pr&per_page=1")["total_count"],
        "issues": api(f"/search/issues?q=author:{USER}+type:issue&per_page=1")["total_count"],
        "repos": len(repos),
        "langs": langs,
    }


def load_stats():
    try:
        s = fetch_stats()
        with open(CACHE, "w") as f:
            json.dump(s, f)
        return s
    except Exception as e:
        print("API indisponível, usando cache:", e)
        with open(CACHE) as f:
            return json.load(f)


def shell(w, h, title, body, anim=""):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">
<defs>
<pattern id="gr" width="16" height="16" patternUnits="userSpaceOnUse"><path d="M16 0H0V16" fill="none" stroke="{G}" stroke-opacity="0.05"/></pattern>
<linearGradient id="ar" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{G}" stop-opacity="0.35"/><stop offset="1" stop-color="{G}" stop-opacity="0"/></linearGradient>
<style>
.t{{{FONT}}}
.ln{{stroke-dasharray:1;stroke-dashoffset:1;animation:dr 2.2s ease forwards}}
.pu{{animation:pu 2s ease-in-out infinite}}
@keyframes dr{{to{{stroke-dashoffset:0}}}}
@keyframes pu{{50%{{opacity:.35}}}}
{anim}
</style>
</defs>
<rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" rx="10" fill="{CARD}" stroke="{G}" stroke-opacity="0.3"/>
<rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" rx="10" fill="url(#gr)"/>
<rect x="0" y="14" width="4" height="{h-28}" rx="2" fill="{G}"/>
<path d="M{w-34} 10 H{w-10} V34" fill="none" stroke="{G}" stroke-opacity="0.6" stroke-width="2"/>
<path d="M{w-34} {h-10} H{w-10} V{h-34}" fill="none" stroke="{G}" stroke-opacity="0.25" stroke-width="2"/>
<text class="t" x="24" y="36" font-size="16" font-weight="700" fill="{G}">{title}</text>
{body}
</svg>"""


def stats_card(s, days):
    total = sum(c for _, c in days)
    active = sum(1 for _, c in days if c > 0)
    frac = min(1, active / 365)
    circ = 2 * math.pi * 36
    rows = [("Total de estrelas", s["stars"]), ("Commits (total)", s["commits"]),
            ("Pull requests", s["prs"]), ("Issues", s["issues"]), ("Repositórios", s["repos"])]
    body = ""
    for i, (k, v) in enumerate(rows):
        y = 70 + i * 22
        body += f'<rect x="24" y="{y-9}" width="8" height="8" fill="none" stroke="{G}" stroke-width="1.5" transform="rotate(45 28 {y-5})"/>'
        body += f'<text class="t" x="44" y="{y}" font-size="13" fill="{T}">{k}:</text>'
        body += f'<text class="t" x="218" y="{y}" font-size="13" font-weight="700" fill="#ffffff" text-anchor="end">{v}</text>'
    body += f'<circle cx="320" cy="108" r="36" fill="none" stroke="{G}" stroke-opacity="0.15" stroke-width="7"/>'
    body += f'<circle cx="320" cy="108" r="36" fill="none" stroke="{G}" stroke-width="7" stroke-linecap="round" stroke-dasharray="{circ*frac:.1f} {circ:.1f}" transform="rotate(-90 320 108)"/>'
    body += f'<text class="t" x="320" y="113" font-size="17" font-weight="700" fill="#ffffff" text-anchor="middle">{total}</text>'
    body += f'<text class="t" x="320" y="156" font-size="10" fill="{M}" text-anchor="middle">contribuições / ano</text>'
    return shell(410, 180, "Estatísticas do GitHub", body)


def langs_card(s):
    langs = sorted(s["langs"].items(), key=lambda x: -x[1])
    tot = sum(v for _, v in langs) or 1
    top = langs[:6]
    body = f'<clipPath id="bc"><rect x="24" y="52" width="362" height="10" rx="5"/></clipPath><g clip-path="url(#bc)">'
    x = 24.0
    for i, (k, v) in enumerate(top):
        w = 362 * v / tot
        body += f'<rect x="{x:.1f}" y="52" width="{w+0.5:.1f}" height="10" fill="{PALETTE[i % len(PALETTE)]}"/>'
        x += w
    body += "</g>"
    for i, (k, v) in enumerate(top):
        col, row = divmod(i, 3)
        cx, y = 24 + col * 190, 92 + row * 26
        body += f'<circle cx="{cx+5}" cy="{y-4}" r="5" fill="{PALETTE[i % len(PALETTE)]}"/>'
        body += f'<text class="t" x="{cx+18}" y="{y}" font-size="13" fill="{T}">{k}</text>'
        body += f'<text class="t" x="{cx+168}" y="{y}" font-size="12" fill="{M}" text-anchor="end">{100*v/tot:.1f}%</text>'
    return shell(410, 180, "Linguagens mais usadas", body)


def fmt(d):
    return date.fromisoformat(d).strftime("%d/%m") if d else "-"


def streak_card(days):
    total = sum(c for _, c in days)
    cur, longest, bs, be = streaks(days)
    circ = 2 * math.pi * 42
    frac = min(1, cur / max(longest, 1))
    body = ""
    for x in (280, 560):
        body += f'<line x1="{x}" y1="52" x2="{x}" y2="140" stroke="{G}" stroke-opacity="0.2"/>'
    body += f'<text class="t" x="140" y="96" font-size="40" font-weight="700" fill="#ffffff" text-anchor="middle">{total}</text>'
    body += f'<text class="t" x="140" y="122" font-size="14" fill="{G}" text-anchor="middle">Contribuições</text>'
    body += f'<text class="t" x="140" y="140" font-size="11" fill="{M}" text-anchor="middle">último ano</text>'
    body += f'<circle cx="420" cy="86" r="42" fill="none" stroke="{G}" stroke-opacity="0.15" stroke-width="7"/>'
    body += f'<circle cx="420" cy="86" r="42" fill="none" stroke="{G}" stroke-width="7" stroke-linecap="round" stroke-dasharray="{circ*frac:.1f} {circ:.1f}" transform="rotate(-90 420 86)"/>'
    body += f'<text class="t" x="420" y="96" font-size="30" font-weight="700" fill="#ffffff" text-anchor="middle">{cur}</text>'
    body += f'<text class="t" x="420" y="148" font-size="14" fill="{G}" text-anchor="middle">Sequência atual</text>'
    body += f'<text class="t" x="700" y="96" font-size="40" font-weight="700" fill="{G}" text-anchor="middle">{longest}</text>'
    body += f'<text class="t" x="700" y="122" font-size="14" fill="{G}" text-anchor="middle">Maior sequência</text>'
    body += f'<text class="t" x="700" y="140" font-size="11" fill="{M}" text-anchor="middle">{fmt(bs)} - {fmt(be)}</text>'
    return shell(840, 164, "Sequência de contribuições", body)


MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]


def weekly(days):
    days = days[-364:]
    buckets = []
    for i in range(len(days) - 1, -1, -7):
        chunk = days[max(0, i - 6): i + 1]
        buckets.append((chunk[0][0], sum(c for _, c in chunk)))
    return buckets[::-1]


def activity_card(days):
    wk = weekly(days)
    vals = [v for _, v in wk]
    n = len(wk)
    ymax = max(4, math.ceil(max(vals) / 4) * 4)
    x0, x1, y0, y1 = 56, 810, 66, 196
    pts = [(x0 + i * (x1 - x0) / (n - 1), y1 - v * (y1 - y0) / ymax) for i, v in enumerate(vals)]
    sweep, hold = 14, 5
    total = sweep + hold
    kt = sweep / total
    xs, xe = x0 - 12, x1 + 12
    grid = ""
    for k in range(0, 5):
        v = ymax * k / 4
        y = y1 - v * (y1 - y0) / ymax
        grid += f'<line x1="{x0}" y1="{y:.1f}" x2="{x1}" y2="{y:.1f}" stroke="{G}" stroke-opacity="0.12" stroke-dasharray="3 5"/>'
        grid += f'<text class="t" x="{x0-10}" y="{y+4:.1f}" font-size="10" fill="{M}" text-anchor="end">{v:g}</text>'
    prev = None
    for (d, v), (x, y) in zip(wk, pts):
        m = date.fromisoformat(d).month
        if m != prev:
            grid += f'<text class="t" x="{x:.1f}" y="{y1+18}" font-size="10" fill="{M}" text-anchor="middle">{MESES[m-1]}</text>'
            prev = m
    line = " ".join(f"{'M' if i == 0 else 'L'}{x:.1f} {y:.1f}" for i, (x, y) in enumerate(pts))
    chart = f'<path d="{line} L{pts[-1][0]:.1f} {y1} L{pts[0][0]:.1f} {y1} Z" fill="url(#ar)"/>'
    chart += f'<path d="{line}" fill="none" stroke="{G}" stroke-width="2.5" stroke-linejoin="round" stroke-linecap="round"/>'
    for x, y in pts:
        chart += f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="#000000" stroke="{G}" stroke-width="1.6"/>'
    full = xe - xs
    clip = (f'<clipPath id="rv"><rect x="{xs}" y="40" width="0" height="190">'
            f'<animate attributeName="width" values="0;{full};{full}" keyTimes="0;{kt:.4f};1" dur="{total}s" repeatCount="indefinite"/>'
            f'</rect></clipPath>')
    times = [0.0] + [kt * (x - xs) / full for x, _ in pts] + [1.0]
    places = [pts[0]] + pts + [pts[-1]]
    kts = ";".join(f"{t:.4f}" for t in times)
    vls = ";".join(f"{x:.1f} {y:.1f}" for x, y in places)
    marker = (f'<g><animateTransform attributeName="transform" type="translate" values="{vls}" keyTimes="{kts}" dur="{total}s" repeatCount="indefinite"/>'
              f'<circle r="11" fill="{G}" opacity="0.25" class="pu"/><circle r="5.5" fill="{G}"/><circle r="2" fill="#ffffff"/></g>')
    right = f'<text class="t" x="810" y="36" font-size="12" fill="{M}" text-anchor="end">{sum(vals)} contribuições em 12 meses</text>'
    body = clip + grid + f'<g clip-path="url(#rv)">{chart}{marker}</g>' + right
    return shell(840, 232, "Atividade no último ano", body)


def main():
    os.makedirs(OUT, exist_ok=True)
    days = calendar()
    s = load_stats()
    files = {
        "stats.svg": stats_card(s, days),
        "languages.svg": langs_card(s),
        "streak.svg": streak_card(days),
        "activity.svg": activity_card(days),
    }
    for name, svg in files.items():
        with open(os.path.join(OUT, name), "w") as f:
            f.write(svg)
    print("ok", len(days), "dias")


main()
