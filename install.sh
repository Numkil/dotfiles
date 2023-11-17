cp -f ./custom/profile.sh ~/.bash_profile
cp -f ./completions/git-completion.sh ~/.git-completion.sh
cp -f ./completions/ssh-completion.sh ~/.ssh-completion.sh
cp -f ./custom/helper-functions.sh ~/.helper-functions.sh
cp -f ./custom/aliases.sh ~/.aliases.sh
cp -f ./custom/sudo.sh ~/.sudo.sh
cp -f ./starship/starship.toml ~/.config/starship.toml
rm -rf ~/.config/lsd && cp -rf ./lsd ~/.config/lsd
rm -rf ~/.config/wezterm && cp -rf ./wezterm ~/.config/wezterm
rm -rf ~/.config/ripgrep && cp -rf ./ripgrep ~/.config/ripgrep

echo "If no errors were reported, you can now run 'source ~/.bash_profile' to load the new settings."
