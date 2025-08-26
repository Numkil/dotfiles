# DotFiles

Content inside my dotfiles:

- My bash setup, aliases, functions etc..
- Wezterm settings
- Ghostty settings
- My Neovim setup
- Starship configuration
- Lsd configuration
- Ripgrep configuration
- Raycast config binary for importing
- A script to copy all of the above config files to their correct destination

## Setting up my terminal

Please install the following binaries via homebrew

```
brew install ghostty
brew install bash
brew install bash_completion@2
brew install thefuck
brew install lsd
brew install ripgrep
brew install fzf
brew install yabai
brew install skhd
brew install starship
brew install neovim
brew install tldr
brew install bat
brew tap homebrew/cask-fonts
brew install font-hack-nerd-font // for now the least amount of work to get set up.
```

and change the default shell to the new bash binary

```
sudo vim /etc/shells
add "/opt/homebrew/bin/bash"
chsh -s opt/homebrew/bin/bash
```

after everything is installed run the following command

`chmod +x install.sh && sh install.sh`

## Other stuff I want to document i use on a regular basis but do not keep config for

Some good mac apps

```
brew install raycast
brew install 1password
brew install discord
brew install slack
brew install whatsapp
brew install firefox
```

PHP development tools

```
brew install ddev
brew install colima # auto start colima ((brew services start colima))
brew install sequelpro
brew install cargo
cargo install ludtwig
```
