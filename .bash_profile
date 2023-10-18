####General definitions####
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

# enter a few characters and press UpArrow/DownArrow
# to search backwards/forwards through the history
if [[ ${SHELLOPTS} =~ (vi|emacs) ]]; then
	bind '"\e[A":history-search-backward'
	bind '"\e[B":history-search-forward'
fi

# Make sure composer and nvm available on path
export PATH="$HOME/.composer/vendor/bin:$PATH"
export NVM_DIR="$HOME/.nvm"
  [ -s "/opt/homebrew/opt/nvm/nvm.sh" ] && \. "/opt/homebrew/opt/nvm/nvm.sh"  # This loads nvm
  [ -s "/opt/homebrew/opt/nvm/etc/bash_completion.d/nvm" ] && \. "/opt/homebrew/opt/nvm/etc/bash_completion.d/nvm"

#init homebrew
eval $(/opt/homebrew/bin/brew shellenv)

# source thefuck command
eval $(thefuck --alias)

# Source our custom bash files and other usefull scripts
echo "Initializing Merel's bash setup. Check that all expected files are being sourced!" 
files=(
  "/opt/homebrew/etc/profile.d/bash_completion.sh"
  "${HOME}/bash-git-completion.sh"
  "${HOME}/bash-ssh-completion.sh"
  "${HOME}/bash-functions.sh"
  "${HOME}/bash-aliases.sh"
  "${HOME}/bash-prompt.sh"
)
for file in "${files[@]}"; do
    [ -r "$file" ] && echo "sourcing $file" && source "$file"
done
unset file
