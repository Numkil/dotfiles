DotFiles
=======

Content inside DotFiles:

* All bash scripts
* Starship configuration
* basic configuration for the lsd command
* wezterm settings

Mandatory brew installs for using bash

```
brew install wezterm
brew install bash
brew install bash_completion@2
brew install thefuck
brew install lsd
brew install ripgrep
brew install starship
brew install neovim
brew install tldr
brew install bat
brew tap homebrew/cask-fonts
brew install font-hack-nerd-font // for now the least amount of work to get set up. 
```

The following libaries are optional and i won't include config for it in here.

My personal preference on mac apps

```
brew install amethyst
brew install alfred
brew install 1password
```

PHP development tools

```
brew install ddev
brew install colima
```

and change the default shell to the new bash binary

```
sudo vim /etc/shells
add "/opt/homebrew/bin/bash"
chsh -s opt/homebrew/bin/bash
```

after everything is installed run the following command

``` chmod +x install.sh && sh install.sh ```
