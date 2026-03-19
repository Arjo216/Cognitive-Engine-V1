import streamlit as st
import requests
import json
import time

# 1. Page Config
st.set_page_config(page_title="The Oracle", page_icon="🧠", layout="wide")

# 2. Peak Aesthetic CSS
st.markdown("""
    <style>
    .stChatFloatingInputContainer { background-color: rgba(0,0,0,0); }
    .stChatMessage { border: 1px solid #333; border-radius: 10px; padding: 10px; background: #0e1117; }
    .source-card { border-left: 3px solid #00ffa2; padding-left: 10px; margin: 10px 0; font-size: 0.9rem; color: #aaa; }
    </style>
""", unsafe_allow_html=True) # <-- FIXED PARAMETER

if "messages" not in st.session_state:
    st.session_state.messages = []

st.title("🧠 The Founder's Oracle")
st.markdown("*Streaming Neural RAG Engine powered by Pinecone & Gemini 2.5*")

# 3. Sidebar Stats
with st.sidebar:
    st.header("⚙️ Engine Metrics")
    st.info("Vector Index: v2 (Active)")
    st.info("Reranker: MiniLM-L-12 (Enabled)")
    if st.button("Reset Session"):
        st.session_state.messages = []
        st.rerun()

# 4. Display Chat
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "sources" in msg:
            with st.expander("References"):
                for s in msg["sources"]:
                    st.markdown(f"[{s['title']}]({s['url']}) | Confidence: {s['score']}")

# 5. User Input
if prompt := st.chat_input("Ask the Oracle..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # Real-time Status Indicators
        with st.status("Thinking...", expanded=True) as status:
            st.write("🔍 Probing Vector Memory...")
            
            resp_container = st.empty()
            full_response = ""
            sources = []

            try:
                # Fire the Streaming Request
                with requests.post("http://127.0.0.1:8000/ask_stream", json={"text": prompt}, stream=True) as r:
                    status.update(label="🧬 Neural Reranking...", state="running")
                    
                    lines = r.iter_lines(decode_unicode=True)
                    
                    # Capture Metadata Line
                    source_line = next(lines)
                    sources = json.loads(source_line)["sources"]
                    
                    status.update(label="✍️ Synthesizing Answer...", state="running")
                    
                    # Handle the Stream with Typing effect
                    for chunk in lines:
                        if chunk:
                            full_response += chunk
                            resp_container.markdown(full_response + "▌")
                            # Micro-delay for smooth animation
                            time.sleep(0.01)

                status.update(label="Processing Complete", state="complete", expanded=False)
                resp_container.markdown(full_response)
                
                # Show references
                with st.expander("References"):
                    for s in sources:
                        st.markdown(f"[{s['title']}]({s['url']}) | Confidence: {s['score']}")

                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": full_response, 
                    "sources": sources
                })

            except Exception as e:
                st.error(f"Engine Exception: {e}")