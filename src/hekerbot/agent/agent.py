from hekerbot.agent.brain import HekerBrain
from hekerbot.executor.docker_executor import DockerExecutor
from hekerbot.executor.local_executor import LocalExecutor
from hekerbot.persistence.state import SessionState, PersistenceManager, CommandResult
from rich.console import Console
import time
import uuid
import os
import json
import shlex
import re
import threading
from urllib.parse import urlparse

console = Console(color_system=None)

class HekerAgent:
    MAX_TERMINAL_CHARS = 4000
    MAX_OBSERVATION_CHARS = 6000
    AVAILABLE_TOOLS = [
        "amass", "subfinder", "httpx-toolkit", "dnsx", "whois", "dig",
        "masscan", "rustscan", "nmap", "ffuf", "katana", "nuclei", "chromium",
        "wpscan", "nikto", "trivy", "msfconsole", "searchsploit", "sqlmap",
        "xsstrike", "jwt-tool", "hydra", "hashcat", "john", "kerbrute",
        "netexec", "impacket-*", "bloodhound.py", "evil-winrm", "chisel",
    ]
    TOOL_ALIASES = {
        "httpx": "httpx-toolkit",
        "jwt_tool": "jwt-tool",
    }
    TOOL_PROBE_CANDIDATES = {
        "amass": ["amass"],
        "subfinder": ["subfinder"],
        "httpx-toolkit": ["httpx", "httpx-toolkit"],
        "dnsx": ["dnsx"],
        "whois": ["whois"],
        "dig": ["dig"],
        "masscan": ["masscan"],
        "rustscan": ["rustscan"],
        "nmap": ["nmap"],
        "ffuf": ["ffuf"],
        "katana": ["katana"],
        "nuclei": ["nuclei"],
        "chromium": ["chromium", "chromium-browser"],
        "wpscan": ["wpscan"],
        "nikto": ["nikto"],
        "trivy": ["trivy"],
        "msfconsole": ["msfconsole"],
        "searchsploit": ["searchsploit"],
        "sqlmap": ["sqlmap"],
        "xsstrike": ["xsstrike"],
        "jwt-tool": ["jwt-tool", "jwt_tool"],
        "hydra": ["hydra"],
        "hashcat": ["hashcat"],
        "john": ["john"],
        "kerbrute": ["kerbrute"],
        "netexec": ["netexec"],
        "impacket-*": ["impacket-psexec", "impacket-secretsdump", "impacket-wmiexec"],
        "bloodhound.py": ["bloodhound-python", "bloodhound.py"],
        "evil-winrm": ["evil-winrm"],
        "chisel": ["chisel"],
    }
    PHASE_TOOL_PRIORITY = {
        "recon": ["subfinder", "amass", "dnsx", "dig", "whois", "httpx-toolkit", "katana"],
        "port-scan": ["masscan", "rustscan", "nmap"],
        "service-enum": ["nmap", "httpx-toolkit", "katana", "chromium"],
        "vuln-scan": ["nuclei", "nikto", "wpscan", "trivy", "sqlmap", "xsstrike", "searchsploit"],
        "exploit-analysis": ["searchsploit", "msfconsole", "hydra", "kerbrute", "netexec", "impacket-*", "bloodhound.py", "evil-winrm", "chisel", "jwt-tool"],
        "reporting": [],
    }

    def __init__(self, model: str = None):
        self.brain = HekerBrain(model=model)
        self.executor = DockerExecutor()
        self.local_executor = LocalExecutor()
        self.persistence = PersistenceManager()
        self.running = False
        self.current_state = None
        self.session_goal = ""
        self.docker_mode_enabled = os.getenv("HEKER_DOCKER_MODE", "on").strip().lower() not in {"off", "false", "0", "no"}
        self._effective_backend = None
        self._tool_inventory_cache = {}
        self._operator_lock = threading.Lock()
        self._pending_operator_messages = []
        self._recent_operator_messages = []

    def set_docker_mode(self, enabled: bool):
        self.docker_mode_enabled = enabled

    def docker_mode(self) -> str:
        return "on" if self.docker_mode_enabled else "off"

    def execution_mode(self) -> str:
        return "docker" if self.docker_mode_enabled else "local"

    def active_executor(self):
        return self.executor if self.docker_mode_enabled else self.local_executor

    def is_execution_available(self) -> bool:
        mode = self.execution_mode()
        if mode == "docker":
            return self.executor.is_available() or self.local_executor.is_available()
        return self.local_executor.is_available() or self.executor.is_available()

    def run_session(self, target: str, goal: str = ""):
        self.running = True
        self.session_goal = (goal or "").strip()
        self._tool_inventory_cache.clear()
        with self._operator_lock:
            self._pending_operator_messages = []
            self._recent_operator_messages = []
        self.brain.reset(target, self.session_goal)
        
        session_id = str(uuid.uuid4())[:8]
        self.current_state = SessionState(session_id=session_id, target=target, goal=self.session_goal or None)
        if not self._ensure_execution_ready():
            self.running = False
            return
        console.print(
            f"[bold #d4d4d8]MISSION STARTED[/] id={session_id} target={target} mode={self.execution_mode()}"
        )
        self._mission_loop()
        console.print(f"[bold #a1a1aa]Mission {session_id} stopped.[/]")

    def stop(self):
        self.running = False
        try:
            self.active_executor().kill_active()
        except AttributeError:
            pass

    def resume_session(self, session_id: str):
        """Resume a previously saved session."""
        state = self.persistence.load_session(session_id)
        if not state:
            console.print(f"[!] Session {session_id} not found.")
            return

        self.running = True
        self.current_state = state
        target = state.target
        self.session_goal = (state.goal or "").strip()
        self._tool_inventory_cache.clear()
        with self._operator_lock:
            self._pending_operator_messages = []
            self._recent_operator_messages = []
            for entry in state.history:
                if isinstance(entry, dict) and entry.get("type") == "operator_input":
                    message = str(entry.get("message", "")).strip()
                    if message:
                        self._recent_operator_messages.append(message)
        if not self._ensure_execution_ready():
            self.running = False
            return

        # Rebuild brain context from session history
        self.brain.reset(target, self.session_goal)
        for entry in state.history:
            # Re-feed past thoughts so the LLM has context
            self.brain.history.append({
                "role": "assistant",
                "content": json.dumps(entry, default=str)
            })

        console.print(
            f"[bold #d4d4d8]MISSION RESUMED[/] id={session_id} target={target} mode={self.execution_mode()}"
        )
        console.print(f"[#a1a1aa]Loaded {len(state.command_results)} previous commands.[/]")
        self._mission_loop()
        console.print(f"[bold #a1a1aa]Session {session_id} stopped.[/]")

    def add_operator_input(self, message: str) -> bool:
        text = (message or "").strip()
        if not text:
            return False
        if not self.current_state:
            return False

        with self._operator_lock:
            self._pending_operator_messages.append(text)
            self._recent_operator_messages.append(text)
            self._recent_operator_messages = self._recent_operator_messages[-20:]

        self.current_state.history.append({
            "type": "operator_input",
            "message": text,
            "timestamp": time.time(),
        })
        self.persistence.save_session(self.current_state)
        return True

    def _mission_loop(self):
        observation = None
        step = len(self.current_state.command_results) + 1

        while self.running:
            executor, backend = self._resolve_runtime_executor()
            if executor is None:
                console.print(
                    "[bold #ef4444]No runnable backend available.[/]\n"
                    "Enable Docker or ensure local bash is available."
                )
                self.running = False
                break

            self._announce_backend_if_changed(backend)
            operator_messages = self._drain_operator_messages()
            if operator_messages:
                console.print(f"[#d4d4d8]Operator input received:[/] {operator_messages[-1]}")
                addition = "\n".join(f"- {msg}" for msg in operator_messages)
                if observation:
                    observation += f"\n\nOperator guidance:\n{addition}"
                else:
                    observation = f"Operator guidance:\n{addition}"

            console.print(f"\n[bold #d4d4d8]STEP {step} · DECISION[/]")
            decision = self.brain.think(
                observation,
                self.current_state.discovery_graph,
                self._build_scan_context(backend),
            )

            if not self.running:
                break

            thought = decision.get("thought", "...")
            command = decision.get("command", "")
            updates = decision.get("updates")
            finished = decision.get("finished", False)

            self.current_state.history.append(decision)
            self._print_decision(decision)

            if updates and isinstance(updates, dict):
                self._apply_updates(updates)

            if finished:
                summary = decision.get("summary", "Mission completed.")
                console.print(f"\n[bold #22c55e]MISSION COMPLETE[/]\n{summary}")
                self.running = False
                break

            if not command:
                console.print("[bold #ef4444]No command provided by model.[/] Retrying next step.")
                observation = "No command provided. Provide a concrete scanner command for the next step."
                step += 1
                continue

            console.print(f"[bold #d4d4d8]STEP {step} · EXECUTE[/] ({backend})")
            console.print(f"[#d4d4d8]$ {command}[/]")

            authorized, reason = self._is_command_authorized(command)
            if not authorized:
                console.print(f"[bold #ef4444]Command blocked by strict target policy:[/] {reason}")
                observation = (
                    f"Command blocked by strict authorization policy: {reason}. "
                    f"You must target only '{self.current_state.target}' and no other host, range, or file-based target list."
                )
                step += 1
                continue

            try:
                result = executor.execute_command(command)
            except Exception as e:
                console.print(f"[bold #ef4444]Execution error:[/] {str(e)}")
                observation = f"Execution error: {str(e)}"
                step += 1
                continue

            if not self.running:
                break

            stdout = result.get("stdout", "")
            stderr = result.get("stderr", "")
            exit_code = result.get("exit_code", 0)
            backend = result.get("backend", self.execution_mode())
            container_id = result.get("container_id", "")

            cmd_result = CommandResult(
                command=command,
                stdout=stdout,
                stderr=stderr,
                exit_code=exit_code
            )
            self.current_state.command_results.append(cmd_result)

            self._print_command_result(exit_code, stdout, stderr, backend, container_id)
            if self._command_not_found(stderr):
                self._refresh_tool_inventory(backend, executor, force=True)
            observation = self._build_observation(exit_code, stdout, stderr, backend)
            self.persistence.save_session(self.current_state)

            step += 1
            time.sleep(0.5)

    def _print_decision(self, decision):
        phase = decision.get("phase", "unspecified")
        objective = decision.get("objective", "No explicit objective provided.")
        thought = decision.get("thought", "...")

        console.print(f"[#a1a1aa]Phase:[/] {phase}")
        console.print(f"[#a1a1aa]Objective:[/] {objective}")
        console.print(f"[#d4d4d8]{thought}[/]")

        decision_meta = decision.get("decision")
        if isinstance(decision_meta, dict):
            why_now = decision_meta.get("why_now")
            expected_signal = decision_meta.get("expected_signal")
            fallback = decision_meta.get("fallback")
            if why_now:
                console.print(f"[#a1a1aa]Why now:[/] {why_now}")
            if expected_signal:
                console.print(f"[#a1a1aa]Expected signal:[/] {expected_signal}")
            if fallback:
                console.print(f"[#a1a1aa]Fallback:[/] {fallback}")

    def _print_command_result(self, exit_code: int, stdout: str, stderr: str, backend: str, container_id: str):
        status_color = "#22c55e" if exit_code == 0 else "#ef4444"
        backend_label = backend.upper() if backend else self.execution_mode().upper()
        if backend == "docker" and container_id:
            console.print(f"[#a1a1aa]Backend:[/] {backend_label} [#a1a1aa]container:[/] {container_id}")
        else:
            console.print(f"[#a1a1aa]Backend:[/] {backend_label}")
        console.print(f"[#a1a1aa]Exit code:[/] [bold {status_color}]{exit_code}[/]")

        trimmed_stdout = self._trim(stdout, self.MAX_TERMINAL_CHARS)
        trimmed_stderr = self._trim(stderr, self.MAX_TERMINAL_CHARS)

        if trimmed_stdout:
            console.print(f"[bold #d4d4d8]STDOUT[/]\n{trimmed_stdout}")
        if trimmed_stderr:
            console.print(f"[bold #f59e0b]STDERR[/]\n{trimmed_stderr}")
        if not trimmed_stdout and not trimmed_stderr:
            console.print("[#a1a1aa]No command output.[/]")

    def _apply_updates(self, updates):
        ip = updates.get("ip")
        if not ip:
            return

        self.current_state.update_asset(
            ip=ip,
            hostname=updates.get("hostname"),
            ports=updates.get("new_ports"),
            vulnerabilities=updates.get("new_vulnerabilities")
        )

        asset = self.current_state.discovery_graph.get(ip)
        ports = sorted(asset.ports) if asset else []
        vulns = asset.vulnerabilities if asset else []
        console.print(
            f"[bold #22c55e]Knowledge graph updated[/] ip={ip} ports={ports or 'none'} vulns={vulns or 'none'}"
        )

    def _build_observation(self, exit_code: int, stdout: str, stderr: str, backend: str) -> str:
        trimmed_stdout = self._trim(stdout, self.MAX_OBSERVATION_CHARS)
        trimmed_stderr = self._trim(stderr, self.MAX_OBSERVATION_CHARS)
        inventory = self._tool_inventory_cache.get(backend, {})
        available_tools = inventory.get("available_tools", [])
        unavailable_tools = inventory.get("unavailable_tools", [])
        return (
            "Analyze this command result and choose the next best scanning step.\n"
            f"Execution backend: {backend}\n"
            f"Available tools on backend: {available_tools}\n"
            f"Unavailable tools on backend: {unavailable_tools}\n"
            f"Exit code: {exit_code}\n"
            f"STDOUT:\n{trimmed_stdout}\n\n"
            f"STDERR:\n{trimmed_stderr}\n"
        )

    def _trim(self, text: str, max_chars: int) -> str:
        if not text:
            return ""
        if len(text) <= max_chars:
            return text
        omitted = len(text) - max_chars
        return f"{text[:max_chars]}\n...[truncated {omitted} chars]..."

    def _build_scan_context(self, backend: str) -> dict:
        executor = self.executor if backend == "docker" else self.local_executor
        inventory = self._refresh_tool_inventory(backend, executor, force=False)
        available_tools = inventory.get("available_tools", [])
        unavailable_tools = inventory.get("unavailable_tools", [])

        used_tools = sorted({
            tool
            for result in self.current_state.command_results
            for tool in [self._extract_tool(result.command)]
            if tool
        })
        remaining_tools = [tool for tool in available_tools if tool not in used_tools]
        current_phase = self._current_phase()
        phase_candidates = [
            tool for tool in self.PHASE_TOOL_PRIORITY.get(current_phase, [])
            if tool in remaining_tools
        ]
        discovered_ports = sorted({
            port
            for asset in self.current_state.discovery_graph.values()
            for port in asset.ports
        })
        return {
            "used_tools": used_tools,
            "remaining_tools": remaining_tools,
            "current_phase": current_phase,
            "phase_candidates": phase_candidates,
            "phase_tool_priority": self.PHASE_TOOL_PRIORITY,
            "discovered_ports": discovered_ports,
            "preferred_execution_mode": self.execution_mode(),
            "effective_backend": backend,
            "available_tools": available_tools,
            "unavailable_tools": unavailable_tools,
            "authorized_target": self.current_state.target,
            "strict_target_enforcement": True,
            "session_goal": self.session_goal,
            "operator_messages": self._recent_operator_messages[-8:],
        }

    def _extract_tool(self, command: str) -> str:
        if not command:
            return ""
        try:
            parts = shlex.split(command)
        except ValueError:
            parts = command.strip().split()
        if not parts:
            return ""

        candidate = parts[0]
        if candidate in {"sudo", "time"} and len(parts) > 1:
            candidate = parts[1]
        if candidate.endswith(".py"):
            return candidate
        if candidate.startswith("impacket-"):
            return "impacket-*"

        return self.TOOL_ALIASES.get(candidate, candidate)

    def _current_phase(self) -> str:
        if not self.current_state or not self.current_state.history:
            return "recon"
        for entry in reversed(self.current_state.history):
            phase = entry.get("phase")
            if phase in self.PHASE_TOOL_PRIORITY:
                return phase
        return "recon"

    def _ensure_execution_ready(self) -> bool:
        executor, backend = self._resolve_runtime_executor()
        if executor is None:
            console.print(
                "[bold #ef4444]No execution backend available.[/]\n"
                "Docker is unreachable and local bash is not available."
            )
            return False
        self._announce_backend_if_changed(backend, force=True)
        self._refresh_tool_inventory(backend, executor, force=True)
        return True

    def _resolve_runtime_executor(self):
        docker_available = self.executor.is_available()
        local_available = self.local_executor.is_available()
        preferred = self.execution_mode()

        if preferred == "docker":
            if docker_available:
                return self.executor, "docker"
            if local_available:
                return self.local_executor, "local"
        else:
            if local_available:
                return self.local_executor, "local"
            if docker_available:
                return self.executor, "docker"
        return None, None

    def _announce_backend_if_changed(self, backend: str, force: bool = False):
        if not force and backend == self._effective_backend:
            return

        preferred = self.execution_mode()
        if backend == "docker":
            console.print(f"[#a1a1aa]Execution backend:[/] DOCKER image={self.executor.image_name}")
        else:
            console.print("[#a1a1aa]Execution backend:[/] LOCAL")

        if backend != preferred:
            console.print(
                f"[bold #eab308]Backend fallback active:[/] preferred={preferred.upper()} using={backend.upper()}"
            )
        elif self._effective_backend and self._effective_backend != backend:
            console.print(f"[bold #22c55e]Backend switched:[/] now using {backend.upper()}")

        self._effective_backend = backend

    def _refresh_tool_inventory(self, backend: str, executor, force: bool = False) -> dict:
        if not force and backend in self._tool_inventory_cache:
            return self._tool_inventory_cache[backend]

        checks = []
        for tool in self.AVAILABLE_TOOLS:
            candidates = self.TOOL_PROBE_CANDIDATES.get(tool, [tool])
            joined = " ".join(candidates)
            checks.append(f"{tool}|{joined}")
        checks_str = " ".join(shlex.quote(item) for item in checks)

        probe_script = (
            "for spec in " + checks_str + "; do "
            "tool=${spec%%|*}; bins=${spec#*|}; found=''; "
            "for bin in $bins; do "
            "if command -v \"$bin\" >/dev/null 2>&1; then found=$bin; break; fi; "
            "done; "
            "if [ -n \"$found\" ]; then echo \"TOOL:$tool:1:$found\"; "
            "else echo \"TOOL:$tool:0:\"; fi; "
            "done"
        )

        result = executor.execute_command(probe_script, timeout=90)
        stdout = result.get("stdout", "")
        available = []
        unavailable = []
        resolved_bins = {}
        for line in stdout.splitlines():
            if not line.startswith("TOOL:"):
                continue
            _, tool, flag, binary = line.split(":", 3)
            if flag == "1":
                available.append(tool)
                resolved_bins[tool] = binary
            else:
                unavailable.append(tool)

        inventory = {
            "available_tools": sorted(available),
            "unavailable_tools": sorted(unavailable),
            "resolved_bins": resolved_bins,
        }
        self._tool_inventory_cache[backend] = inventory
        return inventory

    def _command_not_found(self, stderr: str) -> bool:
        if not stderr:
            return False
        lower = stderr.lower()
        return ("command not found" in lower) or ("not found" in lower and "/bin/bash" in lower)

    def _drain_operator_messages(self):
        with self._operator_lock:
            if not self._pending_operator_messages:
                return []
            messages = self._pending_operator_messages[:]
            self._pending_operator_messages = []
        return messages

    def _is_command_authorized(self, command: str):
        if not self.current_state or not self.current_state.target:
            return False, "No authorized target is set for this session."

        target_raw = self.current_state.target.strip()
        target_host = self._normalize_target_host(target_raw)
        target_raw_l = target_raw.lower()
        target_host_l = target_host.lower()

        tokens = self._split_command_tokens(command)
        if not tokens:
            return False, "Empty command."

        disallowed_flags = {"-iL", "--iL", "--input-file", "--shodan"}
        for token in tokens:
            if token in disallowed_flags:
                return False, f"Disallowed broad-target flag '{token}'."

        host_candidates = self._extract_host_candidates(tokens)
        if not host_candidates:
            return False, "Command does not explicitly include the authorized target."

        target_seen = False
        for host in host_candidates:
            h = host.lower()
            if self._is_exact_authorized_target(h, target_raw_l, target_host_l):
                target_seen = True
                continue
            return False, f"Unauthorized target detected: '{host}'."

        if not target_seen:
            return False, f"Authorized target '{target_raw}' was not found in command."

        return True, ""

    def _split_command_tokens(self, command: str):
        try:
            return shlex.split(command)
        except ValueError:
            return command.strip().split()

    def _normalize_target_host(self, target: str) -> str:
        t = target.strip()
        if "://" in t:
            parsed = urlparse(t)
            host = parsed.hostname or ""
            return host

        t = t.split("/", 1)[0].strip()
        if ":" in t and not t.startswith("["):
            left, right = t.rsplit(":", 1)
            if right.isdigit():
                t = left
        return t

    def _extract_host_candidates(self, tokens):
        candidates = []
        host_pattern = re.compile(r"^(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}$")
        ipv4_pattern = re.compile(r"^\d{1,3}(?:\.\d{1,3}){3}$")
        ipv4_cidr_pattern = re.compile(r"^\d{1,3}(?:\.\d{1,3}){3}/\d{1,2}$")

        for token in tokens:
            for piece in self._token_pieces(token):
                p = piece.strip()
                if not p or p.startswith("-"):
                    continue

                if "://" in p:
                    parsed = urlparse(p)
                    if parsed.hostname:
                        candidates.append(parsed.hostname)
                    continue

                if ipv4_cidr_pattern.match(p):
                    candidates.append(p)
                    continue

                host_port = p
                if ":" in host_port and host_port.count(":") == 1:
                    left, right = host_port.rsplit(":", 1)
                    if right.isdigit():
                        host_port = left

                if ipv4_pattern.match(host_port) or host_pattern.match(host_port):
                    candidates.append(host_port)

        # Preserve order while removing duplicates
        return list(dict.fromkeys(candidates))

    def _token_pieces(self, token: str):
        # Handles patterns like --host=example.com
        if "=" in token:
            left, right = token.split("=", 1)
            return [left, right]
        return [token]

    def _is_exact_authorized_target(self, host: str, target_raw_l: str, target_host_l: str) -> bool:
        if host == target_raw_l or host == target_host_l:
            return True

        # CIDR/range scanning is blocked unless it is exactly the user-specified raw target
        if "/" in host:
            return host == target_raw_l

        return False
