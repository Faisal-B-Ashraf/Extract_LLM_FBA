import time
import pdfplumber
import re
import unicodedata



def extract_text_from_pdf(pdf_path):
    """Extracts text from a PDF file using pdfplumber and cleans it."""
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"  # Ensure each page is separated properly
    except Exception as e:
        print(f"❌ Error reading {pdf_path}: {e}")
    
    return clean_text(text)  # Clean text before returning


def clean_text(text):
    """Removes extra spaces, non-printable characters, and corrupted symbols."""
    text = unicodedata.normalize("NFKD", text)  # Normalize unicode (fixes some weird characters)
    text = re.sub(r'\s+', ' ', text).strip()  # Replace multiple spaces/newlines with a single space
    text = re.sub(r'[^a-zA-Z0-9.,;:\'"\s-]', '', text)  # Remove all non-text symbols except punctuation
    return text


def split_text_by_tokens(text, word_length=1000, overlap=100):
    """Splits text into chunks of given word length with overlap."""
    start_time = time.time()  # Start time for debugging

    words = text.split()  # Split text into words
    result = []
    start = 0
    n = len(words)
    
    if n < word_length:
        return [text]  # If the text is smaller than chunk size, return as-is
    
    while start < n:
        end = min(start + word_length, n)  # Define chunk range
        result.append(" ".join(words[start:end]))  # Join words into a string
        start = end - overlap if end - overlap > start else end  # Adjust for overlap

    end_time = time.time()  # End time for debugging
    print(f"✅ Splitting complete. ⏳ Time taken: {end_time - start_time:.2f} seconds")
    print(f"📄 Total chunks created: {len(result)}")

    return result
