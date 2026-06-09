import sys
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.history import FileHistory
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from prompt_toolkit.patch_stdout import patch_stdout
from hekerbot.agent.agent import HekerAgent
import threading

console = Console()

class HekerShell:
    def __init__(self):
        self.session = PromptSession(history=FileHistory(".hekerbot_history"))
        self.completer = WordCompleter([
            "help", "exit", "start", "stop", "status", "sessions", "clear", "build"
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

        if cmd == "exit":
            self.stop_agent()
            self.running = False
        elif cmd == "help":
            self.show_help()
        elif cmd == "clear":
            console.clear()
        elif cmd == "status":
            self.show_status()
        elif cmd == "sessions":
            self.list_sessions()
        elif cmd == "start":
            if not args:
                console.print("[red]Usage: start <target>[/red]")
            else:
                self.start_agent(args[0])
        elif cmd == "stop":
            self.stop_agent()
        elif cmd == "build":
            self.build_sandbox()
        else:
            console.print(f"[yellow]Unknown command: {cmd}[/yellow]")

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
        table.add_row("clear", "Clear the terminal")
        table.add_row("help", "Show this help message")
        table.add_row("exit", "Exit HekerBOT")
        
        console.print(table)

    def show_status(self):
        status = "[bold green]Running[/bold green]" if self.agent.running else "[bold yellow]Idle[/bold yellow]"
        msg = f"Agent is {status}"
        if self.agent.running and self.agent.current_state:
            msg += f"\nTarget: {self.agent.current_state.target}\nSession: {self.agent.current_state.session_id}"
        console.print(Panel(msg, title="Status"))

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
