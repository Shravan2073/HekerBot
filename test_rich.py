from rich.console import Console
console = Console(color_system=None)
with open('out.txt', 'w') as f:
    console.file = f
    console.print("\033[32mhello\033[0m")
