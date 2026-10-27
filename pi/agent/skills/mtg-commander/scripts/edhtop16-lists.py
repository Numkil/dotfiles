#!/usr/bin/env python3
"""Download tournament decklists for one or more commanders from EDHTop16.

EDHTop16's GraphQL API only accepts persisted queries, so this scrapes the
server-rendered HTML instead. Each commander page links to at most 48 recent
decklists; each decklist page embeds the card list as JSON.

Usage:
  python3 -I edhtop16-lists.py "Tasigur, the Golden Fang" [more commanders...] \
      [--period ONE_YEAR] [--min-size 16] [--out lists.json]

Partner pairs use " / " between names, e.g. "Thrasios, Triton Hero / Tymna the Weaver".
Output: JSON {commander: [{link, player, standing, size, date, cards: [...]}, ...]}
"""
import argparse, json, re, sys, time, urllib.parse, urllib.request

UA = {"User-Agent": "Mozilla/5.0"}
CARD_RE = re.compile(r'\{"count":\d+,"spice":[^,]*,"commanderPlayRate":[^,]*,"card":\{"id":"[^"]*","name":"((?:[^"\\]|\\.)*)"')


def get(url):
    for _ in range(3):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30).read().decode("utf-8", "replace")
        except Exception:
            time.sleep(2)
    return ""


def field(pattern, html, cast=str):
    m = re.search(pattern, html)
    return cast(m.group(1)) if m else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("commanders", nargs="+")
    ap.add_argument("--period", default="ONE_YEAR", help="ONE_MONTH, THREE_MONTHS, SIX_MONTHS, ONE_YEAR, ALL_TIME")
    ap.add_argument("--min-size", type=int, default=16, help="minimum event size")
    ap.add_argument("--out", default="-")
    args = ap.parse_args()

    result = {}
    for name in args.commanders:
        url = (f"https://edhtop16.com/commander/{urllib.parse.quote(name, safe='')}"
               f"?timePeriod={args.period}&sortBy=NEW&minEventSize={args.min_size}")
        links = sorted(set(re.findall(r'/tournament/[^"\\]*/decklist/[^"\\]*', get(url))))
        print(f"{name}: {len(links)} decklists", file=sys.stderr)
        decks = []
        for link in links:
            html = get("https://edhtop16.com" + link)
            time.sleep(0.25)
            cards = sorted({json.loads('"' + n + '"') for n in CARD_RE.findall(html)})
            decks.append({
                "link": link,
                "player": field(r'"player":\{[^}]*"name":"([^"]+)"', html),
                "standing": field(r'"standing":(\d+)', html, int),
                "size": field(r'"size":(\d+)', html, int),
                "date": (field(r'"tournamentDate":"([^"]+)"', html) or "")[:10],
                "cards": cards,
            })
        result[name] = decks

    out = json.dumps(result, indent=1)
    if args.out == "-":
        print(out)
    else:
        open(args.out, "w").write(out)


if __name__ == "__main__":
    main()
