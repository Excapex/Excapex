"""Generates dark_mode.svg / light_mode.svg — a neofetch-style profile card.

Runs daily in GitHub Actions (see .github/workflows/build.yml). Needs a
classic PAT in env ACCESS_TOKEN (scopes: repo, read:user) so private
contributions and lines-of-code from private repos are counted.
Local dry run without a token: `python today.py --offline`.
"""
import datetime as dt
import html
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

USER = "Excapex"
BIRTHDAY = dt.date(2004, 7, 2)
HERE = Path(__file__).parent
WIDTH = 60  # characters in the info column

INFO = [
    ("title", "sergej@stojanovic"),
    ("OS", "Windows 11, Linux, Android"),
    ("Uptime", "{uptime}"),
    ("Host", "PMF Novi Sad, BSc Information Technologies"),
    ("Kernel", "Full-stack developer, product builder"),
    ("IDE", "IntelliJ IDEA, VS Code, Claude Code"),
    ("gap", ""),
    ("Languages.Programming", "Java, TypeScript, Python, C"),
    ("Languages.Stack", "Spring Boot, Next.js, PostgreSQL"),
    ("Languages.Real", "Serbian, English (C1)"),
    ("gap", ""),
    ("Projects.Shipping", "Glamour, EvidLab, Saglasnik"),
    ("Hobbies", "Rowing, choir, guitar, investing"),
    ("section", "Contact"),
    ("Email", "sergej.stojanovic.04.ns@gmail.com"),
    ("LinkedIn", "sergej-stojanovic-4a875836a"),
    ("section", "GitHub Stats"),
    ("stats1", ""),
    ("stats2", ""),
    ("stats3", ""),
]

THEMES = {
    "dark": dict(bg="#161b22", fg="#c9d1d9", key="#ffa657", val="#a5d6ff", dim="#616e7f", add="#3fb950", rem="#f85149"),
    "light": dict(bg="#f6f8fa", fg="#24292f", key="#953800", val="#0a3069", dim="#c2cfde", add="#1a7f37", rem="#cf222e"),
}


def uptime(today=None):
    today = today or dt.date.today()
    y = today.year - BIRTHDAY.year
    m = today.month - BIRTHDAY.month
    d = today.day - BIRTHDAY.day
    if d < 0:
        m -= 1
        prev_month_end = today.replace(day=1) - dt.timedelta(days=1)
        d += prev_month_end.day
    if m < 0:
        y -= 1
        m += 12
    plural = lambda n, w: f"{n} {w}{'' if n == 1 else 's'}"
    return f"{plural(y, 'year')}, {plural(m, 'month')}, {plural(d, 'day')}"


def gh(query, variables, token):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={"Authorization": f"bearer {token}"},
    )
    with urllib.request.urlopen(req) as r:
        body = json.load(r)
    if "errors" in body:
        raise RuntimeError(body["errors"])
    return body["data"]


def rest(path, token):
    req = urllib.request.Request(f"https://api.github.com{path}", headers={"Authorization": f"token {token}"})
    with urllib.request.urlopen(req) as r:
        return r.status, (json.load(r) if r.status == 200 else None)


def fetch_stats(token):
    q = """query($login:String!){ user(login:$login){
        followers{totalCount}
        repositories(ownerAffiliations:OWNER, first:100){ totalCount nodes{ nameWithOwner stargazerCount } }
        repositoriesContributedTo(contributionTypes:[COMMIT,PULL_REQUEST,REPOSITORY], first:1){ totalCount }
        contributionsCollection{ totalCommitContributions restrictedContributionsCount }
    }}"""
    u = gh(q, {"login": USER}, token)["user"]
    repos = u["repositories"]["nodes"]
    add = rem = commits = 0
    for repo in repos:
        # the stats endpoint answers 202 while GitHub computes; retry a few times
        for _ in range(5):
            status, data = rest(f"/repos/{repo['nameWithOwner']}/stats/contributors", token)
            if status == 200:
                break
            time.sleep(3)
        for c in data or []:
            if c.get("author") and c["author"]["login"].lower() == USER.lower():
                commits += c["total"]
                for w in c["weeks"]:
                    add += w["a"]
                    rem += w["d"]
    return dict(
        repos=u["repositories"]["totalCount"],
        contributed=u["repositoriesContributedTo"]["totalCount"],
        stars=sum(r["stargazerCount"] for r in repos),
        followers=u["followers"]["totalCount"],
        commits=commits,
        loc_add=add,
        loc_rem=rem,
    )


def ascii_art():
    path = HERE / "ascii.txt"
    if path.exists():
        return path.read_text(encoding="utf-8").rstrip("\n").splitlines()
    return MONOGRAM


