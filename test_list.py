from textual.app import App, ComposeResult
from textual.widgets import OptionList

class TestApp(App):
    CSS = """
    Screen { background: black; color: #00ff00; }
    OptionList {
        color: #00aa00;
        background: transparent;
    }
    """
    def compose(self) -> ComposeResult:
        yield OptionList("Option 1", "Option 2")

if __name__ == "__main__":
    app = TestApp()
    # app.run()
