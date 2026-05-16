import socket
import threading
import json
import os
import requests
from dotenv import load_dotenv

load_dotenv()

# Shared Global Alert Queue that your Streamlit frontend app.py will read from
INCIDENT_QUEUE = []

class AutonomousEventEngine:
    def __init__(self, host="0.0.0.0", port=514):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.is_running = False

    def start_listener(self):
        """Spins up the UDP background logging listener server thread."""
        self.socket.bind((self.host, self.port))
        self.is_running = True
        self.thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.thread.start()
        print(f"[*] NetBrain Autonomous Event Engine active on UDP port {self.port}...")

    def _listen_loop(self):
        while self.is_running:
            try:
                data, addr = self.socket.recvfrom(4096)
                raw_log = data.decode('utf-8', errors='ignore')
                
                # Filter out unneeded background noise chatty logs
                if any(trigger in raw_log for trigger in ["DOWN", "UPDOWN", "CHANGED", "FAIL", "MISMATCH", "ERR"]):
                    self._process_incident_with_ai(raw_log, addr[0])
            except Exception as e:
                print(f"[!] Error reading incoming UDP stream socket packet: {e}")

    def _process_incident_with_ai(self, raw_log: str, source_ip: str):
        """Hands the live network failure message directly over to Gemini for structural triage."""
        api_key = os.getenv("OPENROUTER_API_KEY")
        endpoint = "https://openrouter.ai/api/v1/chat/completions"
        
        system_rules = (
            "You are an Autonomous AI NetDevOps Diagnostic Engineer.\n"
            "You have received a raw live incident log from a router in the fabric infrastructure.\n"
            "Analyze the log, identify the root cause issue, find which node failed, and generate a valid "
            "JSON orchestration response mapping out the fix.\n\n"
            "Return EXACTLY a raw JSON block with no markdown formatting backticks. Match this exact format schema:\n"
            "{\n"
            "  \"incident_summary\": \"Human readable description of what broke\",\n"
            "  \"target_nodes\": [\"r1\" or \"r2\"],\n"
            "  \"proposed_feature\": \"ospf\" | \"vlan\" | \"acl\",\n"
            "  \"remediation_variables\": {\"variables corresponding to the feature fix configuration inputs\"}\n"
            "}"
        )

        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {
            "model": "google/gemini-2.5-flash",
            "messages": [
                {"role": "system", "content": system_rules},
                {"role": "user", "content": f"Source Router IP: {source_ip}\nRaw Syslog Alert Text: {raw_log}"}
            ]
        }
        
        try:
            response = requests.post(endpoint, headers=headers, json=payload, timeout=20)
            analysis = json.loads(response.json()['choices'][0]['message']['content'].strip())
            
            # Enqueue the incident with an active state status tracking token flag
            incident_payload = {
                "id": len(INCIDENT_QUEUE) + 1,
                "raw_log": raw_log,
                "summary": analysis.get("incident_summary"),
                "target_nodes": analysis.get("target_nodes", ["r1"]),
                "feature": analysis.get("proposed_feature"),
                "variables": analysis.get("remediation_variables", {}),
                "status": "Awaiting Human-In-The-Loop Approval"
            }
            INCIDENT_QUEUE.append(incident_payload)
        except Exception as e:
            print(f"[!] Failed to parse incident telemetry through AI engine core framework: {e}")
