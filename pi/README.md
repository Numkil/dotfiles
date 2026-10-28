# PI Coding Agent Configuration

This directory contains your PI coding agent configuration. `pi/agent/` is the single
source of truth — the root `install.sh` copies it to `~/.pi/agent/`.

## 📁 Structure

```
pi/
├── agent/                  # Mirrors ~/.pi/agent/ — the canonical config
│   ├── AGENTS.md           # Global instructions (stack, workflow preferences)
│   ├── APPEND_SYSTEM.md    # Appended system prompt (behavioral rules)
│   ├── settings.json       # PI settings (model, theme, packages, compaction)
│   ├── mcp.json            # MCP servers (context7, github, sequential-thinking)
│   ├── hermes-memory-config.json  # Persistent memory configuration
│   ├── extensions/         # Custom TypeScript extensions
│   │   ├── caveman-auto-activate.ts # Auto-activates caveman mode for token optimization
│   │   ├── capability-reminder.ts   # Shows contextual reminders for available tools
│   │   ├── command-permissions.ts   # Blocks dangerous bash commands
│   │   ├── craft-skills-auto-load.ts # Auto-loads Craft CMS skills
│   │   ├── summarize.ts             # Conversation summarization
│   │   └── whimsical.ts             # Fun working messages
│   ├── agents/             # Sub-agent definitions
│   │   ├── craft-planner.md          # Breaks large Craft work into implementation steps
│   │   ├── craft-feature-builder.md  # Implements one feature from a plan
│   │   ├── craft-site-builder.md     # Builds Craft front-end templates/components
│   │   ├── craft-code-reviewer.md    # Everyday diff review
│   │   ├── craft-code-reviewer-deep.md # Deep review for release branches
│   │   └── craft-debugger.md         # Debugs Craft CMS issues
│   ├── skills/             # Skill library (Craft CMS, ddev, hosting, tools)
│   └── themes/             # Custom themes (gruvbox-material, gruvbox-material-light)
└── README.md               # This file
```

Machine-specific state (`trust.json`, `skills-lock.json`, `auth.json`, sessions, npm
installs) is gitignored — see `.gitignore`.

## 🚀 Quick Setup

To set up PI on a new machine with your configuration:

### 1. Clone your dotfiles
```bash
git clone <your-dotfiles-repo> ~/Documents/projects/numkil/dotfiles
```

### 2. Run the install script from the repo root
```bash
cd ~/Documents/projects/numkil/dotfiles
chmod +x install.sh
./install.sh
```

The installer copies the PI config to `~/.pi/agent/`, installs the npm packages
listed in `settings.json`, updates them to the latest versions, and installs the
caveman skill.

### 3. Restart PI
```bash
pi --reload
```

## 📦 Installed Packages

The following npm packages are configured in `agent/settings.json` and are
installed/updated automatically by `install.sh`:

| Package | Purpose |
|---------|---------|
| `pi-hermes-memory` | Persistent memory with session search and secret scanning |
| `@narumitw/pi-lsp` | LSP integration for code intelligence |
| `pi-subagents` | Sub-agent delegation and multi-agent workflows |
| `@narumitw/pi-goal` | Autonomous goal-based task completion |
| `pi-web-access` | Web search, URL fetching, GitHub cloning, PDF extraction |
| `pi-vision-handoff` | Vision capabilities for image understanding |
| `pi-agent-browser-native` | Browser automation as a native tool |
| `pi-intercom` | 1:1 messaging between Pi sessions on the same machine |
| `@signalridge/pi-statusline` | Theme-native status footer (replaces the old custom minimal-footer extension) |

### Caveman Extension
The caveman-auto-activate extension automatically enables caveman mode on session start for token optimization, making responses shorter and reducing API costs. The Caveman skill is installed separately via `npx skills add JuliusBrussee/caveman` (handled by the install script).

**Caveman commands:**
```
/caveman          # Toggle on/off
/caveman lite     # Light compression (~25% reduction)
/caveman full     # Medium compression (~50% reduction)
/caveman ultra    # Maximum compression (~65% reduction)
```

