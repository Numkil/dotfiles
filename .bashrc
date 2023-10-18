####General definitions####
    # Make vim the default editor.
    export EDITOR='nvim';

    # Always use UTF8
    export LANG='en_US.UTF-8';

    # History, ignore duplicates, append
    export SHELL_SESSION_HISTORY=0
    export HISTSIZE="10000"
    export HISTFILESIZE="10000"
    export HISTCONTROL=$HISTCONTROL${HISTCONTROL+:}ignoredups
    shopt -s histappend

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
    for file in ~/.{'/opt/homebrew/etc/profile.d/bash_completion.sh','bash-git-completion.sh','bash-functions.sh','bash-aliases.sh','bash-prompt.sh'}; do
        [ -r "$file" ] && source "$file"
    done
