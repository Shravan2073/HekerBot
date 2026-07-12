import os
import math
import asyncio
import subprocess
from textual import work
from textual.app import App, ComposeResult
from textual.screen import Screen
from textual.containers import Vertical, Horizontal, VerticalScroll
from textual.widgets import Static, OptionList, Input, Button, Label, RichLog, Footer, TextArea
from textual.reactive import reactive
from textual.color import Color
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

class Spinner(Static):
    """A braille-frame spinner, in the spirit of modern CLI 'working' indicators."""

    FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    frame_index = reactive(0)
    label_text = reactive("Agent executing")

    def on_mount(self) -> None:
        self.set_interval(0.08, self._tick)

    def _tick(self) -> None:
        self.frame_index = (self.frame_index + 1) % len(self.FRAMES)

    def render(self) -> Text:
        return Text(f"{self.FRAMES[self.frame_index]}  {self.label_text}...", style="bold #22d3ee")


class ShineText(Static):
    """A line of plain text with a slow light sweep passing across it —
    the same idea as BigBanner's shine, generalized for ordinary labels."""

    shine_offset = reactive(-8.0)

    def __init__(self, text: str, base_color: str = "#71717a", shine_color: str = "#f4f4f5",
                 speed: float = 0.6, **kwargs) -> None:
        super().__init__(**kwargs)
        self._text = text
        self._base_color = base_color
        self._shine_color = shine_color
        self._speed = speed

    def on_mount(self) -> None:
        self.set_interval(0.05, self._tick)

    def _tick(self) -> None:
        self.shine_offset += self._speed
        if self.shine_offset > len(self._text) + 8:
            self.shine_offset = -8.0

    @staticmethod
    def _hex(color: str) -> tuple[int, int, int]:
        return int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)

    def render(self) -> Text:
        result = Text()
        br, bg_, bb = self._hex(self._base_color)
        sr, sg, sb = self._hex(self._shine_color)
        for i, char in enumerate(self._text):
            distance = abs(i - self.shine_offset)
            if distance < 5:
                intensity = (1.0 - (distance / 5.0)) ** 1.5
                r = int(br + (sr - br) * intensity)
                g = int(bg_ + (sg - bg_) * intensity)
                b = int(bb + (sb - bb) * intensity)
                result.append(char, style=f"#{r:02x}{g:02x}{b:02x}")
            else:
                result.append(char, style=self._base_color)
        return result


