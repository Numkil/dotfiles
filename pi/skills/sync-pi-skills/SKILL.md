---
name: sync-pi-skills
description: Sync skills between the pi CLI tool, Claude Code, and the dotfiles repo. Use when the user wants to copy, sync, or share skills between any of these — either direction, at global (~/.pi / ~/.claude) or project (.pi / .claude) level. Also handles syncing to/from the dotfiles repo at ~/Documents/Projects/numkil/dotfiles.
---

# Sync Pi Skills

Skills have identical SKILL.md format in both tools. Syncing is a directory copy operation. To activate the caveman plugin in pi, you need to add the caveman skill to the pi skills directory. You can do this by running the following command: `cp -r ~/.claude/skills/caveman ~/.pi/agent/skills/`

## Paths

| Scope    | Pi CLI                     | Claude Code               | Dotfiles repo                                              |
|----------|----------------------------|---------------------------|------------------------------------------------------------|
| Global   | `~/.pi/agent/skills/`      | `~/.claude/skills/`       | `~/Documents/Projects/numkil/dotfiles/pi/agent/skills/`   |
| Project  | `.pi/agent/skills/`        | `.claude/skills/`         | n/a (dotfiles only tracks global skills)                   |

The dotfiles repo mirrors the pi skills directory (`~/.pi/agent/skills/`). When syncing to dotfiles, always use the pi path as the source of truth, then commit the result.

## Workflow

### Step 1: Determine intent

Ask the user (or infer from context):
- **Direction**: pi → claude, claude → pi, dotfiles → live, live → dotfiles, or a full three-way sync?
- **Scope**: global, project, or both?
- **Which skills**: all, or specific skill names?

If the user said "keep in sync" without specifying direction, do a **bidirectional merge** across all three locations: copy any skill that exists in one place but not another. Do NOT overwrite if the skill already exists on the destination side.

### Step 2: List skills in all locations

```bash
# Global live locations
ls ~/.pi/agent/skills/ 2>/dev/null || echo "(empty)"
ls ~/.claude/skills/ 2>/dev/null || echo "(empty)"

# Dotfiles
ls ~/Documents/Projects/numkil/dotfiles/pi/agent/skills/ 2>/dev/null || echo "(empty)"

# Project (run from project root)
ls .pi/agent/skills/ 2>/dev/null || echo "(empty)"
ls .claude/skills/ 2>/dev/null || echo "(empty)"
```

### Step 3: Compute diff

Compare the lists and determine:
- Skills only in pi → candidates for copying to claude and/or dotfiles
- Skills only in claude → candidates for copying to pi and/or dotfiles
- Skills only in dotfiles → candidates for copying to pi and claude
- Skills in multiple places → potential conflicts (check modification dates before overwriting)

### Step 4: Copy skills

```bash
# Copy a single skill from pi to claude (global)
cp -r ~/.pi/agent/skills/<skill-name> ~/.claude/skills/

# Copy a single skill from claude to pi (global)
cp -r ~/.claude/skills/<skill-name> ~/.pi/agent/skills/

# Copy a single skill from pi to dotfiles
cp -r ~/.pi/agent/skills/<skill-name> ~/Documents/Projects/numkil/dotfiles/pi/agent/skills/

# Copy a single skill from dotfiles to pi
cp -r ~/Documents/Projects/numkil/dotfiles/pi/agent/skills/<skill-name> ~/.pi/agent/skills/

# Copy all missing skills from pi to claude (global, no overwrite)
# Note: no trailing slash on $skill — trailing slash causes cp -r to copy contents, not the dir itself
for skill in ~/.pi/agent/skills/*/; do
  name=$(basename "$skill")
  if [ ! -d ~/.claude/skills/"$name" ]; then
    cp -r ~/.pi/agent/skills/$name ~/.claude/skills/
    echo "Copied $name (pi → claude)"
  fi
done

# Copy all missing skills from claude to pi (global, no overwrite)
for skill in ~/.claude/skills/*/; do
  name=$(basename "$skill")
  if [ ! -d ~/.pi/agent/skills/"$name" ]; then
    cp -r ~/.claude/skills/$name ~/.pi/agent/skills/
    echo "Copied $name (claude → pi)"
  fi
done

# Copy all missing skills from pi to dotfiles (no overwrite)
DOTFILES_SKILLS=~/Documents/Projects/numkil/dotfiles/pi/agent/skills
for skill in ~/.pi/agent/skills/*/; do
  name=$(basename "$skill")
  if [ ! -d "$DOTFILES_SKILLS/$name" ]; then
    cp -r ~/.pi/agent/skills/$name "$DOTFILES_SKILLS/"
    echo "Copied $name (pi → dotfiles)"
  fi
done

# Update a single skill in all three locations at once (overwrite)
SKILL_NAME="my-skill"
cp -r ~/.claude/skills/$SKILL_NAME ~/.pi/agent/skills/
cp -r ~/.claude/skills/$SKILL_NAME ~/Documents/Projects/numkil/dotfiles/pi/agent/skills/
echo "Propagated $SKILL_NAME to pi and dotfiles"
```

For project-level, replace `~/.pi/agent/skills/` with `.pi/agent/skills/` and `~/.claude/skills/` with `.claude/skills/`.

### Step 5: Confirm result

After copying, list all three locations to confirm they match:

```bash
echo "=== Pi skills ===" && ls ~/.pi/agent/skills/
echo "=== Claude skills ===" && ls ~/.claude/skills/
echo "=== Dotfiles skills ===" && ls ~/Documents/Projects/numkil/dotfiles/pi/agent/skills/
```

### Step 6: Commit dotfiles (if dotfiles were updated)

If changes were made to the dotfiles repo, offer to commit them:

```bash
cd ~/Documents/Projects/numkil/dotfiles
git status
git add pi/agent/skills/
git commit -m "sync: update <skill-name> skill"
```

## Conflict handling

If a skill exists in multiple places, **do not overwrite silently**. Show the user:
- Modification dates of all copies (`ls -la`)
- Which one is newest

Then ask which version to keep, or skip.

## Notes

- Skills may include `references/` and `scripts/` subdirectories — `cp -r` handles these automatically.
- Some Claude-specific skills (from plugins in `~/.claude/plugins/`) are read-only marketplace installs — do not sync those to pi or dotfiles.
- Only sync skills under `~/.claude/skills/` (user-created) and `.claude/skills/` (project-level).
- The dotfiles repo mirrors the pi layout (`pi/agent/skills/`), not the claude layout.
- If the pi, claude, or dotfiles skills directory doesn't exist yet, create it with `mkdir -p` before copying.
