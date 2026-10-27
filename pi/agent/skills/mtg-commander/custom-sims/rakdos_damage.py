#!/usr/bin/env python3
"""
Damage-output sim for the Rakdos (mono-B) Pauper tempo deck.
Companion to rakdos_tempo.py (reuses its verified card data + Game machinery).

MODE: "blockers we clear", RACE sequencing.
  - Opponent starts at 20 life, deploys one 2/2 blocker each of its turns. We take NO damage back.
  - Ravens fly over (opp has no fliers). Ground creatures connect only when blockers run out.
  - Our removal (Soul Reap / You Are Already Dead / Jarl) + Cuombajj pings + sac death-pings +
    combat trades clear blockers; once their board empties, Perigee & co. connect for big chunks.

Damage sources: combat, Raven drain, death-pings (Fear/Footlight), Cuombajj tap, Jagged ETB,
Soul Reap -3. Lifegain: Raven drains (1/Raven) + Fear deaths (1 each).

Opp blocking AI (not suicidal): blocks the highest-power attackers it can at least TRADE with
(attacker toughness <= blocker power); never chump-blocks a creature it can't kill UNLESS the
unblocked swing is lethal. That's why Perigee starts connecting once the board is controlled.
Blockers default 2/2 (--blk-tough/--blk-power to vary).

Validate with --verbose N before trusting aggregates.
"""

import argparse
import random
from collections import defaultdict

from rakdos_tempo import (
    Game, build_deck, VARIANTS,
    FEAR, FOOTLIGHT, CUOMBAJJ, RAVEN, CORRUPTED, VILLAGE, THORN, BLADE, SIGN, VAULT, FAKE, CHAOS,
    CUTTHROAT, MOURNERS, PERIGEE, SCARBLADE, YAAD, SOUL_REAP, JARL,
    JAGGED_BARRENS, SAC_OUTLETS, DEATH_PINGERS,
)

MERC = "Mercenary token"   # 1/1 from Mourner's Surprise
ELF = "Elf token"          # 2/2 from Scarblade's Malice

# Combat stats: name -> (power, toughness, flier)
STATS = {
    FEAR: (1, 1, False), FOOTLIGHT: (1, 1, False), RAVEN: (1, 2, True),
    PERIGEE: (4, 5, False), BLADE: (3, 2, False), THORN: (1, 3, False),
    JARL: (3, 2, False), MERC: (1, 1, False), ELF: (2, 2, False),
    VAULT: (3, 1, False), CHAOS: (5, 4, False),
}  # Cuombajj is held back to tap


