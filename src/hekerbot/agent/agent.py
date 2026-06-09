from hekerbot.agent.brain import HekerBrain
from hekerbot.executor.docker_executor import DockerExecutor
from hekerbot.persistence.state import SessionState, PersistenceManager, CommandResult
from rich.console import Console
from rich.panel import Panel
from rich.live import Live
from rich.spinner import Spinner
import time
import uuid

console = Console()

class HekerAgent:
    def __init__(self, model: str = None):
        self.brain = HekerBrain(model=model)
        self.executor = DockerExecutor()
        self.persistence = PersistenceManager()
        self.running = False
        self.current_state = None

    def run_session(self, target: str):
        self.running = True
        self.brain.reset(target)
        
        session_id = str(uuid.uuid4())[:8]
        self.current_state = SessionState(session_id=session_id, target=target)
        
        console.print(Panel(f"Starting mission [bold magenta]{session_id}[/bold magenta] on target: [bold cyan]{target}[/bold cyan]", title="Mission Initialized", border_style="green"))
        
        observation = None
        while self.running:
            # 1. Think
            with console.status("[bold blue]Agent is thinking...[/bold blue]"):
                decision = self.brain.think(observation)
            
            if not self.running: break

            thought = decision.get("thought", "...")
            command = decision.get("command", "")
            finished = decision.get("finished", False)

            # Record thought
            self.current_state.history.append(decision)

            # Display Thought
            console.print(Panel(thought, title="[bold blue]Thought[/bold blue]", border_style="blue"))

            if finished:
                summary = decision.get("summary", "Mission completed.")
                console.print(Panel(summary, title="[bold green]Mission Complete[/bold green]", border_style="green"))
                self.running = False
                break

            if not command:
                console.print("[yellow]Agent provided no command. Retrying...[/yellow]")
                observation = "No command provided. Please specify a tool and arguments."
                continue

            # 2. Act (Execute in sandbox)
            console.print(f"[bold magenta]Executing:[/bold magenta] [cyan]{command}[/cyan]")
            
            with console.status(f"[bold yellow]Running {command.split()[0]}...[/bold yellow]"):
                try:
                    result = self.executor.execute_command(command)
                except Exception as e:
                    console.print(f"[bold red]Docker Error:[/bold red] {str(e)}")
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
                console.print("[dim]STDOUT:[/dim]")
                console.print(stdout[:500] + ("..." if len(stdout) > 500 else "")) 
            if stderr:
                console.print(f"[bold red]STDERR:[/bold red] {stderr}")

            observation = f"Exit code: {exit_code}\nSTDOUT: {stdout}\nSTDERR: {stderr}"
            
            # Save state
            self.persistence.save_session(self.current_state)
            
            time.sleep(1)
        
        console.print(f"[yellow]Mission {session_id} stopped.[/yellow]")

    def stop(self):
        self.running = False
