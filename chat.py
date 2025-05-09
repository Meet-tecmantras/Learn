import streamlit as st
import requests

st.title("💬 Chat with LLaMA 3.1 (Local)")

# Store conversation
if "history" not in st.session_state:
    st.session_state.history = []

# User input
user_input = st.text_input("Your message", "")

# When user submits a message
if st.button("Send") and user_input.strip():
    st.session_state.history.append({"role": "user", "content": user_input})

    # Format conversation as prompt
    messages = "\n".join([f"{m['role'].capitalize()}: {m['content']}" for m in st.session_state.history])
    prompt = f"{messages}\nAssistant:"

    # Send prompt to local Ollama LLaMA model
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "llama3",
            "prompt": prompt,
            "stream": False
        }
    )

    result = response.json()
    assistant_reply = result.get("response", "").strip()
    st.session_state.history.append({"role": "assistant", "content": assistant_reply})

# Display conversation
for msg in st.session_state.history:
    if msg["role"] == "user":
        st.markdown(f"**You**: {msg['content']}")
    else:
        st.markdown(f"**LLaMA 3.1**: {msg['content']}")
