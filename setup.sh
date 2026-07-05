#!/bin/bash
set -e

# HekerBOT Setup Script

echo -e "\033[1;32m[*] Checking requirements for HekerBOT...\033[0m"

# 1. Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "\033[1;31m[-] Python3 could not be found. Please install Python 3.10+\033[0m"
    exit 1
fi
echo -e "\033[1;32m[+] Python3 is installed.\033[0m"

# 2. Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "\033[1;31m[-] Docker could not be found. Please install Docker to use the Sandbox.\033[0m"
    exit 1
fi

if ! docker info &> /dev/null; then
    echo -e "\033[1;33m[-] Docker daemon is not running or your user does not have permission.\033[0m"
    echo -e "\033[1;33m    Hint: sudo systemctl start docker\033[0m"
    echo -e "\033[1;33m    Hint: sudo usermod -aG docker \$USER\033[0m"
    exit 1
fi
echo -e "\033[1;32m[+] Docker is installed and running.\033[0m"

# 3. Create .env if it doesn't exist
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        echo -e "\033[1;34m[*] Creating default .env file from .env.example...\033[0m"
        cp .env.example .env
        echo -e "\033[1;33m[!] IMPORTANT: Please edit the .env file to add your API keys!\033[0m"
    fi
fi

# 4. Setup Python Environment
echo -e "\033[1;34m[*] Setting up Python virtual environment...\033[0m"
python3 -m venv .venv
source .venv/bin/activate

echo -e "\033[1;34m[*] Installing dependencies...\033[0m"
pip install -e .

# 5. Build Docker Image
echo -e "\033[1;34m[*] Building Docker Sandbox Image (hekerbot-sandbox)...\033[0m"
docker build -t hekerbot-sandbox .

# 6. Create `hkb` wrapper script
echo -e "\033[1;34m[*] Creating 'hkb' shortcut...\033[0m"
mkdir -p ~/.local/bin

REPO_DIR="$(pwd)"
cat << EOF > ~/.local/bin/hkb
#!/bin/bash
# HekerBOT execution wrapper
cd "${REPO_DIR}"

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

source "${REPO_DIR}/.venv/bin/activate"
exec hekerbot "\$@"
EOF

chmod +x ~/.local/bin/hkb

# Ensure ~/.local/bin is in PATH for the current session warning
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo -e "\033[1;33m[!] Note: ~/.local/bin is not in your PATH.\033[0m"
    echo -e "\033[1;33m    You may need to run 'export PATH=\$HOME/.local/bin:\$PATH' or add it to your ~/.bashrc\033[0m"
fi

echo -e "\033[1;32m============================================================\033[0m"
echo -e "\033[1;32m[+] Setup Complete!\033[0m"
echo -e "\033[1;32m[+] You can now run the application from anywhere by typing:\033[0m"
echo -e "\033[1;37m    hkb\033[0m"
echo -e "\033[1;32m============================================================\033[0m"