class SettingsScreen(Screen):
    """API Center — configure provider keys and the active agent model."""
    BINDINGS = [
        ("up", "focus_previous", "Previous"),
        ("down", "focus_next", "Next"),
        ("escape", "return_to_arcade", "Back"),
    ]

    # (field id, display name, placeholder, env var, accent color)
    PROVIDERS = [
        ("openai-key", "OpenAI", "sk-...", "OPENAI_API_KEY", "#10a37f"),
        ("anthropic-key", "Anthropic", "sk-ant-...", "ANTHROPIC_API_KEY", "#d97757"),
        ("gemini-key", "Gemini", "AIza...", "GEMINI_API_KEY", "#4285f4"),
        ("opencode-key", "OpenCode", "sk-...", "OPENCODE_API_KEY", "#8b5cf6"),
    ]

    def compose(self) -> ComposeResult:
        with Vertical(id="settings-container"):
            with Vertical(id="settings-header"):
                yield ShineText("API CENTER", base_color="#a1a1aa", shine_color="#ffffff", speed=0.5, id="settings-title")
                yield Static("[dim]Configure provider keys and the active agent model[/]", id="settings-subtitle")

            with VerticalScroll(id="settings-scroll"):
                with Vertical(classes="settings-section"):
                    yield ShineText("MODEL PROVIDERS", base_color="#52525b", shine_color="#d4d4d8", speed=0.3, classes="section-label")
                    for field_id, name, placeholder, _env, color in self.PROVIDERS:
                        with Vertical(classes="provider-card", id=f"{field_id}-card"):
                            yield Input(placeholder=placeholder, id=field_id, password=True)

                with Vertical(classes="settings-section"):
                    with Vertical(classes="config-card", id="config-card"):
                        with Vertical(classes="key-field-single"):
                            yield Label("Custom Base URL (optional)")
                            yield Input(placeholder="https://...", id="other-key", password=False)
                        with Vertical(classes="key-field-single"):
                            yield Label("Agent Model  [dim](e.g. opencode/deepseek-coder, gemini/gemini-2.5-flash)[/]")
                            yield Input(placeholder="opencode/deepseek-coder", id="heker-model", password=False)

            with Horizontal(id="settings-actions"):
                yield Button("SAVE & RETURN", id="save-settings", variant="primary")

            yield Static(
                "[dim]ESC[/dim] cancel   [dim]TAB[/dim] navigate fields   [dim]ENTER[/dim] confirm",
                id="settings-hints",
            )

    _card_phase = 0.0

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

        # Provider name embedded directly in the card's border line.
        for field_id, name, _placeholder, _env, color in self.PROVIDERS:
            card = self.query_one(f"#{field_id}-card")
            card.border_title = f"[{color}]●[/] {name}"
        self.query_one("#config-card").border_title = "agent_config"

        self.update_status_pills()

        # Subtle entrance animation, in the spirit of a modern CLI splash-in.
        container = self.query_one("#settings-container")
        container.styles.opacity = 0.0
        container.styles.animate("opacity", value=1.0, duration=0.28, easing="out_cubic")

        # Each card breathes gently, tinted with its own brand color — alive even at idle.
        self.set_interval(0.08, self._tick_card_glow)

    def _tick_card_glow(self) -> None:
        self._card_phase += 0.03
        try:
            for i, (field_id, _name, _placeholder, _env, color) in enumerate(self.PROVIDERS):
                card = self.query_one(f"#{field_id}-card")
                card.styles.border = ("round", Color.parse(self._breathe("#27272a", color, self._card_phase + i * 1.1)))
            self.query_one("#config-card").styles.border = (
                "round", Color.parse(self._breathe("#27272a", "#22d3ee", self._card_phase + 4.4))
            )
        except Exception:
            pass

    @staticmethod
    def _breathe(base_hex: str, bright_hex: str, phase: float, amplitude: float = 0.35) -> str:
        """Low-amplitude color interpolation for an idle breathing border."""
        intensity = ((math.sin(phase) + 1) / 2) * amplitude
        br, bg_, bb = int(base_hex[1:3], 16), int(base_hex[3:5], 16), int(base_hex[5:7], 16)
        tr, tg, tb = int(bright_hex[1:3], 16), int(bright_hex[3:5], 16), int(bright_hex[5:7], 16)
        r = int(br + (tr - br) * intensity)
        g = int(bg_ + (tg - bg_) * intensity)
        b = int(bb + (tb - bb) * intensity)
        return f"#{r:02x}{g:02x}{b:02x}"

    def update_status_pills(self) -> None:
        """Reflect whether each provider key is currently configured, in the card's border subtitle."""
        for field_id, _name, _placeholder, env, _color in self.PROVIDERS:
            card = self.query_one(f"#{field_id}-card")
            val = os.environ.get(env, "")
            if val:
                suffix = val[-4:] if len(val) >= 4 else val
                card.border_subtitle = f"[#22c55e]●[/] configured ···{suffix}"
            else:
                card.border_subtitle = "[dim]○ not set[/]"

    def action_return_to_arcade(self) -> None:
        self.app.pop_screen()

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

            self.update_status_pills()
            self.app.notify("[bold #22d3ee]Configuration saved.[/]", title="API Center", severity="information")
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
        try:
            log = dashboard.query_one("#mission-log", RichLog)

            log.clear()
            log.write(f"[#22d3ee]●[/] [bold]Resuming session[/] [dim]{sid}[/]")
            log.write(f"  [dim]target[/]    {state.target}")
            log.write(f"  [dim]commands[/]  {len(state.command_results)}")
            log.write("")

            self.app.notify(f"[bold #d4d4d8]RESUMING SESSION[/]\n\nSession: {sid}\nTarget: [bold white]{state.target}[/]", title="Resumed")
            dashboard.query_one("#target-input", Input).value = state.target
            dashboard.query_one("#instructions-input", TextArea).text = state.goal or ""
            dashboard.query_one("#mission-loader").remove_class("hidden")
            dashboard.run_agent_resume(sid)
        except Exception as e:
            self.app.notify(f"[bold #ef4444]Failed to resume session:[/] {e}", title="Error", severity="error")

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
                yield Static("[dim]DOCKER[/]", id="docker-sidebar-header")
                yield OptionList(
                    "Toggle Docker Mode",
                    "Back to Dashboard",
                    id="docker-menu-options"
                )
            with Vertical(id="docker-content"):
                yield Static("Checking status...", id="docker-status")
                with Vertical(id="docker-log-panel", classes="dash-panel"):
                    yield RichLog(id="docker-log", wrap=True, markup=True)

    def on_mount(self) -> None:
        self.query_one("#docker-log-panel").border_title = "docker.log"
        self.refresh_status()
        self.log_status()

    def log_status(self) -> None:
        log = self.query_one("#docker-log", RichLog)
        is_enabled = self.app.agent.docker_mode_enabled
        if is_enabled:
            log.write("[bold]● Docker backend[/]")
            log.write("[dim]checking daemon connection...[/]")
            executor = self.app.agent.executor
            if executor.is_available():
                log.write("[#22c55e]●[/] [bold]connected[/] [dim]daemon is reachable[/]")
                log.write("")

                try:
                    # Fetch detailed Docker info
                    client = executor.client
                    info = client.info()
                    version = client.version()

                    log.write(f"  [dim]server[/]    {version.get('Version', 'Unknown')}")
                    log.write(f"  [dim]os/arch[/]   {info.get('OperatingSystem', 'Unknown')} ({info.get('Architecture', 'Unknown')})")
                    log.write(f"  [dim]cpu/mem[/]   {info.get('NCPU', 'Unknown')} cores  ·  {round(info.get('MemTotal', 0) / (1024**3), 2)} GB")
                    log.write("")

                    log.write("[bold]● Sandbox image[/]")
                    try:
                        image = client.images.get(executor.image_name)
                        size_mb = round(image.attrs['Size'] / (1024 * 1024), 1)
                        created = image.attrs.get('Created', 'Unknown')[:10]
                        log.write(f"  [dim]tag[/]       {executor.image_name}:latest")
                        log.write(f"  [dim]size[/]      {size_mb} MB  ·  [dim]created[/] {created}")
                        log.write("  [#22c55e]●[/] [bold]ready[/] [dim]image is available[/]")
                    except Exception:
                        log.write(f"  [dim]tag[/]       {executor.image_name}")
                        log.write("  [#eab308]●[/] [bold]not found[/] [dim]missing — run a mission to auto-build it[/]")
                    log.write("")

                    log.write("[bold]● Active containers[/]")
                    containers = client.containers.list(filters={"ancestor": executor.image_name})
                    if containers:
                        log.write(f"  [dim]running[/]   {len(containers)}")
                        for c in containers:
                            log.write(f"    [dim]-[/] {c.short_id} ({c.status})")
                    else:
                        log.write("  [dim]running[/]   0")

                    log.write("")
                    log.write("[#22c55e]●[/] [bold]subsystems online[/] [dim]and isolated[/]")

                except Exception as e:
                    log.write(f"[#ef4444]●[/] [bold]error[/] failed to fetch advanced info: {str(e)}")
            else:
                log.write("[#ef4444]●[/] [bold]disconnected[/]")
                log.write("[dim]could not connect to the docker daemon[/]")
                log.write("[dim]check if docker is running and your user has permissions[/]")
        else:
            log.write("[bold]● Docker backend[/]")
            log.write("[dim]○ offline[/]")
            log.write("")
            log.write("[dim]docker isolation is disabled — commands run directly on the local host[/]")

    def refresh_status(self) -> None:
        is_enabled = self.app.agent.docker_mode_enabled
        status_text = "[bold]ENABLED[/] (ready to sandbox)" if is_enabled else "[dim]DISABLED[/] (running on local host)"
        self.query_one("#docker-status", Static).update(f"Docker isolation is currently {status_text}.")
        try:
            panel = self.query_one("#docker-log-panel")
            panel.border_subtitle = "[#22c55e]●[/] enabled" if is_enabled else "[dim]○ disabled[/]"
        except Exception:
            pass

        try:
            for screen in self.app.screen_stack:
                if hasattr(screen, "update_docker_header"):
                    screen.update_docker_header()
        except Exception:
            pass

    def action_toggle_docker(self) -> None:
        self.app.agent.docker_mode_enabled = not self.app.agent.docker_mode_enabled
        self.refresh_status()
        self.query_one("#docker-log", RichLog).write("")
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
    MENU_ITEMS = [
        ("▶", "Start Mission", "start"),
        ("■", "Stop Mission", "stop"),
        ("◆", "Agent Status", "status"),
        ("▤", "Sessions", "sessions"),
        ("⬡", "Docker Mode", "docker"),
    ]
    ACTION_MAP = {f"{icon}  {label}": action for icon, label, action in MENU_ITEMS}

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
            with Horizontal(id="dash-brand"):
                yield Static("[bold #d4d4d8]⬡[/] ", id="dash-brand-icon")
                yield ShineText("HEKERBOT", base_color="#a1a1aa", shine_color="#ffffff", speed=0.5, id="dash-brand-text")
            yield Static("", id="dash-status-line")

        with Horizontal(id="dash-body"):
            # Sidebar
            with Vertical(id="sidebar"):
                yield ShineText("OPERATIONS", base_color="#52525b", shine_color="#d4d4d8", speed=0.3, id="sidebar-header")
                yield OptionList(
                    *(f"{icon}  {label}" for icon, label, _action in self.MENU_ITEMS),
                    id="menu-options"
                )
                yield Static("", id="sidebar-spacer")
                yield Static("[dim]ESC[/dim] back  [dim]?[/dim] help", id="sidebar-hints")

            # Main content
            with Vertical(id="content-container"):
                with Horizontal(id="stat-tiles"):
                    with Vertical(id="tile-agent", classes="stat-tile"):
                        yield Static("", id="stat-agent-value", classes="stat-tile-value")
                    with Vertical(id="tile-docker", classes="stat-tile"):
                        yield Static("", id="stat-docker-value", classes="stat-tile-value")
                    with Vertical(id="tile-sessions", classes="stat-tile"):
                        yield Static("", id="stat-sessions-value", classes="stat-tile-value")

                with Vertical(id="setup-panel", classes="dash-panel"):
                    with Horizontal(classes="panel-body"):
                        with Vertical(id="target-column"):
                            yield Static("[dim]TARGET[/]", id="target-label")
                            yield Input(placeholder="Enter IP or domain...", id="target-input")
                        with Vertical(id="instructions-column"):
                            yield Static("[dim]INSTRUCTIONS (Initial & Live)[/]", id="instructions-label")
                            yield TextArea(id="instructions-input")
                yield Spinner(id="mission-loader", classes="hidden")
                with Vertical(id="terminal-panel", classes="dash-panel"):
                    yield RichLog(id="mission-log", wrap=True, markup=True)
                    yield Static(" ", id="log-cursor")

    _pulse_phase = 0.0
    _idle_phase = 0.0
    _last_running = False

    def on_mount(self) -> None:
        # Titles embedded directly in the border line, in the spirit of a
        # clean native terminal UI — no separate chrome bars needed.
        self.query_one("#tile-agent").border_title = "agent"
        self.query_one("#tile-docker").border_title = "docker"
        self.query_one("#tile-sessions").border_title = "sessions"
        self.query_one("#setup-panel").border_title = "mission_config"
        self.query_one("#terminal-panel").border_title = "mission.log"

        self.update_status_line()
        self.update_docker_header()
        self.update_log_header()
        self.update_setup_badge()
        self._update_panel_glow(self.app.agent.running)
        self.set_interval(0.5, self.update_docker_header)
        self.set_interval(1.0, self.update_status_line)
        self.set_interval(0.08, self._tick_pulse)

        # Staggered cascade-in entrance for the content panels, in the spirit
        # of a modern CLI splash-in (rather than everything popping in at once).
        for i, widget_id in enumerate(("#stat-tiles", "#setup-panel", "#terminal-panel")):
            widget = self.query_one(widget_id)
            widget.styles.opacity = 0.0
            delay = 0.05 + i * 0.08
            self.set_timer(
                delay,
                lambda w=widget: w.styles.animate("opacity", value=1.0, duration=0.25, easing="out_cubic"),
            )

    def _tick_pulse(self) -> None:
        self._pulse_phase += 0.18
        self._idle_phase += 0.035
        running = self.app.agent.running
        if running or running != self._last_running:
            self.update_status_line()
            self.update_log_header()
        self._update_panel_glow(running)
        self._tick_log_cursor()
        self._last_running = running

    def _update_panel_glow(self, running: bool) -> None:
        """Every box breathes gently at all times; the terminal panel + agent tile
        switch to a brighter, faster breath while a mission is actually live."""
        try:
            # Slow, subtle ambient breathing — alive even when idle.
            idle_glow = Color.parse(self._pulse_color("#27272a", "#3f3f46", phase=self._idle_phase))
            self.query_one("#setup-panel").styles.border = ("round", idle_glow)
            self.query_one("#tile-docker").styles.border = (
                "round", Color.parse(self._pulse_color("#27272a", "#3f3f46", phase=self._idle_phase + 1.2))
            )
            self.query_one("#tile-sessions").styles.border = (
                "round", Color.parse(self._pulse_color("#27272a", "#3f3f46", phase=self._idle_phase + 2.4))
            )

            if running:
                glow = Color.parse(self._pulse_color("#0e7490", "#22d3ee"))
            else:
                glow = idle_glow
            self.query_one("#terminal-panel").styles.border = ("round", glow)
            self.query_one("#tile-agent").styles.border = ("round", glow)
        except Exception:
            pass

    def _tick_log_cursor(self) -> None:
        """A soft blinking cursor at the foot of the terminal panel, alive even at idle."""
        try:
            cursor = self.query_one("#log-cursor", Static)
            blink_on = math.sin(self._idle_phase * 2.6) > 0
            cursor.update("[#22d3ee]▌[/]" if blink_on else " ")
        except Exception:
            pass

    def _pulse_color(self, base_hex: str, bright_hex: str, phase: float | None = None) -> str:
        """Interpolate between a base and bright color for a breathing effect."""
        p = self._pulse_phase if phase is None else phase
        intensity = (math.sin(p) + 1) / 2
        br, bg_, bb = int(base_hex[1:3], 16), int(base_hex[3:5], 16), int(base_hex[5:7], 16)
        tr, tg, tb = int(bright_hex[1:3], 16), int(bright_hex[3:5], 16), int(bright_hex[5:7], 16)
        r = int(br + (tr - br) * intensity)
        g = int(bg_ + (tg - bg_) * intensity)
        b = int(bb + (tb - bb) * intensity)
        return f"#{r:02x}{g:02x}{b:02x}"

    def update_status_line(self) -> None:
        try:
            agent = self.app.agent
            if agent.running:
                dot_color = self._pulse_color("#0e7490", "#67e8f9")
                state_text = f"[{dot_color}]●[/] [bold]RUNNING[/]"
            else:
                state_text = "[dim]○ IDLE[/]"
            docker_text = (
                "[#22d3ee]●[/] DOCKER"
                if agent.docker_mode_enabled
                else "[dim]○ LOCAL[/]"
            )
            version = get_app_version()
            self.query_one("#dash-status-line", Static).update(
                f"{state_text}   {docker_text}   [dim]{version}[/]"
            )
            self.query_one("#stat-agent-value", Static).update(state_text)
            self.query_one("#stat-docker-value", Static).update(docker_text)
            try:
                count = len(agent.persistence.list_sessions())
            except Exception:
                count = 0
            self.query_one("#stat-sessions-value", Static).update(f"[dim]{count} saved[/]")
        except Exception:
            pass

    def update_setup_badge(self) -> None:
        try:
            has_target = bool(self.query_one("#target-input", Input).value.strip())
            badge = "[#22c55e]●[/] armed" if has_target else "[dim]○ idle[/]"
            self.query_one("#setup-panel").border_subtitle = badge
        except Exception:
            pass

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "target-input":
            self.update_setup_badge()

    def _refresh_terminal_subtitle(self) -> None:
        try:
            agent = self.app.agent
            docker_text = "[#22d3ee]●[/] docker" if agent.docker_mode_enabled else "[dim]○ local[/]"
            if agent.running:
                dot_color = self._pulse_color("#0e7490", "#67e8f9")
                live_text = f"[{dot_color}]●[/] live"
            else:
                live_text = "[dim]○ idle[/]"
            self.query_one("#terminal-panel").border_subtitle = f"{docker_text}   {live_text}"
        except Exception:
            pass

    def update_docker_header(self) -> None:
        self._refresh_terminal_subtitle()

    def update_log_header(self) -> None:
        self._refresh_terminal_subtitle()

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        if event.option_list.id == "menu-options":
            action = self.ACTION_MAP.get(str(event.option.prompt), "status")
            self.execute_action(action)

    def on_key(self, event: events.Key) -> None:
        if event.key == "enter" and self.query_one("#instructions-input").has_focus:
            if self.app.agent.running:
                self.execute_action("chat")
                event.prevent_default()
                event.stop()
                return

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
        elif event.key == "down" and self.query_one("#instructions-input").has_focus:
            self.query_one("#mission-log").focus()
            event.prevent_default()
        elif event.key == "up" and self.query_one("#mission-log").has_focus:
            self.query_one("#instructions-input").focus()
            event.prevent_default()
        elif event.key == "left" and self.query_one("#mission-log").has_focus:
            self.query_one("#menu-options").focus()
            event.prevent_default()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "target-input":
            self.execute_action("start")

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
            log = self.query_one("#mission-log", RichLog)
        except Exception:
            return
            
        agent = self.app.agent
        
        if action == "start":
            target_raw = self.query_one("#target-input", Input).value.strip()
            try:
                goal_input = self.query_one("#instructions-input", TextArea).text.strip()
            except Exception:
                goal_input = ""
            target, goal = self._parse_target_and_goal(target_raw, goal_input)
            if not target:
                self.notify("[bold #ef4444]ERROR: NO TARGET ACQUIRED[/]\n\nPlease enter a target IP or domain in the input field above.", title="Error", severity="error")
                return
            
            if agent.running:
                self.notify(f"[bold #ef4444]ERROR: AGENT ALREADY RUNNING[/]\n\nTarget: {agent.current_state.target if agent.current_state else 'unknown'}", title="Error", severity="error")
                return
                
            goal_line = f"\nGoal: [bold white]{goal}[/]" if goal else ""
            format_hint = "" if goal else "\n[dim]Tip: You can also use TARGET as: host || your goal[/]"
            self.notify(
                f"[bold #e4e4e7]SYSTEM OVERRIDE INITIATED[/]\n\n"
                f"Target acquired: [bold white]{target}[/]{goal_line}\n"
                "Background payload delivery in progress...\nAgent is now RUNNING."
                f"{format_hint}"
            , title="Status", severity="information")
            
            log.clear()
            log.write("[#22d3ee]●[/] [bold]Mission initialized[/]")
            log.write(f"  [dim]target[/]  {target}")
            if goal:
                log.write(f"  [dim]goal[/]    {goal}")
            log.write("")
            
            self.query_one("#mission-loader").remove_class("hidden")
            self.run_agent_mission(target, goal=goal)
            
        elif action == "stop":
            agent.stop()
            self.notify("[bold #ef4444]MISSION ABORTED[/]\n\nTerminate signal dispatched.", title="Status", severity="information")
            log.write("\n[!] ABORT SIGNAL SENT: Terminating all active threads...\n")
        elif action == "chat":
            try:
                message_input = self.query_one("#instructions-input", TextArea)
            except Exception:
                self.notify("[bold #ef4444]Instructions box not visible in this UI build.[/]", title="Warning", severity="warning")
                return
            msg = message_input.text.strip()
            if not msg:
                self.notify("[bold #ef4444]Empty operator message.[/]", title="Warning", severity="warning")
                return
            accepted = agent.add_operator_input(msg)
            if accepted:
                log.write(f"[OPERATOR] {msg}")
                if agent.running:
                    self.notify("[bold #22c55e]Operator input queued for next decision step.[/]", title="Status", severity="information")
                else:
                    self.notify("[bold #eab308]Saved operator note. Start/resume mission to apply it.[/]", title="Status", severity="information")
                message_input.text = ""
            else:
                self.notify("[bold #ef4444]No active session context. Start or resume a mission first.[/]", title="Warning", severity="warning")
        elif action == "docker":
            self.app.push_screen("docker_modal")
        elif action == "status":
            st = "[bold #22c55e]RUNNING[/]" if agent.running else "[bold #a1a1aa]IDLE[/]"
            self.notify(f"[bold white]AGENT STATUS[/]\n\nState: {st}\nNetwork: SECURE", title="Status", severity="information")
        elif action == "sessions":
            self.app.push_screen("sessions_modal")

