eval $(/opt/homebrew/bin/brew shellenv)

####General definitions####
# Autocomplete using tab
[[ -r "/usr/local/etc/profile.d/bash_completion.sh" ]] && . "/usr/local/etc/profile.d/bash_completion.sh"

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

####FUNCTION#####

# mkdir, cd into it
function mkcd(){
    mkdir -p "$*"
    cd "$*"
}

# Convert all .mp3 files in a folder to .ogg files
function toogg(){
    for fic in *.mp3
    do
        ffmpeg -i "$fic" -acodec libvorbis -aq 60 -vsync 2 "${fic%.mp3}.ogg";
        rm "$fic"
    done
}

# Open last modified file in directory
function vimlast(){
    if [ -d $1 ] ; then
        SOURCE_DIR=`echo $1 | sed 's/^\/\(.*\)\/$/\1/g'`
        LAST_MODIFIED_FILE=`ls -ta ${SOURCE_DIR}| head -1`
        nvim $SOURCE_DIR/$LAST_MODIFIED_FILE
    else
        echo "no directory called $1"
    fi
}

# import db from designated folder into docker container
function importdb(){
    SOURCE_DIR=${PWD##*/}
    SOURCE_DIR=${SOURCE_DIR:-/}

    FILE=`ls ~/.databases/mysql/${SOURCE_DIR}| head -1`
    DB_PATH=~/.databases/mysql/$SOURCE_DIR/$FILE
    echo "Importing database $DB_PATH"
    ddev import-db --src=$DB_PATH
}

# download .env file to local host
function fetchfromlive(){
    SOURCE_DIR=${PWD##*/}
    SOURCE_DIR=${SOURCE_DIR:-/}

    echo "Downloading $1 from $SOURCE_DIR"
    scp ${SOURCE_DIR}livestatikbe@ssh.${SOURCE_DIR}.live.statik.be:/data/sites/web/${SOURCE_DIR}livestatikbe/subsites/${SOURCE_DIR}.live.statik.be/$1 $1
}

# Preserve environment when doing "sudo vim []"
function sudo() {
    case $* in
        vim* ) shift 1; command sudo -E vim "$@" ;;
        nvim* ) shift 1; command sudo -E nvim "$@" ;;
        * ) command sudo "$@" ;;
    esac
}

# Hide difficult logic behind extracting compressed folders
# Use the file extension to determine which command to use
function extract () {
    if [ -f $1 ] ; then
        case $1 in
            *.tar.gz)  tar xzf $1;;
            *.gz)      gunzip $1;;
            *.tar)     tar xf $1;;
            *.tgz)     tar xzf $1;;
            *.tar.bz2) tar xjf $1;;
            *.bz2)     bunzip2 $1;;
            *.rar)     rar x $1;;
            *.tbz2)    tar xjf $1;;
            *.zip)     unzip $1;;
            *.Z)       uncompress $1;;
            *)         echo "can't extract from $1";;
        esac
    else
        echo "no file called $1"
    fi
}

####ALIAS####

#Force rm interactive mode
alias rm="rm -i"
#Force rg case insensitive search
alias rg="rg -i"
#Lock the screen
alias afk="osascript -e 'tell application \"System Events\" to keystroke \"q\" using {command down,control down}'"
#Shortcut for my work folder
alias cdw="cd ~/Documents/projects"
#Always give ls in list form
alias lsa="ls -larth"
#Force nvim instead of vim
alias vim="nvim"
#shortcuts custom commands
alias ffl="fetchfromlive"
alias dbi="importdb"

####AWESOME BASH PROMPT####

if [[ ! "${prompt_colors[@]}" ]]; then
    prompt_colors=(
    "36" # information color
    "37" # bracket color
    "31" # error color
    )

    if [[ "$SSH_TTY" ]]; then
        # connected via ssh
        prompt_colors[0]="32"
    elif [[ "$USER" == "root" ]]; then
        # logged in as root
        prompt_colors[0]="35"
    fi
fi

# Inside a prompt function, run this alias to setup local $c0-$c9 color vars.
alias prompt_getcolors='prompt_colors[9]=; local i; for i in ${!prompt_colors[@]}; do local c$i="\[\e[0;${prompt_colors[$i]}m\]"; done'

