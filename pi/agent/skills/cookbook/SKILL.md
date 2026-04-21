---
name: cookbook
description: Manage a personal Markdown cookbook stored in cookbook/. Use when the user asks to fetch a new recipe from the internet, add it to the cookbook, scale ingredient quantities for a different number of people, or improve/clean up an existing recipe file. Knows the repository's folder conventions, file format, and ingredient notation.
---

# Cookbook Skill

The cookbook lives in `cookbook/` at the repo root. Each recipe is a single Markdown file inside a category folder.

## Repository layout

```
cookbook/
├── baking-savoury/
├── baking-sweet/
├── basics/              # shared building blocks: stocks, sauces, doughs (e.g. dashi)
├── bulgur/
├── burgers/
├── couscous/
├── desserts/
├── noodles/
├── pasta/
├── pizza/
├── potatoes-fish/
├── potatoes-meat/
├── rice/
├── slow-cooker/
├── toast-sandwishes/     # note: existing (mis)spelling, keep it
└── wraps/
```

Pick the folder by the dominant starch / carrier / cooking method:
- Pasta shapes → `pasta/`, noodle dishes (udon, ramen, pad thai, rice noodles) → `noodles/`
- Rice-based mains → `rice/`, couscous → `couscous/`, bulgur → `bulgur/`
- Potato + meat or potato + fish → `potatoes-meat/` / `potatoes-fish/`
- Slow-cooker stews/soups → `slow-cooker/`
- Sweet bakes → `baking-sweet/`, savoury bakes (quiche, focaccia…) → `baking-savoury/`
- Desserts that aren't bakes → `desserts/`
- Burgers / pizza / wraps / toast-sandwishes → their own folders
- Reusable building blocks (stocks, master sauces, pizza dough, pastry, spice mixes) → `basics/`. Reference them from other recipes via a relative link, e.g. `see ../basics/dashi.md`.

If nothing fits, ask the user before creating a new category folder.

## File naming

- kebab-case, lowercase, `.md` extension: `miso-salmon.md`, `spaghetti-bolognaise.md`.
- A few legacy files use capitals/spaces; do not rename existing files unless asked. New files: always lowercase kebab-case.

## Recipe file format

Match what is already in the repo. Canonical template:

```markdown
# Recipe Title

### Ingredients: [2 people]
200g spaghetti
100g pancetta
2 cloves garlic
...

### Recipe

Step 1. ...
Step 2. ...

#### Notes

Optional storage / variation notes.

![optional screenshot](https://...)
```

Observed variations (all acceptable, prefer the first):
- Header sometimes `### Ingredients` without `[N people]` — always add `[N people]` for new recipes.
- Steps header sometimes `### Instructions` instead of `### Recipe` — prefer `### Recipe` for new files, keep existing ones as-is unless improving.
- Ingredient lines: `amount name` (`100g pancetta`), `name - amount` (`onion - 1`), or bullet lists. When rewriting, normalise to `amount name` with metric units.
- Some recipes have sub-sections (`### Making the soup.` / `### Making the extras`) — keep that structure when a recipe has distinct phases or components.
- Keep any trailing image link at the bottom.

## Workflow 1 — Fetch a recipe from the internet

When the user asks for a new recipe (e.g. "add a bibimbap recipe"):

1. Ask which source if they haven't given one, otherwise search / use the URL they provide.
2. Fetch the page:
   ```bash
   curl -sL --compressed -A "Mozilla/5.0" "<URL>" -o /tmp/recipe.html
   ```
   If the HTML is heavy, strip to text: `lynx -dump -nolist /tmp/recipe.html` or `python3 -c "import sys,html2text,pathlib;print(html2text.html2text(pathlib.Path('/tmp/recipe.html').read_text()))"`. Many recipe sites expose JSON-LD — try `grep -oE '<script type="application/ld\+json">[^<]+' /tmp/recipe.html` first, it usually contains structured `recipeIngredient` and `recipeInstructions`.
3. Convert to the cookbook template:
   - Convert imperial to metric (grams, ml, °C). Keep °F only if the original is imperial and conversion is awkward — but prefer metric.
   - Default to `[2 people]` unless the user asks otherwise or the recipe is clearly family-sized (then scale down, see Workflow 2).
   - Keep instructions in prose paragraphs like the existing files, not numbered lists — concise but complete.
   - Credit the source at the bottom: `Source: <url>`.
4. Save to the correct category folder with a kebab-case filename. Confirm the chosen path with the user before writing if ambiguous.
5. Show a short summary (path + servings) after writing.

## Workflow 2 — Scale ingredients

When the user asks to scale a recipe for N people:

1. Read the target file and find the `### Ingredients: [X people]` header.
2. Compute factor = N / X. If no person count is present, ask.
3. Rewrite every numeric quantity in the ingredients block, keeping units. Rules:
   - Round weights to the nearest 5g (or 10g above 200g); volumes to sensible cook-friendly values (5ml, 1 tbsp, ¼ tsp…).
   - Whole items (eggs, onions, cloves): round to nearest whole, but keep halves/quarters when that makes the ratio meaningfully better (e.g. `1.5 onions` → `1½ onion`).
   - "to taste" / "a pinch" / "splash" — leave unchanged.
   - Update quantities mentioned inside the `### Recipe` body too (e.g. "add 350g spaghetti", "200ml water per person"). Search the whole file.
4. Update the header to `### Ingredients: [N people]`.
5. Ask before overwriting if the user might want a copy instead.

## Workflow 3 — Improve a recipe

When the user asks to improve / clean up a recipe:

Focus on clarity and consistency, not reinvention. Do:
- Normalise the header format (`# Title`, `### Ingredients: [N people]`, `### Recipe`).
- Normalise ingredient lines to `amount unit name` with metric units, one per line, ordered roughly by use.
- Fix typos and grammar. Keep the author's casual voice.
- Merge tiny fragmented steps, split run-on steps. Each paragraph = one logical stage (prep / cook / finish).
- Add missing obvious info: pan size, heat level, approximate timing, resting time, doneness cues.
- Preserve: the title's intent, sub-section structure, trailing image, `#### Notes` section, any `Source:` link.
- Do not invent ingredients or change the dish. If something is genuinely missing (e.g. salt never mentioned), add it and mention the addition to the user.

After editing, briefly list the changes you made so the user can review the diff meaningfully.

## Quick commands

```bash
# List all recipes
find cookbook -name '*.md' | sort

# Search recipes by ingredient
grep -lRi "miso" cookbook/

# Show a recipe
cat cookbook/pasta/carbonara.md
```
