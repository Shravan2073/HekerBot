import sys
import os
import threading
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.history import FileHistory
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from prompt_toolkit.patch_stdout import patch_stdout
from hekerbot.agent.agent import HekerAgent

# Global console for the whole app
console = Console(color_system=None)

class HekerShell:
    def __init__(self):
        self.session = PromptSession(history=FileHistory(".hekerbot_history"))
        self.commands = {
            "help": self.show_help,
            "exit": self.exit_shell,
            "start": self.start_agent,
            "stop": self.stop_agent,
            "status": self.show_status,
            "sessions": self.list_sessions,
            "build": self.build_sandbox,
            "clear": self.clear_terminal,
            "diag": self.run_diagnostics
        }
        self.completer = WordCompleter([
            "help", "exit", "start", "stop", "status", "sessions", "clear", "build", "diag"
        ], ignore_case=True)
        self.running = True
        self.agent = HekerAgent()
        self.agent_thread = None
        self._check_docker()

    def _check_docker(self):
        if not self.agent.executor.is_available():
            console.print(Panel(
                "[bold red]WARNING: Docker is not available.[/bold red]\n"
                "HekerBOT requires Docker for sandboxed command execution.\n"
                "Please ensure Docker is running and you have proper permissions.",
                title="System Check",
                border_style="red"
            ))

    def exit_shell(self, args=None):
        self.stop_agent()
        self.running = False

    def clear_terminal(self, args=None):
        console.clear()

    def display_banner(self):
        banner = Text(r"""
  _    _      _             ____   ____ _______ 
 | |  | |    | |           |  _ \ / __ \__   __|
 | |__| | ___| | _____ _ __| |_) | |  | | | |   
 |  __  |/ _ \ |/ / _ \ '__|  _ <| |  | | | |   
 | |  | |  __/   <  __/ |  | |_) | |__| | | |   
 |_|  |_|\___|_|\_\___|_|  |____/ \____/  |_|   
        """, style="bold red")
        console.print(Panel(banner, subtitle="Autonomous Red Teaming Framework", border_style="red"))

    def handle_command(self, cmd_line):
        parts = cmd_line.strip().split()
        if not parts:
            return
        
        cmd = parts[0].lower()
        args = parts[1:]

        if cmd in self.commands:
            try:
                if cmd in ["start"]:
                    if not args:
                        console.print("[red]Usage: start <target>[/red]")
                    else:
                        self.commands[cmd](args[0])
                else:
                    self.commands[cmd]()
            except Exception as e:
                console.print(f"[bold red]Error executing command {cmd}:[/bold red] {str(e)}")
        else:
            console.print(f"[yellow]Unknown command: {cmd}[/yellow]")

    def run_diagnostics(self):
        table = Table(title="HekerBOT Diagnostics", border_style="yellow")
        table.add_column("Component", style="cyan")
        table.add_column("Status")
        table.add_column("Details")

        # Environment
        table.add_row("Working Directory", "[blue]INFO[/blue]", os.getcwd())
        table.add_row("User", "[blue]INFO[/blue]", os.getenv("USER", "unknown"))

        # Docker
        docker_ok = self.agent.executor.is_available()
        docker_socket_exists = os.path.exists("/var/run/docker.sock")
        
        docker_detail = "Connected"
        if not docker_ok:
            if not docker_socket_exists:
                docker_detail = "Socket /var/run/docker.sock not found. Is Docker installed?"
            else:
                docker_detail = "Permission denied. Try running with 'sudo' or add user to 'docker' group."
        
        table.add_row(
            "Docker", 
            "[green]OK[/green]" if docker_ok else "[red]FAIL[/red]",
            docker_detail
        )

        # API Keys
        for key in ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GEMINI_API_KEY"]:
            val = os.getenv(key)
            status = "[green]SET[/green]" if val and "your_" not in val else "[yellow]MISSING[/yellow]"
            table.add_row(f"API Key: {key}", status, "Ready" if status == "[green]SET[/green]" else "Check .env")

        # Model
        model = os.getenv("HEKER_MODEL", "Not Set")
        table.add_row("Configured Model", "[blue]INFO[/blue]", model)

        console.print(table)

    def build_sandbox(self):
        console.print("[bold blue]Building sandbox Docker image...[/bold blue]")
        try:
            self.agent.executor.build_image()
            console.print("[bold green]Sandbox image built successfully.[/bold green]")
        except Exception as e:
            console.print(f"[bold red]Build failed:[/bold red] {str(e)}")

    def start_agent(self, target):
        if self.agent.running:
            console.print("[yellow]Agent is already running. Use 'stop' first.[/yellow]")
            return
        
        if not self.agent.executor.is_available():
            console.print("[bold red]Error: Docker is not available. Mission cannot start.[/bold red]")
            console.print("[yellow]Run 'diag' to check your environment.[/yellow]")
            return

        console.print(f"[green]Starting background mission for target: {target}[/green]")
        self.agent_thread = threading.Thread(target=self.agent.run_session, args=(target,), daemon=True)
        self.agent_thread.start()

    def stop_agent(self):
        if self.agent.running:
            console.print("[yellow]Stopping agent...[/yellow]")
            self.agent.stop()
            if self.agent_thread:
                self.agent_thread.join(timeout=5)
            console.print("[green]Agent stopped.[/green]")
        else:
            console.print("[yellow]No agent is currently running.[/yellow]")

    def show_help(self):
        table = Table(title="Available Commands", border_style="blue")
        table.add_column("Command", style="cyan")
        table.add_column("Description")
        
        table.add_row("start <target>", "Start a new background pentest on the specified target")
        table.add_row("stop", "Stop the current agent mission")
        table.add_row("status", "Show current agent status")
        table.add_row("sessions", "List previous sessions")
        table.add_row("build", "Build the Docker sandbox image")
        table.add_row("diag", "Run system diagnostics")
        table.add_row("clear", "Clear the terminal")
        table.add_row("help", "Show this help message")
        table.add_row("exit", "Exit HekerBOT")
        
        console.print(table)

    def show_status(self):
        status = "[bold green]Running[/bold green]" if self.agent.running else "[bold yellow]Idle[/bold yellow]"
        msg = f"Agent Status: {status}"
        
        if self.agent.current_state:
            state = self.agent.current_state
            msg += f"\n[bold]Target:[/bold] {state.target}"
            msg += f"\n[bold]Session ID:[/bold] {state.session_id}"
            msg += f"\n[bold]Assets Discovered:[/bold] {len(state.discovery_graph)}"
            
            if state.history:
                last_thought = state.history[-1].get("thought", "N/A")
                msg += f"\n\n[bold blue]Last Thought:[/bold blue]\n{last_thought}"
            
            if state.command_results:
                last_cmd = state.command_results[-1].command
                msg += f"\n\n[bold magenta]Last Command:[/bold magenta] {last_cmd}"

        console.print(Panel(msg, title="HekerBOT Status"))

    def list_sessions(self):
        sessions = self.agent.persistence.list_sessions()
        if not sessions:
            console.print("[yellow]No saved sessions found.[/yellow]")
            return
        
        table = Table(title="Saved Sessions", border_style="magenta")
        table.add_column("Session ID", style="cyan")
        
        for sid in sessions:
            table.add_row(sid)
        
        console.print(table)

    def run(self):
        self.display_banner()
        with patch_stdout():
            while self.running:
                try:
                    user_input = self.session.prompt("hekerbot > ", completer=self.completer)
                    if user_input:
                        self.handle_command(user_input)
                except KeyboardInterrupt:
                    continue
                except EOFError:
                    break
        console.print("[bold red]Exiting HekerBOT...[/bold red]")

if __name__ == "__main__":
    shell = HekerShell()
    shell.run()
