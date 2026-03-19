#!/usr/bin/env bash
# Fetch a decklist from Archidekt by deck ID or URL
# Usage: ./deck-fetch.sh <deck_id_or_url> [--summary|--full|--json]
# Examples:
#   ./deck-fetch.sh 12345
#   ./deck-fetch.sh https://archidekt.com/decks/12345/my-deck
#   ./deck-fetch.sh 12345 --summary
#   ./deck-fetch.sh 12345 --full

set -euo pipefail

if [ $# -lt 1 ]; then
  echo "Usage: $0 <deck_id_or_url> [--summary|--full|--json]"
  echo ""
  echo "  --summary   Show deck overview with card counts per category (default)"
  echo "  --full      Show full decklist with card details"
  echo "  --json      Output raw JSON"
  exit 1
fi

INPUT="$1"
MODE="${2:---summary}"

# Extract deck ID from URL or use directly
DECK_ID=$(echo "$INPUT" | python3 -c "
import sys, re
inp = sys.stdin.read().strip()
# Match archidekt.com/decks/<id> or archidekt.com/api/decks/<id>
m = re.search(r'(?:archidekt\.com/(?:api/)?decks?/)(\d+)', inp)
if m:
    print(m.group(1))
else:
    # Assume it's a bare ID
    print(inp)
")

RESPONSE=$(curl -s "https://archidekt.com/api/decks/${DECK_ID}/")

# Check for errors
ERROR_CHECK=$(echo "$RESPONSE" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    if 'detail' in data:
        print(f\"Error: {data['detail']}\")
    elif 'id' not in data:
        print('Error: Unexpected response format')
    else:
        print('ok')
except:
    print('Error: Failed to parse response')
" 2>/dev/null)

if [ "$ERROR_CHECK" != "ok" ]; then
  echo "$ERROR_CHECK"
  exit 1
fi

if [ "$MODE" = "--json" ]; then
  echo "$RESPONSE" | python3 -m json.tool
  exit 0
fi

echo "$RESPONSE" | python3 -c "
import json, sys

data = json.load(sys.stdin)
mode = '$MODE'

name = data.get('name', 'Unknown')
owner = data.get('owner', {}).get('username', 'Unknown')
fmt_map = {1: 'Standard', 2: 'Modern', 3: 'Commander/EDH', 4: 'Legacy', 5: 'Vintage',
           6: 'Pauper', 7: 'Frontier', 8: 'Future Standard', 9: 'Penny Dreadful',
           10: 'One v One Commander', 11: 'Duel Commander', 12: 'Brawl', 13: 'Oathbreaker',
           14: 'Pioneer', 15: 'Historic', 16: 'Pauper EDH', 17: 'Alchemy', 18: 'Explorer',
           19: 'Historic Brawl', 20: 'Gladiator', 21: 'Premodern', 22: 'Predh', 23: 'Timeless',
           24: 'Standard Brawl'}
deck_format = fmt_map.get(data.get('deckFormat', 0), f\"Format #{data.get('deckFormat', '?')}\")
cards = data.get('cards', [])

# Organize by category
categories = {}
commanders = []
companion = None
total_cards = 0

for entry in cards:
    qty = entry.get('quantity', 1)
    card_data = entry.get('card', {})
    oracle = card_data.get('oracleCard', {})
    card_name = card_data.get('displayName') or oracle.get('name', 'Unknown')
    cats = entry.get('categories') or ['Uncategorized']
    is_companion = entry.get('companion', False)

    card_info = {
        'name': card_name,
        'quantity': qty,
        'mana_cost': oracle.get('manaCost', ''),
        'cmc': oracle.get('cmc', 0),
        'type_line': oracle.get('typeLine', '') or ' '.join((oracle.get('superTypes') or []) + (oracle.get('types') or [])),
        'color_identity': oracle.get('colorIdentity', []),
        'oracle_text': oracle.get('oracleText', ''),
        'power': oracle.get('power'),
        'toughness': oracle.get('toughness'),
    }

    if is_companion:
        companion = card_info

    for cat in cats:
        if cat.lower() == 'commander':
            commanders.append(card_info)
        categories.setdefault(cat, []).append(card_info)

    total_cards += qty

# Get included-in-deck categories
included_cats = set()
for cat_info in data.get('categories', []):
    if cat_info.get('includedInDeck', True):
        included_cats.add(cat_info['name'])

deck_card_count = sum(
    entry.get('quantity', 1)
    for entry in cards
    if any(c in included_cats for c in (entry.get('categories') or ['Uncategorized']))
)

print(f\"{'='*60}\")
print(f\"Deck:      {name}\")
print(f\"Owner:     {owner}\")
print(f\"Format:    {deck_format}\")
print(f\"Cards:     {deck_card_count} (in deck)\")
print(f\"URL:       https://archidekt.com/decks/{data['id']}\")

if commanders:
    cmdr_names = ', '.join(c['name'] for c in commanders)
    print(f\"Commander: {cmdr_names}\")

    # Calculate color identity from commanders
    ci = set()
    for c in commanders:
        ci.update(c['color_identity'])
    name_to_letter = {'White': 'W', 'Blue': 'U', 'Black': 'B', 'Red': 'R', 'Green': 'G'}
    ci_letters = set(name_to_letter.get(c, c) for c in ci)
    ci_str = ''.join(sorted(ci_letters, key=lambda x: 'WUBRG'.index(x) if x in 'WUBRG' else 99)) if ci_letters else 'Colorless'
    print(f\"Color ID:  {ci_str}\")

if companion:
    print(f\"Companion: {companion['name']}\")

print(f\"{'='*60}\")

if mode == '--summary':
    print()
    for cat_name in sorted(categories.keys()):
        cat_cards = categories[cat_name]
        count = sum(c['quantity'] for c in cat_cards)
        print(f\"  {cat_name} ({count}):\")
        for card in sorted(cat_cards, key=lambda x: (x['cmc'], x['name'])):
            qty_str = f\"{card['quantity']}x \" if card['quantity'] > 1 else '   '
            mana = card['mana_cost'] or ''
            print(f\"    {qty_str}{card['name']}  {mana}\")
        print()

elif mode == '--full':
    print()
    for cat_name in sorted(categories.keys()):
        cat_cards = categories[cat_name]
        count = sum(c['quantity'] for c in cat_cards)
        print(f\"### {cat_name} ({count}) ###\")
        print()
        for card in sorted(cat_cards, key=lambda x: (x['cmc'], x['name'])):
            qty_str = f\"{card['quantity']}x \" if card['quantity'] > 1 else ''
            print(f\"  {qty_str}{card['name']}  {card['mana_cost'] or ''}\")
            print(f\"    Type: {card['type_line']}\")
            if card['oracle_text']:
                for line in card['oracle_text'].split('\n'):
                    print(f\"    {line}\")
            if card['power'] is not None:
                print(f\"    {card['power']}/{card['toughness']}\")
            print()
"
