cp -f ./bash/custom/profile.sh ~/.bash_profile
cp -f ./bash/completions/git-completion.sh ~/.git-completion.sh
cp -f ./bash/completions/ssh-completion.sh ~/.ssh-completion.sh
cp -f ./bash/custom/helper-functions.sh ~/.helper-functions.sh
cp -f ./bash/custom/aliases.sh ~/.aliases.sh
cp -f ./bash/custom/sudo.sh ~/.sudo.sh
cp -f ./starship/starship.toml ~/.config/starship.toml
cp -f ./git/.gitconfig ~/.gitconfig
cp -f ./git/.gitignore ~/.gitignore
rm -rf ~/.config/lsd && cp -rf ./lsd ~/.config/lsd
rm -rf ~/.config/wezterm && cp -rf ./wezterm ~/.config/wezterm
rm -rf ~/.config/ripgrep && cp -rf ./ripgrep ~/.config/ripgrep
rm -rf ~/.config/nvim && cp -rf ./nvim ~/.config/nvim

echo "If no errors were reported, you can now run 'source ~/.bash_profile' to load the new settings."
