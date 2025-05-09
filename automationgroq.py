import streamlit as st
import requests
import json
import fitz  # PyMuPDF
import docx
import re
from github import Github

# === Configuration ===


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

# === LLM via Groq ===
def analyze_with_groq(content):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    prompt = f"""
You are a software project planner. Analyze the following project document and return the following:

- Main Tasks
- Sub-Tasks for each Main Task

Return strictly in JSON format:
{{
  "Main Task 1": ["Sub-task 1", "Sub-task 2"],
  "Main Task 2": ["Sub-task A", "Sub-task B"]
}}

Document:
\"\"\"
{content}
\"\"\"
"""
    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant that extracts structured project planning tasks from documentation."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,
        "max_tokens": 1024
    }

    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()['choices'][0]['message']['content']

# === Jira Creation ===
def get_valid_issue_types():
    """Fetch valid Jira issue types."""
    url = f"{JIRA_BASE_URL}/rest/api/3/issuetype"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    auth = (JIRA_EMAIL, JIRA_API_TOKEN)

    response = requests.get(url, headers=headers, auth=auth)
    if response.status_code == 200:
        return {item['name']: item['id'] for item in response.json()}
    else:
        st.warning("⚠️ Could not fetch issue types from Jira.")
        return {}


def create_jira_task(summary, description, issue_type="Epic", parent_id=None):
    st.write(f"📝 Creating Jira {issue_type}: {summary}")

    url = f"{JIRA_BASE_URL}/rest/api/3/issue"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    auth = (JIRA_EMAIL, JIRA_API_TOKEN)

    # Detect allowed issue types
    issue_types = get_valid_issue_types()
    if issue_type not in issue_types:
        st.warning(f"⚠️ Issue type '{issue_type}' not found. Falling back to 'Task'.")
        issue_type = "Epic"

    issue_type_name = "Task" if parent_id else issue_type

    payload = {
        "fields": {
            "project": {"key": JIRA_PROJECT_KEY},
            "summary": summary,
            "description": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {
                                "type": "text",
                                "text": description
                            }
                        ]
                    }
                ]
            },
            "issuetype": {"name": issue_type_name}
        }
    }

    if parent_id:
        payload["fields"]["parent"] = {"key": parent_id}

    response = requests.post(url, json=payload, headers=headers, auth=auth)

    if response.status_code == 201:
        issue_key = response.json().get('key')
        st.success(f"✅ Created Jira {issue_type_name}: {issue_key}")
        return issue_key
    else:
        st.error(f"❌ Failed to create Jira {issue_type_name}: {summary}")
        st.code(response.text)
        return None

# === GitHub Branch Creation ===
def create_github_branch(branch_name, base="main"):
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(GITHUB_REPO)

    try:
        source = repo.get_branch(base)
    except Exception as e:
        st.error(f"⚠️ Could not find base branch '{base}'. Check if it exists in your GitHub repo.")
        st.stop()

    repo.create_git_ref(ref=f"refs/heads/{branch_name}", sha=source.commit.sha)

# === Streamlit UI ===
st.set_page_config(page_title="Project Planning Automation (Groq)", layout="wide")
st.title("🧠 Project Planning Automation (Groq + Streamlit)")

uploaded_file = st.file_uploader("📂 Upload your project doc (.pdf, .docx, .txt)", type=['pdf', 'docx', 'txt'])

if uploaded_file:
    with st.spinner("📖 Reading and analyzing..."):
        content = extract_text_from_file(uploaded_file)
        llama_response = analyze_with_groq(content)

    try:
        # Extract JSON from text using regex
        match = re.search(r"\{[\s\S]*\}", llama_response)
        if not match:
            raise ValueError("No JSON found in response.")
        clean_json = match.group()
        task_map = json.loads(clean_json)

    except Exception as e:
        st.error("⚠️ Groq model returned invalid JSON. Here's the raw output:")
        st.code(llama_response)
        st.stop()

    st.subheader("📋 Review Extracted Tasks")
    for main_task, sub_tasks in task_map.items():
        with st.expander(f"📌 {main_task}"):
            for sub in sub_tasks:
                st.markdown(f"- [ ] {sub}")

    if st.button("✅ Confirm & Create Jira + GitHub"):
        with st.spinner("⏳ Creating Jira tickets and GitHub branches..."):
            for main_task, sub_tasks in task_map.items():
                # ✅ Use "Task" instead of "Story"
                main_key = create_jira_task(main_task, "Created from Groq response", "Epic")
                create_github_branch(main_task.replace(" ", "-").lower())

                for sub in sub_tasks:
                    sub_key = create_jira_task(sub, f"Sub-task of {main_key}", "Task", parent_id=main_key)
                    create_github_branch(sub.replace(" ", "-").lower())
        st.success("🎉 Jira tickets and GitHub branches created!")

