# HekerBOT TUI Design Specification

## Overview
HekerBOT is transitioning to a full-screen, highly polished Terminal User Interface (TUI) powered by the **Textual** framework (by the creators of Rich). The goal is to provide a sleek, highly usable, and aesthetically pleasing interface inspired by modern minimalist terminal apps, complete with smooth CSS-styled animations, reactive state, and intuitive keyboard navigation.

## Layout & Architecture
The UI will use a two-pane layout powered by Textual's CSS layout engine:
- **Header (`Header` widget):** Contains the app title, version, and global status indicators (e.g., agent running state).
- **Left Sidebar (Navigation):** A minimalist vertical `OptionList` or custom list where users navigate using arrow keys. Selected items will be highlighted via Textual CSS rules.
- **Main Content Area (Right):** The primary view built using reactive Textual widgets. It updates instantly based on the selected item in the sidebar, displaying help, diagnostics, session lists, and dynamic status logs.
- **Footer (`Footer` widget):** A persistent footer displaying contextual keyboard shortcuts (e.g., `↑↓ move`, `↵ select`, `esc quit`).

## Visual Aesthetic
- **Color Palette:** Muted, elegant dark mode styled via Textual CSS (`.tcss`). Off-white text for primary content, subtle greys for unfocused elements, and minimal accent colors (like gold or cyan) for highlights.
- **Separators:** Handled cleanly by Textual CSS borders (e.g., `border-right: vkey $background;`), eliminating messy box-drawing character handling.

## Animations & Interactivity
- **The "Shine" Effect:** We will implement a custom Textual widget or Rich renderable that uses `set_interval` to animate the HEKERBOT text/logo. This will sweep a brighter color across the text to create a "shining" loop asynchronously.
- **Creative Loading Indicators:** We will use `rich.spinner.Spinner` or custom Textual `LoadingIndicator` widgets with the creative spinner sequences requested:
  `·` → `✢` → `✳` → `✶` → `✻` → `✽`
- **Responsiveness:** Textual inherently provides extremely fast, reactive updates. Arrow key navigation will feel instantaneous.

## Components & Screens
- **Dashboard/Help:** Default view explaining the commands.
- **Diagnostics View:** Neatly aligned key-value pairs (`DataTable` or custom layout) showing system health, Docker status, and API key presence.
- **Status View:** Live updating reactive view of the agent's current state, target, and recent thoughts/commands.
- **Action Prompts:** Textual `Input` widgets or modals for commands requiring input (like `start [target]`).

## Technical Implementation Notes
- **Framework:** Transition entirely from `prompt_toolkit` to `textual`.
- **Dependencies:** Add `textual` to `pyproject.toml`.
- **CSS:** Use an external `.tcss` file for styling to keep Python code clean.
- **Asynchronous Execution:** Textual uses `asyncio`. The background HekerAgent thread must communicate with the Textual app using `app.call_from_thread` or Textual's `Worker` API to safely update the UI when the agent state changes.