**Note:** Caveman only compresses output tokens, not input. It's particularly effective for reducing Mistral API costs. The extension auto-activates caveman mode when a session starts.

## 🔧 Extensions

### caveman-auto-activate.ts
Automatically activates caveman mode at the start of each session for token optimization. Caveman reduces API costs by making responses more concise.

### capability-reminder.ts
Shows contextual reminders based on your intent. For example:
- "Build a new feature" → "Remember: use /goal for autonomous task completion"
- "This is a large task" → "Remember: use /subagent to delegate parts of this work"
- "Remember to save this" → "Remember: use /memory:add to store this in long-term memory"
- Craft CMS keywords → "Remember: use /skill:craftcms for Craft CMS guidance"

**Commands:**
- `/reminders` - Show summary of available reminders
- `/reminders:list` - List all reminder mappings
- `/reminders:test <message>` - Test reminder detection

### command-permissions.ts
Blocks dangerous bash commands and prompts for confirmation:
- `rm -rf`, `sudo`, `chmod 777`
- System control commands (`reboot`, `shutdown`, etc.)
- Root operations (`> /`, `cp /`, etc.)
- Network/remote access (`ssh`, `scp`, `curl`, `wget`)
- Git force operations

### craft-skills-auto-load.ts
Automatically loads Craft CMS-related skills when working in a Craft project:
- craftcms
- craft-cloud
- craft-content-modeling
- craft-garnish
- craft-pest
- craft-php-guidelines
- craft-plugin-release
- craft-plugins
- craft-project-setup
- craft-site
- craft-twig-guidelines
- ddev

### summarize.ts
Adds `/summarize` command to generate conversation summaries and `summarize_conversation` tool for LLM use.

### whimsical.ts
Displays fun, rotating working messages while PI is thinking (e.g., "Cogitating...", "Flibbertigibbeting...", "Reticulating splines...").

## 🤖 Agents

Sub-agent definitions in `agent/agents/`, used with `/subagent`:

| Agent | Purpose |
|-------|---------|
| `craft-planner` | Breaks large Craft plugin/module work into feature-by-feature steps with verification gates. Use before `craft-feature-builder`. |
| `craft-feature-builder` | Implements one feature from a plan, layer by layer. |
| `craft-site-builder` | Builds Craft front-end templates and components. |
| `craft-code-reviewer` | Reviews a diff for quality, security, and Craft conventions. Use before merge. |
| `craft-code-reviewer-deep` | Deep review for release branches and high-stakes changes. |
| `craft-debugger` | Debugs Craft CMS issues (read-only investigation). |

## 🧠 Memory

`pi-hermes-memory` provides persistent memory across sessions. Configuration lives in
`agent/hermes-memory-config.json`. Useful commands:

- `/memory:add <text>` - Save a memory
- `/memory:search <query>` - Search memories and past sessions
- `/memory-skills` - Manage procedural skills
- `/memory-index-sessions` - Index past sessions for search (one-time)

## 🎯 Usage Tips

### Starting a new task
```
You: "I need to build a new Craft plugin for client X"
PI: [Status] Remember: use /goal for autonomous task completion
You: /goal: Build a new Craft plugin for client X with these requirements...
```

### Working with memory
```
You: "Remember that we decided to use X approach for this"
PI: [Status] Remember: use /memory:add to store this in long-term memory
You: /memory:add We decided to use X approach for handling Y in the Z plugin
```

### Delegating complex work
```
You: "This is a big feature with frontend and backend components"
PI: [Status] Remember: use /subagent to delegate parts of this work
You: /subagent:create Frontend specialist
You: /subagent:create Backend specialist
```

### Craft-specific help
```
You: "How do I set up a Matrix field with nested entries?"
PI: [Status] Remember: use /skill:craftcms for Craft CMS guidance
You: /skill:craft-content-modeling
```

## 📝 Customization

### Adding a new extension
1. Create a new `.ts` file in `pi/agent/extensions/`
2. Commit it to your dotfiles
3. Run `./install.sh` from the repo root on the target machine

### Adding a new skill
1. Add the skill directory to `pi/agent/skills/`
2. Commit it to your dotfiles
3. Run `./install.sh` from the repo root on the target machine

