import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

class IntentProcessor:
    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.endpoint = "https://openrouter.ai/api/v1/chat/completions"

    def extract_network_parameters(self, raw_prompt: str) -> dict:
        """Translates open-ended enterprise requests or plain informational questions into structured schemas."""
        system_rules = (
            "You are an expert Enterprise Network Orchestration Engine. Your job is to classify the user's intent.\n"
            "CRITICAL: Determine if the user is making a dynamic network changes (like configuring OSPF, VLAN, ACL) "
            "or if they are simply asking an informational question/query (like 'what is the IP', 'show me routes').\n\n"
            "If they are asking a plain question, set 'feature_type' to 'query' and put troubleshooting diagnostic "
            "commands like 'show ip interface brief' or 'show ip route' inside the 'verification_commands' array.\n\n"
            "Return EXACTLY a raw JSON block with no markdown formatting tags, no backticks, and no conversation. "
            "Use this exact schema structure:\n"
            "{\n"
            "  \"feature_type\": \"ospf\" | \"vlan\" | \"acl\" | \"query\" | \"unknown\",\n"
            "  \"target_nodes\": [\"r1\"], [\"r2\"], or [\"r1\", \"r2\"],\n"
            "  \"variables\": {},\n"
            "  \"verification_commands\": [\"list of show commands needed to answer the user's query or verify configs\"]\n"
            "}"
        )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "google/gemini-2.5-flash",
            "messages": [
                {"role": "system", "content": system_rules},
                {"role": "user", "content": raw_prompt}
            ]
        }
        
        try:
            response = requests.post(self.endpoint, headers=headers, json=payload, timeout=30)
            text_data = response.json()['choices'][0]['message']['content'].strip()
            
            if text_data.startswith("```json"):
                text_data = text_data.replace("```json", "").replace("```", "").strip()
            return json.loads(text_data)
        except Exception:
            # Safe conversational fallback blueprint if API times out
            return {
                "feature_type": "query",
                "target_nodes": ["r1"],
                "variables": {},
                "verification_commands": ["show ip interface brief", "show ip route"]
            }
