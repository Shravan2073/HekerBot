import os
import asyncio
import subprocess
from textual import work
from textual.app import App, ComposeResult
from textual.screen import Screen
from textual.containers import Vertical, Horizontal
from textual.widgets import Static, OptionList, Input, Button, Label, RichLog, Footer, LoadingIndicator, TextArea
from textual.reactive import reactive
from textual import events
from rich.text import Text
from dotenv import set_key, find_dotenv

from hekerbot.agent.agent import HekerAgent, console

def get_app_version() -> str:
    base_version = "0.1-venom-it-is"
    try:
        # Assuming the CWD is inside the git repo when the app runs
        res = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, timeout=1)
        if res.returncode == 0:
            commit_hash = res.stdout.strip()
            return f"{base_version} ({commit_hash})"
    except Exception:
        pass
    return base_version

HEKERBOT_ASCII = [
    r"██╗  ██╗███████╗██╗  ██╗███████╗██████╗ ██████╗  ██████╗ ████████╗      ██████╗     ",
    r"██║  ██║██╔════╝██║ ██╔╝██╔════╝██╔══██╗██╔══██╗██╔═══██╗╚══██╔══╝    ██████████╗   ",
    r"███████║█████╗  █████╔╝ █████╗  ██████╔╝██████╔╝██║   ██║   ██║       ██╔╗██╔╗██║   ",
    r"██╔══██║██╔══╝  ██╔═██╗ ██╔══╝  ██╔══██╗██╔══██╗██║   ██║   ██║       ██╚╝██╚╝██║   ",
    r"██║  ██║███████╗██║  ██╗███████╗██║  ██║██████╔╝╚██████╔╝   ██║       ╚████████╔╝   ",
    r"╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═════╝  ╚═════╝    ╚═╝        ╚█║█║█║█╝    "
]

class BigBanner(Static):
    """A straight, sharp ASCII banner with an ANSI shadow greyscale theme and shiny animation."""
    
    shine_offset = reactive(-20.0)

    def on_mount(self) -> None:
        # Update the animation 20 times per second
        self.set_interval(0.05, self.update_shine)

    def update_shine(self) -> None:
        # Move the shine across the banner
        self.shine_offset += 2.5
        if self.shine_offset > 120:
            self.shine_offset = -20.0

    def render(self) -> Text:
        result = Text()
        for row in HEKERBOT_ASCII:
            row_text = Text()
            for i, char in enumerate(row):
                if char == "█":
                    # Base color is light grey (#cccccc)
                    r, g, b = 180, 180, 180
                    
                    # Calculate distance from the shine's center
                    distance = abs(i - self.shine_offset)
                    
                    # Apply a bright white shine effect if within the radius
                    if distance < 8:
                        intensity = 1.0 - (distance / 8.0)
                        r = int(r + (255 - r) * (intensity ** 1.5))
                        g = int(g + (255 - g) * (intensity ** 1.5))
                        b = int(b + (255 - b) * (intensity ** 1.5))
                        
                    color = f"#{r:02x}{g:02x}{b:02x}"
                    row_text.append(char, style=color)
                elif char in "╗║╝╔═╚":
                    # Darker grey/subtle outline for the shadow characters
                    row_text.append(char, style="#555555")
                else:
                    row_text.append(char)
            result.append(row_text)
            result.append("\n")
        return result


class HelpPanel(Static):
    """Lightweight keyboard help overlay."""

    def __init__(self):
        super().__init__(
            "[bold #d4d4d8]HELP[/]\n"
            "[dim]Navigation:[/] ↑/↓/←/→\n"
            "[dim]Start mission:[/] Enter on target input\n"
            "[dim]Send operator chat:[/] Enter on operator input\n"
            "[dim]Toggle help:[/] ?\n"
            "[dim]Back:[/] ESC\n"
            "[dim]Quit:[/] CTRL+Q",
            id="help-panel",
        )

