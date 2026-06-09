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

if __name__ == "__main__":
    unittest.main()
