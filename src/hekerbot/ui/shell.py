import sys
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.history import FileHistory
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from hekerbot.agent.agent import HekerAgent
import threading

console = Console()

class HekerShell:
    def __init__(self):
        self.session = PromptSession(history=FileHistory(".hekerbot_history"))
        self.completer = WordCompleter([
            "help", "exit", "start", "stop", "status", "sessions", "clear"
        ], ignore_case=True)
        self.running = True
        self.agent = HekerAgent()
        self.agent_thread = None

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
        else:
            console.print(f"[yellow]Unknown command: {cmd}[/yellow]")

    def start_agent(self, target):
        if self.agent.running:
            console.print("[yellow]Agent is already running. Use 'stop' first.[/yellow]")
            return
        
        # In a real app, we might want to run this in a thread to keep the shell interactive,
        # but for simplicity in this TUI, we'll let it take over the console.
        # However, to be "Hardcore", let's try to run it and allow interruption.
        try:
            self.agent.run_session(target)
        except KeyboardInterrupt:
            console.print("\n[yellow]Interrupted by user. Agent stopping...[/yellow]")
            self.agent.stop()

    def stop_agent(self):
        if self.agent.running:
            self.agent.stop()
            console.print("[green]Agent stopped.[/green]")
        else:
            console.print("[yellow]No agent is currently running.[/yellow]")

    def show_help(self):
        table = Table(title="Available Commands", border_style="blue")
        table.add_column("Command", style="cyan")
        table.add_column("Description")
        
        table.add_row("start <target>", "Start a new pentest on the specified target")
        table.add_row("stop", "Stop the current agent mission")
        table.add_row("status", "Show current agent status")
        table.add_row("sessions", "List previous sessions")
        table.add_row("clear", "Clear the terminal")
        table.add_row("help", "Show this help message")
        table.add_row("exit", "Exit HekerBOT")
        
        console.print(table)

    def show_status(self):
        status = "[bold green]Running[/bold green]" if self.agent.running else "[bold yellow]Idle[/bold yellow]"
        console.print(Panel(f"Agent is {status}", title="Status"))

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
        while self.running:
            try:
                user_input = self.session.prompt("hekerbot > ", completer=self.completer)
                self.handle_command(user_input)
            except KeyboardInterrupt:
                continue
            except EOFError:
                break
        console.print("[bold red]Exiting HekerBOT...[/bold red]")

if __name__ == "__main__":
    shell = HekerShell()
    shell.run()
