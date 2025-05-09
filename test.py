import docx2txt
import os


DOCX_PATH = "project.docx"

def extract_text_from_docx(docx_path):
    """
    Extracts text from a .docx file and returns it as a string.
    """
    text = docx2txt.process(docx_path)
    return text

def prrse_tasks(text):
    lines = text.split('\n')
    return [line for line in lines if line.strip() != '']

def run_pipeline(docx_path):
    # Extract text from the .docx file
    text = extract_text_from_docx(docx_path)
    
    # Parse tasks from the extracted text
    tasks = prrse_tasks(text)
    print("Tasks extracted from the document:")
    for task in tasks:
        print(task)
   

if __name__ == "__main__":
    run_pipeline(DOCX_PATH)
#     run_pipeline(file_path)