class ArcadeScreen(Screen):
    """The Arcade entry screen."""
    def compose(self) -> ComposeResult:
        with Vertical(id="main-container"):
            yield Static(get_app_version(), id="top-info")
            yield BigBanner(id="banner")
            yield ShineText(
                "AUTONOMOUS   AGENTIC   RED   TEAMING",
                base_color="#3f3f46", shine_color="#a1a1aa", speed=0.4,
                id="tagline",
            )

            with Horizontal(id="menu-row"):
                with Vertical(id="menu-card"):
                    yield OptionList(
                        "▶  Get Cracking !!",
                        "⬡  API Center",
                        id="menu"
                    )
                    yield Static("", id="arcade-pulse")

        with Horizontal(id="start-hints"):
            yield Static("Navigation: [bold white]↑/↓[/] · Select: [bold white]ENTER[/] · Back: [bold white]ESC[/]", id="hints-left")
            yield Static("Quit: [bold white]CTRL+Q[/]", id="hints-right")

    _idle_phase = 0.0

    def on_mount(self) -> None:
        container = self.query_one("#main-container")
        container.styles.opacity = 0.0
        container.styles.animate("opacity", value=1.0, duration=0.3, easing="out_cubic")

        # Gentle ambient life on the menu card, even with nothing running.
        self.set_interval(0.08, self._tick_idle)

    def _tick_idle(self) -> None:
        self._idle_phase += 0.035
        intensity = (math.sin(self._idle_phase) + 1) / 2
        base, bright = (0x27, 0x27, 0x2a), (0x3f, 0x3f, 0x46)
        r = int(base[0] + (bright[0] - base[0]) * intensity)
        g = int(base[1] + (bright[1] - base[1]) * intensity)
        b = int(base[2] + (bright[2] - base[2]) * intensity)
        try:
            self.query_one("#menu-card").styles.border = ("round", Color.parse(f"#{r:02x}{g:02x}{b:02x}"))
            dot_on = math.sin(self._idle_phase * 1.4) > 0
            dot = "[#22d3ee]●[/]" if dot_on else "[dim]●[/]"
            self.query_one("#arcade-pulse", Static).update(f"{dot} [dim]system ready[/]")
        except Exception:
            pass

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        if event.option_list.id == "menu":
            label = str(event.option.prompt)
            if "Get Cracking" in label:
                self.app.push_screen("dashboard")
            elif "API Center" in label:
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