class SettingsScreen(Screen):
    """Settings screen for configuring API keys and models."""
    BINDINGS = [
        ("up", "focus_previous", "Previous"),
        ("down", "focus_next", "Next"),
    ]

    def compose(self) -> ComposeResult:
        with Vertical(id="settings-container"):
            yield Static("[bold #e4e4e7]API KEY CONFIGURATION[/]", id="settings-title")
            
            yield Label("OpenAI API Key:")
            yield Input(placeholder="sk-...", id="openai-key", password=True)
            
            yield Label("Anthropic API Key:")
            yield Input(placeholder="sk-ant-...", id="anthropic-key", password=True)
            
            yield Label("Gemini API Key:")
            yield Input(placeholder="AIza...", id="gemini-key", password=True)
            
            yield Label("OpenCode API Key:")
            yield Input(placeholder="sk-...", id="opencode-key", password=True)
            
            yield Label("Other Model/Provider URL (Optional):")
            yield Input(placeholder="https://...", id="other-key", password=False)

            yield Label("Agent Model (e.g. opencode/deepseek-coder, gemini/gemini-2.5-flash):")
            yield Input(placeholder="opencode/deepseek-coder", id="heker-model", password=False)
            
            yield Button("SAVE & RETURN", id="save-settings")

    def on_mount(self) -> None:
        if "OPENAI_API_KEY" in os.environ:
            self.query_one("#openai-key", Input).value = os.environ["OPENAI_API_KEY"]
        if "ANTHROPIC_API_KEY" in os.environ:
            self.query_one("#anthropic-key", Input).value = os.environ["ANTHROPIC_API_KEY"]
        if "GEMINI_API_KEY" in os.environ:
            self.query_one("#gemini-key", Input).value = os.environ["GEMINI_API_KEY"]
        if "OPENCODE_API_KEY" in os.environ:
            self.query_one("#opencode-key", Input).value = os.environ["OPENCODE_API_KEY"]
        if "HEKER_MODEL" in os.environ:
            self.query_one("#heker-model", Input).value = os.environ["HEKER_MODEL"]

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save-settings":
            env_file = find_dotenv()
            if not env_file:
                env_file = os.path.join(os.getcwd(), ".env")

            openai_val = self.query_one("#openai-key", Input).value.strip()
            if openai_val:
                os.environ["OPENAI_API_KEY"] = openai_val
                set_key(env_file, "OPENAI_API_KEY", openai_val)
            
            anthropic_val = self.query_one("#anthropic-key", Input).value.strip()
            if anthropic_val:
                os.environ["ANTHROPIC_API_KEY"] = anthropic_val
                set_key(env_file, "ANTHROPIC_API_KEY", anthropic_val)
            
            gemini_val = self.query_one("#gemini-key", Input).value.strip()
            if gemini_val:
                os.environ["GEMINI_API_KEY"] = gemini_val
                set_key(env_file, "GEMINI_API_KEY", gemini_val)
            
            opencode_val = self.query_one("#opencode-key", Input).value.strip()
            if opencode_val:
                os.environ["OPENCODE_API_KEY"] = opencode_val
                set_key(env_file, "OPENCODE_API_KEY", opencode_val)
            
            other_url = self.query_one("#other-key", Input).value.strip()
            if other_url:
                os.environ["OPENAI_BASE_URL"] = other_url
                set_key(env_file, "OPENAI_BASE_URL", other_url)
            
            model_val = self.query_one("#heker-model", Input).value.strip()
            if model_val:
                os.environ["HEKER_MODEL"] = model_val
                self.app.agent.brain.model = model_val
                set_key(env_file, "HEKER_MODEL", model_val)
            
            self.app.pop_screen()

