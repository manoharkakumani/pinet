import os
import json
import requests
import pandas as pd
from pathlib import Path

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

try:
    import docx  # python-docx
except ImportError:
    docx = None

def load_knowledge(path_or_url: str, chunk_size: int = 500) -> str:
    """Load knowledge from various formats with chunking."""
    if path_or_url.startswith("http://") or path_or_url.startswith("https://"):
        return _load_url(path_or_url, chunk_size)

    ext = Path(path_or_url).suffix.lower()

    if ext == ".pdf" and fitz:
        return _load_pdf(path_or_url, chunk_size)
    elif ext == ".docx" and docx:
        return _load_docx(path_or_url, chunk_size)
    elif ext == ".csv":
        return _load_csv(path_or_url, chunk_size)
    elif ext in [".json"]:
        return _load_json(path_or_url, chunk_size)
    elif ext in [".xlsx", ".xls"]:
        return _load_excel(path_or_url, chunk_size)
    elif ext in [".txt", ".md"]:
        return _load_text(path_or_url, chunk_size)
    else:
        raise ValueError(f"Unsupported knowledge format: {path_or_url}")

# Function to process PDF in chunks
def _load_pdf(path, chunk_size: int):
    doc = fitz.open(path)
    full_text = "\n".join([page.get_text() for page in doc])
    
    # Split the full text into chunks of the specified size
    return [full_text[i:i+chunk_size] for i in range(0, len(full_text), chunk_size)]

# Function to process DOCX in chunks
def _load_docx(path, chunk_size: int):
    doc = docx.Document(path)
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    
    # Split paragraphs into chunks of size chunk_size
    chunks = []
    current_chunk = ""
    for paragraph in paragraphs:
        if len(current_chunk + paragraph) > chunk_size:
            chunks.append(current_chunk)
            current_chunk = paragraph
        else:
            current_chunk += paragraph
    if current_chunk:
        chunks.append(current_chunk)
    
    return chunks

# Function to process CSV in chunks
def _load_csv(path, chunk_size: int):
    df = pd.read_csv(path)
    chunks = []
    for start in range(0, len(df), chunk_size):
        chunk = df.iloc[start:start+chunk_size]
        chunks.append(chunk.to_markdown(index=False))
    return chunks

# Function to process Excel in chunks
def _load_excel(path, chunk_size: int):
    df = pd.read_excel(path)
    chunks = []
    for start in range(0, len(df), chunk_size):
        chunk = df.iloc[start:start+chunk_size]
        chunks.append(chunk.to_markdown(index=False))
    return chunks

# Function to process JSON in chunks
def _load_json(path, chunk_size: int):
    with open(path) as f:
        data = json.load(f)
    
    # Convert the entire JSON to a string and split into chunks
    json_str = json.dumps(data, indent=2)
    return [json_str[i:i+chunk_size] for i in range(0, len(json_str), chunk_size)]

# Function to process text files in chunks
def _load_text(path, chunk_size: int):
    with open(path, encoding="utf-8") as f:
        text = f.read()
    
    # Split text into chunks of chunk_size
    return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

# Function to load URL content and chunk it
def _load_url(url, chunk_size: int):
    try:
        resp = requests.get(url)
        resp.raise_for_status()
        full_text = resp.text
        # Split the content into chunks of chunk_size
        return [full_text[i:i+chunk_size] for i in range(0, len(full_text), chunk_size)]
    except Exception as e:
        return [f"[Failed to load {url}: {e}]"]