MONOGRAM = ["(run ascii.py to generate the portrait)"]


def leader(key, value, width=WIDTH):
    dots = width - len(key) - len(value) - 4
    return key, "." * max(dots, 1), value


def svg(theme, stats):
    t = THEMES[theme]
    art = ascii_art()
    e = html.escape
    lines = []
    y0, lh = 30, 20
    for i, row in enumerate(art):
        lines.append(f'<tspan x="15" y="{y0 + i * lh}">{e(row)}</tspan>')
    right = []
    y = y0
    for key, value in INFO:
        if key == "title":
            right.append(f'<tspan x="390" y="{y}">{e(value)}</tspan> -{"—" * (WIDTH - len(value) - 2)}')
        elif key == "section":
            right.append(f'<tspan x="390" y="{y}">- {e(value)}</tspan> -{"—" * (WIDTH - len(value) - 4)}')
        elif key == "gap":
            right.append(f'<tspan x="390" y="{y}" class="cc">. </tspan>')
        elif key.startswith("stats"):
            right.append(stats_line(key, stats, y))
        else:
            value = value.format(uptime=uptime())
            k, dots, v = leader(key, value)
            right.append(
                f'<tspan x="390" y="{y}" class="cc">. </tspan><tspan class="key">{e(k)}</tspan>:'
                f'<tspan class="cc"> {dots} </tspan><tspan class="value">{e(v)}</tspan>'
            )
        y += lh
    height = max(y0 + len(art) * lh, y) + 10
    return f"""<?xml version='1.0' encoding='UTF-8'?>
<svg xmlns="http://www.w3.org/2000/svg" font-family="ConsolasFallback,Consolas,monospace" width="985px" height="{height}px" font-size="16px">
<style>
@font-face {{ src: local('Consolas'), local('Consolas Bold'); font-family: 'ConsolasFallback'; font-display: swap; -webkit-size-adjust: 109%; size-adjust: 109%; }}
.key {{fill: {t['key']};}} .value {{fill: {t['val']};}} .addColor {{fill: {t['add']};}} .delColor {{fill: {t['rem']};}}
.cc {{fill: {t['dim']};}} text, tspan {{white-space: pre;}}
</style>
<rect width="985px" height="{height}px" fill="{t['bg']}" rx="15"/>
<text x="15" y="30" fill="{t['fg']}" class="ascii">{''.join(lines)}</text>
<text x="390" y="30" fill="{t['fg']}">{''.join(right)}</text>
</svg>
"""


def stats_line(key, s, y):
    fmt = lambda n: f"{n:,}" if isinstance(n, int) else str(n)
    if key == "stats1":
        a, b = f"{fmt(s['repos'])} {{Contributed: {fmt(s['contributed'])}}}", fmt(s["stars"])
        return (f'<tspan x="390" y="{y}" class="cc">. </tspan><tspan class="key">Repos</tspan>:<tspan class="cc"> .... </tspan>'
                f'<tspan class="value">{a}</tspan> | <tspan class="key">Stars</tspan>:<tspan class="cc"> ...... </tspan><tspan class="value">{b}</tspan>')
    if key == "stats2":
        return (f'<tspan x="390" y="{y}" class="cc">. </tspan><tspan class="key">Commits</tspan>:<tspan class="cc"> ....... </tspan>'
                f'<tspan class="value">{fmt(s["commits"])}</tspan> | <tspan class="key">Followers</tspan>:<tspan class="cc"> .. </tspan>'
                f'<tspan class="value">{fmt(s["followers"])}</tspan>')
    net = s["loc_add"] - s["loc_rem"] if isinstance(s["loc_add"], int) else "?"
    return (f'<tspan x="390" y="{y}" class="cc">. </tspan><tspan class="key">Lines of Code</tspan>:<tspan class="cc"> .. </tspan>'
            f'<tspan class="value">{fmt(net)}</tspan> ( <tspan class="addColor">{fmt(s["loc_add"])}++</tspan>, '
            f'<tspan class="delColor">{fmt(s["loc_rem"])}--</tspan> )')


def main():
    offline = "--offline" in sys.argv
    token = os.environ.get("ACCESS_TOKEN")
    if not token and os.environ.get("CI"):
        # without the PAT only public stats are visible; keep the committed card instead
        print("ACCESS_TOKEN not set, skipping refresh")
        return
    if offline or not token:
        stats = dict(repos="?", contributed="?", stars="?", followers="?", commits="?", loc_add="?", loc_rem="?")
    else:
        stats = fetch_stats(token)
    for theme in THEMES:
        (HERE / f"{theme}_mode.svg").write_text(svg(theme, stats), encoding="utf-8")
    print("written", stats)


if __name__ == "__main__":
    main()