class SessionsModal(Screen):
    """Modal screen for managing sessions."""
    BINDINGS = [
        ("r", "resume_session", "Resume"),
        ("v", "view_session", "View"),
        ("d", "delete_session", "Delete"),
        ("e", "export_session", "Export"),
        ("escape", "pop_screen", "Back")
    ]

    def compose(self) -> ComposeResult:
        with Vertical(id="sessions-modal"):
            yield Static("[bold #d4d4d8]SESSIONS[/]", id="modal-title")
            yield OptionList(id="session-list")
            yield Static("[dim]No session selected.[/]", id="modal-status")

            # Session details panel (hidden by default)
            with Vertical(id="session-detail", classes="hidden"):
                yield Static("", id="session-info")

            # Export path input (hidden by default)
            with Vertical(id="export-container", classes="hidden"):
                yield Input(placeholder="Export path (press Enter)...", id="export-path")

            yield Static(
                "\n[dim][bold white]R[/] resume · [bold white]V[/] view · [bold white]D[/] delete · [bold white]E[/] export · [bold white]ESC[/] back[/dim]",
                id="modal-guidance"
            )

    def on_mount(self) -> None:
        self.refresh_sessions()

    def on_screen_resume(self) -> None:
        self.refresh_sessions()
        self.query_one("#export-container").add_class("hidden")
        self.query_one("#session-detail").add_class("hidden")
        self.query_one("#modal-status", Static).update("[dim]No session selected.[/]")

    def action_pop_screen(self) -> None:
        export_container = self.query_one("#export-container")
        if not export_container.has_class("hidden"):
            export_container.add_class("hidden")
            self.query_one("#export-path", Input).value = ""
            self.query_one("#session-list").focus()
            self.query_one("#modal-status", Static).update("[dim]Export cancelled.[/]")
        else:
            self.app.pop_screen()

    def refresh_sessions(self) -> None:
        session_list = self.query_one("#session-list", OptionList)
        session_list.clear_options()
        sessions = self.app.agent.persistence.list_sessions()
        for s in sessions:
            # Try to load target info for a richer display
            state = self.app.agent.persistence.load_session(s)
            if state:
                label = f"{s}  [dim]→ {state.target}  ({len(state.command_results)} cmds)[/]"
            else:
                label = s
            session_list.add_option(label)

    def _get_selected_id(self):
        """Extract the raw session ID from the selected option."""
        session_list = self.query_one("#session-list", OptionList)
        if session_list.highlighted is None:
            return None
        prompt = str(session_list.get_option_at_index(session_list.highlighted).prompt)
        # The ID is the first 8 chars before the dim tag
        return prompt.split(" ")[0].strip()

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        if event.option_list.id == "session-list":
            sid = self._get_selected_id()
            if sid:
                self.query_one("#modal-status", Static).update(f"Selected: [bold white]{sid}[/]")

    def action_view_session(self) -> None:
        sid = self._get_selected_id()
        if not sid:
            self.query_one("#modal-status", Static).update("[bold #ef4444]No session selected.[/]")
            return
        state = self.app.agent.persistence.load_session(sid)
        if not state:
            self.query_one("#modal-status", Static).update("[bold #ef4444]Session not found.[/]")
            return

        # Build a summary view
        lines = []
        lines.append(f"[bold #d4d4d8]Session:[/] {sid}")
        lines.append(f"[bold #d4d4d8]Target:[/]  {state.target}")
        if state.goal:
            lines.append(f"[bold #d4d4d8]Goal:[/]    {state.goal}")
        lines.append(f"[bold #d4d4d8]Started:[/] {state.start_time.strftime('%Y-%m-%d %H:%M')}")
        lines.append(f"[bold #d4d4d8]Commands:[/] {len(state.command_results)}")
        if state.command_results:
            lines.append("")
            lines.append("[dim]Last 5 commands:[/]")
            for cmd in state.command_results[-5:]:
                lines.append(f"  [#71717a]$[/] {cmd.command}")

        self.query_one("#session-info", Static).update("\n".join(lines))
        self.query_one("#session-detail").remove_class("hidden")
        self.query_one("#modal-status", Static).update(f"Viewing session [bold white]{sid}[/]")

    def action_resume_session(self) -> None:
        sid = self._get_selected_id()
        if not sid:
            self.query_one("#modal-status", Static).update("[bold #ef4444]No session selected.[/]")
            return

        agent = self.app.agent
        if agent.running:
            self.query_one("#modal-status", Static).update("[bold #ef4444]Agent is already running. Stop it first.[/]")
            return

        state = self.app.agent.persistence.load_session(sid)
        if not state:
            self.query_one("#modal-status", Static).update("[bold #ef4444]Session not found.[/]")
            return

        # Pop back to dashboard and start the resumed session
        self.app.pop_screen()

        # Get the dashboard and kick off the resume
        dashboard = self.app.screen
        log = dashboard.query_one("#mission-log", RichLog)
        status = dashboard.query_one("#status-display", Static)

        log.clear()
        log.write("==================================================")
        log.write(f" RESUMING SESSION: {sid}")
        log.write(f" Target: {state.target}")
        log.write(f" Previous commands: {len(state.command_results)}")
        log.write("==================================================\n")

        status.update(f"[bold #d4d4d8]RESUMING SESSION[/]\n\nSession: {sid}\nTarget: [bold white]{state.target}[/]")
        dashboard.query_one("#target-input", Input).value = state.target
        try:
            dashboard.query_one("#instructions-input", TextArea).text = state.goal or ""
        except Exception:
            pass
        try:
            dashboard.query_one("#goal-input", Input).value = state.goal or ""
        except Exception:
            pass
        dashboard.query_one("#mission-loader").remove_class("hidden")
        dashboard.run_agent_resume(sid)

    def action_delete_session(self) -> None:
        sid = self._get_selected_id()
        if not sid:
            self.query_one("#modal-status", Static).update("[bold #ef4444]No session selected.[/]")
            return
        storage_dir = self.app.agent.persistence.storage_dir
        session_file = os.path.join(storage_dir, f"{sid}.json")
        if os.path.exists(session_file):
            os.remove(session_file)
            self.query_one("#modal-status", Static).update(f"[#d4d4d8]Deleted[/] session {sid}")
            self.query_one("#session-detail").add_class("hidden")
        else:
            self.query_one("#modal-status", Static).update("[bold #ef4444]Session not found.[/]")
        self.refresh_sessions()

    def action_export_session(self) -> None:
        sid = self._get_selected_id()
        if not sid:
            self.query_one("#modal-status", Static).update("[bold #ef4444]No session selected.[/]")
            return
        self.query_one("#export-container").remove_class("hidden")
        self.query_one("#export-path").focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "export-path":
            sid = self._get_selected_id()
            if not sid:
                return
            path = event.value.strip()
            if not path:
                self.query_one("#modal-status", Static).update("[bold #ef4444]Enter a valid path.[/]")
                return

            storage_dir = self.app.agent.persistence.storage_dir
            session_file = os.path.join(storage_dir, f"{sid}.json")
            if not os.path.exists(session_file):
                self.query_one("#modal-status", Static).update("[bold #ef4444]Session not found.[/]")
                return
            try:
                import json
                with open(session_file, "r") as f:
                    data = json.load(f)

                with open(path, "w") as f:
                    f.write(f"--- EXPORTED SESSION: {sid} ---\n")
                    f.write(f"Target: {data.get('target', 'Unknown')}\n\n")
                    if data.get("goal"):
                        f.write(f"Goal: {data.get('goal')}\n\n")
                    f.write("COMMAND HISTORY:\n")
                    for res in data.get('command_results', []):
                        f.write(f"\n> {res.get('command', '')}\n")
                        f.write(f"{res.get('stdout', '')}\n")
                        if res.get('stderr'):
                            f.write(f"[ERR] {res.get('stderr')}\n")

                self.query_one("#modal-status", Static).update(f"[#d4d4d8]Exported[/] to {path}")
                self.query_one("#export-container").add_class("hidden")

                import subprocess
                import platform
                try:
                    if platform.system() == "Darwin":
                        subprocess.Popen(["open", path])
                    elif platform.system() == "Windows":
                        os.startfile(path)
                    else:
                        subprocess.Popen(["xdg-open", path])
                except Exception:
                    pass

            except Exception as e:
                self.query_one("#modal-status", Static).update(f"[bold #ef4444]Export failed:[/] {str(e)}")

