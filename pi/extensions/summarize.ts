/**
 * Conversation Summarizer Extension
 *
 * Adds /summarize command to generate a summary of the current conversation.
 * Uses the current active model.
 */

import type { ExtensionAPI, ExtensionCommandContext } from "@earendil-works/pi-coding-agent";

export default function (pi: ExtensionAPI) {
	pi.registerCommand("summarize", {
		description: "Summarize the current conversation",
		handler: async (_args, ctx) => {
			const branch = ctx.sessionManager.getBranch();
			const conversationText = buildConversationText(branch);

			if (!conversationText.trim()) {
				ctx.ui.notify("No conversation to summarize", "warning");
				return;
			}

			ctx.ui.notify("Generating summary...", "info");

			const prompt = [
				"Summarize this conversation so I can resume it later.",
				"Include goals, key decisions, progress, open questions, and next steps.",
				"Keep it concise and structured with headings.",
				"",
				"<conversation>",
				conversationText,
				"</conversation>",
			].join("\n");

			// Send as a user message to get a summary from the current model
			await ctx.sendUserMessage(prompt);
		},
	});

	// Also add a tool that the LLM can call
	pi.registerTool({
		name: "summarize_conversation",
		label: "Summarize Conversation",
		description: "Generate a summary of the current conversation for context",
		parameters: {},
		async execute(_toolCallId, _params, _signal, _onUpdate, ctx) {
			const branch = (ctx as unknown as ExtensionCommandContext).sessionManager.getBranch();
			const conversationText = buildConversationText(branch);

			if (!conversationText.trim()) {
				return {
					content: [{ type: "text", text: "No conversation to summarize." }],
					details: {},
				};
			}

			const prompt = [
				"Summarize this conversation in 3-5 bullet points for context.",
				"Focus on key decisions, current state, and next steps.",
				"",
				"<conversation>",
				conversationText,
				"</conversation>",
			].join("\n");

			return {
				content: [{ type: "text", text: prompt }],
				details: {},
			};
		},
	});
}

function buildConversationText(entries: any[]): string {
	const sections: string[] = [];

	for (const entry of entries) {
		if (entry.type !== "message" || !entry.message?.role) {
			continue;
		}

		const role = entry.message.role;
		const isUser = role === "user";
		const isAssistant = role === "assistant";

		if (!isUser && !isAssistant) {
			continue;
		}

		const roleLabel = isUser ? "User" : "Assistant";
		const content = entry.message.content;

		if (!content || typeof content !== "object") {
			continue;
		}

		const textParts: string[] = [];
		const toolCalls: string[] = [];

		if (Array.isArray(content)) {
			for (const part of content) {
				if (!part || typeof part !== "object") {
					continue;
				}
				if (part.type === "text" && typeof part.text === "string") {
					textParts.push(part.text);
				} else if (part.type === "toolCall" && typeof part.name === "string") {
					toolCalls.push(`Tool: ${part.name}`);
				}
			}
		}

		const messageText = textParts.join("").trim();
		if (messageText.length > 0) {
			sections.push(`${roleLabel}: ${messageText}`);
		}
		if (toolCalls.length > 0) {
			sections.push(toolCalls.join(", "));
		}
	}

	return sections.join("\n\n");
}
