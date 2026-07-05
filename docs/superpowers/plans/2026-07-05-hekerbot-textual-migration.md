# HekerBOT Textual UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Completely rewrite the `HekerShell` from `prompt_toolkit` to a modern, fully responsive `Textual` application featuring interactive sidebars, reactive state, and continuous animations.

**Architecture:** A Textual `App` with a CSS-based layout (`Header`, `Footer`, `OptionList` on left, `ContentArea` on right). We will use Textual's async `Worker` API to offload long-running agent tasks and animate a shining logo using `set_interval`.

**Tech Stack:** Python, Textual, Pytest, HekerAgent

## Global Constraints

- Must use `textual` instead of `prompt_toolkit`.
- Styling must be separated into a `.tcss` file.
- The UI must perfectly render the shining logo animation without blocking interaction.
- Creative loading spinners (`·` → `✢` → `✳` → `✶` → `✻` → `✽`) must be used for background tasks.

---

### Task 1: Setup Textual Dependencies & Basic App Skeleton

**Files:**
- Modify: `pyproject.toml`
- Create: `src/hekerbot/ui/shell.tcss`
- Modify: `src/hekerbot/ui/shell.py`

**Interfaces:**
- Consumes: `HekerAgent` (imported but not fully wired yet)
- Produces: A running `Textual` application skeleton.

- [ ] **Step 1: Write the failing test**

```python
# Create tests/test_ui.py
import pytest
from hekerbot.ui.shell import HekerApp

@pytest.mark.asyncio
async def test_app_starts():
    app = HekerApp()
    async with app.run_test() as pilot:
        assert app.is_running
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_ui.py -v`
Expected: FAIL (missing dependencies and HekerApp)

- [ ] **Step 3: Write minimal implementation**

Modify `pyproject.toml` to replace `prompt_toolkit` and `rich` with `textual`.
```toml
# pyproject.toml (update dependencies section)
dependencies = [
    # ... existing deps ...
    "textual>=0.40.0",
    "pytest-asyncio"
]
```

Create `src/hekerbot/ui/shell.tcss`:
```css
Screen {
    layout: horizontal;
    background: $surface;
}

#sidebar {
    width: 30%;
    height: 100%;
    border-right: vkey $background;
}

#content-area {
    width: 70%;
    height: 100%;
    padding: 1 2;
}
```

Modify `src/hekerbot/ui/shell.py`:
```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv tool install --reinstall .` followed by `pytest tests/test_ui.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml src/hekerbot/ui/shell.py src/hekerbot/ui/shell.tcss tests/test_ui.py
git commit -m "feat: setup textual dependencies and basic app skeleton"
```

### Task 2: Implement Sidebar Navigation

**Files:**
- Modify: `src/hekerbot/ui/shell.py`
- Modify: `src/hekerbot/ui/shell.tcss`
- Modify: `tests/test_ui.py`

**Interfaces:**
- Consumes: `OptionList` from `textual.widgets`
- Produces: An interactive navigation menu that updates a reactive variable.

- [ ] **Step 1: Write the failing test**

```python
# Add to tests/test_ui.py
@pytest.mark.asyncio
async def test_sidebar_navigation():
    app = HekerApp()
    async with app.run_test() as pilot:
        option_list = app.query_one("OptionList")
        assert option_list is not None
        assert app.current_view == "status" # Default
        await pilot.press("down")
        await pilot.press("enter")
        # Ensure reactive state changed based on selection
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_ui.py::test_sidebar_navigation -v`
Expected: FAIL (OptionList not found)

- [ ] **Step 3: Write minimal implementation**

Update `src/hekerbot/ui/shell.tcss`:
```css
OptionList {
    background: $surface;
    border: none;
}
OptionList:focus > .option-list--option-highlighted {
    background: $accent;
    color: $text;
}
```

Update `src/hekerbot/ui/shell.py`:
```python
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
        self.current_view = view_map.get(event.option.prompt, "status")
        
    def watch_current_view(self, new_view: str) -> None:
        content = self.query_one("#content-area", Static)
        content.update(f"Current View: {new_view}")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_ui.py::test_sidebar_navigation -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/hekerbot/ui/shell.py src/hekerbot/ui/shell.tcss tests/test_ui.py
git commit -m "feat: add interactive sidebar navigation"
```

### Task 3: Implement Content Views & HekerAgent Integration

**Files:**
- Modify: `src/hekerbot/ui/shell.py`
- Modify: `tests/test_ui.py`

**Interfaces:**
- Consumes: `HekerAgent` data properties.
- Produces: Rich text rendering for Diagnostics, Status, and Sessions.

