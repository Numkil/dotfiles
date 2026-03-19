#!/usr/bin/env bash
# Validate an Archidekt deck against Commander rules using Scryfall legality data
# Usage: ./deck-validate.sh <deck_id_or_url>
# Checks: deck size (100), commander validity, color identity, card legality, singleton rule

set -euo pipefail

if [ $# -lt 1 ]; then
  echo "Usage: $0 <deck_id_or_url>"
  exit 1
fi

INPUT="$1"

DECK_ID=$(echo "$INPUT" | python3 -c "
import sys, re
inp = sys.stdin.read().strip()
m = re.search(r'(?:archidekt\.com/(?:api/)?decks?/)(\d+)', inp)
if m:
    print(m.group(1))
else:
    print(inp)
")

RESPONSE=$(curl -s "https://archidekt.com/api/decks/${DECK_ID}/")

echo "$RESPONSE" | python3 -c "
import json, sys, urllib.request, urllib.parse, time

data = json.load(sys.stdin)

if 'detail' in data:
    print(f\"Error: {data['detail']}\")
    sys.exit(1)

name = data.get('name', 'Unknown')
cards = data.get('cards', [])
errors = []
warnings = []

# Get included-in-deck categories
included_cats = set()
for cat_info in data.get('categories', []):
    if cat_info.get('includedInDeck', True):
        included_cats.add(cat_info['name'])

# Separate commanders and main deck
commanders = []
deck_cards = []

for entry in cards:
    card_data = entry.get('card', {})
    oracle = card_data.get('oracleCard', {})
    card_name = card_data.get('displayName') or oracle.get('name', 'Unknown')
    cats = entry.get('categories') or ['Uncategorized']
    qty = entry.get('quantity', 1)
    type_line = oracle.get('typeLine', '') or ''
    # Build type_line from components if not provided
    if not type_line:
        supertypes = oracle.get('superTypes') or oracle.get('supertypes') or []
        types = oracle.get('types') or []
        subtypes = oracle.get('subTypes') or oracle.get('subtypes') or []
        main_part = ' '.join(supertypes + types)
        if subtypes:
            sub_str = ' '.join(subtypes)
            type_line = main_part + ' -- ' + sub_str
        else:
            type_line = main_part
    # Normalize color identity — Archidekt uses full names, we want single letters
    name_to_letter = {'White': 'W', 'Blue': 'U', 'Black': 'B', 'Red': 'R', 'Green': 'G',
                       'W': 'W', 'U': 'U', 'B': 'B', 'R': 'R', 'G': 'G'}
    raw_ci = oracle.get('colorIdentity', [])
    color_identity = set(name_to_letter.get(c, c) for c in raw_ci)
    legalities = oracle.get('legalities', {})

    card_info = {
        'name': card_name,
        'quantity': qty,
        'categories': cats,
        'type_line': type_line,
        'color_identity': color_identity,
        'commander_legal': legalities.get('commander', 'unknown'),
        'oracle_text': oracle.get('oracleText', ''),
    }

    if 'Commander' in cats:
        commanders.append(card_info)

    # Only count cards that are included in the deck
    if any(c in included_cats for c in cats):
        deck_cards.append(card_info)

print(f\"Validating: {name}\")
print(f\"{'='*60}\")
print()

# 1. Check commander exists
if not commanders:
    errors.append('No commander designated! A Commander deck must have a commander.')
else:
    for cmdr in commanders:
        t = cmdr['type_line'].lower()
        oracle = cmdr['oracle_text'].lower()
        is_legendary_creature = 'legendary' in t and 'creature' in t
        can_be_commander = 'can be your commander' in oracle
        # Planeswalker commanders (some have the text)
        is_legendary_planeswalker = 'legendary' in t and 'planeswalker' in t and can_be_commander

        if not is_legendary_creature and not can_be_commander:
            errors.append(f\"{cmdr['name']} cannot be a commander. Must be a legendary creature or have 'can be your commander' text.\")

# 2. Check commander count
if len(commanders) > 2:
    errors.append(f\"Too many commanders ({len(commanders)}). Maximum is 2 (with Partner).\")
elif len(commanders) == 2:
    # Check for partner
    has_partner = all('partner' in c['oracle_text'].lower() for c in commanders)
    # Check for specific partner pairings (Friends Forever, Choose a Background, Doctor's Companion)
    special_partner_keywords = ['friends forever', 'choose a background', \"doctor's companion\"]
    has_special_partner = any(
        any(kw in c['oracle_text'].lower() for kw in special_partner_keywords)
        for c in commanders
    )

    if not has_partner and not has_special_partner:
        errors.append(f\"Two commanders ({commanders[0]['name']} and {commanders[1]['name']}) but neither has Partner or a partner-like ability.\")

# 3. Determine commander color identity
commander_ci = set()
for cmdr in commanders:
    commander_ci.update(cmdr['color_identity'])

color_map = {'W': 'White', 'U': 'Blue', 'B': 'Black', 'R': 'Red', 'G': 'Green'}
ci_display = ', '.join(color_map.get(c, c) for c in sorted(commander_ci, key=lambda x: 'WUBRG'.index(x) if x in 'WUBRG' else 99)) if commander_ci else 'Colorless'
print(f\"Commander Color Identity: {ci_display}\")
print()

# 4. Check deck size (should be exactly 100 including commander)
total = sum(c['quantity'] for c in deck_cards)
if total != 100:
    errors.append(f\"Deck has {total} cards (including commander). Must be exactly 100.\")

# 5. Check singleton rule and color identity
seen_cards = {}
basic_lands = {'Plains', 'Island', 'Swamp', 'Mountain', 'Forest',
               'Snow-Covered Plains', 'Snow-Covered Island', 'Snow-Covered Swamp',
               'Snow-Covered Mountain', 'Snow-Covered Forest', 'Wastes'}

for card in deck_cards:
    cname = card['name']

    # Singleton check (except basic lands and cards that say 'a deck can have any number')
    is_basic = cname in basic_lands
    any_number = 'a deck can have any number' in card['oracle_text'].lower()

    if not is_basic and not any_number:
        seen_cards.setdefault(cname, 0)
        seen_cards[cname] += card['quantity']
        if seen_cards[cname] > 1:
            errors.append(f\"'{cname}' appears {seen_cards[cname]} times. Commander is singleton (1 copy max, except basic lands).\")

    # Color identity check
    card_ci = card['color_identity']
    if card_ci and not card_ci.issubset(commander_ci):
        offending = card_ci - commander_ci
        offending_str = ', '.join(color_map.get(c, c) for c in offending)
        errors.append(f\"'{cname}' has color identity outside commander's: {offending_str}\")

    # Legality check
    if card['commander_legal'] == 'banned':
        errors.append(f\"'{cname}' is BANNED in Commander!\")
    elif card['commander_legal'] == 'not_legal':
        warnings.append(f\"'{cname}' may not be legal in Commander (Scryfall says: not_legal).\")

# Print results
if errors:
    print(f\"❌ ERRORS ({len(errors)}):\")
    for e in errors:
        print(f\"  • {e}\")
    print()

if warnings:
    print(f\"⚠️  WARNINGS ({len(warnings)}):\")
    for w in warnings:
        print(f\"  • {w}\")
    print()

if not errors and not warnings:
    print('✅ Deck passes all Commander validation checks!')
elif not errors:
    print('✅ No rule violations found (check warnings above).')
else:
    print(f\"❌ {len(errors)} rule violation(s) found.\")
"
