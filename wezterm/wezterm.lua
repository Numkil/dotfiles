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
-- This table will hold the configuration.
local config = {}

local os_name = _run_command("uname")
local IS_LINUX = os_name ~= "Darwin"

-- In newer versions of wezterm, use the config_builder which will
-- help provide clearer error messages
if wezterm.config_builder then
	config = wezterm.config_builder()
end

-- color scheme
config.color_scheme = "Everforest Light (Gogh)"

-- fonts
config.font_size = 12.4
config.line_height = 1.1
if IS_LINUX then
	config.font_size = 10
end
config.font = wezterm.font_with_fallback({
	{ family = "Hack Nerd Font Mono", weight = "Medium" },
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
