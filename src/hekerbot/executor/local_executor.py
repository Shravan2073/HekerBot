import shutil
import subprocess
from typing import Dict, Any


class LocalExecutor:
    """Runs commands on the host machine (no Docker isolation)."""

    def is_available(self) -> bool:
        return shutil.which("bash") is not None

    def execute_command(self, command: str, timeout: int = 300) -> Dict[str, Any]:
        if not self.is_available():
            return {
                "stdout": "",
                "stderr": "bash is not available on this host",
                "exit_code": -1,
            }

        try:
            result = subprocess.run(
                ["/bin/bash", "-lc", command],
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.returncode,
                "backend": "local",
                "container_id": "",
            }
        except subprocess.TimeoutExpired:
            return {
                "stdout": "",
                "stderr": f"Command timed out after {timeout}s",
                "exit_code": -1,
                "backend": "local",
                "container_id": "",
            }
        except Exception as e:
            return {
                "stdout": "",
                "stderr": str(e),
                "exit_code": -1,
                "backend": "local",
                "container_id": "",
            }
