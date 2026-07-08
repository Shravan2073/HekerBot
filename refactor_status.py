import re

with open('src/hekerbot/ui/shell.py', 'r') as f:
    content = f.read()

# Remove status-display from compose
content = re.sub(r'[ \t]*yield Static\("", id="status-display"\)\n', '', content)

# Update SessionsModal
content = re.sub(r'status = self\.app\.query_one\("#status-display", Static\)', 'pass  # No status display anymore', content)
content = re.sub(r'status\.update\(\s*(f?"\[bold #[a-f0-9]+\]RESUMING SESSION\[/\]\\n\\nSession: \{sid\}\\nTarget: \[bold white\]\{state\.target\}\[/\]")\s*\)', r'self.app.notify(\1, title="Resumed")', content)

# Update execute_action
content = re.sub(r'status = self\.query_one\("#status-display", Static\)', 'pass # No status display anymore', content)

# Replace all status.update(...) with self.notify(...)
def replace_status(match):
    msg = match.group(1)
    # Strip basic color tags for notify
    clean_msg = re.sub(r'\[bold #[^\]]+\]|\[bold white\]|\[/\]', '', msg)
    if 'ERROR' in msg:
        return f'self.notify({msg}, title="Error", severity="error")'
    elif 'WARNING' in msg or 'Empty' in msg or 'No active' in msg or 'not visible' in msg:
        return f'self.notify({msg}, title="Warning", severity="warning")'
    else:
        return f'self.notify({msg}, title="Status", severity="information")'

content = re.sub(r'status\.update\((.*?)\)', replace_status, content, flags=re.DOTALL)

with open('src/hekerbot/ui/shell.py', 'w') as f:
    f.write(content)
