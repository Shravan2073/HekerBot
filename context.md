# HekerBOT Context Guide

HekerBOT is an autonomous pentesting assistant with an interactive terminal shell. It uses an LLM for reasoning (`plan -> act -> observe -> reflect`) and executes generated commands either in:

1. **Docker mode (recommended)**: isolated Kali-based sandbox.
2. **Local mode**: commands run directly on your host machine.

---

## 1. What this application contains

- **CLI entrypoints**: `hkb` (short), `hekerbot` (full)
- **Main shell**: `src/hekerbot/ui/shell.py`
- **Agent loop**: `src/hekerbot/agent/agent.py`
- **LLM reasoning**: `src/hekerbot/agent/brain.py`
- **Executors**:
  - Docker executor: `src/hekerbot/executor/docker_executor.py`
  - Local executor: `src/hekerbot/executor/local_executor.py`
- **Session persistence**: `src/hekerbot/persistence/state.py` (saved under `sessions/`)
- **Sandbox image recipe**: `Dockerfile`

---

## 2. Prerequisites

- Python 3.10+
- One LLM API key (Gemini/OpenAI/Anthropic)
- Docker (only required for Docker mode)
- Linux shell with `bash` (required for local mode execution)

---

## 3. Fresh start after pulling from GitHub

From a new clone or after `git pull`:

```bash
git clone https://github.com/yourusername/HekerBOT.git
cd HekerBOT
uv sync
```

Create `.env` from the example:

```bash
cp .env.example .env
```

Set at least one API key in `.env`:

```env
GEMINI_API_KEY=your_key_here
# or OPENAI_API_KEY / ANTHROPIC_API_KEY
HEKER_MODEL=gemini/gemini-2.5-flash
```

Start the app:

```bash
hkb
```

---

## 4. Runtime commands in the shell

- `help` — list commands
- `diag` — environment and mode diagnostics
- `build` — build/update Docker sandbox image
- `start <target>` — begin autonomous mission
- `status` — current mission status
- `stop` — stop mission
- `sessions` — list prior saved sessions
- `docker on|off|status` — switch execution mode (Docker/local)
- `clear` — clear terminal
- `exit` — exit app

---

## 5. Docker environment mode

### Enable Docker mode at runtime

Inside HekerBOT:

```text
docker on
```

Then verify:

```text
docker status
diag
```

If needed, build sandbox image:

```text
build
```

### Disable Docker mode (switch to local execution)

```text
docker off
```

When off, `start <target>` runs tool commands on the host machine instead of inside Docker.

### Startup default

Docker mode defaults to **on** unless `HEKER_DOCKER_MODE` is set to `off` / `false` / `0` / `no` in environment.

---

## 6. Safety notes

- Use Docker mode for safer isolation.
- Local mode executes generated commands on your host; use only in controlled environments.
- Only test targets you own or are explicitly authorized to test.

---

## 7. Quick onboarding flow (recommended)

1. `uv sync`
2. Configure `.env`
3. Run `hkb`
4. Run `diag`
5. Run `docker on`
6. Run `build` (first-time only)
7. Run `start <authorized-target>`
