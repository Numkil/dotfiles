####FUNCTIONS#####

# go straight to project folder or into a project
function cdw(){
    if [ -n $1 ]; then
        cd ~/Documents/projects/$1
    else
        cd ~/Documents/projects
    fi
}

# mkdir, cd into it
function mkcd(){
    mkdir -p "$*"
    cd "$*"
}

function nukeModulesAndLogs(){
    cd ~/Documents/projects
    echo "Nuking logs"
    find . -path '*/storage/logs' -type d -prune -exec rm -rf '{}' +
    echo "Nuking modules"
    find . -name 'node_modules' -type d -prune -exec rm -rf '{}' +
}

function copyCombellDb(){
    SOURCE_DIR=${PWD##*/}
    SOURCE_DIR=~/.databases/mysql/${SOURCE_DIR:-/}

    FILE=`ls ~/Downloads/com-linweb*| head -1`
    echo "Moving $FILE to $SOURCE_DIR"
    rm -rf $SOURCE_DIR/*
    mv $FILE $SOURCE_DIR
}

# checkout git branch/tag, with a preview showing the commits between the tag/branch and HEAD
checkoutGitBranchViaFzf() {
  local tags branches target
  branches=$(
    git --no-pager branch --all \
      --format="%(if)%(HEAD)%(then)%(else)%(if:equals=HEAD)%(refname:strip=3)%(then)%(else)%1B[0;34;1mbranch%09%1B[m%(refname:short)%(end)%(end)" \
    | sed '/^$/d') || return
  tags=$(
    git --no-pager tag | awk '{print "\x1b[35;1mtag\x1b[m\t" $1}') || return
  target=$(
    (echo "$branches"; echo "$tags") |
    fzf --no-hscroll --no-multi -n 2 \
        --ansi --preview="git --no-pager log -150 --pretty=format:%s '..{2}'") || return
  git checkout $(awk '{print $2}' <<<"$target" )
}


# fuzzy grep open via rg with line number, and preview
openViaRg() {
  local file

  file="$(rg --no-heading $@ | fzf -0 -1 | awk -F: '{print $1}')"

  if [[ -n $file ]]
  then
     nvim $file
  fi
}

# Show a list of directories and cd into it when selected via fzf
cdViaFzf() {
  local dir
  dir=$(find ${1:-.} -path '*/\.*' -prune \
                  -o -type d -print 2> /dev/null | fzf +m) &&
  cd "$dir"
}

# import db from designated folder into docker container
function importdb(){
    SOURCE_DIR=${PWD##*/}
    SOURCE_DIR=${SOURCE_DIR:-/}

    FILE=`ls ~/.databases/mysql/${SOURCE_DIR}| head -1`
    DB_PATH=~/.databases/mysql/$SOURCE_DIR/$FILE
    echo "Importing database $DB_PATH"
    ddev import-db --file=$DB_PATH
}

# export db into designated folder from docker container
function exportdb(){
    SOURCE_DIR=${PWD##*/}
    SOURCE_DIR=${SOURCE_DIR:-/}

    FILE=`ls ~/.databases/mysql/${SOURCE_DIR}| head -1`
    DB_PATH=~/.databases/mysql/$SOURCE_DIR/$FILE
    echo "Exporting database to $DB_PATH"
    ddev export-db --gzip=false --file=$DB_PATH
}

# download .env file to local host
function fetchfromlive(){
    SOURCE_DIR=${PWD##*/}
    SOURCE_DIR=${SOURCE_DIR:-/}

    echo "Downloading $1 from $SOURCE_DIR"
    scp -r ${SOURCE_DIR}livestatikbe@${SOURCE_DIR}.ssh.statik.be:/data/sites/web/${SOURCE_DIR}livestatikbe/subsites/${SOURCE_DIR}.live.statik.be/$1 $1
}

# ssh to the project without having to remember hostname
function sshtolive(){
    SOURCE_DIR=${PWD##*/}
    SOURCE_DIR=${SOURCE_DIR:-/}

    echo "Sshing to $SOURCE_DIR"
    ssh ${SOURCE_DIR}livestatikbe@${SOURCE_DIR}.ssh.statik.be
}

# basics of setting up a project
function setupproject(){
    if [ -n $1 ]; then
        echo "Cloning project"
        git clone git@bitbucket.org:statikbe/$1.git
        cd $1
        echo "Moving database file from downloads to dedicated folder"
        mkdir -p ~/.databases/mysql/$1
        mv ~/Downloads/com*.sql ~/.databases/mysql/$1/
        echo "Fetching .env file"
        fetchfromlive .env
        echo "Spinning up project!"
        ddev stop -aRO
        ddev get ddev/ddev-phpmyadmin
        ddev start
        importdb
        echo "Installing vendor files"
        ddev composer install
    else
        echo "Provide at least one argument"
    fi
}

function get_default_branch() {
    if git branch | grep -q '^. main\s*$'; then
        echo main
    else
        echo master
    fi
}

# release develop branch to master
function release() {
    RELEASE_VERSION="release/$(date +%Y%m%d%H%M)"

    echo "Releasing version ${RELEASE_VERSION}"

    git checkout develop
    git pull origin develop
    git push origin develop
    git checkout -b ${RELEASE_VERSION}
    git checkout $(get_default_branch)
    git pull origin $(get_default_branch)
    git merge --no-ff ${RELEASE_VERSION}
    git push origin $(get_default_branch)
}

# Hide difficult logic behind extracting compressed folders
# Use the file extension to determine which command to use
function extract () {
    if [ -f $1 ] ; then
        case $1 in
            *.tar.gz)  tar xzf $1 ;;
            *.gz)      gunzip $1 ;;
            *.tar)     tar xf $1 ;;
            *.tgz)     tar xzf $1 ;;
            *.tar.bz2) tar xjf $1 ;;
            *.bz2)     bunzip2 $1 ;;
            *.rar)     rar x $1 ;;
            *.tbz2)    tar xjf $1 ;;
            *.zip)     unzip $1 ;;
            *.Z)       uncompress $1 ;;
            *.7z)      7za x $1 ;;
            *)         echo "'$1' cannot be extracted via extract" >&2 ;;
        esac
    else
        echo "no file called $1"
    fi
}
