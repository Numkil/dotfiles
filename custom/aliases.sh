####ALIAS####

#Force rm interactive mode
alias rm="rm -i"
#Force rg case insensitive search
alias rg="rg -i"
#Lock the screen
alias afk="osascript -e 'tell application \"System Events\" to keystroke \"q\" using {command down,control down}'"
#Prefer bat binary over cat
alias cat="bat"
#Prefer lsd binary over ls
alias ls="lsd"
#ls with more options
alias lsa="lsd -larth"
#ls in a full tree form!
alias lst="lsd --tree"
#Force nvim instead of vim
alias vim="nvim"
alias v="nvim"
#shortcuts custom commands
alias ffl="fetchfromlive"
alias sshl="sshtolive"
alias dbi="importdb"
alias dbe="exportdb"
alias user="ddev craft users/create --admin=1 --email=tje@tje.tje --password=FakePassword12!@ --interactive=0"
alias redo="ddev stop -aRO && ddev start && dbi && ddev craft up && user"
#git aliases
alias push='git push origin $(git branch --show-current)'
alias pull='git pull origin $(git branch --show-current)'
alias gcd='git checkout develop'
alias gcm='git checkout $(get_default_branch)'

###OTHER KEYBINDINGS###

# Enter a few characters and press UpArrow/DownArrow
# to search backwards/forwards through the history
if [[ ${SHELLOPTS} =~ (vi|emacs) ]]; then
    bind '"\e[A":history-search-backward'
    bind '"\e[B":history-search-forward'
fi

