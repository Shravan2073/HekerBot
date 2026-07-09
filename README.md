
    ██╗  ██╗███████╗██╗  ██╗███████╗██████╗ ██████╗  ██████╗ ████████╗      ██████╗     
    ██║  ██║██╔════╝██║ ██╔╝██╔════╝██╔══██╗██╔══██╗██╔═══██╗╚══██╔══╝    ██████████╗   
    ███████║█████╗  █████╔╝ █████╗  ██████╔╝██████╔╝██║   ██║   ██║       ██╔╗██╔╗██║   
    ██╔══██║██╔══╝  ██╔═██╗ ██╔══╝  ██╔══██╗██╔══██╗██║   ██║   ██║       ██╚╝██╚╝██║   
    ██║  ██║███████╗██║  ██╗███████╗██║  ██║██████╔╝╚██████╔╝   ██║       ╚████████╔╝   
    ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═════╝  ╚═════╝    ╚═╝        ╚█║█║█║█╝    


Autonomous Agentic Red Teaming Framework (The "AI Pentester")

HekerBOT is an autonomous agent designed to perform controlled penetration testing. It uses Large Language Models (LLMs) to plan, execute, and reflect on security testing tasks within a secure, sandboxed Docker environment.

## 🚀 Key Features
- **Autonomous Agentic Loop**: Iterative Plan -> Act -> Observe -> Reflect cycle.
- **Full-Screen Dashboard**: A beautiful, responsive TUI built with `textual` featuring side-by-side components.
- **Live Operator Chat**: Send real-time instructions to the AI agent while a mission is running!
- **Auto-Updater**: Automatically checks and seamlessly pulls the latest updates on launch.
- **Background Execution**: Missions run in the background, updating a live terminal log.
- **Kali Linux Sandbox**: Now uses `kalilinux/kali-rolling` as a base for a professional-grade toolset.
- **Expanded Toolset**: Over 20+ integrated tools for Recon, Web Enum, Exploitation, and Post-Exploitation.
- **Secure Sandboxing**: All tools run inside isolated Docker containers with `NET_RAW` capabilities.
- **Persistence**: Automatically saves session state and command history.

## 📋 Prerequisites

Before installing HekerBOT, ensure your system meets the following requirements:

| Requirement | Description |
| :--- | :--- |
| 🐳 **Docker** | Required for the secure Kali Linux sandbox. [Install Here](https://docs.docker.com/get-docker/). |
| 🐍 **Python 3.10+** | The core framework language. |
| 🔑 **API Key** | Google Gemini (recommended), OpenAI, OpenCode, or Anthropic. |

## 🛠️ Setup

### 1. One-Line Install (Recommended)
You can instantly install HekerBOT using our web install script:
```bash
curl -sL https://shravan.lol/install.sh | bash 
```
*(This script will automatically clone the repository to `~/HekerBOT`, set up a virtual environment, and install the `hkb` global command.)*

### 2. Configure Environment
Add the API keys in the main menu at "API Center" 

Updates happen automatically on Startup

## 🎮 Usage

Launch the full-screen dashboard:
```bash
hkb
```

### The Dashboard Interface
- **Sidebar Menu**: Navigate between starting/stopping missions, checking agent status, managing past sessions, and configuring Docker mode.
- **Target & Instructions**: Simply enter a target (IP or domain) and your initial goal. The unified **INSTRUCTIONS** box is used for both initial goals and live chat.
- **Operator Chat**: While a mission is actively running, you can type directly into the Instructions box and press `Enter` to inject live commands or feedback directly into the agent's thought process!
- **Live Terminal**: Watch the agent execute commands in real-time in the scrollable log window.

### 🔄 Auto-Update
HekerBOT now automatically checks the remote GitHub repository for new features when you run `hkb`. If an update is found, it will seamlessly stash your changes, pull the latest code, and reinstall dependencies before launching the UI!

## 🐳 Docker Management

### Setting up the Sandbox
HekerBOT needs a specialized Docker image to run its tools securely. You can manage this from the **Docker Mode** menu option inside the TUI, which will guide you through building the `hekerbot-sandbox` image.

### Emergency Cleanup
If HekerBOT exits unexpectedly and leaves containers running, you can clean them up using standard Docker commands:
```bash
docker stop $(docker ps -q --filter ancestor=hekerbot-sandbox)
docker rm $(docker ps -aq --filter ancestor=hekerbot-sandbox)
```

## 🛡️ Ethical Use & Disclaimer
HekerBOT is for **educational and authorized security testing only**. Never use this tool against targets you do not have explicit, written permission to test. The authors are not responsible for any misuse or damage caused by this tool.
