if [[ "${OSTYPE}" == 'darwin'* ]]; then
  cp -f ./bash-profile ~/.bash_profile
else
  cp -f ./bash-profile ~/.bashrc
fi
cp -f ./bash-git-completion.sh ~/bash-git-completion.sh
cp -f ./bash-ssh-completion.sh ~/bash-ssh-completion.sh
cp -f ./bash-functions.sh ~/bash-functions.sh
cp -f ./bash-aliases.sh ~/bash-aliases.sh
cp -f ./bash-prompt.sh ~/bash-prompt.sh

echo "If no errors were reported, you can now run 'source ~/.bash_profile' to load the new settings."
