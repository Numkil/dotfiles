# Make vim the default editor.
export EDITOR='nvim';

# Always use UTF8
export LANG='en_US.UTF-8';

# Git completion should function case insensitive
export GIT_COMPLETION_IGNORE_CASE=1

# Define where we will configure ripgrep for our purposes
export RIPGREP_CONFIG_PATH="${HOME}/.config/ripgrep/config"

# History, ignore duplicates, append
export SHELL_SESSION_HISTORY=0
export HISTSIZE="10000"
export HISTFILESIZE="10000"
export HISTCONTROL=$HISTCONTROL${HISTCONTROL+:}ignoredups
shopt -s histappend

# Set the colours to use in prompt
export TERM="wezterm"

# Disable bell
bind "set bell-style visible"
# Ignore case on auto-completion
bind "set completion-ignore-case on"
# Show auto-completion list automatically, without double
bind "set show-all-if-ambiguous On"

