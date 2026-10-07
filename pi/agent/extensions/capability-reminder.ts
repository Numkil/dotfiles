/**
 * Capability Reminder Extension
 * 
 * Suggests relevant PI extensions/commands based on user intent.
 * Shows subtle reminders like "Remember: use /goal for autonomous task completion"
 * 
 * Features:
 * - Intent detection from user prompts
 * - Configurable keyword -> reminder mappings
 * - Rate limiting to avoid spam
 * - Non-intrusive status messages
 */

import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

// ============================================================================
// Configuration
// ============================================================================

interface ReminderConfig {
  // Keywords that trigger this reminder
  keywords: string[];
  // The reminder message to show
  message: string;
  // Minimum interval between showing this reminder (in messages)
  cooldown: number;
  // Priority (higher = shown first when multiple match)
  priority: number;
  // Should this reminder be shown in the status bar or as a notification?
  type: "status" | "notify";
}

interface ReminderState {
  // Track last shown message index for each reminder
  lastShown: Map<string, number>;
  // Track if reminder was acted upon (user used the command)
  actedUpon: Map<string, boolean>;
}

// Default reminders for your installed extensions
const DEFAULT_REMINDERS: ReminderConfig[] = [
  // ========================================================================
  // Goal & Sub-agents (High Priority)
  // ========================================================================
  
  // Goal-based autonomous work
  {
    keywords: [
      "build", "create", "implement", "develop", "make", 
      "write a", "write the", "add a", "add the",
      "new feature", "new functionality", "feature request",
      "task", "todo", "need to", "should", "must",
      "complete", "finish", "do this", "handle",
      "migrate", "upgrade", "refactor", "restructure",
      "set up", "configure", "install", "setup",
      "fix", "debug", "solve", "resolve",
    ],
    message: "Remember: use /goal for autonomous task completion",
    cooldown: 5,
    priority: 10,
    type: "status",
  },
  
  // Sub-agents for delegation
  {
    keywords: [
      "big", "large", "complex", "complicated", "multi-part",
      "multiple", "several", "many", "parallel",
      "delegate", "split", "divide", "break down",
      "at the same time", "simultaneously",
      "frontend and backend", "both", "also need",
    ],
    message: "Remember: use /subagent to delegate parts of this work",
    cooldown: 5,
    priority: 9,
    type: "status",
  },
  
  // ========================================================================
  // Memory (High Priority)
  // ========================================================================
  
  // Memory for knowledge retention
  {
    keywords: [
      "remember", "recall", "keep in mind", "note", "noted",
      "save this", "store this", "don't forget",
      "important", "crucial", "key point",
      "decision", "chose", "decided", "agreed",
      "lesson learned", "best practice", "convention",
    ],
    message: "Remember: use /memory:add to store this in long-term memory",
    cooldown: 3,
    priority: 8,
    type: "status",
  },
  
  // Memory search
  {
    keywords: [
      "how did we", "what did we", "where was", "find", "locate",
      "search", "look for", "previous", "earlier", "before",
      "similar", "like this", "example", "reference",
      "recall", "remember when", "did we do",
    ],
    message: "Remember: use /memory:search to find past conversations",
    cooldown: 4,
    priority: 7,
    type: "status",
  },
  
  // ========================================================================
  // Craft CMS Specific (High Priority for your workflow)
  // ========================================================================
  
  // Craft CMS general
  {
    keywords: [
      "craft cms", "craft5", "craft 5", "craftcms",
      "entry", "entries", "section", "sections",
      "field", "fields", "matrix", "category", "categories",
      "asset", "assets", "volume", "volumes",
      "user", "users", "element", "elements",
      "twig", "template", "templates",
      "plugin", "plugins", "module", "modules",
      "config", "configuration", "general.php",
      "composer", "composer.json",
    ],
    message: "Remember: use /skill:craftcms for Craft CMS guidance",
    cooldown: 5,
    priority: 10,
    type: "status",
  },
  
  // PHP development
  {
    keywords: [
      "php", "php 8", "class", "method", "function",
      "service", "services", "model", "models",
      "record", "records", "migration", "migrations",
      "validation", "rules", "behavior", "behaviors",
      "event", "events", "hook", "hooks",
      "yii", "yii2",
    ],
    message: "Remember: use /skill:craft-php-guidelines for PHP best practices",
    cooldown: 5,
    priority: 9,
    type: "status",
  },
  
  // Twig templates
  {
    keywords: [
      "twig", "template", "templates", ".twig",
      "include", "embed", "extends", "block",
      "macro", "macros", "filter", "filters",
      "variable", "variables", "loop", "for",
      "if", "unless", "set", "dump",
      "component", "components", "atomic",
      "props", "extends", "only",
    ],
    message: "Remember: use /skill:craft-twig-guidelines for Twig conventions",
    cooldown: 5,
    priority: 9,
    type: "status",
  },
  
  // Frontend (Next.js, Astro, Tailwind)
  {
    keywords: [
      "next.js", "nextjs", "react", "typescript", "tsx",
      "astro", "component", "components",
      "tailwind", "css", "style", "styles",
      "vite", "build", "bundler",
      "frontend", "ui", "interface",
    ],
    message: "Remember: use /skill:craft-site for frontend component patterns",
    cooldown: 5,
    priority: 8,
    type: "status",
  },
  
  // DDEV local development
  {
    keywords: [
      "ddev", "local", "development", "dev environment",
      "container", "containers", "docker",
      "database", "db", "mysql", "mariadb",
      "xdebug", "debug", "phpmyadmin", "mailpit",
      "start", "stop", "restart", "exec",
      "import-db", "export-db", "backup",
    ],
    message: "Remember: use /skill:ddev for local development commands",
    cooldown: 5,
    priority: 8,
    type: "status",
  },
  
  // Craft Cloud
  {
    keywords: [
      "craft cloud", "cloud", "pixel & tonic",
      "deploy", "deployment", "release",
      "build", "migrate", "migration",
      "environment", "environments", "preview",
      "ephemeral", "filesystem", "s3",
      "cdn", "cache", "static",
      "edge", "image transforms",
    ],
    message: "Remember: use /skill:craft-cloud for Craft Cloud deployment",
    cooldown: 5,
    priority: 8,
    type: "status",
  },
  
  // Craft Content Modeling
  {
    keywords: [
      "content model", "modeling", "content architecture",
      "section type", "single", "channel", "structure",
      "entry type", "field layout", "field type",
      "matrix", "nested", "relations", "related to",
      "eager loading", "with", "eagerly",
      "propagation", "multi-site", "localization",
      "project config", "yaml", "config",
    ],
    message: "Remember: use /skill:craft-content-modeling for content architecture",
    cooldown: 5,
    priority: 8,
    type: "status",
  },
  
  // Craft Plugins
  {
    keywords: [
      "plugin", "plugins", "formie", "seomatic", "blitz",
      "feed me", "imager", "image optimize",
      "navigation", "retour", "hyper",
      "sprig", "element api", "typogrify",
      "color swatches", "password policy",
      "custom field", "field type", "widget",
    ],
    message: "Remember: use /skill:craft-plugins for plugin-specific guidance",
    cooldown: 5,
    priority: 8,
    type: "status",
  },
  
  // ========================================================================
  // General Development
  // ========================================================================
  
  // LSP for code intelligence
  {
    keywords: [
      "why is this", "what does this", "how does this",
      "error", "warning", "type error", "undefined",
      "syntax", "lint", "check", "validate", "verify",
      "autocomplete", "suggestion", "intellisense",
      "go to definition", "hover", "documentation",
      "refactor", "rename", "extract",
    ],
    message: "Remember: LSP is active - use your editor or ask about code",
    cooldown: 5,
    priority: 6,
    type: "status",
  },
  
  // Web access for research
  {
    keywords: [
      "documentation", "docs", "manual", "guide",
      "tutorial", "example", "reference", "spec",
      "check online", "look up", "research", "google",
      "what is", "how to", "best way", "recommendation",
      "latest", "new version", "update", "changelog",
    ],
    message: "Remember: use /skill:web-search for documentation and research",
    cooldown: 5,
    priority: 7,
    type: "status",
  },
  
  // Git operations
  {
    keywords: [
      "git", "commit", "push", "pull", "merge",
      "branch", "checkout", "stash", "rebase",
      "version control", "checkpoint", "save progress",
    ],
    message: "Remember: git operations available - ask for help with version control",
    cooldown: 3,
    priority: 5,
    type: "status",
  },
];

