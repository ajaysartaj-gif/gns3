from flask import Flask, request, jsonify
import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
PORT = 5140

def send_to_gemini_ai(raw_log: str, router_ip: str):
    print("\n🤖 Passing raw log to Gemini AI for structural diagnosis...")
    api_key = os.getenv("OPENROUTER_API_KEY")
    endpoint = "https://openrouter.ai/api/v1/chat/completions"
    
    system_rules = (
        "You are an Autonomous AI NetDevOps Diagnostic Engineer.\n"
        "Analyze the raw router log, identify the root cause, figure out which node failed, "
        "and generate a valid JSON orchestration payload back.\n\n"
        "Return EXACTLY a raw JSON block with no markdown formatting or backticks. Match this schema:\n"
        "{\n"
        "  \"incident_summary\": \"Human readable description of what broke\",\n"
        "  \"target_nodes\": [\"r1\"],\n"
        "  \"proposed_feature\": \"ospf\" | \"vlan\" | \"interface\",\n"
        "  \"remediation_variables\": {\"description\": \"variables for the fix configuration\"}\n"
        "}"
    )

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": "google/gemini-2.5-flash",
        "messages": [
            {"role": "system", "content": system_rules},
            {"role": "user", "content": f"Source Router IP: {router_ip}\nRaw Syslog Alert Text: {raw_log}"}
        ]
    }
    
    try:
        response = requests.post(endpoint, headers=headers, json=payload, timeout=20)
        ai_response = response.json()['choices'][0]['message']['content'].strip()
        print("✅ Gemini Analysis Complete:")
        print(ai_response)
        return json.loads(ai_response)
    except Exception as e:
        print(f"[!] Gemini processing failed: {e}")
        return None

@app.route('/syslog', methods=['POST'])
def handle_syslog():
    payload = request.json
    raw_log = payload.get('log', '')
    router_ip = payload.get('ip', '192.168.87.51')
    
    print(f"\n[🚨 WEBHOOK TELEMETRY RECEIVED]")
    print(f"    Raw Data: {raw_log}")
    
    # Pass it straight to Gemini
    send_to_gemini_ai(raw_log, router_ip)
    return jsonify({"status": "received"}), 200

if __name__ == "__main__":
    print(f"[*] Cloud Agent Webhook listening on port {PORT}...")
    app.run(host='0.0.0.0', port=PORT)