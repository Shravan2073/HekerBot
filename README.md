
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
- **Interactive Shell**: A responsive TUI built with `rich` and `prompt_toolkit`.
- **Background Execution**: Missions run in the background, keeping the UI interactive.
- **Kali Linux Sandbox**: Now uses `kalilinux/kali-rolling` as a base for a professional-grade toolset.
- **Expanded Toolset**: Over 20+ integrated tools for Recon, Web Enum, Exploitation, and Post-Exploitation.
- **Secure Sandboxing**: All tools run inside isolated Docker containers with `NET_RAW` capabilities.
- **Persistence**: Automatically saves session state and command history.

## 📋 Prerequisites
- **Docker**: Required for tool execution. [Install Docker](https://docs.docker.com/get-docker/).
- **Python 3.10+**: The core framework is written in Python.
- **LLM API Key**: Google Gemini (recommended), OpenAI, or Anthropic.

## 🛠️ Setup

1. **Clone and Install**:
   ```bash
   git clone https://github.com/yourusername/HekerBOT.git
   cd HekerBOT
   pip install -e .
   ```
   This installs both `hekerbot` and the short command `hkb`.

2. **Configure Environment**:
   Create a `.env` file in the root directory:
   ```bash
   GEMINI_API_KEY=your_key_here
   # Or OPENAI_API_KEY / ANTHROPIC_API_KEY
   
   # Optional: set preferred model
   HEKER_MODEL=gemini/gemini-1.5-flash
   ```

3. **Build the Sandbox**:
   HekerBOT needs a specialized Docker image to run its tools.
   ```bash
   hkb
   # Inside the shell, run:
   hekerbot (idle) > build
   ```
   *Alternatively, run `docker build -t hekerbot-sandbox .` from the root.*

## 🎮 Usage

Launch the interactive shell:
```bash
hkb
```
(`hekerbot` also works.)

### Commands:
- `build`: Build/Update the Docker sandbox image.
- `start <target>`: Start a background pentest on a target (e.g., `start 192.168.1.1`).
- `status`: Check if the agent is running and see mission details.
- `stop`: Gracefully stop the current mission.
- `sessions`: List previous session IDs.
- `clear`: Clear the terminal screen.
- `help`: Show all available commands.
- `exit`: Quit HekerBOT.

## 🐳 Docker Management

### Stopping a Mission
Inside the HekerBOT shell, simply run:
```bash
hekerbot > stop
```
This will stop the agent's reasoning loop. Note that the currently executing tool will finish its task before the agent fully stops.

### Emergency Cleanup
If HekerBOT exits unexpectedly and leaves containers running, you can clean them up using standard Docker commands:
```bash
# Stop all containers using the hekerbot-sandbox image
docker stop $(docker ps -q --filter ancestor=hekerbot-sandbox)

# Remove all stopped containers using that image
docker rm $(docker ps -aq --filter ancestor=hekerbot-sandbox)
```

## 🛡️ Ethical Use & Disclaimer
HekerBOT is for **educational and authorized security testing only**. Never use this tool against targets you do not have explicit, written permission to test. The authors are not responsible for any misuse or damage caused by this tool.
