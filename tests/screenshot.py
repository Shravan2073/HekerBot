import asyncio
from hekerbot.ui.shell import HekerApp

async def take_screenshot():
    app = HekerApp()
    async with app.run_test() as pilot:
        # Take a screenshot of ArcadeScreen
        with open("tests/arcade.svg", "w") as f:
            f.write(app.export_screenshot(title="Arcade"))
        
        # Navigate to Dashboard
        await pilot.press("enter")
        
        # Take a screenshot of DashboardScreen
        with open("tests/dashboard.svg", "w") as f:
            f.write(app.export_screenshot(title="Dashboard"))

if __name__ == "__main__":
    asyncio.run(take_screenshot())
