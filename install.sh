if [[ "${OSTYPE}" == 'darwin'* ]]; then
  cp -f ./profile.sh ~/.bash_profile
else
  cp -f ./profile.sh ~/.bashrc
fi
cp -f ./git-completion.sh ~/.git-completion.sh
cp -f ./ssh-completion.sh ~/.ssh-completion.sh
cp -f ./helper-functions.sh ~/.helper-functions.sh
cp -f ./aliases.sh ~/.aliases.sh
cp -f ./prompt.sh ~/.prompt.sh
cp -f ./sudo.sh ~/.sudo.sh
cp -f ./starship.toml ~/.config/starship.toml

echo "If no errors were reported, you can now run 'source ~/.bash_profile' to load the new settings."
