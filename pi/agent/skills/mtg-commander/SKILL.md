---
name: mtg-commander
description: "Magic: The Gathering Commander/EDH format assistant. Use when the user asks about MTG Commander rules, card lookups, deck building, card interactions, deck analysis, or anything related to the Commander format. Can look up cards via Scryfall, fetch decklists from Archidekt, and validate decks against Commander rules."
---

# MTG Commander Skill

This skill provides tools for working with Magic: The Gathering's Commander (EDH) format. It can look up card details, fetch and analyze decklists, validate decks against format rules, and answer rules questions.

## Quick Start

Before answering any Commander question, read the [Commander rules reference](references/commander-rules.md) to ground your answers in the official rules.

For Scryfall search syntax, see the [Scryfall syntax reference](references/scryfall-syntax.md).

## Card Lookup

When a user mentions a card by name, **always look it up** to get accurate details rather than relying on memory:

```bash
# Look up a single card by name (fuzzy match)
./scripts/card-lookup.sh "Sol Ring"
./scripts/card-lookup.sh "Thassa, Deep-Dwelling"
./scripts/card-lookup.sh "Kenrith, the Returned King"

# Get raw JSON for further analysis
./scripts/card-lookup.sh "Sol Ring" --json
```

The script uses Scryfall's fuzzy matching — partial or misspelled names work. It returns: name, mana cost, type, oracle text, color identity, Commander legality, and links.

**Important:** Whenever a card is mentioned in conversation — whether for rules questions, deck advice, or comparison — run the lookup script to confirm the card's actual oracle text, color identity, and legality. Do NOT rely on memory for card details.

## Batch Card Lookup

When you need to verify multiple cards at once (e.g. verifying a deck description, checking a list of suggestions):

```bash
# Look up multiple cards by name as arguments
./scripts/card-lookup-batch.sh "Sol Ring" "Arcane Signet" "Command Tower"

# Pipe card names via stdin (one per line)
echo -e "Sol Ring\nArcane Signet\nCommand Tower" | ./scripts/card-lookup-batch.sh --stdin
```

This calls `card-lookup.sh` for each card with proper Scryfall rate limiting (100ms between requests). Reports found/failed counts at the end. Use this instead of repeated individual lookups when verifying 3+ cards.

## Card Search

Find cards matching specific criteria using Scryfall search syntax:

```bash
# Search for cards (default: 10 results, sorted by EDHREC popularity)
./scripts/card-search.sh "t:legendary t:creature ci:bg cmc<=4"

# Limit results
./scripts/card-search.sh "o:\"draw a card\" ci<=u f:commander" 5

# Find possible commanders
./scripts/card-search.sh "is:commander ci=wubrg"

# Find cards with specific abilities
./scripts/card-search.sh "keyword:partner t:legendary"
```

## Archidekt Decklists

Fetch and analyze decklists from Archidekt:

```bash
# By deck ID
./scripts/deck-fetch.sh 12345

# By URL
./scripts/deck-fetch.sh "https://archidekt.com/decks/12345/my-deck-name"

# Summary view (default) — shows categories with card lists
./scripts/deck-fetch.sh 12345 --summary

# Full view — includes oracle text for every card
./scripts/deck-fetch.sh 12345 --full

# Deck description/primer text only
./scripts/deck-fetch.sh 12345 --description

# Raw JSON for custom analysis
./scripts/deck-fetch.sh 12345 --json
```

## Deck Validation

Validate an Archidekt deck against Commander format rules:

```bash
./scripts/deck-validate.sh 12345
./scripts/deck-validate.sh "https://archidekt.com/decks/12345/my-deck"
```

This checks:
- ✅ Deck is exactly 100 cards
- ✅ Commander is a valid legendary creature (or has "can be your commander")
- ✅ Partner/Partner-with validity for dual commanders
- ✅ All cards' color identity is within the commander's color identity
- ✅ No banned cards
- ✅ Singleton rule (no duplicates except basic lands and exempt cards)

## Answering Rules Questions

When answering rules questions:

1. **Always consult** the [Commander rules reference](references/commander-rules.md) first
2. **Look up any cards mentioned** using `card-lookup.sh` to get their exact oracle text
3. Cite the specific rule from the reference
4. If a question involves card interactions, look up ALL cards involved
5. If unsure about a card's current legality, check with the lookup script (Scryfall data is authoritative)

## Common Tasks

### "Is [card] legal in Commander?"
```bash
./scripts/card-lookup.sh "Card Name"
# Check the "Commander:" line in the output
```

### "What's the color identity of [card]?"
```bash
./scripts/card-lookup.sh "Card Name"
# Check the "Color Identity:" line
```

### "Can [card] be my commander?"
```bash
./scripts/card-lookup.sh "Card Name"
# Check: Is it legendary creature? Or does oracle text say "can be your commander"?
```

### "Suggest cards for my [theme] deck in [colors]"
```bash
./scripts/card-search.sh "o:\"relevant ability\" ci<=COLORS f:commander" 15
```

### "Analyze my Archidekt deck"
```bash
./scripts/deck-fetch.sh DECK_ID --summary
./scripts/deck-validate.sh DECK_ID
# Then look up specific cards of interest with card-lookup.sh
```

### "Verify/review my deck description"

Deck descriptions and primers frequently contain errors — wrong power/toughness, incorrect oracle text paraphrasing, or references to cards that aren't actually in the deck. Follow this workflow:

1. Fetch the decklist and description:
```bash
./scripts/deck-fetch.sh DECK_ID --full
./scripts/deck-fetch.sh DECK_ID --description
```

2. Extract every card name mentioned in the description text. Cross-reference each one against the actual decklist. Flag any card names that appear in the description but NOT in the deck — these are phantom references (cards that were cut or never added).

3. Look up every card mentioned in the description to verify claims:
```bash
./scripts/card-lookup-batch.sh "Card One" "Card Two" "Card Three"
```

4. Check for these common errors:
   - **Wrong stats**: power/toughness, mana cost, CMC quoted incorrectly
   - **Phantom cards**: cards described that aren't in the decklist
   - **Misquoted abilities**: oracle text paraphrased incorrectly (e.g., saying a card "creates a token" when it doesn't, or wrong trigger conditions)
   - **Wrong counts**: "the deck runs five X" when the actual count differs
   - **Assumed synergies that don't work**: abilities that don't interact the way the description claims (always verify against actual oracle text)
   - **Legality issues**: cards that aren't legal in Commander (Un-sets, banned cards) without noting Rule Zero

## API Rate Limits

- **Scryfall**: Requests should be spaced by 50-100ms. The scripts make single requests so this is generally fine. Do not bulk-query in tight loops.
- **Archidekt**: No official rate limit documentation, but be reasonable with requests.

## Tips

- Scryfall fuzzy search is forgiving — "thassa deep" will find "Thassa, Deep-Dwelling"
- For double-faced cards (MDFCs, transform), both faces are displayed
- The Archidekt deck format number 3 = Commander/EDH
- When helping with deck building, consider: mana curve, ramp, card draw, removal, win conditions, and mana base
- A typical Commander deck wants: ~36-38 lands, 10+ ramp, 10+ card draw, 5-10 removal, and the rest toward the deck's strategy
