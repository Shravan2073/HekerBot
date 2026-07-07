from hekerbot.agent.brain import HekerBrain
from hekerbot.executor.docker_executor import DockerExecutor
from hekerbot.executor.local_executor import LocalExecutor
from hekerbot.persistence.state import SessionState, PersistenceManager, CommandResult
from rich.console import Console
from rich.panel import Panel
from rich.live import Live
from rich.spinner import Spinner
import time
import uuid
import os

console = Console(color_system=None)

class HekerAgent:
    def __init__(self, model: str = None):
        self.brain = HekerBrain(model=model)
        self.executor = DockerExecutor()
        self.local_executor = LocalExecutor()
        self.persistence = PersistenceManager()
        self.running = False
        self.current_state = None
        self.docker_mode_enabled = os.getenv("HEKER_DOCKER_MODE", "on").strip().lower() not in {"off", "false", "0", "no"}

    def set_docker_mode(self, enabled: bool):
        self.docker_mode_enabled = enabled

    def docker_mode(self) -> str:
        return "on" if self.docker_mode_enabled else "off"

    def execution_mode(self) -> str:
        return "docker" if self.docker_mode_enabled else "local"

    def active_executor(self):
        return self.executor if self.docker_mode_enabled else self.local_executor

    def is_execution_available(self) -> bool:
        return self.active_executor().is_available()

    def run_session(self, target: str):
        self.running = True
        self.brain.reset(target)
        
        session_id = str(uuid.uuid4())[:8]
        self.current_state = SessionState(session_id=session_id, target=target)
        
        console.print(f"[*] Starting mission {session_id} on target: {target}")
        
        observation = None
        while self.running:
            # 1. Think
            console.print("[*] Agent is thinking...")
            decision = self.brain.think(observation, self.current_state.discovery_graph)
            
            if not self.running: break

            thought = decision.get("thought", "...")
            command = decision.get("command", "")
            updates = decision.get("updates")
            finished = decision.get("finished", False)

            # Record thought
            self.current_state.history.append(decision)

            # Display Thought
            console.print(f"\n[THOUGHT]\n{thought}\n")

            # Process Updates
            if updates and isinstance(updates, dict):
                ip = updates.get("ip")
                if ip:
                    self.current_state.update_asset(
                        ip=ip,
                        hostname=updates.get("hostname"),
                        ports=updates.get("new_ports"),
                        vulnerabilities=updates.get("new_vulnerabilities")
                    )
                    console.print(f"[+] Knowledge Graph Updated: {ip}")

            if finished:
                summary = decision.get("summary", "Mission completed.")
                console.print(f"\n[MISSION COMPLETE]\n{summary}")
                self.running = False
                break

            if not command:
                console.print("[-] Agent provided no command. Retrying...")
                observation = "No command provided. Please specify a tool and arguments."
                continue

            # 2. Act (Execute command in selected mode)
            console.print(f"[*] Executing: {command}")
            
            try:
                result = self.active_executor().execute_command(command)
            except Exception as e:
                console.print(f"[!] Execution Error: {str(e)}")
                observation = f"Error executing command: {str(e)}"
                continue
            
            if not self.running: break

            stdout = result.get("stdout", "")
            stderr = result.get("stderr", "")
            exit_code = result.get("exit_code", 0)

            # Record result
            cmd_result = CommandResult(
                command=command,
                stdout=stdout,
                stderr=stderr,
                exit_code=exit_code
            )
            self.current_state.command_results.append(cmd_result)

            # 3. Observe
            if stdout:
                console.print(f"[STDOUT]\n{stdout}")
            if stderr:
                console.print(f"[STDERR]\n{stderr}")

            observation = f"Exit code: {exit_code}\nSTDOUT: {stdout}\nSTDERR: {stderr}"
            
            # Save state
            self.persistence.save_session(self.current_state)
            
            time.sleep(1)
        
        console.print(f"Mission {session_id} stopped.")

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

        # Rebuild brain context from session history
        self.brain.reset(target)
        for entry in state.history:
            # Re-feed past thoughts so the LLM has context
            self.brain.messages.append({
                "role": "assistant",
                "content": str(entry)
            })

        console.print(f"[*] Resuming session {session_id} on target: {target}")
        console.print(f"[*] Loaded {len(state.command_results)} previous commands.")

        observation = None
        while self.running:
            console.print("[*] Agent is thinking...")
            decision = self.brain.think(observation, self.current_state.discovery_graph)

            if not self.running: break

            thought = decision.get("thought", "...")
            command = decision.get("command", "")
            updates = decision.get("updates")
            finished = decision.get("finished", False)

            self.current_state.history.append(decision)
            console.print(f"\n[THOUGHT]\n{thought}\n")

            if updates and isinstance(updates, dict):
                ip = updates.get("ip")
                if ip:
                    self.current_state.update_asset(
                        ip=ip,
                        hostname=updates.get("hostname"),
                        ports=updates.get("new_ports"),
                        vulnerabilities=updates.get("new_vulnerabilities")
                    )
                    console.print(f"[+] Knowledge Graph Updated: {ip}")

            if finished:
                summary = decision.get("summary", "Mission completed.")
                console.print(f"\n[MISSION COMPLETE]\n{summary}")
                self.running = False
                break

            if not command:
                console.print("[-] Agent provided no command. Retrying...")
                observation = "No command provided. Please specify a tool and arguments."
                continue

            console.print(f"[*] Executing: {command}")

            try:
                result = self.active_executor().execute_command(command)
            except Exception as e:
                console.print(f"[!] Execution Error: {str(e)}")
                observation = f"Error executing command: {str(e)}"
                continue

            if not self.running: break

            stdout = result.get("stdout", "")
            stderr = result.get("stderr", "")
            exit_code = result.get("exit_code", 0)

            cmd_result = CommandResult(
                command=command,
                stdout=stdout,
                stderr=stderr,
                exit_code=exit_code
            )
            self.current_state.command_results.append(cmd_result)

            if stdout:
                console.print(f"[STDOUT]\n{stdout}")
            if stderr:
                console.print(f"[STDERR]\n{stderr}")

            observation = f"Exit code: {exit_code}\nSTDOUT: {stdout}\nSTDERR: {stderr}"
            self.persistence.save_session(self.current_state)
            time.sleep(1)

        console.print(f"Session {session_id} stopped.")
