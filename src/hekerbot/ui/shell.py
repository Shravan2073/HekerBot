from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, OptionList
from textual.reactive import reactive

class HekerApp(App):
    CSS_PATH = "shell.tcss"
    BINDINGS = [("escape", "quit", "Quit")]
    
    current_view = reactive("status")

    def compose(self) -> ComposeResult:
        yield Header()
        yield OptionList(
            "Start Mission",
            "Stop Mission",
            "Agent Status",
            "Sessions",
            "Build Sandbox",
            "Docker Mode",
            "Diagnostics",
            id="sidebar"
        )
        yield Static("Content", id="content-area")
        yield Footer()

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        view_map = {
            "Start Mission": "start",
            "Stop Mission": "stop",
            "Agent Status": "status",
            "Sessions": "sessions",
            "Build Sandbox": "build",
            "Docker Mode": "docker",
            "Diagnostics": "diag"
        }
        self.current_view = view_map.get(str(event.option.prompt), "status")
        
    def watch_current_view(self, new_view: str) -> None:
        content = self.query_one("#content-area", Static)
        content.update(f"Current View: {new_view}")

if __name__ == "__main__":
    app = HekerApp()
    app.run()
