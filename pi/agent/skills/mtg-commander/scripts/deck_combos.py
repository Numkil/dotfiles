#!/usr/bin/env python3
"""
Find combos in an Archidekt Commander deck using Commander Spellbook.
Identifies complete combos (all cards in deck) and near-misses (1-2 cards away).
"""

import json
import sys
import time
import urllib.request
import urllib.parse
import argparse

SPELLBOOK_BASE = "https://backend.commanderspellbook.com"
RATE_LIMIT = 0.12  # seconds between requests


def fetch_spellbook(url):
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())


def get_combos_for_card(card_name, max_per_card=200, ci_filter=""):
    """Fetch all Spellbook combos containing a specific card, up to max_per_card."""
    encoded = urllib.parse.quote(f'card:"{card_name}"{ci_filter}')
    url = f"{SPELLBOOK_BASE}/variants/?q={encoded}&limit=100"
    combos = []
    while url and len(combos) < max_per_card:
        try:
            data = fetch_spellbook(url)
            combos.extend(data.get("results", []))
            url = data.get("next")
            if url:
                time.sleep(RATE_LIMIT)
        except Exception:
            break
    return combos


COLOR_NAME_TO_LETTER = {"White": "W", "Blue": "U", "Black": "B", "Red": "R", "Green": "G"}
WUBRG_ORDER = "WUBRG"


def get_deck_cards(deck_json):
    """Extract non-maybeboard card names from Archidekt deck JSON."""
    cards = set()
    for entry in deck_json.get("cards", []):
        cats = entry.get("categories") or []
        if "Maybeboard" in cats:
            continue
        oracle = entry.get("card", {}).get("oracleCard", {})
        name = entry.get("card", {}).get("displayName") or oracle.get("name")
        if name:
            cards.add(name)
    return cards


def get_color_identity(deck_json):
    """Derive the deck's color identity from its commander(s)."""
    ci = set()
    for entry in deck_json.get("cards", []):
        cats = entry.get("categories") or []
        if "Commander" not in cats:
            continue
        oracle = entry.get("card", {}).get("oracleCard", {})
        for color in oracle.get("colorIdentity", []):
            letter = COLOR_NAME_TO_LETTER.get(color, color.upper())
            ci.add(letter)
    if not ci:
        return None
    return "".join(c for c in WUBRG_ORDER if c in ci).lower()


def find_combos(deck_json, max_missing=2, verbose=False):
    deck_cards = get_deck_cards(deck_json)
    deck_name = deck_json.get("name", "Unknown")
    color_identity = get_color_identity(deck_json)
    ci_filter = f" ci:{color_identity}" if color_identity else ""

    print(f"Deck:   {deck_name}")
    print(f"Cards:  {len(deck_cards)}")
    if color_identity:
        print(f"Colors: {color_identity.upper()} (filtering combos to color identity)")
    print(f"Querying Commander Spellbook...\n")

    all_combos = {}
    card_list = sorted(deck_cards)
    for i, card in enumerate(card_list):
        print(f"\r  [{i+1}/{len(card_list)}] {card[:45]:<45}", end="", flush=True)
        for combo in get_combos_for_card(card, ci_filter=ci_filter):
            cid = combo["id"]
            if cid not in all_combos:
                if not combo.get("legalities", {}).get("commander", True):
                    continue
                all_combos[cid] = combo
        time.sleep(RATE_LIMIT)

    print(f"\r  Scanned {len(card_list)} cards — {len(all_combos)} unique combos found.   \n")

    results = []
    for combo in all_combos.values():
        combo_cards = [u["card"]["name"] for u in combo.get("uses", [])]
        missing = [c for c in combo_cards if c not in deck_cards]
        if len(missing) <= max_missing:
            results.append({
                "combo": combo,
                "combo_cards": combo_cards,
                "missing": missing,
                "missing_count": len(missing),
            })

    results.sort(key=lambda x: (x["missing_count"], len(x["combo_cards"])))
    return results, deck_cards


def produces_str(combo):
    produces = combo.get("produces", [])
    return ", ".join(p["feature"]["name"] for p in produces) if produces else "?"


def bracket_label(tag):
    labels = {"E": "bracket:5", "H": "bracket:4", "M": "bracket:3", "L": "bracket:2"}
    return labels.get(tag, f"[{tag}]") if tag else ""


def print_results(results, verbose=False):
    complete = [r for r in results if r["missing_count"] == 0]
    near1    = [r for r in results if r["missing_count"] == 1]
    near2    = [r for r in results if r["missing_count"] == 2]

    print("=" * 62)
    print("COMBO SUMMARY")
    print(f"  Complete (all cards in deck):  {len(complete)}")
    print(f"  1 card away:                   {len(near1)}")
    print(f"  2 cards away:                  {len(near2)}")
    print("=" * 62)

    if complete:
        print(f"\n{'─' * 62}")
        print(f"COMPLETE COMBOS  ({len(complete)})")
        print(f"{'─' * 62}")
        for r in complete:
            combo = r["combo"]
            bl = bracket_label(combo.get("bracketTag"))
            print(f"\n  Cards:    {', '.join(r['combo_cards'])}")
            print(f"  Produces: {produces_str(combo)}" + (f"  {bl}" if bl else ""))
            if verbose and combo.get("description"):
                print(f"  Steps:")
                for line in combo["description"].strip().splitlines():
                    print(f"    {line}")

    if near1:
        print(f"\n{'─' * 62}")
        print(f"1 CARD AWAY  ({len(near1)})")
        print(f"{'─' * 62}")
        for r in near1[:25]:
            combo = r["combo"]
            print(f"\n  Add:      {r['missing'][0]}")
            print(f"  Cards:    {', '.join(r['combo_cards'])}")
            print(f"  Produces: {produces_str(combo)}")
            if verbose and combo.get("description"):
                print(f"  Steps:")
                for line in combo["description"].strip().splitlines():
                    print(f"    {line}")

    if near2:
        print(f"\n{'─' * 62}")
        print(f"2 CARDS AWAY  ({len(near2)})")
        print(f"{'─' * 62}")
        for r in near2[:20]:
            combo = r["combo"]
            print(f"\n  Add:      {', '.join(r['missing'])}")
            print(f"  Cards:    {', '.join(r['combo_cards'])}")
            print(f"  Produces: {produces_str(combo)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-missing", type=int, default=2,
                        help="Max cards missing from deck to include (default: 2)")
    parser.add_argument("--verbose", action="store_true",
                        help="Show step-by-step combo instructions")
    args = parser.parse_args()

    deck_json = json.load(sys.stdin)
    results, deck_cards = find_combos(deck_json, max_missing=args.max_missing, verbose=args.verbose)
    print_results(results, verbose=args.verbose)
