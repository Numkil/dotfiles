####IMPROVING DEFAULT SUDO FUNCTIONALITY#####

# Preserve environment when doing "sudo vim []"
function sudo() {
    case $* in
        vim* ) shift 1; command sudo -E nvim "$@" ;;
        nvim* ) shift 1; command sudo -E nvim "$@" ;;
        * ) command sudo "$@" ;;
    esac
}

# toggle sudo at the beginning of the current or the previous command by hitting the ESC key twice
function sudo-command-line() {
  [[ ${#READLINE_LINE} -eq 0 ]] && READLINE_LINE=$(fc -l -n -1 | xargs)
  if [[ $READLINE_LINE == sudo\ * ]]; then
    READLINE_LINE="${READLINE_LINE#sudo }"
  else
    READLINE_LINE="sudo $READLINE_LINE"
  fi
  READLINE_POINT=${#READLINE_LINE}
}

# Define shortcut keys: [Esc] [Esc]

# Readline library requires bash version 4 or later
if [ "${BASH_VERSINFO}" -ge 4 ]; then
  bind -x '"\e\e": sudo-command-line'
fi

