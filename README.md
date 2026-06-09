# HekerBOT 🤖

Autonomous Agentic Red Teaming Framework (The "AI Pentester")

HekerBOT is an autonomous agent designed to perform controlled penetration testing. It uses Large Language Models (LLMs) to plan, execute, and reflect on security testing tasks within a secure, sandboxed Docker environment.

## 🚀 Key Features
- **Autonomous Agentic Loop**: Iterative Plan -> Act -> Observe -> Reflect cycle.
- **Interactive Shell**: A responsive TUI built with `rich` and `prompt_toolkit`.
- **Background Execution**: Missions run in the background, keeping the UI interactive.
- **Secure Sandboxing**: All tools run inside isolated Docker containers.
- **Persistence**: Automatically saves session state and command history.

## 📋 Prerequisites
- **Docker**: Required for tool execution. [Install Docker](https://docs.docker.com/get-docker/).
- **Python 3.10+**: The core framework is written in Python.
- **OpenAI or Anthropic API Key**: Required for the agent's "brain".

## 🛠️ Setup

1. **Clone and Install**:
   ```bash
   git clone https://github.com/yourusername/HekerBOT.git
   cd HekerBOT
   pip install -e .
   ```

2. **Configure Environment**:
   Create a `.env` file in the root directory:
   ```bash
   OPENAI_API_KEY=sk-...
   # Optional: set preferred model
   HEKER_MODEL=gpt-4-turbo-preview
   ```

3. **Build the Sandbox**:
   HekerBOT needs a specialized Docker image to run its tools.
   ```bash
   hekerbot
   # Inside the shell, run:
   hekerbot > build
   ```
   *Alternatively, run `docker build -t hekerbot-sandbox .` from the root.*

## 🎮 Usage

Launch the interactive shell:
```bash
hekerbot
```

### Commands:
- `build`: Build/Update the Docker sandbox image.
- `start <target>`: Start a background pentest on a target (e.g., `start 192.168.1.1`).
- `status`: Check if the agent is running and see mission details.
- `stop`: Gracefully stop the current mission.
- `sessions`: List previous session IDs.
- `clear`: Clear the terminal screen.
- `help`: Show all available commands.
- `exit`: Quit HekerBOT.

## 🛡️ Ethical Use & Disclaimer
HekerBOT is for **educational and authorized security testing only**. Never use this tool against targets you do not have explicit, written permission to test. The authors are not responsible for any misuse or damage caused by this tool.
