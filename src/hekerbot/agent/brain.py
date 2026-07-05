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

Available tools in the sandbox (categorized):

1. **Reconnaissance & Asset Discovery**:
   - amass: Subdomain enumeration, ASN/domain mapping.
   - subfinder: Fast passive subdomain discovery.
   - httpx-toolkit: Probing live HTTP hosts.
   - dnsx: Bulk DNS resolution.
   - whois, dig: Domain/DNS enumeration.

2. **Port Scanning & Service Fingerprinting**:
   - masscan: Extremely fast port scanning.
   - rustscan: Fast port discovery, pipes to Nmap.
   - nmap: Deep service/OS fingerprinting, NSE scripts.

3. **Web Application Enumeration**:
   - ffuf: Directory fuzzing, parameter discovery.
   - katana: Web crawling and endpoint extraction.
   - nuclei: Template-driven vulnerability scanning.
   - chromium: Headless browser for visual/JS tasks.

4. **Vulnerability Scanning**:
   - wpscan: WordPress-specific scanning.
   - nikto: Generic web server scanner.
   - trivy: Container/dependency vulnerability scanning.

5. **Exploitation & Payload Management**:
   - msfconsole: Metasploit Framework.
   - searchsploit: Offline Exploit-DB lookup.
   - sqlmap: SQL injection detection and exploitation.
   - xsstrike: XSS detection and bypass.
   - jwt-tool: JWT token manipulation.

6. **Credential & Auth Testing**:
   - hydra: Online brute-force (SSH, HTTP, etc.).
   - hashcat, john: Offline hash cracking.
   - kerbrute: Kerberos pre-auth brute-force.

7. **Post-Exploitation & Lateral Movement**:
   - netexec: Successor to CrackMapExec; AD post-exploitation tool.
   - impacket-*: Collection of Python classes for working with network protocols (e.g., psexec, secretsdump).
   - bloodhound.py: AD privilege escalation path analysis.
   - evil-winrm: WinRM-based lateral movement shell.

8. **Evasion & C2**:
   - chisel: SOCKS5 tunneling over HTTP.

Target environment is isolated and authorized for testing.
Focus on discovery, vulnerability assessment, and privilege escalation pathways.

Be concise in your thoughts.
"""

class HekerBrain:
    def __init__(self, model: str = None):
        self.model = model or os.getenv("HEKER_MODEL", "opencode/deepseek-coder")
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
            call_model = self.model
            kwargs = {}
            
            # Map opencode custom provider to openai compatible endpoint
            if call_model.startswith("opencode/") or call_model == "opencode":
                call_model = call_model.replace("opencode/", "openai/") if "/" in call_model else "openai/opencode"
                
                opencode_key = os.getenv("OPENCODE_API_KEY")
                if opencode_key:
                    kwargs["api_key"] = opencode_key
                    os.environ["OPENAI_API_KEY"] = opencode_key
                
                if not os.getenv("OPENAI_BASE_URL") and not os.getenv("OPENAI_API_BASE"):
                    kwargs["api_base"] = "https://opencode.ai/zen/go/v1"
                    os.environ["OPENAI_API_BASE"] = "https://opencode.ai/zen/go/v1"

            response = litellm.completion(
                model=call_model,
                messages=self.history,
                response_format={"type": "json_object"},
                **kwargs
            )
            
            content = response.choices[0].message.content
            # Keep history slim by potentially summarizing or only keeping last N observations
            self.history.append({"role": "assistant", "content": content})
            
            # Robust JSON parsing
            content = content.strip()
            try:
                return json.loads(content)
            except json.JSONDecodeError as e:
                # Try to extract JSON from markdown blocks or raw {}
                import re
                
                # 1. Try markdown blocks with optional 'json' tag
                match = re.search(r"```(?:json)?\n?(.*?)\n?```", content, re.DOTALL | re.IGNORECASE)
                if match:
                    try:
                        return json.loads(match.group(1).strip())
                    except json.JSONDecodeError:
                        pass
                
                # 2. Try raw curly brace extraction
                start = content.find('{')
                end = content.rfind('}')
                if start != -1 and end != -1 and end > start:
                    try:
                        return json.loads(content[start:end+1])
                    except json.JSONDecodeError:
                        pass
                
                raise Exception(f"Failed to parse JSON. Raw LLM response: {content[:100]}...") from e

        except Exception as e:
            err_msg = str(e)
            if "Expecting value" in err_msg and "char 0" in err_msg:
                err_msg = "LLM returned an empty or invalid response. Check your API key and base URL."
            return {
                "thought": f"Error thinking: {err_msg}",
                "command": "echo 'error'",
                "finished": True
            }

    def reset(self, target: str):
        self.history = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Start penetration test on target: {target}"}
        ]
