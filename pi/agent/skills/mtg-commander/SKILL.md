---
name: mtg-commander
description: "Magic: The Gathering format assistant for Commander/EDH and Pauper. Use when the user asks about MTG Commander or Pauper rules, card lookups, deck building, card interactions, deck analysis, or anything related to these formats. Can look up cards via Scryfall, fetch decklists from Archidekt, and validate decks against format rules."
---

# MTG Commander Skill

This skill provides tools for working with Magic: The Gathering's Commander (EDH) and Pauper formats. It can look up card details, fetch and analyze decklists, validate decks against format rules, and answer rules questions.

## Quick Start

Before answering any Commander question, read the [Commander rules reference](references/commander-rules.md) to ground your answers in the official rules.

For Pauper questions, see the [Pauper Format](#pauper-format) section below — the rules differ significantly from Commander.

For Scryfall search syntax, see the [Scryfall syntax reference](references/scryfall-syntax.md).

## Pauper Format

Pauper is a 1v1 constructed format with rules distinct from Commander.

### Deck Construction
- Minimum **60 cards** in the main deck (not 100)
- Up to **15 card sideboard**
- Up to **4 copies** of any non-basic land card (basic lands unlimited)
- No commander mechanic — regular 1v1 game rules, no command zone

### Card Legality
A card is Pauper-legal if it has **ever been printed at common rarity** in any official Magic product, including paper sets (any edition) and Magic Online (MTGO) exclusive sets. The card's current or most recent printing rarity is irrelevant.

**Important:** `card-lookup.sh` shows the most recent printing, which may be uncommon or rare. A card that looks uncommon may still be Pauper-legal. Always verify with Scryfall's `f:pauper` filter or check the `pauper` field in the API response directly:

```bash
# Verify Pauper legality (also works around apostrophe issues)
curl -s "https://api.scryfall.com/cards/named?fuzzy=CARD_NAME" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('legalities',{}).get('pauper','N/A'))"

# Search for Pauper-legal cards matching criteria
./scripts/card-search.sh "f:pauper c:b o:discard" 10
```

### Ban List
Pauper has its own ban list separate from Commander. Never assume a card is legal based on rarity alone — always verify via Scryfall. Example: Hymn to Tourach was printed at common but is **banned** in Pauper.

### Apostrophe Workaround
The batch lookup and price scripts break on card names with apostrophes (e.g. "Raven's Crime", "Night's Whisper"). For those cards, call the Scryfall API directly using the fuzzy endpoint with the apostrophe stripped:

```bash
curl -s "https://api.scryfall.com/cards/named?fuzzy=Ravens+Crime" | python3 -c "import sys,json; d=json.load(sys.stdin); p=d.get('prices',{}); l=d.get('legalities',{}); print(f\"Name: {d['name']} | Pauper: {l.get('pauper')} | EUR: {p.get('eur')}\")"
```

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

## Editing Archidekt Decklists

Move cards between categories or remove cards from an existing deck.

**Requires:** `ARCHIDEKT_USERNAME` and `ARCHIDEKT_PASSWORD` set as environment variables.

```bash
# Move a card to a different category (use the deck card ID, not the Scryfall card ID)
./scripts/deck-edit.sh 19369270 move 3081476402 "Recursion"

# Remove a card from the deck entirely
./scripts/deck-edit.sh 19369270 remove 2785909287
```

> ⚠️ **The `add` command in `deck-edit.sh` is broken.** As of mid-2026, Archidekt removed the `POST /api/decks/$DECK_ID/cards/` endpoint (now returns 405) and the card search endpoint `GET /api/cards/?name=...` (now returns "Client Unavailable"). **Adding cards via the API is no longer possible.** Use the Archidekt web UI to add new cards. The `move` and `remove` operations still work because they use PATCH/DELETE on existing card IDs.

**Finding card IDs for move/remove:** Fetch the deck JSON and filter by name:
```bash
curl -s "https://archidekt.com/api/decks/DECK_ID/cards/" | python3 -c "
import sys, json
cards = json.load(sys.stdin)
for c in cards:
    name = c.get('card',{}).get('oracleCard',{}).get('name','')
    if 'SEARCH_TERM' in name.lower():
        print(f\"ID: {c['id']} | {name} | {c['categories']}\")
"
```

**Getting Archidekt integer card IDs (for scripting):** The card search API is dead, but you can extract Archidekt integer card IDs from any existing deck's JSON. Each card entry has `card.id` (Archidekt integer) and `card.uid` (Scryfall printing UUID). If you need IDs for specific cards, fetch a deck that contains them:
```python
import subprocess, json

def build_card_id_map(deck_ids):
    card_map = {}
    for deck_id in deck_ids:
        result = subprocess.run(['./scripts/deck-fetch.sh', str(deck_id), '--json'], capture_output=True, text=True)
        d = json.loads(result.stdout)
        for entry in d.get('cards', []):
            c = entry.get('card', {})
            name = c.get('oracleCard', {}).get('name', '')
            cid = c.get('id')
            if name and cid and name not in card_map:
                card_map[name] = cid
    return card_map
```

**Deck creation:** Not supported via the Archidekt API. Must be done through the web UI.

**Auth note:** The API uses JWT. Credentials are loaded from `.env` in the skill root (git-ignored). Copy `.env.example` to `.env` and fill in your details:
```
ARCHIDEKT_USERNAME=yourusername
ARCHIDEKT_PASSWORD=yourpassword
```

## Combo Finder (Commander Spellbook)

Find infinite combos and near-misses in a deck using [Commander Spellbook](https://commanderspellbook.com):

```bash
# Basic: complete combos + up to 2 cards away
./scripts/deck-combos.sh 12345

# By URL
./scripts/deck-combos.sh "https://archidekt.com/decks/12345/my-deck"

# Only show complete combos and 1-card-away near-misses
./scripts/deck-combos.sh 12345 --max-missing 1

# Show step-by-step instructions for each combo
./scripts/deck-combos.sh 12345 --verbose
```

The script:
- Queries Commander Spellbook for each card in the deck (~0.1s per card)
- Deduplicates across cards and filters for Commander-legal combos
- Reports three tiers: **complete** (all cards present), **1 card away**, **2 cards away**
- Shows what each combo produces (infinite damage, infinite mana, etc.) and bracket rating
- The 2-cards-away list can be long (100s of combos) — use `--max-missing 1` to focus on near-misses

**Note:** Scans 80–100 cards against the Spellbook database; expect ~20–30 seconds runtime.

## Deck Goldfish (Solitaire Testing)

Simulate goldfish games to test mana development, ramp consistency, and commander timing:

```bash
# Basic: 10 games, 6 turns each
./scripts/deck-goldfish.sh 12345

# Custom game count and turn depth
./scripts/deck-goldfish.sh 12345 --games 20 --turns 8

# Set minimum X for X-cost commanders (e.g., Old Stickfingers)
./scripts/deck-goldfish.sh 12345 --commander-min-x 3

# Reproducible results with a seed
./scripts/deck-goldfish.sh 12345 --seed 42

# Only show aggregate stats
./scripts/deck-goldfish.sh 12345 --quiet
```

The simulator:
- Draws opening hands with mulligan logic (keeps 2-5 lands)
- Plays lands with color priority (missing colors first, then duals > basics > colorless)
- **Tries to cast the commander FIRST** each turn if it's castable at `--commander-min-x` (models the real-play decision of holding ramp when you could cast commander instead)
- After commander attempt, casts remaining spells by priority: ramp early, then draw, then creatures, then other
- Heuristically resolves spell effects using oracle text (land ramp, mana rocks, draw, sac-draw, kicker)
- Resolves draw-then-discard spells properly (Frantic Search, Compulsive Research, etc.)
- Detects and creates tokens from ETB/cast triggers and attack triggers
- Detects and tracks non-creature artifact tokens (Clue, Treasure, Blood, Food, Powerstone, Map)
- Cracks Clue tokens for draw and Blood tokens for loot with remaining mana after spell casting
- Detects and uses **activated abilities** on permanents (discard outlets, tap-to-create-token, tap-for-mana, tap-to-draw) with remaining mana after spell casting
- Resolves **upkeep triggers** (forced discard, draw, discard-hand-then-draw wheels, graveyard recursion)
- Tracks commander casting with optional minimum X value
- Reports per-game logs + aggregate stats (mana curve, missed land drops, ramp rate, commander timing, **token count**, **artifact token count**, **discard count**)

**Limitations:** This is a goldfish (no opponent). Spells that target opponents or interact with combat are cast but effects not modeled. Triggered abilities on permanents that fire from game events (e.g., "whenever you discard") are not generically modeled — only the card's own activated abilities and ETB/upkeep/attack triggers are resolved. Modal spells default to draw modes. Sac-draw spells require a creature/artifact on board. For decks with complex trigger chains (discard payoffs, death triggers, etc.), a custom goldfish script may still be needed.

### ⚠️ CRITICAL: Always Sanity-Check Goldfish Output Against Hand-Math

The goldfish uses heuristic priorities that may not match optimal play for a specific deck. **Never present goldfish numbers as ground truth without first validating they match reasonable play sequences.**

**Before drawing conclusions from goldfish statistics, do this check:**

1. **Work out by hand what the "minimum viable" cast turn should be.** E.g., for an X-cost commander like Old Stickfingers at X=3 (5 mana needed): natural curve gets 5 mana on T5, one ramp spell brings it to T4, one 1-CMC ritual or T2 rock brings it to T3.

2. **Estimate a rough floor probability** using hypergeometric math. If the deck has ~50 mana sources in 99 cards, the chance of having enough ramp + lands for a T4–T5 cast should be well above 50%.

3. **If the goldfish number is dramatically lower than your hand-math estimate, the sim is wrong, not you.** Do not rationalize surprising numbers. Investigate.

4. **Common sim pitfalls for X-cost and high-value commanders:**
   - The sim casts ramp spells BEFORE trying to cast the commander each turn. If you have 5 mana + Cultivate + Stickfingers playable, the sim casts Cultivate (3 mana), then tries Stickfingers with 2 mana left → fails. Real play would hold the ramp.
   - The sim's `cast_priority` is: ramp → draw → creatures → other. Commanders are cast in a separate block AFTER hand spells.
   - For decks where the commander IS the win condition (X-cost grave-fillers, combo enablers), this mis-orders play.

5. **When in doubt, run a verbose per-game log (not `--quiet`) and trace 3–5 games manually** to see if the sim is sequencing like a real player would.

6. **If the user's intuition conflicts with sim output, trust the user first and investigate the sim.** Users who built their deck often have a better mental model than the heuristic simulator.

**Lesson from a real session:** A user's 36-land / 13-ramp Old Stickfingers deck showed T5 cast rate of 15.8% and T6 of 32% in the sim. The user pushed back — their own hand-math showed T5 should be achievable 60%+ of the time. Investigation revealed the sim was casting 3-mana ramp spells first and depleting mana before attempting Stickfingers. After patching the sim to try the commander FIRST when castable at min_x, the real rates were T5 = 85%, T6 = 90%. The user was right; the sim was wrong. An earlier deck-building recommendation based on the bad numbers had to be retracted.

**When recommending deck changes based on goldfish data, explicitly note:** "These numbers assume the sim plays correctly. If the numbers look surprisingly bad, we should verify before making changes."

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

### "Goldfish my deck" / "Test my mana base"
```bash
# Basic goldfish test
./scripts/deck-goldfish.sh DECK_ID

# For X-cost commanders, set minimum X
./scripts/deck-goldfish.sh DECK_ID --commander-min-x 3

# More games for better statistics
./scripts/deck-goldfish.sh DECK_ID --games 20 --turns 8 --quiet
```

### "Find combos in my deck" / "What combos does my deck have?"
```bash
# Find complete combos + near-misses
./scripts/deck-combos.sh DECK_ID

# Show only complete combos and 1-card near-misses (faster, less noise)
./scripts/deck-combos.sh DECK_ID --max-missing 1

# Show step-by-step instructions
./scripts/deck-combos.sh DECK_ID --verbose
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
- **Archidekt**: Rate-limits card add operations aggressively (~35 per minute). Space requests at least 0.3s apart; back off 45s if throttled.

## Scryfall Python API Notes

When calling the Scryfall API from Python (`urllib.request`), you **must** include `Accept: application/json` in the request headers or you'll get HTTP 400. The shell scripts use `curl` which sets this automatically, but Python's `urllib` does not.

```python
import urllib.request, json, urllib.parse

def scryfall_lookup(name):
    encoded = urllib.parse.quote(name)
    req = urllib.request.Request(f'https://api.scryfall.com/cards/named?fuzzy={encoded}')
    req.add_header('Accept', 'application/json')          # required — 400 without this
    req.add_header('User-Agent', 'MTG-Commander-Skill/1.0')
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return json.loads(e.read())
```

## Price Checking

When suggesting cards, **always verify prices** before presenting them. Do NOT guess prices from memory.

Use Scryfall's API to get EUR prices (sourced from Cardmarket):
```bash
curl -s "https://api.scryfall.com/cards/named?fuzzy=CARD_NAME" | python3 -c "import sys,json; d=json.load(sys.stdin); p=d.get('prices',{}); print(f\"EUR: {p.get('eur','N/A')}  EUR foil: {p.get('eur_foil','N/A')}\")"
```

For batch price checks:
```bash
for card in "Card One" "Card Two" "Card Three"; do
  echo "=== $card ==="
  encoded=$(python3 -c "import urllib.parse; print(urllib.parse.quote(\"$card\"))")
  curl -s "https://api.scryfall.com/cards/named?fuzzy=$encoded" | python3 -c "import sys,json; d=json.load(sys.stdin); p=d.get('prices',{}); print(f\"  EUR: {p.get('eur','N/A')}  EUR foil: {p.get('eur_foil','N/A')}\")"
  sleep 0.2
done
```

**Note:** Cards with apostrophes in their name (e.g. "Bolas's Citadel") will break the python quoting. Use the fuzzy search without the apostrophe (e.g. "Bolas Citadel") or handle quoting carefully.

When the user has a budget constraint, check prices BEFORE suggesting cards, not after. Present price alongside every suggestion.

## Mana Restriction Awareness

When building around specific mana sources, **always check what that mana can and cannot pay for**. Common restrictions:

- **Powerstone tokens**: "{T}: Add {C}. This mana can't be spent to cast a nonartifact spell." — CAN pay for: artifact spells, activated abilities (on any permanent), equip costs, special costs. CANNOT pay for: creature spells (unless artifact creature), instants, sorceries, enchantments, planeswalkers.
- **Treasure tokens**: No restrictions (any color, any purpose).
- **Eldrazi Spawn/Scion**: Sacrifice for {C}, no spending restrictions but colorless only.
- **Gold tokens**: Any one color, no other restrictions.

When suggesting payoffs for decks built around restricted mana sources, verify every suggestion is actually payable. Do not suggest instants/sorceries as payoffs for Powerstone mana, etc.

## Deck Building Session Workflow

When helping a user build a deck iteratively:

1. Fetch the decklist and understand the commander + gameplan first
2. Ask clarifying questions about win condition, budget, power level, and theme preferences before suggesting cards
3. Present suggestions **one at a time** unless asked otherwise — let the user decide before moving on
4. For each suggestion, include: card name, Scryfall link, EUR price, and a clear explanation of why it fits THIS specific deck
5. Track budget spent vs remaining when the user has a budget constraint
6. When a session is interrupted, offer to write a context file summarizing progress, pending suggestions, and remaining needs

### Hand Composition Constraints

Early in deck analysis, ask not just "what colors do you need" but **"what card properties need to be in your hand at game time?"** Some commanders care about what's sitting in hand (e.g., Rielle + Cinder Seer — lands and colorless artifacts are dead cards for the reveal mechanic). This shapes the entire mana package and changes which ramp pieces are correct.

### Archetype Alignment Check: Storm vs Hold-Cards

Before recommending creatures that reward casting many spells (Guttersnipe, Young Pyromancer, storm payoffs), ask: **does this deck want to cast spells quickly or hold a large hand?** These are opposite gameplans. A hand-size deck actively wants to hold cards and drip them out — pyromancer/storm archetypes are wrong for it and will confuse the gameplan. Confirm the deck's rhythm before recommending any "cast spells fast" payoff.

### Rescan Discipline

If a user asks you to rescan the decklist before each card evaluation, honor it **every single time** without being reminded again. Don't rely on a cached list from earlier in the session — cards may have been added or removed between evaluations.

### Exile ≠ Discard

When evaluating cards for a discard-synergy commander, **always explicitly flag the exile vs discard distinction**. "Exile your hand" does NOT trigger Rielle, Tergrid, Syr Konrad, etc. Cards like Wheel of Potential say "exile your hand" — this is a known trap. If there's any ambiguity, look up the oracle text and call it out directly.

### Replacement Effect Stacking

When evaluating damage multipliers (Fiery Emancipation, Rollercrusher Ride, Furnace of Rath, etc.), proactively work through the stacking math with any multipliers already in the deck. Replacement effects from sources you control apply to ALL damage you deal — including triggered sources like Repercussion. Show the combined multiplier explicitly (e.g., 3× × 2× = 6×) rather than presenting each card in isolation.

## Writing Deck Primers

- **Tone**: Direct and matter-of-fact. No opening flavor quotes, no sales-pitch enthusiasm. Match the user's own register.
- **Length**: Maximum ~13 paragraphs. If a section can be combined without losing information, combine it.
- **Accuracy**: Before writing, rescan the decklist. Every card mentioned must be in the deck. Look up oracle text for any card whose mechanics you're describing — do not paraphrase from memory.
- **Weaknesses**: Be honest about them. If the commander has no built-in recursion, say so plainly.
- **When the user corrects a claim**: Update the assessment immediately. Do not defend the original position.

## Pauper Simulation Discipline

When building or updating Monte Carlo sims for Pauper decks, **always look up oracle text before coding any card**. Do not rely on memory for CMC, effects, or triggers.

### ⚠️ CRITICAL: Verify Oracle Text Before Coding

Run `card-lookup.sh` (or the Scryfall API) for every card you model in a sim — even cards you think you know well. CMC errors and fabricated abilities have invalidated entire sim sessions in the past.

**Named examples of past errors (do not repeat these):**

| Card | What was modeled | Actual oracle text |
|------|------------------|--------------------|
| **Fear of Lost Teeth** | Tagged as "pinger" — could tap to deal 1 damage repeatedly, enabling YAAD combo lines. Also incorrectly described as having native deathtouch. | 1/1 Enchantment Creature — Nightmare. **No keywords, no deathtouch.** Death trigger only: "When ~ dies, deal 1 damage to target, gain 1 life." Cannot tap to deal damage. NOT a pinger. |
| **Mephitic Draught** | CMC 3, modeled with a "-3/-3 removal effect" | CMC 2 (1B). Artifact: ETB draw 1/lose 1 life; goes to GY draw 1/lose 1 life. **No removal effect at all.** |
| **Jarl of the Forsaken** | CMC 2 | CMC 4 (3B). Flash creature; ETB destroy a damaged creature. |
| **Fanatical Offering** | CMC 3 | CMC 2 (1B). Sac a creature or artifact → draw 2 + create a Map token. |
| **Toxin Analysis** | CMC 2 | CMC 1 (B). Instant: target creature gets deathtouch+lifelink until EOT, then Investigate. |
| **Arms of Hadar** | Modeled as -3/-3 to all; CMC 3 | CMC 4 (3B). -2/-2 to **target player's** creatures (not global, not -3/-3). |

### Pinger Board Logic

When coding `has_pinger_board` or equivalent checks, only count **Cuombajj Witches** (the actual pinger). Do NOT include Fear of Lost Teeth — it cannot deal damage except when it dies.

```python
# CORRECT
has_pinger_board = board.get("Cuombajj Witches", 0) > 0

# WRONG — Fear is not a pinger
has_pinger_board = board.get("Cuombajj Witches", 0) > 0 or board.get("Fear of Lost Teeth", 0) > 0
```

### CMC Errors Compound

A wrong CMC affects every game, every matchup, across all sims. A card with CMC 2 coded as CMC 3 will appear unplayable in early turns in every simulation. If results look surprisingly bad or good for a card, verify the CMC first.

### Surprising Sim Results = Verify the Model

If sim output seems too optimistic or too pessimistic for a card or interaction, **do not rationalize it or draw deck-building conclusions from it**. Investigate the model first. The most dangerous error is proposing to cut or add cards based on sim data when the sim has a fabricated ability.

**Lesson from a real session:** Multiple iterations of deck advice were built around Mephitic Draught being a removal spell (the invented -3/-3 effect). When oracle text was finally verified, the actual draw engine it provided completely changed the deck's mana/draw math — and the advice had to be retracted.

### Sim Workflow Checklist

Before running any updated sim:
1. Look up oracle text for every card in the deck list that has any non-trivial effect
2. Verify CMC matches mana cost in the sim definition
3. Verify trigger conditions (ETB, dies, tap, etc.) — do not assume
4. Check that `has_pinger_board` / `has_any_pinger` logic only counts real pingers
5. Verify threshold values for board sweepers (e.g., -2/-2 kills toughness ≤ 2, not ≤ 3)

## Tips

- Scryfall fuzzy search is forgiving — "thassa deep" will find "Thassa, Deep-Dwelling"
- For double-faced cards (MDFCs, transform), both faces are displayed
- The Archidekt deck format number 3 = Commander/EDH
- When helping with deck building, consider: mana curve, ramp, card draw, removal, win conditions, and mana base
- A typical Commander deck wants: ~36-38 lands, 10+ ramp, 10+ card draw, 5-10 removal, and the rest toward the deck's strategy
- Cards with apostrophes break the batch lookup script — call the Scryfall API directly for those (e.g., "Bolas Citadel" without the apostrophe works as a fuzzy match)
