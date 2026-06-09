#!/usr/bin/env bash
# Edit an Archidekt deck: move cards between categories or remove cards.
#
# Usage:
#   ./deck-edit.sh <deck_id> move <card_id> <category>
#   ./deck-edit.sh <deck_id> remove <card_id>
#
# NOTE: The `add` command is broken as of mid-2026.
#   - GET /api/cards/?name=... now returns "Client Unavailable" (routing broken)
#   - POST /api/decks/$DECK_ID/cards/ now returns 405 (endpoint removed)
#   Adding cards must be done through the Archidekt web UI.
#   Only `move` and `remove` still work (they PATCH/DELETE existing card IDs).
#
# Requires:
#   ARCHIDEKT_USERNAME and ARCHIDEKT_PASSWORD environment variables
#
# Examples:
#   ./deck-edit.sh 19369270 move 3081476402 "Recursion"
#   ./deck-edit.sh 19369270 remove 2785909287

set -euo pipefail

DECK_ID="$1"
OPERATION="$2"

# Load .env from skill root if credentials aren't already in the environment
SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ -f "$SKILL_DIR/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$SKILL_DIR/.env"
  set +a
fi

if [[ -z "${ARCHIDEKT_USERNAME:-}" || -z "${ARCHIDEKT_PASSWORD:-}" ]]; then
  echo "Error: ARCHIDEKT_USERNAME and ARCHIDEKT_PASSWORD are not set."
  echo "Create $SKILL_DIR/.env with:"
  echo "  ARCHIDEKT_USERNAME=yourusername"
  echo "  ARCHIDEKT_PASSWORD=yourpassword"
  exit 1
fi

# --- Auth ---
_login() {
  local response
  response=$(curl -s -X POST "https://archidekt.com/api/rest-auth/login/" \
    -H "Content-Type: application/json" \
    -d "{\"username\":\"$ARCHIDEKT_USERNAME\",\"password\":\"$ARCHIDEKT_PASSWORD\"}")

  # djangorestframework-jwt returns {"token": "..."}, simplejwt returns {"access": "..."}
  local token
  token=$(echo "$response" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(d.get('token') or d.get('access') or '')
")

  if [[ -z "$token" ]]; then
    echo "Error: Login failed. Check your credentials."
    echo "Response: $response"
    exit 1
  fi
  echo "$token"
}

TOKEN=$(_login)
AUTH="Authorization: JWT $TOKEN"

# --- Operations ---
case "$OPERATION" in
  move)
    CARD_ID="$3"
    CATEGORY="$4"
    result=$(curl -s -X PATCH "https://archidekt.com/api/decks/$DECK_ID/cards/$CARD_ID/" \
      -H "Content-Type: application/json" \
      -H "$AUTH" \
      -d "{\"categories\":[\"$CATEGORY\"]}")
    new_cats=$(echo "$result" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('categories','error'))" 2>/dev/null || echo "error")
    if [[ "$new_cats" == "error" ]]; then
      echo "Error moving card $CARD_ID: $result"
      exit 1
    fi
    echo "Card $CARD_ID moved to: $new_cats"
    ;;

  remove)
    CARD_ID="$3"
    http_code=$(curl -s -o /dev/null -w "%{http_code}" -X DELETE \
      "https://archidekt.com/api/decks/$DECK_ID/cards/$CARD_ID/" \
      -H "$AUTH")
    if [[ "$http_code" == "204" ]]; then
      echo "Card $CARD_ID removed from deck."
    else
      echo "Error removing card $CARD_ID (HTTP $http_code)"
      exit 1
    fi
    ;;

  add)
    CARD_NAME="$3"
    CATEGORY="$4"
    # Look up the card on Scryfall to get its name (canonical)
    encoded=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$CARD_NAME'))")
    scryfall=$(curl -s "https://api.scryfall.com/cards/named?fuzzy=$encoded")
    canonical_name=$(echo "$scryfall" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('name',''))" 2>/dev/null)
    if [[ -z "$canonical_name" ]]; then
      echo "Error: Card '$CARD_NAME' not found on Scryfall."
      exit 1
    fi

    # Search Archidekt for the card by name to get its card ID
    encoded_name=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$canonical_name'))")
    archidekt_card=$(curl -s "https://archidekt.com/api/cards/?name=$encoded_name&formats=3" | \
      python3 -c "
import sys, json
d = json.load(sys.stdin)
results = d.get('results', [])
if results:
    # Prefer exact name match
    for r in results:
        if r.get('oracleCard',{}).get('name','').lower() == '$canonical_name'.lower():
            print(r['id'])
            break
    else:
        print(results[0]['id'])
" 2>/dev/null)

    if [[ -z "$archidekt_card" ]]; then
      echo "Error: Could not find '$canonical_name' in Archidekt card database."
      exit 1
    fi

    result=$(curl -s -X POST "https://archidekt.com/api/decks/$DECK_ID/cards/" \
      -H "Content-Type: application/json" \
      -H "$AUTH" \
      -d "{\"card\":$archidekt_card,\"categories\":[\"$CATEGORY\"],\"quantity\":1,\"modifier\":\"Normal\"}")
    added_name=$(echo "$result" | python3 -c "
import sys, json
d = json.load(sys.stdin)
name = d.get('card',{}).get('oracleCard',{}).get('name','')
cats = d.get('categories','?')
print(f'{name} added to {cats}')
" 2>/dev/null || echo "error")
    if [[ "$added_name" == "error" ]]; then
      echo "Error adding card: $result"
      exit 1
    fi
    echo "$added_name"
    ;;

  *)
    echo "Unknown operation: $OPERATION"
    echo "Usage: $0 <deck_id> move|remove|add ..."
    exit 1
    ;;
esac
