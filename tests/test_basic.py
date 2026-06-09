import unittest
from unittest.mock import patch, MagicMock
from hekerbot.ui.shell import HekerShell
from hekerbot.agent.brain import HekerBrain
from hekerbot.executor.docker_executor import DockerExecutor

class TestHekerBot(unittest.TestCase):
    def test_brain_init(self):
        brain = HekerBrain()
        self.assertEqual(len(brain.history), 1)
        self.assertIn("HekerBOT", brain.history[0]["content"])

    @patch('docker.from_env')
    def test_executor_init(self, mock_docker):
        mock_client = MagicMock()
        mock_docker.return_value = mock_client
        executor = DockerExecutor()
        self.assertEqual(executor.image_name, "hekerbot-sandbox")
        self.assertEqual(executor.client, mock_client)

    @patch('docker.from_env')
    def test_executor_is_available(self, mock_docker):
        mock_client = MagicMock()
        mock_docker.return_value = mock_client
        executor = DockerExecutor()
        self.assertTrue(executor.is_available())
        
        # Test failure
        mock_docker.side_effect = Exception("Docker not running")
        executor = DockerExecutor()
        self.assertFalse(executor.is_available())

    def test_session_state_update_asset(self):
        from hekerbot.persistence.state import SessionState
        state = SessionState(session_id="test", target="127.0.0.1")
        state.update_asset(ip="192.168.1.1", hostname="test-host", ports=[80], vulnerabilities=["VULN-1"])
        
        self.assertIn("192.168.1.1", state.discovery_graph)
        asset = state.discovery_graph["192.168.1.1"]
        self.assertEqual(asset.hostname, "test-host")
        self.assertEqual(asset.ports, [80])
        self.assertEqual(asset.vulnerabilities, ["VULN-1"])
        
        # Update existing asset
        state.update_asset(ip="192.168.1.1", ports=[443])
        self.assertEqual(asset.ports, [80, 443])

    @patch('hekerbot.ui.shell.PromptSession')
    @patch('hekerbot.agent.agent.HekerAgent')
    def test_shell_command_aliases(self, mock_agent, mock_session):
        shell = HekerShell()
        
        # Test help aliases
        self.assertEqual(shell.commands["h"], shell.show_help)
        self.assertEqual(shell.commands["?"], shell.show_help)
        self.assertEqual(shell.commands["help"], shell.show_help)
        
        # Test exit aliases
        self.assertEqual(shell.commands["q"], shell.exit_shell)
        self.assertEqual(shell.commands["quit"], shell.exit_shell)
        self.assertEqual(shell.commands["exit"], shell.exit_shell)
        
        # Test unknown command
        with patch('hekerbot.ui.shell.console.print') as mock_print:
            shell.handle_command("unknown_cmd_xyz")
            mock_print.assert_called()
            args, _ = mock_print.call_args
            self.assertIn("Unknown command", args[0])

if __name__ == "__main__":
    unittest.main()
