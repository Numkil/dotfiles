# cEDH Research & Deckbuilding Reference

Lessons from real cEDH sessions. Read this before researching a cEDH commander,
comparing lists, or tuning a competitive deck.

## Data sources and how to reach them

### Moxfield (most cEDH lists live here)
- `curl` to `api2.moxfield.com` is blocked by Cloudflare. Use the Chrome extension:
  open any moxfield.com page, then run `fetch('https://api2.moxfield.com/v3/decks/all/<publicId>')`
  in the page with `javascript_tool`.
- Useful fields: `boards.mainboard/commanders/sideboard/maybeboard.cards[*].card` (name,
  set, cn, type_line, cmc), `authorTags` (card name -> tags), `description`, `hubs`,
  `lastUpdatedAtUtc`, `createdByUser.userName`.
- Primers are not in the API response. Navigate to `/decks/<id>/primer`, wait ~4s, then
  `get_page_text`.
- **Private decks** return no boards to an unauthenticated fetch. Read them from the
  rendered deck page with `get_page_text` instead.
- The extension blocks output that looks like a query string or cookie (for example long
  `name (SET) 123` strings). Return `JSON.stringify` of arrays instead.
- Deck search API: `/v2/decks/search?filter=<text>&fmt=commander&sortType=views` finds decks
  by name (for example a list someone heard about by name). Its commander filter does not
  work reliably.

### Editing Moxfield decks with Chrome (only when the user asks)
- **Bulk Edit** (`/decks/<id>/edit`) is the reliable way to add cards. One card per line:
  `1 Card Name (SET) 123 #Tag Name`. Set and collector number are optional; a deck tag can
  contain spaces. Click into the textarea, press `cmd+End`, type, then press **Save**.
- The Considering board has its own tab in Bulk Edit. Use "Save & Continue Editing" before
  switching tabs.
- To move a single card, open its chevron menu and choose "Move to Considering".
- **Moxfield copies tags the user already gave a card in their other decks.** After adding
  cards, check the tag view. Never "fix" those tags without asking; the user may have set
  them deliberately.
- Shift+click a card name opens Change Tags. The layout shifts after every save, so confirm
  the dialog title names the right card before saving.
- New decks: "Your Decks" -> "New Deck". Set visibility under Advanced options (the default
  is Public), and pick the commander from the autocomplete dropdown.

### EDHTop16 (tournament results)
- The GraphQL API only accepts persisted queries. Scrape the server-rendered HTML instead,
  with `scripts/edhtop16-lists.py`.
- Commander page: `/commander/<url-encoded name>?timePeriod=ONE_YEAR&sortBy=NEW&minEventSize=16`.
  It lists at most 48 recent decklist links, so large commanders are sampled, not counted fully.
- Commanders by color identity: `/?colorId=BG&timePeriod=ONE_YEAR&minEntries=0`. The
  colorId is WUBRG-ordered (`UBG`, not `BUG`), and the names are embedded as
  `"name":"...","colorId":"..."`.
- `WebFetch` works for summary stats (entries, conversion rate, meta share). The Chrome
  extension may not be permitted to read edhtop16.com.
- Deduplicate by pilot: keep each player's latest list before counting card frequencies.
  Otherwise one prolific pilot skews the numbers.

### Archidekt deck search (casual and self-labelled cEDH lists)
- Search API: `https://archidekt.com/api/decks/v3/?name=<text>&edhBracket=5&orderBy=-updatedAt&page=N`
  (60 results per page, plain `curl` with a browser User-Agent works). Each result has `id`,
  `name`, `owner.username`, `updatedAt`, `size`, `viewCount`.
- Fetch each deck with `https://archidekt.com/api/decks/<id>/` (sleep ~0.6s between calls). Skip
  cards whose categories include Maybeboard/Sideboard.
