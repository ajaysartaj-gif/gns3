import streamlit as st
import requests
import os
from engine.intent_processor import IntentProcessor
from engine.orchestration_core import OrchestrationCore

st.set_page_config(page_title="NetBrain Enterprise AI OS", page_icon="🌐", layout="wide")

# Modern Dark UI Theme Styling
st.markdown("""
    <style>
    .stApp { background-color: #090a0f; color: #f0f0f5; }
    .gemini-gradient-header { 
        font-size: 2.8rem; font-weight: 700; 
        background: linear-gradient(90deg, #667eea 0%, #764ba2 50%, #6b8cce 100%); 
        -webkit-background-clip: text; -webkit-text-fill-color: transparent; 
        margin-bottom: 5px; 
    }
    .subtext { color: #8e92a6; font-size: 1.1rem; margin-bottom: 30px; }
    .answer-card { background-color: #131520; border: 1px solid #23a964; border-radius: 14px; padding: 25px; margin-bottom: 25px; }
    .console-card { background-color: #131520; border: 1px solid #222538; border-radius: 14px; padding: 20px; margin-top: 15px; }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1 class='gemini-gradient-header'>NetBrain Orchestration Core</h1>", unsafe_allow_html=True)
st.markdown("<div class='subtext'>Universal AI Control Engine for multi-router network fabrics.</div>", unsafe_allow_html=True)

if "execution_history" not in st.session_state:
    st.session_state.execution_history = []

def summarize_output_with_ai(user_prompt, raw_logs):
    """Passes the raw router log back to Gemini to extract a direct answer."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    endpoint = "https://openrouter.ai/api/v1/chat/completions"
    
    system_rule = (
        "You are the voice of an intelligent network assistant. The user asked a specific question.\n"
        "I will provide you with the raw Cisco router output logs answering that question.\n"
        "Your job is to read the logs and answer the user's question directly, clearly, and concisely.\n"
        "If they asked for an IP, extract and give them just the IP address cleanly. Do not show raw command outputs."
    )
    
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": "google/gemini-2.5-flash",
        "messages": [
            {"role": "system", "content": system_rule},
            {"role": "user", "content": f"User Question: {user_prompt}\n\nRaw Router Logs:\n{raw_logs}"}
        ]
    }
    try:
        response = requests.post(endpoint, headers=headers, json=payload, timeout=20)
        return response.json()['choices'][0]['message']['content'].strip()
    except:
        return "Unable to parse clean summary. Please review raw logs below."

# Work Canvas Split
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("### Response Console")
    
    if st.session_state.execution_history:
        # ALWAYS pull the absolute latest interaction from the tracking history array
        latest_session = st.session_state.execution_history[-1]
        
        # Display the crisp, AI-summarized answer card
        st.markdown(f"""
        <div class='answer-card'>
            <div style='font-size: 0.9rem; color: #8e92a6; text-transform: uppercase; margin-bottom: 5px;'>Direct AI Answer</div>
            <div style='font-size: 1.4rem; font-weight: 500; color: #f0f0f5;'>{latest_session['ai_summary']}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Expandable drop-down for troubleshooting raw logs if needed
        with st.expander("View Raw Cisco CLI Logs & Telemetry"):
            st.markdown(f"""
            <div class='console-card'>
                <p style='color: #6c728a; font-family: monospace;'>TARGET DEVICES: {', '.join(latest_session['schema']['target_nodes'])}</p>
                <pre style='background-color: #0b0c12; color: #4af626; padding: 15px; border-radius: 8px;'>{latest_session['logs']}</pre>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("System ready. Input an informational query or configuration command below.")

with col2:
    st.markdown("### Active Parameters")
    if st.session_state.execution_history:
        st.json(st.session_state.execution_history[-1]['schema'])
    else:
        st.caption("JSON parameters blueprint will render here.")

# Bottom Entry Panel
prompt_input = st.chat_input("Ask a question or configure a feature...")

if prompt_input:
    with st.spinner("🤖 Orchestrating network fabric requests..."):
        processor = IntentProcessor()
        orchestrator = OrchestrationCore()
        
        # 1. Get structured schema intent
        schema_blueprint = processor.extract_network_parameters(prompt_input)
        
        # 2. Fetch raw data from routers
        output_reports = orchestrator.deploy_feature(schema_blueprint)
        
        # 3. Clean up the response using Gemini
        clean_summary = summarize_output_with_ai(prompt_input, output_reports)
        
        # 4. Save to history state
        st.session_state.execution_history.append({
            "prompt": prompt_input,
            "schema": schema_blueprint,
            "logs": output_reports,
            "ai_summary": clean_summary
        })
        st.rerun()
