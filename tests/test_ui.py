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
        option_list = app.query_one("OptionList")
        assert option_list is not None
        assert app.current_view == "start" # Default
        await pilot.press("down")
        await pilot.press("enter")
        assert app.current_view == "stop"
