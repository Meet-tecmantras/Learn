import streamlit as st
import fitz  # PyMuPDF
import docx
import requests
import json
from github import Github


# === File Handling ===
def extract_text_from_file(uploaded_file):
    ext = uploaded_file.name.split('.')[-1].lower()
    if ext == 'pdf':
        doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        return "\n".join([page.get_text() for page in doc])
    elif ext == 'docx':
        doc = docx.Document(uploaded_file)
        return "\n".join([para.text for para in doc.paragraphs])
    elif ext == 'txt':
        return uploaded_file.read().decode('utf-8')
    else:
        st.error("Unsupported file format.")
        return ""

# === LLaMA Analysis ===
def analyze_with_llama(content):
    prompt = f"""
You are a project planning assistant.
Given the following documentation, identify:
1. Main tasks
2. Sub-tasks for each main task

Return the result in this JSON format:
{{
  "Main Task 1": ["Sub-task 1.1", "Sub-task 1.2"],
  "Main Task 2": ["Sub-task 2.1", "Sub-task 2.2"]
}}

Content:
{content}
"""

    response = requests.post(LLAMA_API_URL, json={
        "model": "gemma3:1b",
        "prompt": prompt,
        "stream": False
    })
    
    return response

# === Jira Creation ===
def create_jira_task(summary, description, issue_type="Task", parent_id=None):
    url = f"{JIRA_BASE_URL}/rest/api/3/issue"
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    auth = (JIRA_EMAIL, JIRA_API_TOKEN)

    payload = {
        "fields": {
            "project": {"key": JIRA_PROJECT_KEY},
            "summary": summary,
            "description": description,
            "issuetype": {"name": issue_type}
        }
    }
    if parent_id and issue_type == "Sub-task":
        payload["fields"]["parent"] = {"key": parent_id}

    response = requests.post(url, json=payload, headers=headers, auth=auth)
    return response.json().get('key')

# === GitHub Branch Creation ===
def create_github_branch(branch_name, base='main'):
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(GITHUB_REPO)
    source = repo.get_branch(base)
    repo.create_git_ref(ref=f"refs/heads/{branch_name}", sha=source.commit.sha)

# === Streamlit App ===
st.set_page_config(page_title="Project Planning Automation (Local LLaMA)", layout="wide")
st.title("🧠 Project Planning Automation (Powered by Local LLaMA)")

uploaded_file = st.file_uploader("📂 Upload project documentation (.pdf, .docx, .txt)", type=['pdf', 'docx', 'txt'])

if uploaded_file:
    with st.spinner("🔍 Extracting and analyzing..."):
        content = extract_text_from_file(uploaded_file)
        llama_response = analyze_with_llama(content)
        # st.text_area("📄 Extracted Content", llama_response, height=300)

        try:
            task_map = json.loads(llama_response.text)
        except json.JSONDecodeError:
            st.error("❌ Failed to parse LLaMA response. Please check the model output.")
            st.text("Raw LLaMA Response:")
            st.text(llama_response.text)
            st.stop()

    st.subheader("📋 Review Extracted Tasks")
    st.text(llama_response.text)
    st.markdown("### Extracted Tasks")
    st.text_area("Extracted Tasks", json.dumps(task_map, indent=2), height=300)
    st.markdown("### Summary of Tasks")
    st.markdown("### Main Tasks and Sub-tasks")
    st.markdown("The following tasks were extracted from the document. Please review them before proceeding.")
    for main_task, sub_tasks in task_map.items():
        with st.expander(f"📌 {main_task}"):
            for sub in sub_tasks:
                st.markdown(f"- [ ] {sub}")

    if st.button("✅ Confirm and Create Jira + GitHub"):
        with st.spinner("🚀 Creating tasks and branches..."):
            for main_task, sub_tasks in task_map.items():
                main_key = create_jira_task(main_task, "Generated from LLaMA", "Story")
                create_github_branch(main_task.replace(" ", "-").lower())

                for sub in sub_tasks:
                    sub_key = create_jira_task(sub, f"Sub-task of {main_key}", "Sub-task", parent_id=main_key)
                    create_github_branch(sub.replace(" ", "-").lower())
        st.success("✅ Jira and GitHub setup completed successfully!")