class DockerScreen(Screen):
    """Screen for managing Docker settings and viewing daemon logs."""
    BINDINGS = [
        ("t", "toggle_docker", "Toggle"),
        ("escape", "pop_screen", "Back")
    ]

    def compose(self) -> ComposeResult:
        with Horizontal():
            with Vertical(id="docker-sidebar"):
                yield Static("[bold #e4e4e7]DOCKER[/]", id="docker-sidebar-header")
                yield OptionList(
                    "Toggle Docker Mode",
                    "Back to Dashboard",
                    id="docker-menu-options"
                )
            with Vertical(id="docker-content"):
                yield Static("[bold #e4e4e7]DOCKER DAEMON LOGS[/]", id="docker-log-title")
                yield Static("Checking status...", id="docker-status")
                yield RichLog(id="docker-log", wrap=True)

    def on_mount(self) -> None:
        self.refresh_status()
        self.log_status()

    def log_status(self) -> None:
        log = self.query_one("#docker-log", RichLog)
        is_enabled = self.app.agent.docker_mode_enabled
        if is_enabled:
            log.write("[bold #d4d4d8]DOCKER BACKEND STATUS[/]")
            log.write("[SYSTEM] Checking daemon connection...")
            executor = self.app.agent.executor
            if executor.is_available():
                log.write("[bold #22c55e]CONNECTED[/] Daemon is reachable.\n")
                
                try:
                    # Fetch detailed Docker info
                    client = executor.client
                    info = client.info()
                    version = client.version()
                    
                    log.write(f"  [#71717a]Server Version:[/] {version.get('Version', 'Unknown')}")
                    log.write(f"  [#71717a]OS/Arch:[/] {info.get('OperatingSystem', 'Unknown')} ({info.get('Architecture', 'Unknown')})")
                    log.write(f"  [#71717a]CPUs:[/] {info.get('NCPU', 'Unknown')}  |  [#71717a]Memory:[/] {round(info.get('MemTotal', 0) / (1024**3), 2)} GB\n")

                    log.write("[bold #d4d4d8]SANDBOX IMAGE[/]")
                    try:
                        image = client.images.get(executor.image_name)
                        size_mb = round(image.attrs['Size'] / (1024 * 1024), 1)
                        created = image.attrs.get('Created', 'Unknown')[:10]
                        log.write(f"  [#71717a]Tag:[/] {executor.image_name}:latest")
                        log.write(f"  [#71717a]Size:[/] {size_mb} MB  |  [#71717a]Created:[/] {created}")
                        log.write("  [bold #22c55e]READY[/] Image is available.\n")
                    except Exception:
                        log.write(f"  [#71717a]Tag:[/] {executor.image_name}")
                        log.write("  [bold #eab308]NOT FOUND[/] Image is missing. Run a mission to auto-build it.\n")

                    log.write("[bold #d4d4d8]ACTIVE CONTAINERS[/]")
                    containers = client.containers.list(filters={"ancestor": executor.image_name})
                    if containers:
                        log.write(f"  [#71717a]Running sandbox containers:[/] {len(containers)}")
                        for c in containers:
                            log.write(f"    - {c.short_id} ({c.status})")
                    else:
                        log.write("  [#71717a]Running sandbox containers:[/] 0")
                        
                    log.write("\n[bold #22c55e]Subsystems ONLINE and isolated.[/]")
                    
                except Exception as e:
                    log.write(f"[ERROR] Failed to fetch advanced info: {str(e)}")
            else:
                log.write("[bold #ef4444]DISCONNECTED[/]")
                log.write("[ERROR] Could not connect to Docker daemon!")
                log.write("[!] Check if Docker is running and your user has permissions.")
        else:
            log.write("[bold #d4d4d8]DOCKER BACKEND STATUS[/]")
            log.write("[bold #a1a1aa]OFFLINE[/]")
            log.write("\n[SYSTEM] Docker isolation is DISABLED.")
            log.write("[WARNING] Commands will be executed directly on the local host!")

    def refresh_status(self) -> None:
        is_enabled = self.app.agent.docker_mode_enabled
        status_text = "[bold white]ENABLED[/] (Ready to sandbox)" if is_enabled else "[bold #a1a1aa]DISABLED[/] (Running on local host)"
        self.query_one("#docker-status", Static).update(f"Docker isolation is currently {status_text}.")
        
        try:
            for screen in self.app.screen_stack:
                if hasattr(screen, "update_docker_header"):
                    screen.update_docker_header()
        except Exception:
            pass

    def action_toggle_docker(self) -> None:
        self.app.agent.docker_mode_enabled = not self.app.agent.docker_mode_enabled
        self.refresh_status()
        self.query_one("#docker-log", RichLog).write("==================================================")
        self.log_status()
        
    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        if event.option_list.id == "docker-menu-options":
            action = str(event.option.prompt)
            if action == "Toggle Docker Mode":
                self.action_toggle_docker()
            elif action == "Back to Dashboard":
                self.app.pop_screen()

