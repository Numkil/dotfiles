#### INITIALIZING FILE ####

# Make vim the default editor.
export EDITOR='nvim';

# Always use UTF8
export LANG='en_US.UTF-8';

# Git completion should function case insensitive
export GIT_COMPLETION_IGNORE_CASE=1

# History, ignore duplicates, append
export SHELL_SESSION_HISTORY=0
export HISTSIZE="10000"
export HISTFILESIZE="10000"
export HISTCONTROL=$HISTCONTROL${HISTCONTROL+:}ignoredups
shopt -s histappend

# Set the colours to use in prompt
if [[ $COLORTERM = gnome-* && $TERM = xterm ]] && infocmp gnome-256color >/dev/null 2>&1; then
    export TERM=gnome-256color
elif infocmp xterm-256color >/dev/null 2>&1; then
    export TERM=xterm-256color
fi

# Register composer on path
export PATH="$HOME/.composer/vendor/bin:$PATH"

# Set nvm directory
export NVM_DIR="${NVM_DIR:-$HOME/.nvm}"

# Define where we will configure ripgrep for our purposes
export RIPGREP_CONFIG_PATH="${HOME}/.config/ripgrep/config"

# Determine correct bash completion script and set some OS specific settings
if [[ "${OSTYPE}" == 'darwin'* ]]; then
    # Register brew on path
    eval $(/opt/homebrew/bin/brew shellenv)

    HOMEBREW_PREFIX="$(brew --prefix)"
    completionfile="${HOMEBREW_PREFIX}/etc/profile.d/bash_completion.sh"

    # Register nvm on path
    [ -s "${HOMEBREW_PREFIX}/opt/nvm/nvm.sh" ] && source "${HOMEBREW_PREFIX}/opt/nvm/nvm.sh"  # This loads nvm
    [ -s "${HOMEBREW_PREFIX}/opt/nvm/etc/bash_completion.d/nvm" ] && source "${HOMEBREW_PREFIX}/opt/nvm/etc/bash_completion.d/nvm"

else
    completionfile="/etc/profile.d/bash_completion.sh"

    # Register nvm on path
    [[ -s "$NVM_DIR/nvm.sh" ]] && source "$NVM_DIR/nvm.sh"
    [[ -s "$NVM_DIR/bash_completion" ]] && source "$NVM_DIR/bash_completion"

    # Make sure that the local bin folder is on the path
    export PATH="$HOME/.local/bin:$PATH"

    # Make sure wezterm is executable
    alias wezterm='flatpak run org.wezfurlong.wezterm'
fi

# Source thefuck command
eval $(thefuck --alias)

# Source our custom bash files and other usefull scripts
echo "Initializing Merel's bash setup. Check that all expected files are being sourced!"
files=(
    "${completionfile}"
    "${HOME}/.git-completion.sh"
    "${HOME}/.ssh-completion.sh"
    "${HOME}/.sudo.sh"
    "${HOME}/.helper-functions.sh"
    "${HOME}/.aliases.sh"
)
for file in "${files[@]}"; do
    [ -r "$file" ] && echo "sourcing $file" && source "$file"
done
unset file

# Launching starship
eval "$(starship init bash)"
