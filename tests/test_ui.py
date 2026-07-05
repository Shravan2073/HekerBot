import pytest
from hekerbot.ui.shell import HekerApp

@pytest.mark.asyncio
async def test_app_starts():
    app = HekerApp()
    async with app.run_test() as pilot:
        assert app.is_running
