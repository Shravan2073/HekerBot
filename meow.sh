#!/bin/bash
set -e

# HekerBOT Web Install Script
# curl -sL https://shravan.lol/install.sh | bash

# Colors & Formatting
C_RESET="\033[0m"
C_GREEN="\033[1;32m"
C_BLUE="\033[1;34m"
C_RED="\033[1;31m"
C_YELLOW="\033[1;33m"
C_DIM="\033[90m"
C_BOLD="\033[1m"

# Print Banner
echo -e "${C_BLUE}"
echo "    __  __     __                   ____  ____  ________"
echo "   / / / /__  / /_____  _____      / __ )/ __ \/_  __/"
echo "  / /_/ / _ \/ //_/ _ \/ ___/_____/ __  / / / / / /   "
echo " / __  /  __/ ,< /  __/ /  /_____/ /_/ / /_/ / / /    "
echo "/_/ /_/\___/_/|_|\___/_/        /_____/\____/ /_/     "
echo -e "${C_RESET}"
echo -e "         ${C_DIM}Autonomous Agentic Red Teaming Framework${C_RESET}"
echo ""

# Helper functions
step() { echo -e " ${C_BLUE}➜${C_RESET}  $1"; }
success() { echo -e " ${C_GREEN}✔${C_RESET}  $1"; }
warn() { echo -e " ${C_YELLOW}⚠${C_RESET}  $1"; }
error() { echo -e " ${C_RED}✖${C_RESET}  $1"; exit 1; }

# 1. Check Requirements
step "Checking system requirements..."
command -v git >/dev/null || error "git is not installed."
command -v python3 >/dev/null || error "python3 is not installed."

HAS_DOCKER=1
if ! command -v docker >/dev/null || ! docker info >/dev/null 2>&1; then
    warn "Docker daemon not available. Sandbox disabled."
    HAS_DOCKER=0
fi
success "Requirements satisfied."

# 2. Clone Repository
INSTALL_DIR="$HOME/HekerBOT"
if [ -d "$INSTALL_DIR" ]; then
    step "Updating existing repository..."
    cd "$INSTALL_DIR" && git pull --quiet
else
    step "Cloning repository..."
    git clone --quiet https://github.com/Shravan2073/HekerBOT.git "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi
success "Repository ready."

# 3. Setup Environment
if [ ! -f .env ] && [ -f .env.example ]; then
    step "Creating .env template..."
    cp .env.example .env
    warn "Please edit $INSTALL_DIR/.env to add your API keys later."
fi

step "Setting up virtual environment & dependencies..."
python3 -m venv .venv
source .venv/bin/activate
pip install -e . --quiet
success "Dependencies installed."

# 4. Build Sandbox
if [ $HAS_DOCKER -eq 1 ]; then
    step "Building Docker Sandbox (this might take a minute)..."
    docker build -t hekerbot-sandbox . > /dev/null 2>&1
    success "Docker sandbox ready."
fi

# 5. Create executable
step "Configuring 'hkb' shortcut..."
mkdir -p ~/.local/bin
cat << EOF > ~/.local/bin/hkb
#!/bin/bash
cd "${INSTALL_DIR}"
if timeout 3 git fetch origin main --quiet 2>/dev/null; then
    L=\$(git rev-parse HEAD 2>/dev/null)
    R=\$(git rev-parse origin/main 2>/dev/null)
    if [ -n "\$L" ] && [ -n "\$R" ] && [ "\$L" != "\$R" ]; then
        git pull --quiet
        source .venv/bin/activate
        pip install -e . --quiet
    fi
fi
source "${INSTALL_DIR}/.venv/bin/activate"
exec hekerbot "\$@"
EOF
chmod +x ~/.local/bin/hkb
success "Shortcut created."

# 6. Finish
echo ""
echo -e "${C_GREEN}${C_BOLD}Installation Complete!${C_RESET}"
echo -e "You can now launch the application by typing: ${C_BOLD}hkb${C_RESET}"

if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo ""
    warn "~/.local/bin is not in your PATH."
    echo -e "    Run: ${C_BOLD}export PATH=\$HOME/.local/bin:\$PATH${C_RESET} to use the command"
fi
echo ""