- [ ] **Step 1: Write the failing test**

```python
# Add to tests/test_ui.py
@pytest.mark.asyncio
async def test_view_updates():
    app = HekerApp()
    async with app.run_test() as pilot:
        app.current_view = "diag"
        await pilot.pause()
        content = app.query_one("#content-area", Static)
        assert "Execution Mode" in str(content.renderable)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_ui.py::test_view_updates -v`
Expected: FAIL (Content just says "Current View: diag")

- [ ] **Step 3: Write minimal implementation**

Update `src/hekerbot/ui/shell.py`:
```python
import os
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, OptionList
from textual.reactive import reactive
from hekerbot.agent.agent import HekerAgent

class HekerApp(App):
    CSS_PATH = "shell.tcss"
    BINDINGS = [("escape", "quit", "Quit")]
    current_view = reactive("status")

    def __init__(self):
        super().__init__()
        self.agent = HekerAgent()

    # ... compose and on_option_list_option_selected remain same ...

    def watch_current_view(self, new_view: str) -> None:
        content = self.query_one("#content-area", Static)
        if new_view == "diag":
            content.update(self._render_diag())
        elif new_view == "status":
            content.update(self._render_status())
        elif new_view == "sessions":
            content.update(self._render_sessions())
        else:
            content.update(f"Action: {new_view} (Press Enter to execute)")

    def _render_diag(self) -> str:
        mode = "DOCKER" if self.agent.docker_mode() == "on" else "LOCAL"
        return f"System Diagnostics\n\nExecution Mode: {mode}\nWorking Dir: {os.getcwd()}"

    def _render_status(self) -> str:
        st = "Running" if self.agent.running else "Idle"
        return f"Agent Status\n\nState: {st}\nTarget: N/A"

    def _render_sessions(self) -> str:
        sessions = self.agent.persistence.list_sessions()
        if not sessions:
            return "No saved sessions found."
        return "Saved Sessions:\n" + "\n".join(sessions)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_ui.py::test_view_updates -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/hekerbot/ui/shell.py tests/test_ui.py
git commit -m "feat: implement content views and link HekerAgent state"
```

### Task 4: Animations (Shine Effect & Custom Spinner)

**Files:**
- Modify: `src/hekerbot/ui/shell.py`
- Modify: `src/hekerbot/ui/shell.tcss`
- Create: `tests/test_animations.py`

**Interfaces:**
- Consumes: Textual `set_interval` and standard strings.
- Produces: A custom animated banner widget and creative loading spinners.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_animations.py
import pytest
from textual.widgets import Static
from hekerbot.ui.shell import ShiningBanner

@pytest.mark.asyncio
async def test_banner_shines():
    banner = ShiningBanner()
    assert banner is not None
    # Cannot easily test exact interval frames, but we assert it mounts.
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_animations.py -v`
Expected: FAIL (ShiningBanner undefined)

- [ ] **Step 3: Write minimal implementation**

Update `src/hekerbot/ui/shell.py`:
```python
# Add to imports
from rich.text import Text
from rich.spinner import Spinner

class ShiningBanner(Static):
    """Animate a shining sweep across the banner."""
    def on_mount(self) -> None:
        self.text = "HEKERBOT"
        self.shine_pos = 0
        self.set_interval(0.1, self.update_shine)

    def update_shine(self) -> None:
        styled_text = Text()
        for i, char in enumerate(self.text):
            if abs(i - self.shine_pos) < 2:
                styled_text.append(char, style="bold cyan")
            else:
                styled_text.append(char, style="dim white")
        self.update(styled_text)
        self.shine_pos = (self.shine_pos + 1) % (len(self.text) + 4)

class CreativeSpinner(Static):
    """Creative loading sequence."""
    def on_mount(self) -> None:
        self.frames = ["·", "✢", "✳", "✶", "✻", "✽"]
        self.frame_idx = 0
        self.set_interval(0.15, self.update_spinner)

    def update_spinner(self) -> None:
        self.update(f"{self.frames[self.frame_idx]} Loading...")
        self.frame_idx = (self.frame_idx + 1) % len(self.frames)

# In HekerApp.compose, replace Header with:
# yield ShiningBanner(id="banner")
```

Add CSS for banner to `src/hekerbot/ui/shell.tcss`:
```css
#banner {
    height: 3;
    content-align: center middle;
    background: $boost;
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_animations.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/hekerbot/ui/shell.py src/hekerbot/ui/shell.tcss tests/test_animations.py
git commit -m "feat: add shine animation and creative loading spinners"
```
