#!/bin/bash
set -e

# HekerBOT Web Install Script
# Designed to be run via: curl -sL https://shravan.lol/install.sh | bash

echo -e "\033[1;35m"
echo "  _   _      _             ____   ___ _____ "
echo " | | | | ___| | _____ _ __| __ ) / _ \_   _|"
echo " | |_| |/ _ \ |/ / _ \ '__|  _ \| | | || |  "
echo " |  _  |  __/   <  __/ |  | |_) | |_| || |  "
echo " |_| |_|\___|_|\_\___|_|  |____/ \___/ |_|  "
echo "                                            "
echo -e "\033[0m"

echo -e "\033[1;32m[*] Initializing HekerBOT Installation...\033[0m"

# 1. Check requirements first
if ! command -v git &> /dev/null; then
    echo -e "\033[1;31m[-] git could not be found. Please install git.\033[0m"
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo -e "\033[1;31m[-] Python3 could not be found. Please install Python 3.10+\033[0m"
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo -e "\033[1;33m[!] Docker could not be found. Sandbox features will be disabled.\033[0m"
else
    if ! docker info &> /dev/null; then
        echo -e "\033[1;33m[!] Docker daemon is not running or lacks permissions. Fix later with: sudo usermod -aG docker \$USER\033[0m"
    fi
fi

# 2. Clone the repository
INSTALL_DIR="$HOME/HekerBOT"
if [ -d "$INSTALL_DIR" ]; then
    echo -e "\033[1;33m[*] Directory $INSTALL_DIR already exists. Updating...\033[0m"
    cd "$INSTALL_DIR"
    git pull
else
    echo -e "\033[1;34m[*] Cloning HekerBOT to $INSTALL_DIR...\033[0m"
    git clone https://github.com/Shravan2073/HekerBOT.git "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi

# 3. Create .env if it doesn't exist
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        echo -e "\033[1;34m[*] Creating default .env file...\033[0m"
        cp .env.example .env
        echo -e "\033[1;33m[!] IMPORTANT: Remember to edit ~/HekerBOT/.env to add your API keys later!\033[0m"
    fi
fi

# 4. Setup Python Environment
echo -e "\033[1;34m[*] Setting up Python virtual environment...\033[0m"
python3 -m venv .venv
source .venv/bin/activate

echo -e "\033[1;34m[*] Installing dependencies...\033[0m"
pip install -e .

# 5. Build Docker Image (if docker is available and working)
if command -v docker &> /dev/null && docker info &> /dev/null; then
    echo -e "\033[1;34m[*] Building Docker Sandbox Image (hekerbot-sandbox)...\033[0m"
    docker build -t hekerbot-sandbox .
fi

# 6. Create `hkb` wrapper script
echo -e "\033[1;34m[*] Creating 'hkb' shortcut...\033[0m"
mkdir -p ~/.local/bin

cat << EOF > ~/.local/bin/hkb
#!/bin/bash
# HekerBOT execution wrapper
cd "${INSTALL_DIR}"

# Fast, silent check for updates (timeout prevents hanging if offline)
echo -ne "\033[90m[*] Checking for updates...\r\033[0m"
if timeout 3 git fetch origin main --quiet 2>/dev/null; then
    LOCAL=\$(git rev-parse HEAD 2>/dev/null)
    REMOTE=\$(git rev-parse origin/main 2>/dev/null)
    if [ -n "\$LOCAL" ] && [ -n "\$REMOTE" ] && [ "\$LOCAL" != "\$REMOTE" ]; then
        echo -e "\n\033[1;33m[*] New version detected! Updating HekerBOT...\033[0m"
        git pull --quiet
        source .venv/bin/activate
        pip install -e . --quiet
        echo -e "\033[1;32m[*] Update complete.\033[0m"
    fi
fi
echo -ne "\033[2K\r"

source "${INSTALL_DIR}/.venv/bin/activate"
exec hekerbot "\$@"
EOF

chmod +x ~/.local/bin/hkb

echo -e "\033[1;32m============================================================\033[0m"
echo -e "\033[1;32m[+] HekerBOT successfully installed!\033[0m"
echo -e "\033[1;32m[+] To start the application, just type:\033[0m"
echo -e "\033[1;37m    hkb\033[0m"
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo -e "\033[1;33m[!] Note: ~/.local/bin is not in your PATH.\033[0m"
    echo -e "\033[1;33m    You must run 'export PATH=\$HOME/.local/bin:\$PATH' to use the 'hkb' command!\033[0m"
fi
echo -e "\033[1;32m============================================================\033[0m"
