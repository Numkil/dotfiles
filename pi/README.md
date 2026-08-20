# PI Coding Agent Configuration

This directory contains your PI coding agent configuration, including extensions, settings, and skills.

## 📁 Structure

```
pi/
├── extensions/          # Custom TypeScript extensions
│   ├── capability-reminder.ts    # Shows contextual reminders for available tools
│   ├── command-permissions.ts   # Blocks dangerous bash commands
│   ├── craft-skills-auto-load.ts # Auto-loads Craft CMS skills
│   ├── minimal-footer.ts         # Clean, minimal status footer
│   ├── summarize.ts              # Conversation summarization
│   └── whimsical.ts              # Fun working messages
├── settings.json        # PI settings (models, themes, packages)
├── install.sh          # Installation script for new environments
└── README.md            # This file
```

## 🚀 Quick Setup

To set up PI on a new machine with your configuration:

### 1. Clone your dotfiles
```bash
# Clone your dotfiles repository
git clone <your-dotfiles-repo> ~/Documents/projects/numkil/dotfiles
```

### 2. Run the install script
```bash
# Navigate to the pi directory
cd ~/Documents/projects/numkil/dotfiles/pi

# Make executable (if not already)
chmod +x install.sh

# Run the installer
./install.sh
```

### 3. Restart PI
```bash
pi --reload
```

## 📦 Installed Packages

The following npm packages are configured in `settings.json` and will be automatically installed:

| Package | Purpose |
|---------|---------|
| `pi-hermes-memory` | Persistent memory with session search and secret scanning |
| `@narumitw/pi-lsp` | LSP integration for code intelligence |
| `pi-subagents` | Sub-agent delegation and multi-agent workflows |
| `@narumitw/pi-goal` | Autonomous goal-based task completion |
| `pi-web-access` | Web search, URL fetching, GitHub cloning, PDF extraction |
| `pi-vision-handoff` | Vision capabilities for image understanding |
| `pi-agent-browser-native` | Browser automation as a native tool |

## 🔧 Extensions

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

### minimal-footer.ts
Provides a clean, minimal footer showing:
- Current directory and git branch
- Active model and thinking level
- Context window usage with color-coded progress bar

### summarize.ts
Adds `/summarize` command to generate conversation summaries and `summarize_conversation` tool for LLM use.

### whimsical.ts
Displays fun, rotating working messages while PI is thinking (e.g., "Cogitating...", "Flibbertigibbeting...", "Reticulating splines...").

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
1. Create a new `.ts` file in the `extensions/` directory
2. Add it to your dotfiles
3. Run `install.sh` on the target machine

### Adding a new reminder
Edit `extensions/capability-reminder.ts` and add a new entry to the `DEFAULT_REMINDERS` array:

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
1. Install the package locally: `pi install npm:package-name`
2. Add it to `settings.json` under the `packages` array
3. Commit the updated `settings.json` to your dotfiles

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
   # Pull the latest changes
   cd ~/Documents/projects/numkil/dotfiles
   git pull
   
   # Run the installer
   cd pi
   ./install.sh
   ```

## 🎨 Settings

Your `settings.json` includes:

- **Model preferences**: Default provider (Mistral) and model (mistral-medium-3.5)
- **Theme**: gruvbox-material-light
- **Thinking level**: high
- **UI preferences**: Fullscreen display, Mermaid streaming
- **Compaction**: Enabled with 16384 token reserve
- **Packages**: All installed npm packages

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
| minimal-footer | Clean status footer | Always |
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
