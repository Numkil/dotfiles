#!/bin/bash
# PI Configuration Install Script
# This script syncs PI extensions, settings, and packages to the current machine.

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# PI directories
PI_AGENT_DIR="${HOME}/.pi/agent"
PI_EXTENSIONS_DIR="${PI_AGENT_DIR}/extensions"
PI_SETTINGS_FILE="${PI_AGENT_DIR}/settings.json"

# ============================================================================
# Functions
# ============================================================================

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

# ============================================================================
# Install Extensions
# ============================================================================
install_extensions() {
    info "Installing extensions..."
    
    # Create extensions directory if it doesn't exist
    mkdir -p "${PI_EXTENSIONS_DIR}"
    
    # Copy all .ts files from dotfiles to PI extensions directory
    local files_copied=0
    for file in "${SCRIPT_DIR}"/extensions/*.ts; do
        if [ -f "$file" ]; then
            cp "$file" "${PI_EXTENSIONS_DIR}/"
            ((files_copied++))
        fi
    done
    
    if [ $files_copied -gt 0 ]; then
        success "Copied $files_copied extension(s) to ${PI_EXTENSIONS_DIR}/"
    else
        warning "No extension files found in ${SCRIPT_DIR}/extensions/"
    fi
}

# ============================================================================
# Install Settings
# ============================================================================
install_settings() {
    info "Installing settings..."
    
    # Create PI agent directory if it doesn't exist
    mkdir -p "${PI_AGENT_DIR}"
    
    # Copy settings.json
    if [ -f "${SCRIPT_DIR}/settings.json" ]; then
        cp "${SCRIPT_DIR}/settings.json" "${PI_SETTINGS_FILE}"
        success "Copied settings.json to ${PI_SETTINGS_FILE}"
    else
        warning "No settings.json found in ${SCRIPT_DIR}/"
    fi
}

# ============================================================================
# Install NPM Packages
# ============================================================================
install_packages() {
    info "Installing npm packages..."
    
    # Check if settings.json exists and has packages
    if [ ! -f "${PI_SETTINGS_FILE}" ]; then
        warning "No settings.json found, skipping package installation"
        return
    fi
    
    # Extract package names from settings.json
    local packages=$(grep -o '"npm:[^"]*"' "${PI_SETTINGS_FILE}" | sed 's/"npm://;s/"//' || true)
    
    if [ -z "$packages" ]; then
        warning "No npm packages found in settings.json"
        return
    fi
    
    info "Found packages: $packages"
    
    # Install each package
    local packages_installed=0
    local packages_failed=0
    
    for pkg in $packages; do
        if [ -n "$pkg" ]; then
            info "Installing $pkg..."
            if pi install "npm:$pkg" 2>/dev/null; then
                ((packages_installed++))
                success "Installed $pkg"
            else
                ((packages_failed++))
                error "Failed to install $pkg"
            fi
        fi
    done
    
    echo ""
    success "Installed $packages_installed package(s)"
    
    if [ $packages_failed -gt 0 ]; then
        error "Failed to install $packages_failed package(s)"
    fi
}

# ============================================================================
# Install Caveman Skill
# ============================================================================
install_caveman() {
    info "Installing Caveman skill for token optimization..."
    
    # Install caveman via skills CLI (non-interactive with --yes flag)
    if command -v npx &> /dev/null; then
        if npx skills add JuliusBrussee/caveman --yes --agent pi --skill caveman 2>/dev/null; then
            success "Caveman skill installed"
            
            # Get the path to the caveman skill
            local caveman_path=$(npx skills path JuliusBrussee/caveman 2>/dev/null)
            
            # Create a SessionStart hook to auto-activate caveman mode
            local hooks_dir="${HOME}/.pi/agent/hooks"
            mkdir -p "$hooks_dir"
            local hook_file="${hooks_dir}/caveman-auto-activate.js"
            
            cat > "$hook_file" << 'EOF'
module.exports = async (agent, options) => {
  // Activate caveman mode at session start
  await agent.sendMessage("/caveman");
};
EOF
            success "Caveman auto-activation hook installed"
            
            if [ -n "$caveman_path" ]; then
                # Load the skill in Pi
                if pi --skill "$caveman_path" --help &> /dev/null; then
                    success "Caveman skill loaded in Pi"
                else
                    warning "Caveman skill installed but may need manual activation with /caveman"
                fi
            else
                warning "Could not determine caveman skill path"
            fi
        else
            error "Failed to install Caveman skill"
        fi
    else
        error "npx not found, cannot install Caveman skill"
    fi
}

# ============================================================================
# Install Context Files
# ============================================================================
install_context_files() {
    info "Installing context files..."
    
    local context_files=("AGENTS.md" "APPEND_SYSTEM.md")
    local pi_agent_dir="${PI_AGENT_DIR}"
    
    local files_copied=0
    for file in "${context_files[@]}"; do
        if [ -f "${SCRIPT_DIR}/${file}" ]; then
            cp "${SCRIPT_DIR}/${file}" "${pi_agent_dir}/"
            ((files_copied++))
        fi
    done
    
    if [ $files_copied -gt 0 ]; then
        success "Copied $files_copied context file(s) to ${pi_agent_dir}/"
    else
        warning "No context files found in ${SCRIPT_DIR}/"
    fi
}

# Install Themes
# ============================================================================
install_themes() {
    info "Installing themes..."
    
    local themes_dir="${SCRIPT_DIR}/themes"
    local pi_themes_dir="${PI_AGENT_DIR}/themes"
    
    # Create themes directory if it doesn't exist
    mkdir -p "${pi_themes_dir}"
    
    # Copy themes if they exist
    if [ -d "$themes_dir" ] && [ "$(ls -A "$themes_dir")" ]; then
        cp "${themes_dir}/"*.json "${pi_themes_dir}/" 2>/dev/null || true
        success "Copied themes from ${themes_dir}/ to ${pi_themes_dir}/"
    else
        warning "No themes found in ${themes_dir}/"
    fi
}

# Install Skills
# ============================================================================
install_skills() {
    info "Installing skills..."
    
    local skills_dir="${SCRIPT_DIR}/skills"
    local pi_skills_dir="${PI_AGENT_DIR}/skills"
    
    # Create skills directory if it doesn't exist
    mkdir -p "${pi_skills_dir}"
    
    # Copy skills if they exist
    if [ -d "$skills_dir" ] && [ "$(ls -A "$skills_dir")" ]; then
        # Use rsync if available, otherwise cp
        if command -v rsync &> /dev/null; then
            rsync -a "${skills_dir}/" "${pi_skills_dir}/"
        else
            cp -r "${skills_dir}/." "${pi_skills_dir}/" 2>/dev/null || true
        fi
        success "Copied skills from ${skills_dir}/ to ${pi_skills_dir}/"
    else
        warning "No skills found in ${skills_dir}/"
    fi
}

# ============================================================================
# Main Installation
# ============================================================================

main() {
    echo ""
    echo "  ╔═══════════════════════════════════════════════════════════╗"
    echo "  ║         PI Configuration Install Script                ║"
    echo "  ╚═══════════════════════════════════════════════════════════╝"
    echo ""
    
    info "PI Dotfiles Directory: ${SCRIPT_DIR}"
    info "PI Agent Directory: ${PI_AGENT_DIR}"
    echo ""
    
    # Step 1: Install extensions
    install_extensions
    echo ""
    
    # Step 2: Install settings
    install_settings
    echo ""
    
    # Step 2b: Install context files
    install_context_files
    echo ""
    
    # Step 3: Install npm packages
    install_packages
    echo ""
    
    # Step 3b: Install Caveman skill
    install_caveman
    echo ""
    
    # Step 4: Install skills
    install_skills
    echo ""
    
    # Step 5: Install themes
    install_themes
    echo ""
    
    # Summary
    echo ""
    echo "  ╔═══════════════════════════════════════════════════════════╗"
    echo "  ║                    Installation Complete!                  ║"
    echo "  ╚═══════════════════════════════════════════════════════════╝"
    echo ""
    info "To apply changes, restart PI or run: pi --reload"
    info ""
    info "Installed components:"
    info "  - Extensions: ${PI_EXTENSIONS_DIR}/"
    info "  - Settings: ${PI_SETTINGS_FILE}"
    info "  - Skills: ${PI_AGENT_DIR}/skills/"
    echo ""
}

# Run main
main "$@"
