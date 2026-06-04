# HekerBOT

Autonomous Agentic Red Teaming Framework (The "AI Pentester")

## Features
- **Agentic Loop**: Plan -> Act -> Observe -> Reflect.
- **TUI**: Interactive shell using `rich` and `prompt_toolkit`.
- **Sandboxing**: Secure tool execution via Docker.
- **Persistence**: Session state saved as JSON.

## Setup
1. Install dependencies:
   ```bash
   pip install -e .
   ```
2. Configure environment variables in `.env`:
   ```bash
   OPENAI_API_KEY=your_key_here
   # OR
   ANTHROPIC_API_KEY=your_key_here
   ```
3. Run HekerBOT:
   ```bash
   hekerbot
   ```