// ============================================================================
// Extension Implementation
// ============================================================================

export default function (pi: ExtensionAPI) {
  const state: ReminderState = {
    lastShown: new Map(),
    actedUpon: new Map(),
  };

  // Current message index (incremented on each user message)
  let messageIndex = 0;

  // Track which commands the user has used
  const usedCommands = new Set<string>();

  // ==========================================================================
  // Helper Functions
  // ==========================================================================

  /**
   * Normalize text for matching (lowercase, remove punctuation)
   */
  function normalizeText(text: string): string {
    return text
      .toLowerCase()
      .replace(/[.,\/#!$%\^&\*;:{}=\_`~()]/g, "")
      .replace(/\s+/g, " ");
  }

  /**
   * Check if any keyword matches the text
   */
  function matchesAnyKeyword(text: string, keywords: string[]): boolean {
    const normalized = normalizeText(text);
    return keywords.some(keyword => normalized.includes(normalizeText(keyword)));
  }

  /**
   * Get the best matching reminder for a message
   */
  function getBestReminder(message: string): ReminderConfig | null {
    const normalizedMessage = normalizeText(message);
    
    // Filter reminders that match and aren't in cooldown
    const candidates = DEFAULT_REMINDERS.filter(reminder => {
      const lastShown = state.lastShown.get(reminder.message) ?? -Infinity;
      const inCooldown = messageIndex - lastShown < reminder.cooldown;
      return matchesAnyKeyword(message, reminder.keywords) && !inCooldown;
    });

    if (candidates.length === 0) return null;

    // Sort by priority (descending) and pick the highest
    candidates.sort((a, b) => b.priority - a.priority);
    return candidates[0];
  }

  /**
   * Show a reminder to the user
   */
  function showReminder(reminder: ReminderConfig, ctx: any) {
    // Mark as shown
    state.lastShown.set(reminder.message, messageIndex);

    // Show based on type
    if (reminder.type === "notify") {
      ctx.ui.notify(reminder.message, "info");
    } else {
      // Use status bar - show for 8 seconds
      ctx.ui.setStatus("reminder", reminder.message);
      
      // Clear after 8 seconds
      setTimeout(() => {
        ctx.ui.setStatus("reminder", undefined);
      }, 8000);
    }
  }

  // ==========================================================================
  // Event Handlers
  // ==========================================================================

  // Track user messages for intent detection
  pi.on("input", async (event, ctx) => {
    // Only process user messages (not system, not assistant)
    if (event.source !== "user") return;

    const message = event.message;
    if (!message || typeof message !== "string") return;

    // Increment message counter
    messageIndex++;

    // Check for command usage (e.g., "/goal", "/memory:search")
    const commandMatch = message.match(/^\/(\w+(?:\:\w+)*)/);
    if (commandMatch) {
      usedCommands.add(commandMatch[1]);
      
      // If user used a reminded command, mark it as acted upon
      for (const reminder of DEFAULT_REMINDERS) {
        if (reminder.message.includes(commandMatch[1])) {
          state.actedUpon.set(reminder.message, true);
        }
      }
      return; // Don't show reminders for explicit commands
    }

    // Get the best reminder
    const reminder = getBestReminder(message);
    if (reminder) {
      showReminder(reminder, ctx);
    }
  });

  // Reset message index on new session
  pi.on("session_start", async (_event, _ctx) => {
    messageIndex = 0;
  });

  // Clear status on agent start (new prompt)
  pi.on("agent_start", async (_event, ctx) => {
    ctx.ui.setStatus("reminder", undefined);
  });

  // ==========================================================================
  // Commands
  // ==========================================================================

  // Command to show all available reminders
  pi.registerCommand("reminders", {
    description: "Show all available capability reminders",
    handler: async (_args, ctx) => {
      const lines = [
        "=== Capability Reminders ===",
        "",
        "These commands/tools are available:",
        "",
        "• /goal - Autonomous task completion",
        "• /subagent - Delegate work to sub-agents",
        "• /memory:add - Store in long-term memory",
        "• /memory:search - Search past conversations",
        "• /skill:web-search - Web search and research",
        "• LSP - Code intelligence (active in background)",
        "",
        "Type /reminders:list to see all mappings",
      ];
      
      ctx.ui.notify(lines.join("\n"), "info");
    },
  });

  // Command to list all reminder mappings
  pi.registerCommand("reminders:list", {
    description: "List all reminder keyword mappings",
    handler: async (_args, ctx) => {
      const lines = [
        "=== Reminder Mappings ===",
        "",
        ...DEFAULT_REMINDERS.map(r => {
          return `• ${r.message} (priority: ${r.priority}, cooldown: ${r.cooldown})`;
        }),
        "",
        `Total: ${DEFAULT_REMINDERS.length} active reminders`,
      ];
      
      ctx.ui.notify(lines.join("\n"), "info");
    },
  });

  // Command to test a message
  pi.registerCommand("reminders:test", {
    description: "Test reminder detection on a message",
    handler: async (args, ctx) => {
      if (!args) {
        ctx.ui.notify("Usage: /reminders:test <your message>", "warning");
        return;
      }

      const reminder = getBestReminder(args);
      if (reminder) {
        ctx.ui.notify(`Match: ${reminder.message}`, "info");
      } else {
        ctx.ui.notify("No reminder matched this message", "info");
      }
    },
  });

  // ==========================================================================
  // Expose state for debugging
  // ==========================================================================

  // This allows other extensions to access the reminder system
  (pi as any)._capabilityReminder = {
    getReminders: () => DEFAULT_REMINDERS,
    getState: () => state,
    getMessageIndex: () => messageIndex,
    addReminder: (config: ReminderConfig) => {
      DEFAULT_REMINDERS.push(config);
    },
    removeReminder: (message: string) => {
      const index = DEFAULT_REMINDERS.findIndex(r => r.message === message);
      if (index > -1) {
        DEFAULT_REMINDERS.splice(index, 1);
      }
    },
  };
}
