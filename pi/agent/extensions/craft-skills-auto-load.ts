import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { readFileSync } from "node:fs";
import { join } from "node:path";

/**
 * Detects if a directory is a Craft CMS project by checking composer.json
 */
function isCraftProject(cwd: string): boolean {
  const composerPath = join(cwd, "composer.json");
  
  try {
    const composerContent = readFileSync(composerPath, "utf-8");
    const composer = JSON.parse(composerContent);
    
    // Check for Craft CMS type
    if (composer.type === "craft-plugin" || composer.type === "craft-module") {
      return true;
    }
    
    // Check for craftcms/cms requirement
    const requires = composer.require ?? {};
    if (requires["craftcms/cms"] !== undefined) {
      return true;
    }
    
    // Check for craftcms/cms in require-dev
    const requireDev = composer["require-dev"] ?? {};
    if (requireDev["craftcms/cms"] !== undefined) {
      return true;
    }
    
    return false;
  } catch {
    return false;
  }
}

/**
 * Get the global skills directory path
 */
function getGlobalSkillsDir(): string {
  const homeDir = process.env.HOME || process.env.USERPROFILE || "/";
  return join(homeDir, ".pi", "agent", "skills");
}

export default function (pi: ExtensionAPI) {
  pi.on("resources_discover", async (event, _ctx) => {
    // Only run on startup, not on reload (to avoid duplicate loading)
    if (event.reason !== "startup") {
      return {};
    }
    
    // Check if current directory is a Craft CMS project
    if (isCraftProject(event.cwd)) {
      const globalSkillsDir = getGlobalSkillsDir();
      
      // Return paths to all craft-related skills
      return {
        skillPaths: [
          join(globalSkillsDir, "craftcms"),
          join(globalSkillsDir, "craft-cloud"),
          join(globalSkillsDir, "craft-content-modeling"),
          join(globalSkillsDir, "craft-garnish"),
          join(globalSkillsDir, "craft-pest"),
          join(globalSkillsDir, "craft-php-guidelines"),
          join(globalSkillsDir, "craft-plugin-release"),
          join(globalSkillsDir, "craft-plugins"),
          join(globalSkillsDir, "craft-project-setup"),
          join(globalSkillsDir, "craft-site"),
          join(globalSkillsDir, "craft-twig-guidelines"),
          join(globalSkillsDir, "ddev"),
        ],
      };
    }
    
    return {};
  });

  pi.on("before_agent_start", (event, ctx) => {
    if (isCraftProject(ctx.cwd)) {
      return {
        systemPrompt: `This is a Craft CMS project. Immediately load the craftcms skill at the start of any task. For template work, also load craft-site and craft-twig-guidelines. For PHP work, also load craft-php-guidelines. For local development commands, also load ddev. ${event.systemPrompt}`,
      };
    }
    return {};
  });
}
