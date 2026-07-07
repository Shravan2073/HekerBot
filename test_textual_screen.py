from textual.app import App, ComposeResult
from textual.screen import Screen
from textual.widgets import Label

class MyScreen(Screen):
    def on_mount(self):
        print("MOUNTED")
    def on_screen_resume(self):
        print("RESUMED")

class MyApp(App):
    SCREENS = {"my": MyScreen()}
    def on_mount(self):
        self.push_screen("my")
        self.set_timer(0.5, lambda: self.pop_screen())
        self.set_timer(1.0, lambda: self.push_screen("my"))
        self.set_timer(1.5, lambda: self.exit())

if __name__ == "__main__":
    MyApp().run()
