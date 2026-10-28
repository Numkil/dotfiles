cp -f ./bash/custom/profile.sh ~/.bash_profile
cp -f ./bash/completions/git-completion.sh ~/.git-completion.sh
cp -f ./bash/completions/ssh-completion.sh ~/.ssh-completion.sh
cp -f ./bash/custom/helper-functions.sh ~/.helper-functions.sh
cp -f ./bash/custom/options.sh ~/.options.sh
cp -f ./bash/custom/aliases.sh ~/.aliases.sh
cp -f ./bash/custom/sudo.sh ~/.sudo.sh
cp -f ./starship/starship.toml ~/.config/starship.toml
cp -f ./yabai/.yabairc ~/.yabairc
cp -f ./skhd/.skhdrc ~/.skhdrc
cp -f ./git/.gitconfig ~/.gitconfig
cp -f ./git/.gitignore ~/.gitignore
rm -rf ~/.config/lsd && cp -rf ./lsd ~/.config/lsd
rm -rf ~/.config/wezterm && cp -rf ./wezterm ~/.config/wezterm
rm -rf ~/.config/ripgrep && cp -rf ./ripgrep ~/.config/ripgrep
rm -rf ~/.config/nvim && cp -rf ./nvim ~/.config/nvim
rm -rf ~/.config/ghostty && cp -rf ./ghostty ~/.config/ghostty
# PI: use rsync to merge skills (don't wipe skills installed via npx/pi packages)
# Exclude local-only state: secrets (config/, .env), node_modules, python caches
mkdir -p ~/.pi/agent/skills
if command -v rsync &> /dev/null; then
    rsync -a \
        --exclude='config/' \
        --exclude='.env' \
        --exclude='node_modules/' \
        --exclude='__pycache__/' \
        --exclude='*.pyc' \
        ./pi/agent/skills/ ~/.pi/agent/skills/
else
    cp -rf ./pi/agent/skills/. ~/.pi/agent/skills/ 2>/dev/null || true
fi
cp -f ./pi/agent/APPEND_SYSTEM.md ~/.pi/agent/APPEND_SYSTEM.md
cp -f ./pi/agent/AGENTS.md ~/.pi/agent/AGENTS.md 2>/dev/null || true
cp -f ./pi/agent/settings.json ~/.pi/agent/settings.json 2>/dev/null || true
cp -f ./pi/agent/mcp.json ~/.pi/agent/mcp.json 2>/dev/null || true
cp -f ./pi/agent/hermes-memory-config.json ~/.pi/agent/hermes-memory-config.json 2>/dev/null || true
mkdir -p ~/.pi/agent/extensions && cp -f ./pi/agent/extensions/*.ts ~/.pi/agent/extensions/ 2>/dev/null || true
mkdir -p ~/.pi/agent/agents && cp -f ./pi/agent/agents/*.md ~/.pi/agent/agents/ 2>/dev/null || true
mkdir -p ~/.pi/agent/themes && cp -f ./pi/agent/themes/*.json ~/.pi/agent/themes/ 2>/dev/null || true

# PI: install npm packages from settings.json (versions are pinned there)
if command -v pi &> /dev/null; then
    packages=$(grep -o '"npm:[^"]*"' ./pi/agent/settings.json | sed 's/"npm://;s/"//' || true)
    for pkg in $packages; do
        [ -n "$pkg" ] && pi install "npm:$pkg" --approve 2>/dev/null || true
    done
else
    echo "pi not found, skipping PI package installation"
fi

# PI: install caveman skill for token optimization
if command -v npx &> /dev/null; then
    npx skills add JuliusBrussee/caveman --yes --global --agent pi --skill caveman 2>/dev/null || true
else
    echo "npx not found, skipping caveman skill installation"
fi

echo "If no errors were reported, you can now run 'source ~/.bash_profile' to load the new settings."
echo "Restart PI or run 'pi --reload' to apply the PI configuration changes."
