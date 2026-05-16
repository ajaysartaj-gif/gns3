import streamlit as st
from engine.intent_processor import IntentProcessor
from engine.orchestration_core import OrchestrationCore

# Page styling configuration definitions
st.set_page_config(page_title="NetBrain Enterprise AI OS", page_icon="🌐", layout="wide")

# Custom injection of modern CSS mirroring Gemini UX models
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
    .console-card { background-color: #131520; border: 1px solid #222538; border-radius: 14px; padding: 25px; margin-bottom: 20px; }
    .intent-badge { background-color: #2b1f4d; color: #bca7f5; padding: 4px 12px; border-radius: 20px; font-size: 0.85rem; font-weight: bold; }
    </style>
""", unsafe_allow_html=True) # <-- Fixed here

st.markdown("<h1 class='gemini-gradient-header'>NetBrain Orchestration Core</h1>", unsafe_allow_html=True) # <-- Fixed here
st.markdown("<div class='subtext'>Universal AI Control Engine for multi-router network fabrics.</div>", unsafe_allow_html=True) # <-- Fixed here

# Session tracking initialization
if "execution_history" not in st.session_state:
    st.session_state.execution_history = []

# Main Interface Work Area Split
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("### Active Architecture Session")
    if not st.session_state.execution_history:
        st.info("The configuration matrix is clean. Use the core execution input block below to dispatch autonomous parameters.")
    
    for idx, session in enumerate(st.session_state.execution_history):
        with st.container():
            st.markdown(f"""
            <div class='console-card'>
                <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;'>
                    <span style='font-size: 1.2rem; font-weight: bold; color: #a3b8cc;'>Request #{idx+1}: "{session['prompt']}"</span>
                    <span class='intent-badge'>{session['schema']['feature_type'].upper()}</span>
                </div>
                <p style='color: #6c728a; font-family: monospace; font-size: 0.9rem;'>TARGET DEVICES: {', '.join(session['schema']['target_nodes'])}</p>
                <h5 style='color: #8c90a6;'>Execution Verification Output Logs:</h5>
                <pre style='background-color: #0b0c12; color: #4af626; padding: 15px; border-radius: 8px; border: 1px solid #1a1c29; max-height: 300px; overflow-y: auto;'>{session['logs']}</pre>
            </div>
            """, unsafe_allow_html=True) # <-- Fixed here

with col2:
    st.markdown("### AI Parameters Insight")
    if st.session_state.execution_history:
        latest = st.session_state.execution_history[-1]
        st.json(latest['schema'])
    else:
        st.caption("Structured JSON blueprints will reflect here automatically once intent parsing cycles finish execution.")

# Base Input Panel matching Gemini Prompting Interface Designs
prompt_input = st.chat_input("Dispatch declarative infrastructure commands (e.g., 'Configure a vlan with id 50 on r1 and r2')")

if prompt_input:
    # Trigger processing execution sequence
    with st.spinner("🤖 Processing network intent parameters globally..."):
        processor = IntentProcessor()
        orchestrator = OrchestrationCore()
        
        # 1. Structural schema interpretation
        schema_blueprint = processor.extract_network_parameters(prompt_input)
        
        # 2. Command generation and remote fabric deployment
        output_reports = orchestrator.deploy_feature(schema_blueprint)
        
        # 3. Store transaction parameters cleanly inside history trace state
        st.session_state.execution_history.append({
            "prompt": prompt_input,
            "schema": schema_blueprint,
            "logs": output_reports
        })
        st.rerun()
