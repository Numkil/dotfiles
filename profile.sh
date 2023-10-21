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

# Enter a few characters and press UpArrow/DownArrow
# to search backwards/forwards through the history
if [[ ${SHELLOPTS} =~ (vi|emacs) ]]; then
    bind '"\e[A":history-search-backward'
    bind '"\e[B":history-search-forward'
fi

# Register composer on path
export PATH="$HOME/.composer/vendor/bin:$PATH"

# Set nvm directory
export NVM_DIR="${NVM_DIR:-$HOME/.nvm}"

# Determine correct bash completion script and set some OS specific settings
if [[ "${OSTYPE}" == 'darwin'* ]]; then
    bashCompletionScript="/opt/homebrew/etc/profile.d/bash_completion.sh"

    # Register nvm on path
    [ -s "/opt/homebrew/opt/nvm/nvm.sh" ] && source "/opt/homebrew/opt/nvm/nvm.sh"  # This loads nvm
    [ -s "/opt/homebrew/opt/nvm/etc/bash_completion.d/nvm" ] && source "/opt/homebrew/opt/nvm/etc/bash_completion.d/nvm"

    # Register brew on path
    eval $(/opt/homebrew/bin/brew shellenv)
else
    bashCompletionScript="/etc/profile.d/bash_completion.sh"

    # Register nvm on path
    [[ -s "$NVM_DIR/nvm.sh" ]] && source "$NVM_DIR/nvm.sh"
    [[ -s "$NVM_DIR/bash_completion" ]] && source "$NVM_DIR/bash_completion"
fi

# source thefuck command
eval $(thefuck --alias)

# Source our custom bash files and other usefull scripts
echo "Initializing Merel's bash setup. Check that all expected files are being sourced!"
files=(
    "${bashCompletionScript}"
    "${HOME}/.git-completion.sh"
    "${HOME}/.ssh-completion.sh"
    "${HOME}/.sudo.sh"
    "${HOME}/.helper-functions.sh"
    "${HOME}/.aliases.sh"
    "${HOME}/.prompt.sh"
)
for file in "${files[@]}"; do
    [ -r "$file" ] && echo "sourcing $file" && source "$file"
done
unset file