import socket
import json
import os
import requests
from dotenv import load_dotenv

# Load your OpenRouter / Gemini API keys from your existing environment
load_dotenv()

# Configuration Layer
CODESPACE_BIND_IP = "0.0.0.0"   # Listens to traffic coming in through the Pinggy tunnel
SYSLOG_PORT = 5140              # The port your tunnel passes traffic to

def send_to_gemini_ai(raw_log: str, router_ip: str):
    """Hands the raw network error text directly over to Gemini for triage."""
    print("🤖 Passing raw log to Gemini AI for structural diagnosis...")
    
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
        
        # Here we will hook up the push notification to your Streamlit UI dashboard
        return json.loads(ai_response)
    except Exception as e:
        print(f"[!] Failed to parse incident through Gemini engine: {e}")
        return None

def run_cloud_syslog_agent():
    # Setup our lightweight UDP socket receiver
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    try:
        udp_socket.bind((CODESPACE_BIND_IP, SYSLOG_PORT))
        print(f"[*] Cloud NetDevOps Agent actively listening on internal port {SYSLOG_PORT}...")
        print("[*] Tunnel traffic from your GNS3 topology will land here.\n")
    except Exception as e:
        print(f"[!] Critical Error: Cannot bind to port {SYSLOG_PORT}. Details: {e}")
        return

    while True:
        try:
            # Intercept data package streams flying out of your tunnel bridge
            data, addr = udp_socket.recvfrom(4096)
            raw_log = data.decode('utf-8', errors='ignore')
            router_ip = addr[0]
            
            # Look for critical infrastructure flapping signatures
            if any(trigger in raw_log for trigger in ["DOWN", "UPDOWN", "CHANGED", "FAIL", "MISMATCH", "ERR"]):
                print(f"\n[🚨 TELEMETRY PACKET DETECTED]")
                print(f"    Raw Log Data: {raw_log.strip()}")
                
                # Hand it off to the AI mind engine
                send_to_gemini_ai(raw_log.strip(), router_ip)
                print("-" * 60)
                
        except KeyboardInterrupt:
            print("\n[*] Shutting down cloud event agent safely.")
            break
        except Exception as err:
            print(f"[!] Processing loop encountered error: {err}")

if __name__ == "__main__":
    run_cloud_syslog_agent()
