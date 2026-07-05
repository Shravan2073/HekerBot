import docker
import os
from typing import Dict, Any

class DockerExecutor:
    def __init__(self, image_name: str = "hekerbot-sandbox"):
        self._client = None
        self.image_name = image_name
        self._available = None

    @property
    def client(self):
        if self._client is None:
            try:
                self._client = docker.from_env()
                # Test the connection
                self._client.ping()
                self._available = True
            except Exception as e:
                self._available = False
                error_msg = str(e)
                if "Permission denied" in error_msg:
                    hint = "\nHint: You may need to add your user to the 'docker' group: sudo usermod -aG docker $USER"
                else:
                    hint = "\nHint: Ensure the Docker daemon is running."
                
                raise RuntimeError(
                    f"Could not connect to Docker: {error_msg}{hint}"
                ) from e
        return self._client

    def is_available(self) -> bool:
        """Check if Docker is available without raising an exception."""
        if self._available is False:
            return False
        if self._client is not None:
            return True
        
        try:
            client = docker.from_env()
            client.ping()
            self._available = True
            return True
        except Exception:
            self._available = False
            return False

    def build_image(self):
        """Build the sandbox image from the Dockerfile in the root directory."""
        from rich.console import Console
        console = Console(color_system=None)
        console.print(f"Building Docker image {self.image_name}...")

        image, logs = self.client.images.build(path=".", tag=self.image_name, rm=True)
        for line in logs:
            if 'stream' in line:
                console.print(line['stream'].strip(), style="dim")
        return image

    def execute_command(self, command: str, timeout: int = 300) -> Dict[str, Any]:
        """Execute a command in a new container and return the output."""
        try:
            container = self.client.containers.run(
                self.image_name,
                command=["/bin/bash", "-c", command],
                detach=True,
                network_mode="bridge",
                cap_add=["NET_RAW", "NET_ADMIN"]
            )
            
            # Wait for container to finish or timeout
            try:
                result = container.wait(timeout=timeout)
                exit_code = result.get("StatusCode", 1)
            except Exception as e:
                container.kill()
                return {"stdout": "", "stderr": f"Command timed out after {timeout}s", "exit_code": -1}

            stdout = container.logs(stdout=True, stderr=False).decode("utf-8")
            stderr = container.logs(stdout=False, stderr=True).decode("utf-8")
            
            container.remove()
            
            return {
                "stdout": stdout,
                "stderr": stderr,
                "exit_code": exit_code
            }
        except Exception as e:
            return {
                "stdout": "",
                "stderr": str(e),
                "exit_code": -1
            }

if __name__ == "__main__":
    # Quick test
    executor = DockerExecutor()
    # executor.build_image()
    res = executor.execute_command("nmap --version")
    print(res)
