import pytest
from hekerbot.ui.shell import HekerApp

@pytest.mark.asyncio
async def test_app_starts():
    app = HekerApp()
    async with app.run_test() as pilot:
        assert app.is_running

@pytest.mark.asyncio
async def test_sidebar_navigation():
    app = HekerApp()
    async with app.run_test() as pilot:
        option_list = app.screen.query_one("OptionList")
        assert option_list is not None
        await pilot.press("enter")
        assert type(app.screen).__name__ == "DashboardScreen"
