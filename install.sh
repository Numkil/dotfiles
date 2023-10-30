if [[ "${OSTYPE}" == 'darwin'* ]]; then
  cp -f ./custom/profile.sh ~/.bash_profile
else
  cp -f ./custom/profile.sh ~/.bashrc
fi
cp -f ./completions/git-completion.sh ~/.git-completion.sh
cp -f ./completions/ssh-completion.sh ~/.ssh-completion.sh
cp -f ./custom/helper-functions.sh ~/.helper-functions.sh
cp -f ./custom/aliases.sh ~/.aliases.sh
cp -f ./custom/sudo.sh ~/.sudo.sh
cp -f ./starship/starship.toml ~/.config/starship.toml
cp -rf ./lsd ~/.config/lsd

echo "If no errors were reported, you can now run 'source ~/.bash_profile' to load the new settings."
