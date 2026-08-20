/**
 * Command Permission Gate Extension
 *
 * Prompts for confirmation before running potentially dangerous or sensitive bash commands.
 * Patterns checked: rm -rf, sudo, chmod/chown 777, dd, format, mkfs, reboot, shutdown,
 * writing to root, ssh, scp, curl, wget
 */

import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

export default function (pi: ExtensionAPI) {
	const requiresPermission = [
		// File system destruction
		/\brm\s+(-rf?|--recursive)/i,
		/\bdd\b/i,
		/:\s*format/i,
		/\bmkfs/i,
		
		// Privilege escalation
		/\bsudo\b/i,
		/\b(chmod|chown)\b.*777/i,
		
		// System control
		/\breboot/i,
		/\bshutdown/i,
		/\binit\s+[0-6]/i,
		/\bpoweroff/i,
		/\bhalt/i,
		
		// Root operations
		/\bmv\s+\/ /i,
		/\bcp\s+\/ /i,
		/\b>\s*\/ /i,
		/\b>>\s*\/ /i,
		
		// Network/remote access
		/\bssh\b/i,
		/\bscp\b/i,
		/\bcurl\b/i,
		/\bwget\b/i,
		/\bsftp\b/i,
		/\brsync\b/i,
		/\bnc\b/i,
		/\bnetcat\b/i,
		
		// Package managers (global installs)
		/\bnpm.*install.*--global/i,
		/\byarn.*global/i,
		/\bpip.*install.*--user/i,
		
		// Git (force operations)
		/\bgit.*push.*--force/i,
		/\bgit.*reset.*--hard/i,
		/\bgit.*rebase/i,
	];

	// Track confirmed commands per session to avoid re-prompting
	const confirmedCommands = new Set<string>();

	pi.on("tool_call", async (event, ctx) => {
		if (event.toolName !== "bash") return;

		const command = event.input.command as string;

		// Skip already confirmed commands in this session
		if (confirmedCommands.has(command)) return;

		const match = requiresPermission.find(p => p.test(command));
		if (!match) return;

		if (!ctx.hasUI) {
			return { block: true, reason: "Command requires permission (non-interactive mode)" };
		}

		const choice = await ctx.ui.select(
			`⚠️  Command requires permission:\n\n  ${command}\n\nAllow once?`,
			["Yes", "Yes, always for this session", "No"]
		);

		if (choice === "No") {
			return { block: true, reason: "Blocked by user" };
		}

		if (choice === "Yes, always for this session") {
			confirmedCommands.add(command);
		}
	});
}
