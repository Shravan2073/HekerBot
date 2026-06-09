# HekerBOT: Capabilities & Architecture

HekerBOT is an **Autonomous Agentic Red Teaming Framework** designed to bridge the gap between static vulnerability scanners and manual penetration testing. It leverages Large Language Models (LLMs) as a reasoning engine to autonomously plan, execute, and reflect on multi-stage cyberattacks in a controlled environment.

## 1. Autonomous Agentic Loop
The core of HekerBOT is its **Plan -> Act -> Observe -> Reflect** cycle, which allows it to function without constant human intervention:

*   **Plan**: The agent analyzes existing discovery data (open ports, service versions, banner info) and determines the next logical step in the attack chain.
*   **Act**: The agent selects a tool from its arsenal and generates a precise shell command with optimized arguments.
*   **Observe**: The system executes the command in a sandbox and captures the raw output (stdout/stderr).
*   **Reflect**: The LLM parses the results, updates its internal asset graph, and identifies potential new attack vectors or privilege escalation paths.

## 2. Vulnerability Chaining
Unlike traditional scanners that report isolated bugs, HekerBOT is designed for **logical chaining**:
*   **Discovery**: Identifying an open port (e.g., 8080).
*   **Enumeration**: Running a directory brute-forcer (ffuf) to find hidden panels.
*   **Exploitation**: Detecting an old version of a CMS and attempting a known exploit (e.g., SQL injection via sqlmap).
*   **Escalation**: Using discovered credentials or info leaks to move from unauthenticated access to system-level insights.

## 3. Sandboxed Execution (Docker)
Safety and isolation are fundamental to HekerBOT:
*   **Ephemeral Containers**: Every tool execution happens inside a fresh Docker container.
*   **Toolbox**: The sandbox environment is pre-loaded with:
    *   **Network Mapping**: `nmap`, `ping`, `dnsutils`.
    *   **Web Analysis**: `nikto`, `ffuf`, `curl`.
    *   **Database Exploitation**: `sqlmap`.
    *   **General Purpose**: `netcat`, `python3`, `git`.
*   **Zero Host Impact**: Hallucinated or destructive commands (like `rm -rf /`) are confined to the container and cannot damage the host machine.

## 4. Advanced TUI (Terminal User Interface)
The interface is built for real-time monitoring of an autonomous agent:
*   **Thought Traces**: Displays the agent's "internal monologue" so operators can understand the *why* behind every command.
*   **Live Status**: Real-time spinners and status panels show exactly which tool is currently running.
*   **Command History**: A full audit trail of every command executed during a session.
*   **Interactive REPL**: A Metasploit-inspired shell with command completion and help systems.

## 5. Persistence & State Management
HekerBOT ensures that no progress is lost during long-running engagements:
*   **Session Tracking**: Every mission is assigned a unique UUID.
*   **JSON Asset Graph**: Discovered hosts, ports, and vulnerabilities are stored in a structured JSON format.
*   **Auditability**: Complete "thought + command + result" logs are saved for post-engagement reporting and analysis.

## 6. Multi-Provider LLM Support
Leveraging `LiteLLM`, HekerBOT is model-agnostic:
*   **Google Gemini**: Optimized for long context and complex reasoning (e.g., `gemini-1.5-pro`).
*   **OpenAI GPT**: Industry-standard performance with `gpt-4-turbo`.
*   **Anthropic Claude**: Excellent for structured output and safety-aligned reasoning.

---
**Disclaimer**: HekerBOT is intended for authorized security testing and educational purposes only. Always ensure you have explicit permission before testing any target.
