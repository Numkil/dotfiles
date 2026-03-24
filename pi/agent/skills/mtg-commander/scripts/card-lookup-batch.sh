#!/usr/bin/env bash
# Look up multiple Magic: The Gathering cards by name using the Scryfall API
# Usage: ./card-lookup-batch.sh "Card One" "Card Two" "Card Three"
#    or: echo -e "Card One\nCard Two" | ./card-lookup-batch.sh --stdin
# Returns: formatted card details for each card, separated by blank lines
# Respects Scryfall rate limits (100ms between requests)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

if [ $# -lt 1 ]; then
  echo "Usage: $0 \"Card Name\" [\"Card Name\" ...]"
  echo "   or: echo -e \"Card One\nCard Two\" | $0 --stdin"
  echo ""
  echo "Looks up multiple cards in sequence with rate limiting."
  echo "Uses the same output format as card-lookup.sh."
  exit 1
fi

CARDS=()

if [ "$1" = "--stdin" ]; then
  while IFS= read -r line; do
    line=$(echo "$line" | xargs)  # trim whitespace
    [ -n "$line" ] && CARDS+=("$line")
  done
else
  CARDS=("$@")
fi

if [ ${#CARDS[@]} -eq 0 ]; then
  echo "Error: No card names provided"
  exit 1
fi

TOTAL=${#CARDS[@]}
FOUND=0
FAILED=0

for i in "${!CARDS[@]}"; do
  CARD="${CARDS[$i]}"

  # Rate limit: 100ms between requests (Scryfall asks for 50-100ms)
  if [ "$i" -gt 0 ]; then
    sleep 0.1
  fi

  OUTPUT=$("$SCRIPT_DIR/card-lookup.sh" "$CARD" 2>&1) && STATUS=0 || STATUS=$?

  if [ $STATUS -eq 0 ]; then
    echo "$OUTPUT"
    echo ""
    FOUND=$((FOUND + 1))
  else
    echo "=== FAILED: $CARD ==="
    echo "$OUTPUT"
    echo ""
    FAILED=$((FAILED + 1))
  fi
done

echo "--- Batch complete: $FOUND/$TOTAL found, $FAILED failed ---"