class DashboardScreen(Screen):
    """The main working dashboard."""
    VIEW_MAP = {
        "▸ Start Mission": "start",
        "▸ Stop Mission": "stop",
        "▸ Agent Status": "status",
        "▸ Sessions": "sessions",
        "▸ Docker Mode": "docker"
    }

    @staticmethod
    def _parse_target_and_goal(raw_target: str, ui_goal: str) -> tuple[str, str]:
        target = (raw_target or "").strip()
        goal = (ui_goal or "").strip()
        if goal:
            return target, goal
        if "||" in target:
            left, right = target.split("||", 1)
            return left.strip(), right.strip()
        return target, goal

    def compose(self) -> ComposeResult:
        # Top header bar spanning full width
        with Horizontal(id="dash-topbar"):
            yield Static("[bold #d4d4d8]HEKERBOT[/]", id="dash-brand")
            yield Static("", id="dash-status-line")

        with Horizontal(id="dash-body"):
            # Sidebar
            with Vertical(id="sidebar"):
                yield Static("[dim]OPERATIONS[/]", id="sidebar-header")
                yield OptionList(
                    "▸ Start Mission",
                    "▸ Stop Mission",
                    "▸ Agent Status",
                    "▸ Sessions",
                    "▸ Docker Mode",
                    id="menu-options"
                )
                yield Static("", id="sidebar-spacer")
                yield Static("[dim]ESC[/dim] back  [dim]?[/dim] help", id="sidebar-hints")

            # Main content
            with Vertical(id="content-container"):
                with Horizontal(id="input-panels"):
                    with Vertical(id="setup-panel", classes="box-panel"):
                        yield Static("[dim]TARGET[/]", id="target-label")
                        yield Input(placeholder="Enter IP or domain...", id="target-input")
                        yield Static("[dim]INITIAL INSTRUCTIONS[/]", id="instructions-label")
                        yield TextArea(id="instructions-input")
                    with Vertical(id="operator-panel", classes="box-panel"):
                        yield Static("[dim]OPERATOR CHAT (LIVE)[/]", id="operator-label")
                        yield Input(placeholder="Send live instructions during mission and press Enter...", id="operator-input")
                        yield Static("", id="status-display")
                yield LoadingIndicator(id="mission-loader", classes="hidden")
                with Horizontal(id="headers-container"):
                    yield Static("● [bold #d4d4d8]TERMINAL[/] [dim]· live[/]", id="log-header")
                    yield Static("○ [bold #52525b]DOCKER[/] [dim]· offline[/]", id="docker-header")
                yield RichLog(id="mission-log", wrap=True)

    def on_mount(self) -> None:
        self.update_status_line()
        self.update_docker_header()
        self.set_interval(0.5, self.update_docker_header)
        self.set_interval(1.0, self.update_status_line)

    def update_status_line(self) -> None:
        try:
            agent = self.app.agent
            state = "[#d4d4d8]● RUNNING[/]" if agent.running else "[#52525b]○ IDLE[/]"
            docker = "[#d4d4d8]● DOCKER[/]" if agent.docker_mode_enabled else "[#52525b]○ LOCAL[/]"
            version = get_app_version()
            self.query_one("#dash-status-line", Static).update(
                f"{state}  {docker}  [dim]{version}[/]"
            )
        except Exception:
            pass

    def update_docker_header(self) -> None:
        try:
            is_enabled = self.app.agent.docker_mode_enabled
            if is_enabled:
                header = "● [bold #d4d4d8]DOCKER[/] [dim]· ready[/]"
            else:
                header = "○ [bold #52525b]DOCKER[/] [dim]· offline[/]"
            self.query_one("#docker-header", Static).update(header)
        except Exception:
            pass

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        if event.option_list.id == "menu-options":
            action = self.VIEW_MAP.get(str(event.option.prompt), "status")
            self.execute_action(action)

    def on_key(self, event: events.Key) -> None:
        if event.key in {"question_mark", "?"} or event.character == "?":
            self.app.action_help()
            event.prevent_default()
            event.stop()
            return

        if event.key == "right" and self.query_one("#menu-options").has_focus:
            self.query_one("#target-input").focus()
            event.prevent_default()
        elif event.key == "left" and self.query_one("#target-input").has_focus:
            if self.query_one("#target-input").cursor_position == 0:
                self.query_one("#menu-options").focus()
                event.prevent_default()
        elif event.key == "down" and self.query_one("#target-input").has_focus:
            self.query_one("#instructions-input").focus()
            event.prevent_default()
        elif event.key == "down" and self.query_one("#operator-input").has_focus:
            self.query_one("#mission-log").focus()
            event.prevent_default()
        elif event.key == "up" and self.query_one("#mission-log").has_focus:
            self.query_one("#operator-input").focus()
            event.prevent_default()
        elif event.key == "up" and self.query_one("#operator-input").has_focus:
            self.query_one("#instructions-input").focus()
            event.prevent_default()
        elif event.key == "left" and self.query_one("#mission-log").has_focus:
            self.query_one("#menu-options").focus()
            event.prevent_default()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "target-input":
            self.execute_action("start")
        elif event.input.id == "goal-input":
            self.query_one("#operator-input", Input).focus()
        elif event.input.id == "operator-input":
            self.execute_action("chat")
            
    @work(thread=True)
    def run_agent_mission(self, target: str, goal: str = "") -> None:
        log_widget = self.query_one("#mission-log", RichLog)
        
        class LogRedirector:
            def write(self, text):
                if text:
                    t = Text.from_ansi(text.strip("\n"))
                    self.app.call_from_thread(log_widget.write, t)
            def flush(self):
                pass
            def __init__(self, app):
                self.app = app
                
        old_file = console.file
        console.file = LogRedirector(self.app)
        
        try:
            self.app.agent.run_session(target, goal=goal)
        except Exception as e:
            self.app.call_from_thread(log_widget.write, f"[ERROR] Agent crashed: {str(e)}")
        finally:
            console.file = old_file
            self.app.agent.running = False
            self.app.call_from_thread(log_widget.write, "\n[SYSTEM] Agent IDLE.")
            
            def hide_loader():
                try:
                    self.query_one("#mission-loader").add_class("hidden")
                except Exception:
                    pass
            self.app.call_from_thread(hide_loader)

    @work(thread=True)
    def run_agent_resume(self, session_id: str) -> None:
        log_widget = self.query_one("#mission-log", RichLog)

        class LogRedirector:
            def write(self, text):
                if text:
                    t = Text.from_ansi(text.strip("\n"))
                    self.app.call_from_thread(log_widget.write, t)
            def flush(self):
                pass
            def __init__(self, app):
                self.app = app

        old_file = console.file
        console.file = LogRedirector(self.app)

        try:
            self.app.agent.resume_session(session_id)
        except Exception as e:
            self.app.call_from_thread(log_widget.write, f"[ERROR] Agent crashed: {str(e)}")
        finally:
            console.file = old_file
            self.app.agent.running = False
            self.app.call_from_thread(log_widget.write, "\n[SYSTEM] Agent IDLE.")

            def hide_loader():
                try:
                    self.query_one("#mission-loader").add_class("hidden")
                except Exception:
                    pass
            self.app.call_from_thread(hide_loader)
            
    def execute_action(self, action: str) -> None:
        try:
            status = self.query_one("#status-display", Static)
            log = self.query_one("#mission-log", RichLog)
        except Exception:
            return
            
        agent = self.app.agent
        
        if action == "start":
            target_raw = self.query_one("#target-input", Input).value.strip()
            goal_input = ""
            try:
                goal_input = self.query_one("#instructions-input", TextArea).text.strip()
            except Exception:
                try:
                    goal_input = self.query_one("#goal-input", Input).value.strip()
                except Exception:
                    goal_input = ""
            target, goal = self._parse_target_and_goal(target_raw, goal_input)
            if not target:
                status.update("[bold #ef4444]ERROR: NO TARGET ACQUIRED[/]\n\nPlease enter a target IP or domain in the input field above.")
                return
            
            if agent.running:
                status.update(f"[bold #ef4444]ERROR: AGENT ALREADY RUNNING[/]\n\nTarget: {agent.current_state.target if agent.current_state else 'unknown'}")
                return
                
            goal_line = f"\nGoal: [bold white]{goal}[/]" if goal else ""
            format_hint = "" if goal else "\n[dim]Tip: You can also use TARGET as: host || your goal[/]"
            status.update(
                f"[bold #e4e4e7]SYSTEM OVERRIDE INITIATED[/]\n\n"
                f"Target acquired: [bold white]{target}[/]{goal_line}\n"
                "Background payload delivery in progress...\nAgent is now RUNNING."
                f"{format_hint}"
            )
            
            log.clear()
            log.write("==================================================")
            log.write(" MISSION LOG INITIALIZED")
            log.write(f" Target: {target}")
            if goal:
                log.write(f" Goal: {goal}")
            log.write("==================================================\n")
            
            self.query_one("#mission-loader").remove_class("hidden")
            self.run_agent_mission(target, goal=goal)
            
        elif action == "stop":
            agent.stop()
            status.update("[bold #ef4444]MISSION ABORTED[/]\n\nTerminate signal dispatched.")
            log.write("\n[!] ABORT SIGNAL SENT: Terminating all active threads...\n")
        elif action == "chat":
            try:
                message_input = self.query_one("#operator-input", Input)
            except Exception:
                status.update("[bold #ef4444]Operator chat box not visible in this UI build.[/]")
                return
            msg = message_input.value.strip()
            if not msg:
                status.update("[bold #ef4444]Empty operator message.[/]")
                return
            accepted = agent.add_operator_input(msg)
            if accepted:
                log.write(f"[OPERATOR] {msg}")
                if agent.running:
                    status.update("[bold #22c55e]Operator input queued for next decision step.[/]")
                else:
                    status.update("[bold #eab308]Saved operator note. Start/resume mission to apply it.[/]")
                message_input.value = ""
            else:
                status.update("[bold #ef4444]No active session context. Start or resume a mission first.[/]")
        elif action == "docker":
            self.app.push_screen("docker_modal")
        elif action == "status":
            st = "[bold #22c55e]RUNNING[/]" if agent.running else "[bold #a1a1aa]IDLE[/]"
            status.update(f"[bold white]AGENT STATUS[/]\n\nState: {st}\nNetwork: SECURE")
        elif action == "sessions":
            self.app.push_screen("sessions_modal")