### Adding a new reminder
Edit `pi/agent/extensions/capability-reminder.ts` and add a new entry to the `DEFAULT_REMINDERS` array:

```typescript
{
  keywords: ["your", "keywords", "here"],
  message: "Remember: your reminder message",
  cooldown: 5,
  priority: 8,
  type: "status",
}
```

### Adding a new package
1. Install the package locally with a pinned version: `pi install npm:package-name@1.2.3`
2. Add the pinned spec to `pi/agent/settings.json` under the `packages` array
3. Commit the updated `settings.json` to your dotfiles

### Updating a package
Versions in `settings.json` are pinned, so installs are reproducible. To update:

```bash
pi install npm:package-name@<new-version>
```

Then update the pinned version in `pi/agent/settings.json` and commit. Run
`pi list` to see what's installed.

## 🔄 Syncing Across Devices

To keep your PI configuration in sync across devices:

1. **After making changes on one device:**
   ```bash
   # Commit your changes
   cd ~/Documents/projects/numkil/dotfiles
   git add pi/
   git commit -m "Update PI configuration"
   git push
   ```

2. **On another device:**
   ```bash
   # Pull the latest changes and run the installer from the repo root
   cd ~/Documents/projects/numkil/dotfiles
   git pull
   ./install.sh
   ```

Package versions are pinned in `agent/settings.json`, so `./install.sh` installs
exact, reproducible versions on any machine.

## 🎨 Settings

Your `agent/settings.json` includes:

- **Model preferences**: Default provider (Mistral) and model (mistral-large-4)
- **Theme**: gruvbox-material-light
- **Thinking level**: high
- **UI preferences**: Fullscreen TUI mode, Mermaid streaming
- **Compaction**: Enabled with 16384 token reserve
- **Packages**: All installed npm packages

The file references the official settings schema (`https://pi.dev/schemas/settings.schema.json`)
for editor validation and completion.

## 💡 Pro Tips

1. **Use `/hotkeys`** to see all available keyboard shortcuts
2. **Use `/settings`** to adjust PI settings interactively
3. **Use `/tree`** to navigate session history
4. **Use `/compact`** to manually compact long conversations
5. **Use `Ctrl+L`** to switch models
6. **Use `Ctrl+P`/`Shift+Ctrl+P`** to cycle through scoped models
7. **Use `Shift+Tab`** to cycle thinking levels

## 📚 Resources

- [PI Documentation](https://pi.dev)
- [PI Package Catalog](https://pi.dev/packages)
- [PI GitHub](https://github.com/earendil-works/pi)

## 🔍 Troubleshooting

### Extensions not loading
- Check that the file is in `~/.pi/agent/extensions/`
- Run `pi --reload` to reload all extensions
- Check for TypeScript errors in the extension file

### Packages not installing
- Ensure npm is installed and working
- Check your network connection
- Try `pi install npm:package-name` manually
- Run `pi update --extensions` to update installed packages

### Settings not applying
- Verify `settings.json` is in `~/.pi/agent/`
- Run `pi --reload` to apply changes
- Check for JSON syntax errors in the file

## 📊 Installed Extensions Summary

| Extension | Purpose | Trigger |
|-----------|---------|---------|
| capability-reminder | Contextual tool reminders | Automatic |
| command-permissions | Dangerous command blocking | Bash commands |
| craft-skills-auto-load | Auto-load Craft skills | Craft projects |
| summarize | Conversation summary | `/summarize` |
| whimsical | Fun working messages | Thinking |

## 🎯 Craft CMS Workflow

For your Craft CMS development, these are the most useful commands:

- `/skill:craftcms` - General Craft CMS guidance
- `/skill:craft-php-guidelines` - PHP coding standards
- `/skill:craft-twig-guidelines` - Twig template conventions
- `/skill:craft-site` - Frontend component patterns
- `/skill:craft-content-modeling` - Content architecture
- `/skill:ddev` - Local development environment
- `/skill:craft-cloud` - Craft Cloud deployment
- `/skill:craft-plugins` - Plugin-specific guidance

Use these when PI suggests them via the capability reminder!
