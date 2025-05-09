import docx2txt
import subprocess

DOCX_PATH = "demo.docx"
OLLAMA_MODEL_NAME = "llama3.1"  # Use your installed model name from `ollama list`

def extract_text_from_docx(docx_path):
    """Extracts text from a .docx file and returns it as a string."""
    return docx2txt.process(docx_path)

def prrse_tasks(text):
    """Parses lines and filters out empty ones."""
    lines = text.split('\n')
    return [line for line in lines if line.strip() != '']

def clean_text(text):
    """Clean text to avoid encoding issues."""
    return text.encode("utf-8", errors="ignore").decode("utf-8", errors="ignore")

def summarize_with_ollama(text, model_name):
    """Sends text to the LLaMA model via Ollama and returns the summary."""
    prompt = f"""
You are a Jira Ticket Creation Expert.  
Your job is to read and analyze the content of the provided project document and extract the hierarchical structure of tasks involved, suitable for Jira ticketing.

Return strictly in the following JSON format:
{{
  "Main Task 1": {{
    "Sub-task 1.1": ["Sub-sub-task 1.1.1", "Sub-sub-task 1.1.2"],
    "Sub-task 1.2": []
  }},
  "Main Task 2": {{
    "Sub-task 2.1": [],
    "Sub-task 2.2": []
  }}
}}

Instructions:
- Identify **Main Tasks** and their **Sub-tasks**.
- If a sub-task has further breakdowns, include them as nested lists inside the respective sub-task key.
- If a sub-task has no further division, return an empty list `[]`.
- Return **only valid JSON**, with **no additional text**, **no explanation**, and **no formatting outside the JSON**.

Document:
\"\"\"
{text}
\"\"\"
"""

    result = subprocess.run(
        ["ollama", "run", model_name],
        input=prompt,
        capture_output=True,
        text=True,
        encoding='utf-8'  # fixes UnicodeDecodeError 
    )
    if result.returncode == 0:
        return result.stdout.strip()
    else:
        print("Error from Ollama:", result.stderr)
        return None

def run_pipeline(docx_path, model_name):
    text = extract_text_from_docx(docx_path)
    tasks = prrse_tasks(text)
    
    print("Tasks extracted from the document:")
    for task in tasks:
        print(task)

    print("\nGenerating summary using LLaMA...")
    cleaned_text = clean_text(text)
    summary = summarize_with_ollama(cleaned_text, model_name)

    if summary:
        print("\nSummary:")
        print(summary)
    else:
        print("Failed to generate summary.")

if __name__ == "__main__":
    run_pipeline(DOCX_PATH, OLLAMA_MODEL_NAME)
