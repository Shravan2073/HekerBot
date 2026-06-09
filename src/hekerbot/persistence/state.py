from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import json
import os
from datetime import datetime

class CommandResult(BaseModel):
    command: str
    stdout: str
    stderr: str
    exit_code: int
    timestamp: datetime = Field(default_factory=datetime.now)

class Asset(BaseModel):
    ip: str
    hostname: Optional[str] = None
    ports: List[int] = Field(default_factory=list)
    services: Dict[int, str] = Field(default_factory=dict)
    vulnerabilities: List[str] = Field(default_factory=list)

class SessionState(BaseModel):
    session_id: str
    target: str
    start_time: datetime = Field(default_factory=datetime.now)
    history: List[Dict[str, Any]] = Field(default_factory=list) # Agent thoughts and commands
    command_results: List[CommandResult] = Field(default_factory=list)
    discovery_graph: Dict[str, Asset] = Field(default_factory=dict) # IP -> Asset

    def update_asset(self, ip: str, hostname: Optional[str] = None, ports: List[int] = None, vulnerabilities: List[str] = None):
        if ip not in self.discovery_graph:
            self.discovery_graph[ip] = Asset(ip=ip)
        
        asset = self.discovery_graph[ip]
        if hostname:
            asset.hostname = hostname
        if ports:
            for port in ports:
                if port not in asset.ports:
                    asset.ports.append(port)
        if vulnerabilities:
            for vuln in vulnerabilities:
                if vuln not in asset.vulnerabilities:
                    asset.vulnerabilities.append(vuln)

class PersistenceManager:
    def __init__(self, storage_dir: str = "sessions"):
        self.storage_dir = storage_dir
        if not os.path.exists(storage_dir):
            os.makedirs(storage_dir)

    def save_session(self, state: SessionState):
        file_path = os.path.join(self.storage_dir, f"{state.session_id}.json")
        with open(file_path, "w") as f:
            f.write(state.model_dump_json(indent=2))

    def load_session(self, session_id: str) -> Optional[SessionState]:
        file_path = os.path.join(self.storage_dir, f"{session_id}.json")
        if not os.path.exists(file_path):
            return None
        with open(file_path, "r") as f:
            data = json.load(f)
            return SessionState(**data)

    def list_sessions(self) -> List[str]:
        if not os.path.exists(self.storage_dir):
            return []
        return [f.replace(".json", "") for f in os.listdir(self.storage_dir) if f.endswith(".json")]