- Bracket 5 is self-reported. Filter to real cEDH lists (size ~100, has Thassa's Oracle or the
  commander's main combo piece, has fast mana) before counting. Compare against EDHTop16 play
  rates: cards common on Archidekt but rare in tournaments are the "hidden tech" candidates.

### Other sources
- EDHREC JSON (`json.edhrec.com/pages/cards/<slug>.json`, `/pages/tags/<tag>.json`) mixes
  casual and cEDH decks. Don't present it as cEDH data.
- mtgdecks.net mirrors EDHTop16 lists with finishes. It's handy for web search hits.
- The Scryfall `/cards/collection` POST endpoint rate-limits quickly (HTTP 429). For more
  than about 20 cards, use the per-card endpoint with 0.25–0.5s sleeps.

## Analysis patterns that worked
- **Compare against the field.** For each card, count how many pilots play it. List the
  popular cards the user lacks and the user's cards few others play. Also check archetype
  markers (a handful of signature cards) to split a commander into sub-archetypes.
- **Look at what the winners changed.** A winning list's small diff from a primer list is
  stronger evidence than raw play rates.
- **Archetype by rule.** EDHTop16 has no archetype tags, so define them by rule. For
  example, "reanimator-shaped" means at least 3 reanimation spells plus at least 1 of
  Entomb, Buried Alive or Unmarked Grave. Then mine card frequencies inside that group.
  Average per commander so one commander doesn't dominate.
- **Hypergeometric for density questions,** for example "how many interaction pieces by
  turn 3". It gives a concrete trade-off per slot.
- **Monte Carlo for engines** like Necropotence: simulate turn N, pay X life, then check
  "castable win next turn". State the model's simplifications in the answer.
- **Visualize comparisons as an artifact:** overlap counts, cards per role (using the
  user's own tag names), difference lists, and a full card matrix.

## cEDH deckbuilding principles the user holds
- **One win condition, many routes to it, heavy protection.** Don't add backup wincons
  made of cards that are weak alone (for example Witherbloom Apprentice + Chain of Smog,
  or Necrotic Ooze piles). Protect the wincon instead.
- **Every card should do something on its own.** Combo pieces should double as value,
  interaction or mana.
- **Ratio checks for reanimator:** keep the number of binners (Entomb, Buried Alive,
  Intuition, discard outlets) at or above the number of reanimation spells. Reanimation
  spells with no target are dead cards.
- **Price is irrelevant for cEDH** (proxies), but proxies are ordered in batches. Keep a
  "next proxy order" list instead of suggesting single-card orders.
- **Free interaction density matters.** Cards that punish free spells (for example
  Vexing Bauble) are bad in a deck full of its own free spells.

## Rules interactions verified in session (re-verify oracle text before relying on them)
- **Tasigur, the Golden Fang:** you choose the opponent, and they choose *any* nonland card
  in your graveyard, not just the milled ones. With infinite mana, every nonland card comes
  back eventually. Milling with an empty library is safe. Cursed Totem stops the ability.
- **Necropotence:** cards arrive at the beginning of your next end step. Discards are
  exiled, so discarding to hand size at cleanup loses the excess. The draw step is
  skipped, so top-of-library tutors are slow. It doesn't count as drawing, so it doesn't
  trigger Orcish Bowmasters.
- **Shallow Grave / Corpse Dance:** they return only the *top* creature card of your
  graveyard. They're unreliable in creature-heavy decks; bin the target in the same window.
- **Phantasmal Image:** it's sacrificed when targeted, so never Saw in Half an Image copy.
  Sacrificing it as a cost (the Sacrifice spell, Eldritch Evolution) is fine.
- **Token copies** (Saw in Half, Coiling Rebirth with gift) copy the card, not its
  counters; Persist's -1/-1 counter is not carried over.
- **Spree** (Lively Dirge): the chosen modes resolve in printed order, search first and
  return second.
- **Intuition / Gifts piles:** enumerate every split the opponent can choose. A pile only
  works if every split leaves a line. For example, Broodlord / Devoted Druid / Hazel's
  Brewmaster works for Intuition, while Gifts has a losing split.
- **Superior Spider-Man:** it enters as a copy of a creature card from any graveyard and
  keeps that card's mana cost and ETB triggers. It's cast, so it gets past Grafdigger's
  Cage and Containment Priest. It exiles the copied card.
- **Creature spells dodge most free counters** (Fierce Guardianship, Force of Negation,
  An Offer You Can't Refuse, Swan Song, Flusterstorm, Spell Pierce).
- **Devoted Druid infinite mana:** with Machine God's Effigy (a non-creature artifact copy
  that also taps for U) or Hazel's Brewmaster (Druid exiled from the graveyard; Foods gain
  its abilities). Summoning sickness doesn't matter for either.
- **Samut, Tyrant of Naktamun:** split second stops responses to your instants and
  sorceries, including activated graveyard hate like Soul-Guide Lantern. It doesn't stop
  static hate (Rest in Peace, Dauthi Voidwalker).
