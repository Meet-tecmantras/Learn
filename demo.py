import os
from llama_cpp import Llama
from docx import Document
import PyPDF2

# --- Config ---
MODEL_PATH = "./llama-3.1.gguf"  # Adjust this path to your actual model file
CHUNK_WORDS = 500
MAX_TOKENS = 512

# --- Load LLaMA model ---
llm = Llama(model_path=MODEL_PATH, n_ctx=4096)

# --- File reading functions ---
def read_txt(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()

def read_docx(file_path):
    doc = Document(file_path)
    return "\n".join([para.text for para in doc.paragraphs])

def read_pdf(file_path):
    with open(file_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        return "\n".join([page.extract_text() or "" for page in reader.pages])

def load_document(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".txt":
        return read_txt(file_path)
    elif ext == ".docx":
        return read_docx(file_path)
    elif ext == ".pdf":
        return read_pdf(file_path)
    else:
        raise ValueError("Unsupported file type: " + ext)

# --- Chunking function ---
def chunk_text(text, chunk_size=CHUNK_WORDS):
    words = text.split()
    for i in range(0, len(words), chunk_size):
        yield " ".join(words[i:i + chunk_size])

# --- Process document ---
def process_and_save(file_path):
    content = load_document(file_path)
    summaries = []
    
    for i, chunk in enumerate(chunk_text(content)):
        prompt = f"Summarize the following content:\n\n{chunk}\n\nSummary:"
        response = llm(prompt=prompt, max_tokens=MAX_TOKENS, temperature=0.7)
        summary = response["choices"][0]["text"].strip()
        summaries.append(f"--- Summary {i+1} ---\n{summary}\n")
        print(f"Processed chunk {i+1}")

    # Save summaries to file
    summary_filename = os.path.splitext(file_path)[0] + "_summary.txt"
    with open(summary_filename, "w", encoding="utf-8") as f:
        f.write("\n".join(summaries))

    print(f"\n✅ Summaries saved to: {summary_filename}")

# --- Main ---
if __name__ == "__main__":
    file_name = input("Enter the filename (e.g., report.pdf): ").strip()
    file_path = os.path.join(os.getcwd(), file_name)

    if not os.path.isfile(file_path):
        print("❌ File not found in the current folder.")
    else:
        try:
            process_and_save(file_path)
        except Exception as e:
            print("⚠️ Error:", e)
