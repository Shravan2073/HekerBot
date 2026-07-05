import os
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static
from hekerbot.agent.agent import HekerAgent

class HekerApp(App):
    CSS_PATH = "shell.tcss"
    BINDINGS = [("escape", "quit", "Quit")]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("Sidebar", id="sidebar")
        yield Static("Content", id="content-area")
        yield Footer()

if __name__ == "__main__":
    app = HekerApp()
    app.run()
