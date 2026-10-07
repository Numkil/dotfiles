import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

export default function (pi: ExtensionAPI) {
  pi.on("session_start", async (_event, _ctx) => {
    await pi.sendMessage("/caveman");
  });
}