def resolve_combat(attackers, blockers, blk_tough, blk_power, opp_life):
    """attackers: list of [name,power,tough,flier]; blockers: int.
    Returns (face_damage, dead_attacker_names, blockers_killed)."""
    # attackers: [name, power, tough, flier, menace]
    fliers = [a for a in attackers if a[3]]
    ground = sorted([a for a in attackers if not a[3]], key=lambda a: -a[1])
    blocked = [False] * len(ground)
    dead, blk_killed, blk_damaged, B = [], 0, 0, blockers

    def kill_cost(a):
        n = -(-a[2] // blk_power)          # blockers needed to kill via toughness
        if a[4]:                           # menace: needs >=2 blockers to be blocked at all
            n = max(n, 2)
        return n

    # Pass 1: block the highest-power attackers we can kill, when worth committing the blockers.
    for i, a in enumerate(ground):
        if B <= 0:
            break
        nk = kill_cost(a)
        if B >= nk and (a[1] >= 2 or nk == 1):       # prevent >=2 dmg, or a cheap 1-for-1
            blocked[i] = True; B -= nk
            dead.append(a[0])
            blk_killed += min(nk, a[1] // blk_tough)  # attacker kills some blockers back
            if nk == 1 and a[1] < blk_tough:          # lone blocker survives, damaged (YAAD target)
                blk_damaged += 1

    face = sum(a[1] for a in fliers) + sum(a[1] for i, a in enumerate(ground) if not blocked[i])

    # Pass 2: chump only to avoid lethal (menace still needs 2 blockers even to chump).
    if face >= opp_life and B > 0:
        for i in sorted([j for j in range(len(ground)) if not blocked[j]], key=lambda j: -ground[j][1]):
            if B <= 0 or face < opp_life:
                break
            nb = 2 if ground[i][4] else 1
            if B < nb:
                continue
            blocked[i] = True; B -= nb; face -= ground[i][1]
            blk_killed += min(nb, ground[i][1] // blk_tough)
    return face, dead, blk_killed, blk_damaged


def simulate_damage(deck, on_play, rng, max_turns, blk_tough, blk_power,
                    blk_every=1, blk_cap=99, verbose=False):
    g = Game(deck, on_play, rng, verbose)
    opp_life, our_life, opp_blockers = 20, 20, 0
    opp_turns = 0
    treasures = 0                  # Treasure tokens banked (from Fake Your Own Death), = +1 mana each
    chaos_small = 0                # Chaos Spewers that self-blighted to 3/2 (no blight victim available)
    cutthroat_big = 0              # Cindering Cutthroats that entered as 4/3 (opp lost life that turn)
    opp_lost_life = False          # has the opponent lost life THIS turn (reset each turn)
    src = defaultdict(int)
    cum_by_turn, life_by_turn = {}, {}
    kill_turn = None
    perigee_body_turn = None       # first turn a HARDCAST Perigee (4/5 body) is on board

    def dmg(n, source):
        nonlocal opp_life, opp_lost_life
        if n <= 0:
            return
        opp_life -= n; src[source] += n; opp_lost_life = True

    for turn in range(1, max_turns + 1):
        cast = defaultdict(int)                # cast this turn (summoning sick)
        opp_lost_life = False                  # reset each turn (drives Cutthroat's 4/3 mode)
        cutthroat_pending = 0                  # Cutthroats deployed this turn, size settled at EOT
        if not (turn == 1 and on_play):
            opp_turns += 1
            if blk_cap > 0 and opp_turns % blk_every == 0 and opp_blockers < blk_cap:
                opp_blockers += 1              # opp deploys a blocker
            g._draw(1)

        g.play_land(turn, desired_now=99)      # race: maximize untapped mana
        this_drop = [L for L in g.lands if L['etb_turn'] == turn]
        crime = False
        black_spells = 0
        soulreaps = 0
        if this_drop and this_drop[0]['type'] == JAGGED_BARRENS:
            dmg(1, 'jagged'); crime = True

        land_total, black = g.mana(turn)
        total = land_total + treasures      # Treasures are spendable as any-color mana
        black += treasures
        spent = 0
        def afford(c): return (total - spent) >= c
        protected = None                    # creature granted "+2/0 & dies->return tapped" this turn
        grant_used = False
        grant_treasure = False              # Fake Your Own Death also makes a Treasure on the return

        # ---------- PRE-COMBAT ----------
        # Cuombajj taps available (summoning-sick ones cast this turn can't tap)
        cuombajj_taps = g.board[CUOMBAJJ] - cast[CUOMBAJJ] if g.cuombajj_sick_until < turn else 0

        # 1) Clear blockers pre-combat with Soul Reap (unconditional kill + reach).
        while SOUL_REAP in g.hand and opp_blockers > 0 and afford(2):
            g.hand.remove(SOUL_REAP); spent += 2; opp_blockers -= 1
            crime = True; black_spells += 1; soulreaps += 1
            g.log(f"  T{turn}: Soul Reap a blocker")
        # Cuombajj-enabled YAAD: free tap damages a blocker, YAAD destroys it + DRAWS a card.
        while YAAD in g.hand and opp_blockers > 0 and cuombajj_taps > 0 and afford(1):
            cuombajj_taps -= 1
            g.hand.remove(YAAD); spent += 1; opp_blockers -= 1; crime = True; black_spells += 1
            g._draw(1)
            g.log(f"  T{turn}: Cuombajj ping + You Are Already Dead a blocker (+draw)")

        # remaining Cuombajj taps -> face
        if cuombajj_taps > 0:
            dmg(cuombajj_taps, 'cuombajj'); crime = True

        # Perigee: HARDCAST (5) = permanent 4/5 body + ETB pump (the wincon, sorcery speed).
        # WARP (2) = ETB pump ONLY: enters summoning-sick, exiled at this turn's end step,
        #            never attacks, no lasting body. Only warp to push an evasive (flier) attacker
        #            when we can't yet afford the hardcast.
        perigee_grant = fyod_grant = False
        if PERIGEE in g.hand and (total - spent) >= 5:
            g.hand.remove(PERIGEE); g.board[PERIGEE] += 1; cast[PERIGEE] += 1
            spent += 5; black_spells += 1; perigee_grant = True
            if perigee_body_turn is None:
                perigee_body_turn = turn
            g.log(f"  T{turn}: Perigee HARDCAST -> 4/5 body + grant")
        elif PERIGEE in g.hand and afford(2) and (g.board[RAVEN] - cast[RAVEN]) > 0:
            g.hand.remove(PERIGEE); spent += 2; black_spells += 1; perigee_grant = True
            g.log(f"  T{turn}: Perigee WARP -> grant only (no body, exiled EOT)")

        # Chaos Spewer ({2}{B/R}=3, casts off black): 5/4. ETB blight 2 (or pay {2}).
        # Keep it a 5/4 by blighting a spare fodder (-> death-ping + crime), else a token, else pay 2;
        # only self-blight to 3/2 as a last resort.
        while CHAOS in g.hand and afford(3):
            g.hand.remove(CHAOS); spent += 3; black_spells += 1
            g.board[CHAOS] += 1; cast[CHAOS] += 1
            if any(g.board[f] > 0 for f in DEATH_PINGERS):
                f = next(f for f in DEATH_PINGERS if g.board[f] > 0)
                g.board[f] -= 1; dmg(1, 'ping'); crime = True
                if f == FEAR:
                    our_life += 1
                g.log(f"  T{turn}: Chaos Spewer 5/4 (blight {f} -> ping)")
            elif g.board[MERC] > 0 or g.board[ELF] > 0:
                tok = MERC if g.board[MERC] > 0 else ELF
                g.board[tok] -= 1
                g.log(f"  T{turn}: Chaos Spewer 5/4 (blight {tok})")
            elif afford(2):
                spent += 2
                g.log(f"  T{turn}: Chaos Spewer 5/4 (paid 2)")
            else:
                chaos_small += 1
                g.log(f"  T{turn}: Chaos Spewer 3/2 (self-blight)")

        # Cindering Cutthroat ({2}{B/R}=3, off black): summoning-sick regardless, so it's cast in
        # 2nd main (after combat + drain) to guarantee the "opp lost life this turn" 4/3 mode.
        # We deploy it here but settle its 4/3-vs-3/2 size at end of turn (see cutthroat_pending).
        while CUTTHROAT in g.hand and afford(3):
            g.hand.remove(CUTTHROAT); spent += 3; black_spells += 1
            g.board[CUTTHROAT] += 1; cast[CUTTHROAT] += 1; cutthroat_pending += 1
            g.log(f"  T{turn}: Cindering Cutthroat (size settled at end of turn)")

        # 3) Deploy for the future with remaining mana: Ravens, fodder, Thorn, Blade
        while RAVEN in g.hand and g.board[RAVEN] < 4 and afford(2):
            g.hand.remove(RAVEN); g.board[RAVEN] += 1; cast[RAVEN] += 1; spent += 2; black_spells += 1
        if THORN in g.hand and not g.monarch and afford(4):
            g.hand.remove(THORN); g.board[THORN] += 1; cast[THORN] += 1; spent += 4
            g.monarch = True; black_spells += 1
            g.log(f"  T{turn}: Thorn -> MONARCH")
        bcost = 3 if crime else 5             # spectacle if an opponent lost life this turn
        if BLADE in g.hand and afford(bcost):
            g.hand.remove(BLADE); g.board[BLADE] += 1; cast[BLADE] += 1; spent += bcost
            g._draw(1); black_spells += 1
            g.log(f"  T{turn}: Blade Juggler ({'spectacle' if bcost == 3 else 'hardcast'}) -> draw")
        # Sign in Blood (BB) -> draw 2, lose 2 life, NO body
        while SIGN in g.hand and black >= 2 and afford(2):
            g.hand.remove(SIGN); spent += 2; g._draw(2); our_life -= 2; black_spells += 1
            g.log(f"  T{turn}: Sign in Blood -> draw 2, lose 2 life")
        # Vault Plunderer (2B) -> 3/1 body, draw 1, lose 1 life
        while VAULT in g.hand and afford(3):
            g.hand.remove(VAULT); spent += 3; g.board[VAULT] += 1; cast[VAULT] += 1
            g._draw(1); our_life -= 1; black_spells += 1
            g.log(f"  T{turn}: Vault Plunderer -> 3/1 body, draw 1, lose 1")
        # Mourner's Surprise (2): regrowth (≈ draw 1 proxy) + a 1/1 Mercenary token (chip/fodder).
        while MOURNERS in g.hand and afford(2):
            g.hand.remove(MOURNERS); spent += 2; black_spells += 1
            g.board[MERC] += 1; cast[MERC] += 1; g._draw(1)
            g.log(f"  T{turn}: Mourner's Surprise -> 1/1 Mercenary + regrowth")
        for f in (FEAR, FOOTLIGHT):
            while f in g.hand and afford(1):
                g.hand.remove(f); g.board[f] += 1; cast[f] += 1; spent += 1; black_spells += 1
        if CUOMBAJJ in g.hand and black >= 2 and afford(2):
            g.hand.remove(CUOMBAJJ); g.board[CUOMBAJJ] += 1; cast[CUOMBAJJ] += 1
            spent += 2; black_spells += 1; g.cuombajj_sick_until = turn

        # Soul Reap reach: -3 per Soul Reap if another black spell was cast this turn
        if soulreaps and black_spells >= soulreaps + 1:
            dmg(3 * soulreaps, 'soulreap')

        # Scarblade's Malice (1, instant trick): on an attacking fodder vs a blocker ->
        # deathtouch kills the blocker, lifelink gains 1, the fodder dies (death-ping + makes a 2/2 Elf).
        if (SCARBLADE in g.hand and afford(1) and opp_blockers > 0
                and any(g.board[f] - cast[f] > 0 for f in DEATH_PINGERS)):
            f = next(f for f in DEATH_PINGERS if g.board[f] - cast[f] > 0)
            g.hand.remove(SCARBLADE); spent += 1; black_spells += 1
            opp_blockers -= 1                       # deathtouch kill
            our_life += 1                           # lifelink
            g.board[f] -= 1                          # the buffed fodder dies in the trade
            dmg(1, 'ping'); crime = True             # its death trigger -> face
            if f == FEAR:
                our_life += 1
            g.board[ELF] += 1; cast[ELF] += 1        # Scarblade's 2/2 Elf token
            g.log(f"  T{turn}: Scarblade's Malice -> kill blocker, +life, {f} dies (ping), make 2/2 Elf")

        # Fake Your Own Death (1B instant): grant +2/0 & "dies -> return tapped + Treasure".
        # Modeled use = the sac-and-return value line (sac outlet + a death-pinger in play).
        # Its reactive/combat-trick uses (protect vs removal, pump after blocks) are NOT modeled
        # -> FYOD's value here is a FLOOR.
        if (FAKE in g.hand and afford(2) and not (perigee_grant or fyod_grant)
                and any(o in g.hand for o in SAC_OUTLETS)
                and any(g.board[f] > 0 for f in DEATH_PINGERS)):
            g.hand.remove(FAKE); spent += 2; black_spells += 1; fyod_grant = True
            g.log(f"  T{turn}: Fake Your Own Death -> grant (sac-return + Treasure)")

        # ---------- COMBAT ----------
        attackers = []
        chaos_emitted = 0
        for name, (p, t, fly) in STATS.items():
            n = g.board[name] - cast[name]    # non-summoning-sick copies
            for _ in range(max(0, n)):
                if name == CHAOS and chaos_emitted < chaos_small:
                    attackers.append([CHAOS, 3, 2, False, False]); chaos_emitted += 1  # self-blighted
                else:
                    attackers.append([name, p, t, fly, False])
        # Cindering Cutthroat: 4/3 (entered when opp lost life) or 3/2, always attacks with menace.
        n_cut = g.board[CUTTHROAT] - cast[CUTTHROAT]
        big = cutthroat_big
        for _ in range(max(0, n_cut)):
            if big > 0:
                attackers.append([CUTTHROAT, 4, 3, False, True]); big -= 1
            else:
                attackers.append([CUTTHROAT, 3, 2, False, True])
        # Resolve the death-return grant (+2/0): sac-line -> a pinger we'll sac; else a flier.
        if perigee_grant or fyod_grant:
            grant_treasure = fyod_grant
            sac_line = (any(o in g.hand for o in SAC_OUTLETS) and any(g.board[f] > 0 for f in DEATH_PINGERS))
            if sac_line:
                protected = next(f for f in (FEAR, FOOTLIGHT) if g.board[f] > 0)
            elif attackers:
                flier = next((a for a in attackers if a[3]), None)
                protected = flier[0] if flier else max(attackers, key=lambda a: a[1])[0]
            tgt = next((a for a in attackers if a[0] == protected), None)
            if tgt:
                tgt[1] += 2
                g.log(f"  T{turn}: pump {protected} -> {tgt[1]} power")
        face, dead, blk_killed, blk_damaged = resolve_combat(
            attackers, opp_blockers, blk_tough, blk_power, opp_life)
        dmg(face, 'combat')
        opp_blockers = max(0, opp_blockers - blk_killed)
        for name in dead:
            if name == protected and not grant_used:
                grant_used = True; cast[name] += 1        # returns tapped (board count unchanged)
                if grant_treasure:
                    treasures += 1
            else:
                g.board[name] -= 1
                if name == CUTTHROAT and cutthroat_big > 0:
                    cutthroat_big -= 1        # a 4/3 copy left the battlefield
            if name in DEATH_PINGERS:
                dmg(1, 'ping'); crime = True
                if name == FEAR:
                    our_life += 1

        # ---------- POST-COMBAT ----------
        # YAAD / Jarl finish off blockers our attackers damaged in combat (cheap, realistic).
        while YAAD in g.hand and blk_damaged > 0 and opp_blockers > 0 and afford(1):
            g.hand.remove(YAAD); spent += 1; opp_blockers -= 1; blk_damaged -= 1
            crime = True; black_spells += 1; g._draw(1)         # YAAD draws a card
            g.log(f"  T{turn}: You Are Already Dead a damaged blocker (+draw)")
        while JARL in g.hand and blk_damaged > 0 and opp_blockers > 0 and afford(2):
            g.hand.remove(JARL); spent += 2; opp_blockers -= 1; blk_damaged -= 1
            g.board[JARL] += 1; cast[JARL] += 1; crime = True; black_spells += 1
            g.log(f"  T{turn}: Jarl flashes in (3/2 body), destroys a damaged blocker")
        # Any remaining Jarl: flash in as a 3/2 body to chip (hardcast).
        while JARL in g.hand and afford(4):
            g.hand.remove(JARL); spent += 4; g.board[JARL] += 1; cast[JARL] += 1; black_spells += 1
            g.log(f"  T{turn}: Jarl as a 3/2 body")
        # Sac-and-return: a pinger holding the grant -> sac for value, it RETURNS tapped
        # (board count unchanged) + a Treasure if the grant was Fake Your Own Death.
        if (protected in DEATH_PINGERS and not grant_used and g.board[protected] > 0
                and any(o in g.hand for o in SAC_OUTLETS) and afford(1)):
            o = next(o for o in SAC_OUTLETS if o in g.hand)
            g.hand.remove(o); spent += 1; g._draw(2); dmg(1, 'ping'); crime = True
            if protected == FEAR:
                our_life += 1
            grant_used = True; cast[protected] += 1
            if grant_treasure:
                treasures += 1
            g.log(f"  T{turn}: sac {protected} (grant) -> ping+draw2, returns tapped"
                  + (" +Treasure" if grant_treasure else ""))
        # Routine value: sac ONE spare fodder if flooded (>=2), for ping + draw 2 + crime.
        fodder = sum(g.board[f] for f in DEATH_PINGERS)
        if fodder >= 2 and any(o in g.hand for o in SAC_OUTLETS) and afford(1):
            o = next(o for o in SAC_OUTLETS if o in g.hand)
            f = next(f for f in DEATH_PINGERS if g.board[f] > 0)
            g.hand.remove(o); g.board[f] -= 1; spent += 1
            g._draw(2); dmg(1, 'ping'); crime = True
            if f == FEAR:
                our_life += 1

        # ---------- RAVEN DRAIN (one crime this turn -> each Raven triggers once) ----------
        ravens = g.board[RAVEN]
        if crime and ravens > 0:
            dmg(ravens, 'drain'); our_life += ravens

        if g.monarch:
            g._draw(1)

        # Settle Cutthroats deployed this turn: 4/3 if the opponent lost life this turn (the 2nd-main
        # sequencing almost always achieves this once we've attacked/drained), else 3/2.
        if opp_lost_life:
            cutthroat_big += cutthroat_pending

        # Treasures consumed by any over-land spending this turn; the rest stay banked.
        treasures = max(0, treasures - max(0, spent - land_total))

        cum_by_turn[turn] = 20 - opp_life
        life_by_turn[turn] = our_life
        if kill_turn is None and opp_life <= 0:
            kill_turn = turn
        g.log(f"  T{turn}: opp_life={opp_life} (dealt {20-opp_life}), blockers={opp_blockers}, "
              f"ravens={ravens}, our_life={our_life}")
        if opp_life <= 0:
            # fill remaining turns for the curve
            for t in range(turn + 1, max_turns + 1):
                cum_by_turn[t] = 20 - opp_life; life_by_turn[t] = our_life
            break

    return dict(src), cum_by_turn, life_by_turn, kill_turn, perigee_body_turn, g.log_lines


def run(deck, label, games, max_turns, on_play, blk_tough, blk_power, blk_every, blk_cap, seed, verbose):
    rng = random.Random(seed)
    src_tot = defaultdict(int)
    cum_tot = defaultdict(int)
    life_tot = defaultdict(int)
    kills = []
    perigee_turns = []          # turn the first hardcast Perigee body landed (None -> never)
    traced = 0
    for i in range(games):
        v = traced < verbose
        src, cum, life, kt, pt, lines = simulate_damage(
            deck, on_play, rng, max_turns, blk_tough, blk_power, blk_every, blk_cap, v)
        perigee_turns.append(pt)
        if v:
            print(f"\n--- {label} :: game {traced+1} (kill T{kt}) ---")
            for ln in lines:
                print(ln)
            traced += 1
        for k, val in src.items():
            src_tot[k] += val
        for t in range(1, max_turns + 1):
            cum_tot[t] += cum.get(t, cum.get(max(cum), 0))
            life_tot[t] += life.get(t, life.get(max(life), 20))
        if kt:
            kills.append(kt)

    print(f"\n================= {label}  ({'PLAY' if on_play else 'DRAW'}, {games} games, "
          f"{blk_power}/{blk_tough} blockers) =================")
    # Cumulative damage curve + lifegain curve
    print(f"{'Turn':<5}{'AvgDmg':>8}{'KillBy%':>9}{'AvgLifeGain':>13}")
    for t in range(1, max_turns + 1):
        killby = 100 * sum(1 for k in kills if k <= t) / games
        print(f"{t:<5}{cum_tot[t]/games:>8.1f}{killby:>8.0f}%{life_tot[t]/games - 20:>13.1f}")
    # Kill turn stats
    if kills:
        kills_sorted = sorted(kills)
        med = kills_sorted[len(kills_sorted)//2]
        print(f"\nKilled {len(kills)}/{games} ({100*len(kills)/games:.0f}%) within {max_turns} turns | "
              f"avg kill turn {sum(kills)/len(kills):.2f}, median {med}")
    else:
        print(f"\nNo kills within {max_turns} turns.")
    # Source breakdown (avg per game + share of total dealt)
    grand = sum(src_tot.values())
    print("Damage by source (avg/game | share):")
    for k in ('combat', 'drain', 'ping', 'cuombajj', 'jagged', 'soulreap'):
        print(f"   {k:<9} {src_tot[k]/games:>6.1f}   {100*src_tot[k]/grand if grand else 0:>4.0f}%")
    print(f"   {'TOTAL':<9} {grand/games:>6.1f}")
    # Perigee body (hardcast 4/5) landing — measures the "needs 5 mana, sorcery speed" cost
    landed = [p for p in perigee_turns if p]
    by = lambda t: 100 * sum(1 for p in landed if p <= t) / games
    if landed:
        print(f"Perigee BODY (hardcast) lands: ever {100*len(landed)/games:.0f}% | "
              f"by T5 {by(5):.0f}% T6 {by(6):.0f}% T7 {by(7):.0f}% T8 {by(8):.0f}% | "
              f"avg landing turn {sum(landed)/len(landed):.1f}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--games', type=int, default=20000)
    ap.add_argument('--turns', type=int, default=12)
    ap.add_argument('--seed', type=int, default=12345)
    ap.add_argument('--verbose', type=int, default=0)
    ap.add_argument('--draw', action='store_true')
    ap.add_argument('--blk-tough', type=int, default=2)
    ap.add_argument('--blk-power', type=int, default=2)
    ap.add_argument('--blk-every', type=int, default=1, help="opp adds a blocker every N of its turns")
    ap.add_argument('--blk-cap', type=int, default=99, help="max standing blockers (0 = pure goldfish)")
    ap.add_argument('--variant', default='18L-cut2carn', help="VARIANTS name(s), comma-separated, or 'all'")
    args = ap.parse_args()
    on_play = not args.draw
    names = list(VARIANTS) if args.variant == 'all' else args.variant.split(',')
    for name in names:
        kw = VARIANTS[name.strip()]
        nl = kw['swamp'] + kw['barren'] + kw['jagged'] + kw['carnarium']
        label = f"{name.strip()} [Fear{kw['fear']}/Foot{kw['footlight']}, {nl}L]"
        run(build_deck(**kw), label, args.games, args.turns, on_play,
            args.blk_tough, args.blk_power, args.blk_every, args.blk_cap, args.seed, args.verbose)


if __name__ == '__main__':
    main()
