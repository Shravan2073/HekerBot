import litellm
import json
import os
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()

SYSTEM_PROMPT = """
You are HekerBOT, an autonomous agentic red teaming framework. 
Your goal is to perform a controlled penetration test on a given target.

You follow an iterative loop:
1. **Plan**: Analyze your current findings and decide on the next logical step.
2. **Act**: Choose a specific security tool and command to run.
3. **Observe**: Review the output of the tool.
4. **Reflect**: Update your knowledge base and refine your strategy.

Your output MUST be a JSON object with the following structure:
{
  "thought": "Your reasoning for the next step",
  "command": "The exact shell command to run in the sandbox",
  "updates": {
    "ip": "Target IP",
    "hostname": "Optional hostname",
    "new_ports": [80, 443],
    "new_vulnerabilities": ["CVE-XXXX-XXXX"]
  },
  "finished": false,
  "summary": "Optional summary if you are finishing"
}

The 'updates' field is optional but highly recommended when you discover new information.
Available tools in the sandbox: nmap, sqlmap, nikto, ffuf, ping, curl, etc.
Target environment is isolated and authorized for testing.
Focus on discovery, vulnerability assessment, and privilege escalation pathways.

Be concise in your thoughts.
"""

class HekerBrain:
    def __init__(self, model: str = None):
        self.model = model or os.getenv("HEKER_MODEL", "gpt-4-turbo-preview")
        self.history = [{"role": "system", "content": SYSTEM_PROMPT}]

    def think(self, observation: str = None, current_state: Any = None) -> Dict[str, Any]:
        prompt = ""
        if current_state:
            prompt += f"Current Knowledge Graph: {json.dumps(current_state, default=str)}\n"
        
        if observation:
            prompt += f"Observation from last command:\n{observation}"

        if prompt:
            self.history.append({"role": "user", "content": prompt})

        try:
            response = litellm.completion(
                model=self.model,
                messages=self.history,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            # Keep history slim by potentially summarizing or only keeping last N observations
            self.history.append({"role": "assistant", "content": content})
            
            # Robust JSON parsing
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                # Try to extract JSON from markdown blocks
                import re
                match = re.search(r"```json\n?(.*?)\n?```", content, re.DOTALL)
                if match:
                    try:
                        return json.loads(match.group(1))
                    except json.JSONDecodeError:
                        pass
                raise
        except Exception as e:
            return {
                "thought": f"Error thinking: {str(e)}",
                "command": "echo 'error'",
                "finished": True
            }

    def reset(self, target: str):
        self.history = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Start penetration test on target: {target}"}
        ]
