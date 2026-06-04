import docker
import os
from typing import Dict, Any

class DockerExecutor:
    def __init__(self, image_name: str = "hekerbot-sandbox"):
        self.client = docker.from_env()
        self.image_name = image_name

    def build_image(self):
        """Build the sandbox image from the Dockerfile in the root directory."""
        print(f"Building Docker image {self.image_name}...")
        image, logs = self.client.images.build(path=".", tag=self.image_name, rm=True)
        for line in logs:
            if 'stream' in line:
                print(line['stream'].strip())
        return image

    def execute_command(self, command: str, timeout: int = 300) -> Dict[str, Any]:
        """Execute a command in a new container and return the output."""
        try:
            container = self.client.containers.run(
                self.image_name,
                command=["/bin/bash", "-c", command],
                detach=True,
                network_mode="bridge" # Or "none" for extreme isolation if tools don't need internet
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
