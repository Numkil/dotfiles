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
        git clone git@statik.git.beanstalkapp.com:/statik/$1.git
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

# release develop branch to master
function release() {
    RELEASE_VERSION="release/$(date +%Y%m%d%H%M)"

    echo "Releasing version ${RELEASE_VERSION}"

    git checkout develop
    git pull origin develop
    git push origin develop
    git checkout -b ${RELEASE_VERSION}
    git checkout master
    git pull origin master
    git merge --no-ff ${RELEASE_VERSION}
    git push origin master
}

# Preserve environment when doing "sudo vim []"
function sudo() {
    case $* in
        vim* ) shift 1; command sudo -E nvim "$@" ;;
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
