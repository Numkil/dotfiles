-- function to call a system function
local function _run_command(cmd)
	local f = assert(io.popen(cmd, "r"))
	local s = assert(f:read("*a"))
	f:close()
	s = string.gsub(s, "^%s+", "")
	s = string.gsub(s, "%s+$", "")
	s = string.gsub(s, "[\n\r]+", "")
	return s
end

-- Pull in the wezterm API
local wezterm = require("wezterm")
local act = wezterm.action
-- The wezterm config_builder will help provide clearer error messages
local config = wezterm.config_builder()

local os_name = _run_command("uname")
local is_linux = os_name ~= "Darwin"

-- color scheme
config.color_scheme = "Everforest Light (Gogh)"

-- fonts
config.font_size = 12.5
config.line_height = 1
if is_linux then
	config.font_size = 10
end
config.font = wezterm.font_with_fallback({
	"Monaspace Neon",
	"JetBrains Mono",
})

-- tab stuff
config.tab_max_width = 24
config.use_fancy_tab_bar = false

-- window decoration
config.scrollback_lines = 200000
config.window_decorations = "RESIZE" -- no title bar
config.window_padding = {
	left = "0.5cell",
	right = "0.5cell",
	top = "0",
	bottom = "0",
}

-- keybindings
config.use_dead_keys = false
config.keys = {
	{
		key = "C",
		mods = "ALT",
		action = act.AdjustPaneSize({ "Up", 5 }),
	},
	{
		key = "B",
		mods = "ALT",
		action = act.AdjustPaneSize({ "Down", 5 }),
	},
	{
		key = "V",
		mods = "ALT",
		action = act.SplitVertical({ domain = "CurrentPaneDomain" }),
	},
}

-- and finally, return the configuration to wezterm
return config