class ArcadeScreen(Screen):
    """The Arcade entry screen."""
    def compose(self) -> ComposeResult:
        with Vertical(id="main-container"):
            yield Static(get_app_version(), id="top-info")
            yield BigBanner(id="banner")
            
            yield OptionList(
                "Get Cracking !!",
                "API Center",
                id="menu"
            )
            
            
        with Horizontal(id="start-hints"):
            yield Static("Navigation: [bold white]↑/↓[/] · Select: [bold white]ENTER[/] · Back: [bold white]ESC[/]", id="hints-left")
            yield Static("Quit: [bold white]CTRL+Q[/]", id="hints-right")

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        if event.option_list.id == "menu":
            if str(event.option.prompt) == "Get Cracking !!":
                self.app.push_screen("dashboard")
            elif str(event.option.prompt) == "API Center":
                self.app.push_screen("settings")

class HekerApp(App):
    CSS_PATH = "shell.tcss"
    BINDINGS = [
        ("ctrl+q", "quit", "Quit"),
        ("escape", "safe_pop_screen", "Back"),
        ("question_mark", "help", "Help")
    ]
    SCREENS = {
        "dashboard": DashboardScreen, 
        "arcade": ArcadeScreen, 
        "settings": SettingsScreen, 
        "sessions_modal": SessionsModal,
        "docker_modal": DockerScreen
    }

    def __init__(self):
        super().__init__()
        self.agent = HekerAgent()

    def on_mount(self) -> None:
        self.push_screen("arcade")
        
        # Check if we just auto-updated
        import os
        update_info = os.environ.get("HEKERBOT_UPDATED")
        if update_info:
            self.notify(
                f"Successfully updated HekerBOT!\nVersions: {update_info}",
                title="Update Complete",
                severity="information",
                timeout=6.0
            )
            # Remove it so it doesn't persist in child processes unnecessarily
            del os.environ["HEKERBOT_UPDATED"]

    def action_safe_pop_screen(self) -> None:
        # Check if HelpPanel (the keys column) is open and close it first
        help_panels = self.screen.query("HelpPanel")
        if help_panels:
            for panel in help_panels:
                panel.remove()
            return

        # Prevent popping the ArcadeScreen (which leaves only the blank _default screen)
        if len(self.screen_stack) > 2:
            self.pop_screen()

    def action_help(self) -> None:
        help_panels = self.screen.query("HelpPanel")
        if help_panels:
            for panel in help_panels:
                panel.remove()
            return
        self.screen.mount(HelpPanel())

    def on_key(self, event: events.Key) -> None:
        if event.key in {"question_mark", "?"} or event.character == "?":
            self.action_help()
            event.prevent_default()
            event.stop()

if __name__ == "__main__":
    app = HekerApp()
    app.run()
