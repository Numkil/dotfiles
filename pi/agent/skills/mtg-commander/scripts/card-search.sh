#!/usr/bin/env bash
# Search for Magic: The Gathering cards using Scryfall search syntax
# Usage: ./card-search.sh "search query" [limit]
# Examples:
#   ./card-search.sh "t:legendary t:creature ci:bg cmc<=4"
#   ./card-search.sh "o:draw o:cards ci:u" 5
#   ./card-search.sh "is:commander ci:wubrg"

set -euo pipefail

if [ $# -lt 1 ]; then
  echo "Usage: $0 \"scryfall search query\" [limit]"
  echo ""
  echo "Common Scryfall search syntax:"
  echo "  t:creature        - Type contains 'creature'"
  echo "  t:legendary       - Legendary cards"
  echo "  ci:wubrg          - Color identity (w/u/b/r/g, combine for multicolor)"
  echo "  ci<=rg            - Color identity is within Red/Green"
  echo "  c:r               - Card color is Red"
  echo "  cmc=3             - Converted mana cost equals 3"
  echo "  o:\"draw a card\"   - Oracle text contains phrase"
  echo "  is:commander      - Can be a commander"
  echo "  f:commander       - Legal in commander"
  echo "  pow>=5            - Power >= 5"
  echo "  keyword:flying    - Has keyword 'flying'"
  echo "  set:cmr           - From specific set"
  echo "  r:mythic          - Rarity"
  exit 1
fi

QUERY="$1"
LIMIT="${2:-10}"

# URL-encode the query
ENCODED_QUERY=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$QUERY'))")

RESPONSE=$(curl -s "https://api.scryfall.com/cards/search?q=${ENCODED_QUERY}&order=edhrec&unique=cards")

OBJECT_TYPE=$(echo "$RESPONSE" | python3 -c "import json,sys; print(json.load(sys.stdin).get('object',''))" 2>/dev/null)

if [ "$OBJECT_TYPE" = "error" ]; then
  echo "$RESPONSE" | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(f\"Error: {data.get('details', 'No cards found')}\")"
  exit 1
fi

echo "$RESPONSE" | python3 -c "
import json, sys

data = json.load(sys.stdin)
cards = data.get('data', [])
total = data.get('total_cards', 0)
limit = int('$LIMIT')

print(f'Found {total} cards (showing first {min(limit, len(cards))}):')
print()

for card in cards[:limit]:
    name = card.get('name', '?')
    mana = card.get('mana_cost', '')
    type_line = card.get('type_line', '?')
    ci = card.get('color_identity', [])
    ci_str = ''.join(ci) if ci else 'C'

    oracle = card.get('oracle_text', '')
    # For double-faced cards
    if card.get('card_faces') and not oracle:
        oracle = card['card_faces'][0].get('oracle_text', '')
        mana = card['card_faces'][0].get('mana_cost', '')

    # Truncate oracle text for display
    if len(oracle) > 120:
        oracle = oracle[:117] + '...'
    oracle = oracle.replace('\n', ' | ')

    print(f'  {name} {mana}  [{ci_str}]')
    print(f'    {type_line}')
    if oracle:
        print(f'    {oracle}')
    print()
"
