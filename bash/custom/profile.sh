#### INITIALIZING FILE ####
#
echo "Initializing Merel's bash setup. Check that all expected files are being sourced!"

# Load shell options before anything else
file="${HOME}/.options.sh"
[ -r "$file" ] && echo "sourcing $file" && source "$file"

# Register composer on path
export PATH="$HOME/.composer/vendor/bin:$PATH"

# Register rust binaries on path
export PATH="$HOME/.cargo/bin:$PATH"

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
    export NVM_DIR="${NVM_DIR:-$HOME/.nvm}"
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
