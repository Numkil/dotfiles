# kickstart.nvim

https://github.com/kdheepak/kickstart.nvim/assets/1813121/f3ff9a2b-c31f-44df-a4fa-8a0d7b17cf7b

### Introduction

A starting point for Neovim that is:

* Small
* Documented
* Modular

Kickstart.nvim targets *only* the latest ['stable'](https://github.com/neovim/neovim/releases/tag/stable) and latest ['nightly'](https://github.com/neovim/neovim/releases/tag/nightly) of Neovim. If you are experiencing issues, please make sure you have the latest versions.

### Installation

> **NOTE** 
> [Backup](#FAQ) your previous configuration (if any exists)

Requirements:
* Make sure to review the readmes of the plugins if you are experiencing errors. In particular:
  * [ripgrep](https://github.com/BurntSushi/ripgrep#installation) is required for multiple [mini-picker](https://github.com/echasnovski/mini.nvim/blob/main/readmes/mini-pick.md) pickers.

Neovim's configurations are located under the following paths, depending on your OS:

| OS | PATH |
| :- | :--- |
| Linux | `$XDG_CONFIG_HOME/nvim`, `~/.config/nvim` |
| MacOS | `$XDG_CONFIG_HOME/nvim`, '~/.config/nvim` |

Clone kickstart.nvim:

```sh
# on Linux and Mac
git clone https://github.com/numkil/kickstart.nvim.git "${XDG_CONFIG_HOME:-$HOME/.config}"/nvim
```

### Post Installation

Run the following command and then **you are ready to go**!

```sh
nvim --headless "+Lazy! sync" +qa
```
