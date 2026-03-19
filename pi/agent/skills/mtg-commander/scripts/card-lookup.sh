#!/usr/bin/env bash
# Look up a Magic: The Gathering card by name using the Scryfall API
# Usage: ./card-lookup.sh "Card Name"
# Returns: formatted card details (name, mana cost, type, oracle text, legality, color identity, etc.)

set -euo pipefail

if [ $# -lt 1 ]; then
  echo "Usage: $0 \"Card Name\" [--json]"
  echo "  --json    Output raw JSON instead of formatted text"
  exit 1
fi

CARD_NAME="$1"
RAW_JSON="${2:-}"

# URL-encode the card name
ENCODED_NAME=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$CARD_NAME'))")

# Use fuzzy search for best match
RESPONSE=$(curl -s "https://api.scryfall.com/cards/named?fuzzy=${ENCODED_NAME}")

# Check for errors
OBJECT_TYPE=$(echo "$RESPONSE" | python3 -c "import json,sys; print(json.load(sys.stdin).get('object',''))" 2>/dev/null)

if [ "$OBJECT_TYPE" = "error" ]; then
  echo "$RESPONSE" | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(f\"Error: {data.get('details', 'Card not found')}\")"
  exit 1
fi

if [ "$RAW_JSON" = "--json" ]; then
  echo "$RESPONSE" | python3 -m json.tool
  exit 0
fi

# Format the output
echo "$RESPONSE" | python3 -c "
import json, sys

data = json.load(sys.stdin)

def format_card(card):
    lines = []
    lines.append(f\"{'='*60}\")
    lines.append(f\"Name:           {card.get('name', 'N/A')}\")
    lines.append(f\"Mana Cost:      {card.get('mana_cost', 'N/A')}\")
    lines.append(f\"CMC:            {card.get('cmc', 'N/A')}\")
    lines.append(f\"Type:           {card.get('type_line', 'N/A')}\")

    ci = card.get('color_identity', [])
    lines.append(f\"Color Identity: {', '.join(ci) if ci else 'Colorless'}\")

    colors = card.get('colors', [])
    lines.append(f\"Colors:         {', '.join(colors) if colors else 'Colorless'}\")

    oracle = card.get('oracle_text', '')
    if oracle:
        lines.append(f\"Oracle Text:    {oracle}\")

    if card.get('power') is not None:
        lines.append(f\"Power/Tough:    {card.get('power','?')}/{card.get('toughness','?')}\")

    if card.get('loyalty') is not None:
        lines.append(f\"Loyalty:        {card.get('loyalty')}\")

    keywords = card.get('keywords', [])
    if keywords:
        lines.append(f\"Keywords:       {', '.join(keywords)}\")

    legalities = card.get('legalities', {})
    commander_legal = legalities.get('commander', 'unknown')
    lines.append(f\"Commander:      {commander_legal}\")

    rarity = card.get('rarity', 'N/A')
    lines.append(f\"Rarity:         {rarity}\")

    set_name = card.get('set_name', 'N/A')
    set_code = card.get('set', 'N/A')
    lines.append(f\"Set:            {set_name} ({set_code.upper()})\")

    scryfall_uri = card.get('scryfall_uri', '')
    if scryfall_uri:
        lines.append(f\"Scryfall URL:   {scryfall_uri}\")

    edhrec = card.get('related_uris', {}).get('edhrec', '')
    if edhrec:
        lines.append(f\"EDHREC URL:     {edhrec}\")

    lines.append(f\"{'='*60}\")
    return '\n'.join(lines)

# Handle double-faced cards
if data.get('card_faces') and not data.get('oracle_text'):
    for i, face in enumerate(data['card_faces']):
        merged = {**data, **face}
        if i == 0:
            print(format_card(merged))
        else:
            print(f\"--- BACK FACE ---\")
            print(format_card(merged))
else:
    print(format_card(data))
"
