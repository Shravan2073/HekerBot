from textual.app import App
from textual.widgets import RichLog
class MyApp(App):
    def compose(self):
        yield RichLog()
    def on_mount(self):
        log = self.query_one(RichLog)
        for i in range(50):
            if i % 2 == 0:
                log.write(f"\033[32m[>] Running script {i}...\033[0m")
            else:
                log.write(f"Line {i}")
MyApp().run()
