#!/bin/bash
set -e

# HekerBOT Setup & Install Script
#
# Run from inside an existing checkout for local dev setup, or pipe it
# straight from the web to bootstrap a fresh install:
#   curl -sL https://shravan.lol/install.sh | bash

C_RESET="\033[0m"
C_GREEN="\033[1;32m"
C_BLUE="\033[1;34m"
C_RED="\033[1;31m"
C_YELLOW="\033[1;33m"
C_DIM="\033[90m"
C_BOLD="\033[1m"

step() { echo -e " ${C_BLUE}➜${C_RESET}  $1"; }
success() { echo -e " ${C_GREEN}✔${C_RESET}  $1"; }
warn() { echo -e " ${C_YELLOW}⚠${C_RESET}  $1"; }
error() { echo -e " ${C_RED}✖${C_RESET}  $1"; exit 1; }

echo -e "${C_BLUE}"
cat << 'BANNER'
    __  __     __                   ____  ____  ________
   / / / /__  / /_____  _____      / __ )/ __ \/_  __/
  / /_/ / _ \/ //_/ _ \/ ___/_____/ __  / / / / / /
 / __  /  __/ ,< /  __/ /  /_____/ /_/ / /_/ / / /
/_/ /_/\___/_/|_|\___/_/        /_____/\____/ /_/
BANNER
echo -e "${C_RESET}${C_DIM}         Autonomous Agentic Red Teaming Framework${C_RESET}\n"

# 1. Requirements
step "Checking system requirements..."
command -v git >/dev/null || error "git is not installed."
command -v python3 >/dev/null || error "python3 (3.10+) is not installed."

HAS_DOCKER=1
if ! command -v docker >/dev/null || ! docker info >/dev/null 2>&1; then
    warn "Docker daemon not available — the sandbox will stay disabled until it is."
    HAS_DOCKER=0
fi
success "Requirements satisfied."

# 2. Locate or clone the repository.
# Run from inside an existing checkout (local dev) and it's used in place;
# otherwise (e.g. curl | bash with nothing checked out yet) clone fresh.
if [ -f "pyproject.toml" ] && grep -q '^name = "hekerbot"' pyproject.toml 2>/dev/null; then
    REPO_DIR="$(pwd)"
    step "Using existing checkout at ${REPO_DIR}"
else
    REPO_DIR="$HOME/HekerBOT"
    if [ -d "$REPO_DIR/.git" ]; then
        step "Updating existing install at ${REPO_DIR}..."
        (cd "$REPO_DIR" && git pull --quiet)
    else
        step "Cloning repository to ${REPO_DIR}..."
        git clone --quiet https://github.com/Shravan2073/HekerBOT.git "$REPO_DIR"
    fi
    cd "$REPO_DIR"
fi
success "Repository ready at ${REPO_DIR}"

# 3. .env
if [ ! -f .env ] && [ -f .env.example ]; then
    step "Creating default .env from .env.example..."
    cp .env.example .env
    warn "Edit ${REPO_DIR}/.env to add your API keys (or use the in-app API Center)."
fi

# 4. Python environment
step "Setting up virtual environment & installing dependencies..."
python3 -m venv .venv
source .venv/bin/activate
pip install -e . --quiet
success "Dependencies installed."

# 5. Docker sandbox image
if [ "$HAS_DOCKER" -eq 1 ]; then
    step "Building the Docker sandbox image (this can take a minute)..."
    docker build -t hekerbot-sandbox . > /dev/null 2>&1
    success "Sandbox image ready."
fi

# 6. Global 'hkb' / 'hekerbot' commands.
#
# `pip install -e .` already produced real console-scripts for both names
# inside ${REPO_DIR}/.venv/bin (see [project.scripts] in pyproject.toml) —
# no bespoke update-check logic belongs here. Update checking + animation
# lives in hekerbot's own startup path (src/hekerbot/meow.py) so it runs
# identically whichever name launches it, and can never drift out of sync
# with a hardcoded path baked in at install time.
step "Linking 'hkb' and 'hekerbot' onto your PATH..."
mkdir -p ~/.local/bin
ln -sf "${REPO_DIR}/.venv/bin/hekerbot" ~/.local/bin/hekerbot
ln -sf "${REPO_DIR}/.venv/bin/hkb" ~/.local/bin/hkb
success "Both commands now point at ${REPO_DIR}."

if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo ""
    warn "~/.local/bin is not on your PATH."
    echo -e "    Run: ${C_BOLD}export PATH=\$HOME/.local/bin:\$PATH${C_RESET}  (add it to your shell rc to keep it)"
fi

echo ""
echo -e "${C_GREEN}${C_BOLD}Setup complete!${C_RESET} Launch HekerBOT anytime with: ${C_BOLD}hkb${C_RESET}"
echo ""