# Exit code of previous command.
function prompt_exitcode() {
    prompt_getcolors
    [[ $1 != 0 ]] && echo " $c2$1$c9"
}

# Git status.
function prompt_git() {
    prompt_getcolors
    local status output flags branch
    status="$(git status 2>/dev/null)"
    [[ $? != 0 ]] && return;
    output="$(echo "$status" | awk '/# Initial commit/ {print "(init)"}')"
    [[ "$output" ]] || output="$(echo "$status" | awk '/# On branch/ {print $4}')"
    [[ "$output" ]] || output="$(git branch | perl -ne '/^\* \(detached from (.*)\)$/ ? print "($1)" : /^\* (.*)/ && print $1')"
    flags="$(
    echo "$status" | awk 'BEGIN {r=""} \
        /^(# )?Changes to be committed:$/        {r=r "+"}\
        /^(# )?Changes not staged for commit:$/  {r=r "!"}\
        /^(# )?Untracked files:$/                {r=r "?"}\
    END {print r}'
    )"
    if [[ "$flags" ]]; then
        output="$output$c1:$c0$flags"
    fi
    echo "$c1[$c0$output$c1]$c9"
}

# hg status.
function prompt_hg() {
    prompt_getcolors
    local summary output bookmark flags
    summary="$(hg summary 2>/dev/null)"
    [[ $? != 0 ]] && return;
    output="$(echo "$summary" | awk '/branch:/ {print $2}')"
    bookmark="$(echo "$summary" | awk '/bookmarks:/ {print $2}')"
    flags="$(
    echo "$summary" | awk 'BEGIN {r="";a=""} \
        /(modified)/     {r= "+"}\
        /(unknown)/      {a= "?"}\
    END {print r a}'
    )"
    output="$output:$bookmark"
    if [[ "$flags" ]]; then
        output="$output$c1:$c0$flags"
    fi
    echo "$c1[$c0$output$c1]$c9"
}

# SVN info.
function prompt_svn() {
    prompt_getcolors
    local info="$(svn info . 2> /dev/null)"
    local last current
    if [[ "$info" ]]; then
        last="$(echo "$info" | awk '/Last Changed Rev:/ {print $4}')"
        current="$(echo "$info" | awk '/Revision:/ {print $2}')"
        echo "$c1[$c0$last$c1:$c0$current$c1]$c9"
    fi
}

# Maintain a per-execution call stack.
prompt_stack=()
trap 'prompt_stack=("${prompt_stack[@]}" "$BASH_COMMAND")' DEBUG

function prompt_command() {
    local exit_code=$?
    # If the first command in the stack is prompt_command, no command was run.
    # Set exit_code to 0 and reset the stack.
    [[ "${prompt_stack[0]}" == "prompt_command" ]] && exit_code=0
    prompt_stack=()

    # Manually load z here, after $? is checked, to keep $? from being clobbered.
    [[ "$(type -t _z)" ]] && _z --add "$(pwd -P 2>/dev/null)" 2>/dev/null

    # While the simple_prompt environment var is set, disable the awesome prompt.
    [[ "$simple_prompt" ]] && PS1='\n$ ' && return

    prompt_getcolors
    # http://twitter.com/cowboy/status/150254030654939137
    PS1=""
    # path: [user@host:path]
    PS1="$PS1$c1[$c0\u$c1:$c0\w$c1]$c9"
    PS1="$PS1\n"
    # svn: [repo:lastchanged]
    PS1="$PS1$(prompt_svn)"
    # git: [branch:flags]
    PS1="$PS1$(prompt_git)"
    # hg:  [branch:flags]
    PS1="$PS1$(prompt_hg)"
    # date: [HH:MM:SS]
    PS1="$PS1$c1[$c0$(date +"%H$c1:$c0%M$c1:$c0%S")$c1]$c9"
    # exit code: 127
    PS1="$PS1$(prompt_exitcode "$exit_code")"
    PS1="$PS1 \$ "
}

PROMPT_COMMAND="prompt_command"

eval $(thefuck --alias)
