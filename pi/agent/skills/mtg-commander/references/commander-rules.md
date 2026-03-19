# Commander Format — Complete Rules Reference

Last updated: March 2025 (based on official Commander Rules Committee / Wizards of the Coast rules)

## 1. Overview

Commander (also known as EDH — Elder Dragon Highlander) is a multiplayer Magic: The Gathering format. It is the most popular casual constructed format. Games are typically free-for-all with 4 players but support 2+ players.

## 2. Deck Construction Rules

### 2.1 Deck Size
- A Commander deck must contain **exactly 100 cards**, including the commander(s).
- If you have two commanders with Partner, the deck is still exactly 100 cards total (98 + 2 commanders).
- A companion (if used) is **not** counted in the 100 cards. It exists outside the game in the sideboard zone and uses the companion mechanic's modified rules.

### 2.2 Singleton Rule
- A deck may contain **only one copy** of any card, except:
  - **Basic lands**: Plains, Island, Swamp, Mountain, Forest (and their Snow-Covered variants), and Wastes. Any number of basic lands are allowed.
  - **Cards that explicitly override this rule**: Cards whose text states "A deck can have any number of cards named [this card]" (e.g., Relentless Rats, Shadowborn Apostle, Rat Colony, Dragon's Approach, Persistent Petitioners, Seven Dwarves follows its own limit of 7).

### 2.3 Commander
- Each deck has a **designated commander**, which is a legendary creature.
- Some cards have text that says "~ can be your commander" — these cards can serve as your commander even if they aren't creatures (e.g., certain planeswalkers like Aminatou, the Fateshifter).
- The commander starts in the **command zone**, not in the deck.

### 2.4 Partner Commanders
- If your commander has the **Partner** keyword, you may have **two commanders**. Both must have Partner.
- **Partner with [Name]**: Can only partner with the specifically named card.
- **Friends Forever**: Functions like Partner but only pairs with other "Friends Forever" commanders.
- **Choose a Background**: A legendary creature with this ability can partner with a Background enchantment as a second commander.
- **Doctor's Companion**: Functions like Partner but only pairs with a Doctor (Time Lord Doctor creature).
- With two commanders, the deck is 98 cards + 2 commanders = 100 total.

### 2.5 Color Identity
- A card's **color identity** includes:
  - Colors in its mana cost
  - Colors in its rules text (mana symbols)
  - Colors defined by its color indicator
  - Colors defined by its characteristic-defining abilities
- **Every card** in the deck must have a color identity that is a **subset of the commander's color identity**.
- Reminder text does not count toward color identity.
- Lands with basic land types have the associated mana ability implicitly but this does NOT give them a color identity. However, dual lands and shocklands that produce colored mana through their text DO have that color identity.
- Example: If your commander's color identity is Red/White (R/W), you cannot include cards with Blue, Black, or Green in their color identity.
- Hybrid mana symbols count as BOTH colors for color identity purposes (e.g., a {R/W} symbol means the card has both Red AND White in its color identity).
- Phyrexian mana symbols count as their color for color identity purposes.

### 2.6 Banned List
The following cards are **banned** in Commander (as of early 2025):

**Power & Fast Mana:**
- Ancestral Recall
- Balance
- Biorhythm
- Black Lotus
- Channel
- Coalition Victory
- Emrakul, the Aeons Torn
- Erayo, Soratami Ascendant
- Fastbond
- Gifts Ungiven
- Golos, Tireless Pilgrim
- Griselbrand
- Iona, Shield of Emeria
- Karakas
- Leovold, Emissary of Trest
- Library of Alexandria
- Limited Resources
- Lutri, the Spellchaser (as commander or companion)
- Mox Emerald
- Mox Jet
- Mox Pearl
- Mox Ruby
- Mox Sapphire
- Panoptic Mirror
- Paradox Engine
- Primeval Titan
- Prophet of Kruphix
- Recurring Nightmare
- Rofellos, Llanowar Emissary
- Sundering Titan
- Sway of the Stars
- Sylvan Primordial
- Time Vault
- Time Walk
- Tinker
- Tolarian Academy
- Trade Secrets
- Upheaval
- Worldfire
- Yawgmoth's Bargain
- Dockside Extortionist
- Jeweled Lotus
- Mana Crypt
- Nadu, Winged Wisdom

Note: The ban list can change. Always verify with Scryfall (`legalities.commander`) or the official Commander website for the most current list. Use the card-lookup script to check individual cards.

### 2.7 Legal Cards
- All black- and white-bordered Magic cards that are not on the banned list are legal.
- Silver-bordered (Un-set) and Acorn-stamped cards are **not legal** by default (playgroups may allow them via Rule 0).
- Cards from joke sets, promotional cards, etc. follow the Scryfall legality data.

## 3. Gameplay Rules

### 3.1 Starting the Game
- Each player starts with **40 life** (instead of the usual 20).
- Each player's commander starts in the **command zone** face-up.
- Players determine turn order randomly.
- Each player draws an opening hand of **7 cards**.
- The starting player **does draw** a card on their first turn (unlike 1v1 formats).

### 3.2 Free Mulligan (London Mulligan)
- Commander uses the **London Mulligan** system.
- Each player may mulligan any number of times, drawing 7 cards each time, then putting cards from hand on the bottom of library equal to the number of times they mulliganed.
- Many playgroups allow one free mulligan ("first mulligan is free"), but this is a house rule, not an official rule.

### 3.3 The Command Zone
- Your commander begins the game in the command zone.
- You may **cast your commander from the command zone**.
- Each subsequent time you cast your commander from the command zone, it costs an additional **{2} (commander tax)** for each time it was previously cast from the command zone.
- The commander tax applies only when casting from the command zone, not from other zones.

### 3.4 Commander Zone Changes
- If your commander would be put into your **graveyard** from anywhere, you may choose to put it into the command zone instead.
- If your commander would be put into **exile** from anywhere, you may choose to put it into the command zone instead.
- This is a **replacement effect** — the commander never actually goes to the graveyard/exile if you choose to redirect it.
- This applies to any zone change to graveyard or exile (destruction, sacrifice, exile effects, countering, etc.).
- Your commander going to your **hand** or **library** is allowed — it stays there. You don't get the option to redirect it to the command zone from these zones.

### 3.5 Commander Damage
- A player who has been dealt **21 or more combat damage** by a single commander over the course of the game **loses the game**.
- This is tracked per commander separately. If there are two partner commanders, each tracks independently.
- Only **combat damage** counts (damage dealt during the combat damage step from attacking/blocking). Damage from abilities, spells, or non-combat sources does NOT count toward commander damage.
- Commander damage is tracked even if the commander changes zones and returns. The damage is tied to the physical card.

### 3.6 Winning and Losing
A player loses the game if:
- Their **life total** reaches **0 or less**.
- They take **21+ combat damage** from a single commander.
- They attempt to **draw from an empty library**.
- A card effect says they lose the game (e.g., Door to Nothingness).
- They receive **10+ poison counters** (unchanged from normal Magic).

The last player remaining wins the game.

### 3.7 Multiplayer Specifics
- When a player leaves the game, all cards they own leave the game too. All spells and abilities they control on the stack cease to exist. Anything they control that other players own is exiled.
- Effects that reference "your opponents" always mean all remaining opponents.
- Any "target opponent" or "each opponent" effects scale with the number of opponents.
- There is no formal priority for attacks — you choose which opponents to attack during each combat.

## 4. Rule 0 — The Social Contract

- Commander is primarily a **social, casual format**.
- **Rule 0** states that playgroups should discuss expectations before the game: power level, infinite combos, mass land destruction, stax, extra turns, proxies, etc.
- Players may agree to modify rules (e.g., allowing silver-bordered cards, banning additional cards, adjusting starting life).
- Rule 0 is the foundation of Commander — communication is key.

## 5. Companion in Commander

- A companion must meet its deck-building restriction considering ALL 100 cards (including the commander).
- The companion exists outside the game (in the sideboard).
- To use a companion, you must pay {3} to put it from outside the game into your hand (as per the updated companion errata).
- The companion does NOT count toward the 100-card deck count.
- Lutri, the Spellchaser is banned because every singleton deck automatically meets its companion requirement.

## 6. Common Interactions & Clarifications

### 6.1 Color Identity Edge Cases
- **Devoid** cards (colorless with colored mana costs) still have the color identity of their mana costs. E.g., a card with Devoid and {2}{B}{G} in its cost has B/G color identity.
- **Extort** reminder text contains {W/B} but this does NOT count toward color identity (it's reminder text, not rules text).
- **Transguild Courier** has a color indicator making it all 5 colors — its color identity is WUBRG.
- **Flip cards, transform cards, MDFCs**: Both faces/sides count for color identity.

### 6.2 Commander-Specific Cards
- Cards that reference "your commander" or "commander" as a game term (e.g., Command Tower, Commander's Sphere, Arcane Signet) work as printed.
- **Command Tower** taps for any color in your commander's color identity. In a colorless deck, it produces no mana.
- **Commander's Plate** protects from colors not in your commander's identity.

### 6.3 "Dies" Triggers and Commander
- If your commander would "die" (go to graveyard from battlefield) and you redirect it to the command zone, it **does** trigger "dies" abilities because the replacement happens after the event that triggers the ability. **UPDATE**: As of 2024, the commander going to the command zone IS a zone change replacement effect. "Dies" means "put into a graveyard from the battlefield." If you replace going to the graveyard with going to the command zone, the creature did NOT die, so "dies" triggers do NOT trigger. This was clarified in recent rules updates.

### 6.4 Ownership and Control
- You always own your commander even if another player gains control of it.
- If your commander is stolen, it still deals commander damage on behalf of YOU (the owner), which counts toward the 21-damage rule.
- You can still redirect your commander to the command zone if it would go to graveyard/exile, even if you don't control it.

## 7. EDH Bracket System (2024+)

Wizards of the Coast introduced a **bracket system** to help communicate power levels:

- **Bracket 1**: Precon-level, low power, battlecruiser Magic
- **Bracket 2**: Optimized casual, focused strategies but not fully tuned
- **Bracket 3**: High power, strong synergies, combos possible but not dominant
- **Bracket 4**: cEDH (competitive EDH), optimized win-fast strategies

This is a guideline, not a rule. Playgroups can use it as a shorthand for power level discussions.

## 8. Quick Reference

| Rule | Value |
|------|-------|
| Deck size | Exactly 100 (including commander) |
| Copies per card | 1 (except basic lands and special exceptions) |
| Starting life | 40 |
| Commander damage lethal | 21 (combat damage, per commander) |
| Poison counters lethal | 10 |
| Commander tax | +{2} per previous cast from command zone |
| Players | 2+ (typically 4) |
| Commander zone | Face-up, cast from here |
| Commander redirect | Graveyard or exile → may go to command zone |
