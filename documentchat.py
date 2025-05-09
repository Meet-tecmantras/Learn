import streamlit as st
import requests

st.set_page_config(page_title="Chat with llama3")
st.title("📄 Ask Questions Based on Your Document")

# Step 1: Upload a file
uploaded_file = st.file_uploader("Upload a TXT file", type=["txt"])

# Store uploaded content
if uploaded_file is not None:
    context_text = uploaded_file.read().decode("utf-8")
    st.text_area("📚 Extracted Context", context_text, height=200)

    # Store conversation history
    if "qa_history" not in st.session_state:
        st.session_state.qa_history = []

    # Step 2: Ask a question
    question = st.text_input("❓ Ask a question about the document")

    if st.button("Ask") and question.strip():
        # Build prompt: add context + question
        full_prompt = f"""
You are a helpful assistant. Use the following context to answer the question.

Context:
\"\"\"
{context_text}
\"\"\"

Question: {question}
Answer:
"""

        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3",
                "prompt": full_prompt,
                "stream": False
            }
        )

        result = response.json()
        answer = result.get("response", "").strip()

        # Save Q&A
        st.session_state.qa_history.append((question, answer))

    # Display Q&A history
    if st.session_state.qa_history:
        st.markdown("---")
        st.subheader("🧠 Q&A History")
        for q, a in reversed(st.session_state.qa_history):
            st.markdown(f"**Q:** {q}")
            st.markdown(f"**A:** {a}")
            st.markdown("---")
