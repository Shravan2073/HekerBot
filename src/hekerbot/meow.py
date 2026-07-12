import subprocess
import sys
import os
import time
import itertools

CYAN = "\033[38;2;34;211;238m"
DIM = "\033[90m"
GREEN = "\033[38;2;34;197;94m"
RESET = "\033[0m"
BRAILLE_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]


def run_cmd(cmd, cwd=None):
    result = subprocess.run(cmd, capture_output=True, text=True, shell=True, cwd=cwd)
    return result.stdout.strip(), result.stderr.strip(), result.returncode


def _run_animated(cmd, cwd, message):
    """Run a shell command while animating a braille spinner in the raw
    terminal — the same frame set as the TUI's own Spinner widget, so the
    pre-launch experience matches the app's visual language."""
    proc = subprocess.Popen(cmd, shell=True, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    is_tty = sys.stdout.isatty()
    frames = itertools.cycle(BRAILLE_FRAMES)
    while proc.poll() is None:
        if is_tty:
            sys.stdout.write(f"\r{CYAN}{next(frames)}{RESET} {DIM}{message}{RESET}")
            sys.stdout.flush()
        time.sleep(0.08)
    if is_tty:
        sys.stdout.write("\r\033[2K")
        sys.stdout.flush()
    stdout, stderr = proc.communicate()
    return stdout.strip(), stderr.strip(), proc.returncode


def shine_line(text: str, cycles: int = 1, indent: str = "  ") -> None:
    """A brief light-sweep across `text` in the raw terminal — the same idea
    as the TUI's ShineText/BigBanner effects, for the pre-launch splash."""
    if not sys.stdout.isatty():
        print(f"{indent}{text}")
        return
    length = len(text)
    for _ in range(cycles):
        for pos in range(-6, length + 6):
            out = []
            for i, char in enumerate(text):
                distance = abs(i - pos)
                if distance < 5:
                    intensity = (1 - distance / 5) ** 1.5
                    shade = int(150 + 105 * intensity)
                    out.append(f"\033[1;38;2;{shade};{shade};{min(shade + 8, 255)}m{char}")
                else:
                    out.append(f"{DIM}{char}")
            sys.stdout.write(f"\r{indent}" + "".join(out) + RESET)
            sys.stdout.flush()
            time.sleep(0.012)
    sys.stdout.write("\n")


def auto_update():
    """
    Checks for updates and applies them.
    Returns (old_hash, new_hash) if an update was applied, None if already
    up to date (or the pull/install step failed), False if this isn't a
    git checkout at all.
    """
    # Assuming meow.py is in src/hekerbot/meow.py, the repo root is 3 levels up
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

    # Verify it's a git repo
    if not os.path.exists(os.path.join(repo_root, ".git")):
        return False

    _, _, rc = _run_animated("git fetch", repo_root, "checking for updates...")
    if rc != 0:
        return False

    local_hash, _, rc_local = run_cmd("git rev-parse HEAD", cwd=repo_root)
    remote_hash, _, rc_remote = run_cmd("git rev-parse @{u}", cwd=repo_root)
    behind_str, _, rc_behind = run_cmd("git rev-list HEAD..@{u} --count", cwd=repo_root)

    if rc_local != 0 or rc_remote != 0 or rc_behind != 0:
        return False

    if behind_str == "0":
        print(f"{GREEN}✔{RESET} {DIM}HekerBOT is up to date.{RESET}")
        return None

    shine_line(f"✦ updating hekerbot  {local_hash[:7]} → {remote_hash[:7]}")

    status_out, _, _ = run_cmd("git status --porcelain", cwd=repo_root)
    has_changes = len(status_out) > 0

    if has_changes:
        run_cmd("git stash", cwd=repo_root)

    _, stderr, rc = _run_animated("git pull", repo_root, "pulling latest changes...")

    if has_changes:
        run_cmd("git stash pop", cwd=repo_root)

    if rc != 0:
        print(f"{DIM}[-] Failed to pull updates: {stderr}{RESET}")
        return None

    if subprocess.run("which uv", shell=True, capture_output=True).returncode == 0:
        install_cmd = "uv pip install -e ."
    else:
        install_cmd = "pip install -e ."

    _, stderr, rc = _run_animated(install_cmd, repo_root, "reinstalling dependencies...")
    if rc != 0:
        print(f"{DIM}[-] Failed to install dependencies!{RESET}")
        return None

    print(f"{GREEN}✔{RESET} HekerBOT updated to {remote_hash[:7]}")
    return (local_hash[:7], remote_hash[:7])
