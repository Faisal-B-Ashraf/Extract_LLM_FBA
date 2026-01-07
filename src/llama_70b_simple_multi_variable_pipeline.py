"""
Pipeline 3: Simple Multi-Variable Extraction with Llama 3.3 70B

Purpose: Extract multiple variables using simple prompts WITHOUT scoring mechanisms.
Compare against Pipeline 1 (sophisticated targeted extraction) to validate where
complexity improves accuracy.

Variables extracted:
- Project/Dam name
- Owner/Operator information
- Geographic location (county, city, river)
- Generation capacity
- Plant type (run-of-river vs. peaking)
- Licensing dates
- Key stakeholders
- Project costs
- Migratory fish species
- Minimum flow requirements

Approach:
- No chunk pre-scoring (simple sequential chunking)
- No post-extraction scoring (apply_flow_scoring)
- Simple, direct prompts
- Single-pass extraction per variable
"""

import os
import sys
import time
import csv
import datetime
import requests
import json
import logging
from pdf_processor_min_flow import extract_text_from_pdf
from config import get_pdf_folder, ensure_directories, validate_setup
from task_definitions_simple_multi_variable import get_simple_prompt, get_all_variables

# Configure logging
logging.basicConfig(
    filename="simple_multi_variable_pipeline.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Output files
RESULTS_FILE = "multi_variable_simple_results.csv"
TIMING_FILE = "multi_variable_simple_timing.csv"

# Ollama configuration
OLLAMA_HOST = "localhost:11434"
OLLAMA_URL = f"http://{OLLAMA_HOST}/api/generate"
MODEL_NAME = "llama3.3:70b"

# Get variables from task definitions
VARIABLES = get_all_variables()

def log_message(level, message):
    """Log and print messages."""
    print(message)
    getattr(logging, level)(message)

def simple_chunk_text(text, chunk_size=8000, overlap=1000):
    """Simple chunking without scoring - just split text."""
    chunks = []
    start = 0
    text_length = len(text)
    
    while start < text_length:
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap
    
    return chunks

def call_ollama_simple(prompt, document_chunk):
    """Simple API call to Ollama without retries or complex handling."""
    
    full_prompt = f"""{prompt}

Document text:
{document_chunk}

Answer:"""
    
    payload = {
        "model": MODEL_NAME,
        "prompt": full_prompt,
        "stream": False,
        "options": {
            "temperature": 0.1,
            "num_predict": 200
        }
    }
    
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=120)
        response.raise_for_status()
        result = response.json()
        return result.get("response", "").strip()
    except Exception as e:
        log_message("error", f"API error: {str(e)}")
        return "Error"

def extract_variable_simple(document_text, variable_name):
    """Extract a single variable using simple approach."""
    
    # Chunk the document
    chunks = simple_chunk_text(document_text)
    log_message("info", f"   Split into {len(chunks)} chunks for {variable_name}")
    
    # Get prompt for this variable
    prompt = get_simple_prompt(variable_name)
    
    # Try first 5 chunks (simple heuristic - early chunks often have metadata)
    best_answer = "Not mentioned"
    
    for i, chunk in enumerate(chunks[:5]):
        log_message("info", f"   Checking chunk {i+1}/5 for {variable_name}...")
        answer = call_ollama_simple(prompt, chunk)
        
        # If we get a real answer (not "Not mentioned" or "Error"), use it
        if answer and answer not in ["Not mentioned", "Error", "Not found", "None"]:
            best_answer = answer
            log_message("info", f"   ✓ Found in chunk {i+1}: {answer[:100]}...")
            break
    
    return best_answer

def process_single_pdf(pdf_file, pdf_folder):
    """Process one PDF and extract all variables."""
    
    pdf_path = os.path.join(pdf_folder, pdf_file)
    log_message("info", f"\n{'='*60}")
    log_message("info", f"Processing: {pdf_file}")
    log_message("info", f"{'='*60}")
    
    start_time = time.time()
    
    # Check for cached chunks first
    base_name = os.path.splitext(pdf_file)[0]
    chunks_file = os.path.join(os.path.dirname(pdf_path), f"extracted_chunks_{base_name}.txt")
    
    if os.path.exists(chunks_file):
        log_message("info", f"✓ Found cached chunks: {chunks_file}")
        log_message("info", "📄 Loading cached text...")
        try:
            with open(chunks_file, 'r', encoding='utf-8') as f:
                document_text = f.read()
            log_message("info", f"✓ Loaded {len(document_text)} characters from cache")
        except Exception as e:
            log_message("warning", f"⚠️  Could not read cached chunks: {e}")
            log_message("info", "📄 Extracting text from PDF...")
            document_text = extract_text_from_pdf(pdf_path)
    else:
        # Extract text from PDF
        log_message("info", "📄 Extracting text from PDF...")
        document_text = extract_text_from_pdf(pdf_path)
    
    if not document_text:
        log_message("warning", f"⚠️  Could not extract text from {pdf_file}")
        return None
    
    log_message("info", f"✓ Ready to process {len(document_text)} characters")
    
    # Extract each variable
    results = {"filename": pdf_file}
    variable_times = {}
    
    for variable in VARIABLES:
        var_start = time.time()
        log_message("info", f"\n🔍 Extracting: {variable}")
        
        value = extract_variable_simple(document_text, variable)
        results[variable] = value
        
        var_time = time.time() - var_start
        variable_times[variable] = var_time
        
        log_message("info", f"   Result: {value[:100] if len(value) > 100 else value}")
        log_message("info", f"   Time: {var_time:.2f}s")
    
    total_time = time.time() - start_time
    log_message("info", f"\n✅ Completed {pdf_file} in {total_time:.2f} seconds")
    
    return results, total_time, variable_times

def save_results(results_list):
    """Save all results to CSV."""
    
    if not results_list:
        return
    
    fieldnames = ["filename"] + VARIABLES
    
    with open(RESULTS_FILE, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results_list)
    
    log_message("info", f"✅ Saved {len(results_list)} results to {RESULTS_FILE}")

def save_timing(timing_list):
    """Save timing information to CSV."""
    
    if not timing_list:
        return
    
    with open(TIMING_FILE, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=timing_list[0].keys())
        writer.writeheader()
        writer.writerows(timing_list)
    
    log_message("info", f"✅ Saved timing data to {TIMING_FILE}")

def main():
    """Main pipeline execution."""
    
    log_message("info", "\n" + "="*70)
    log_message("info", "🚀 PIPELINE 3: Simple Multi-Variable Extraction with 70B")
    log_message("info", "="*70)
    
    # Validate setup
    log_message("info", "\n📋 Validating setup...")
    validate_setup()
    
    pdf_folder = get_pdf_folder()
    pdf_files = sorted([f for f in os.listdir(pdf_folder) if f.endswith('.pdf')])
    
    log_message("info", f"✓ Found {len(pdf_files)} PDF files")
    log_message("info", f"✓ Model: {MODEL_NAME}")
    log_message("info", f"✓ Variables to extract: {len(VARIABLES)}")
    log_message("info", f"✓ Approach: Simple prompts, no scoring")
    
    # Process all PDFs
    all_results = []
    all_timing = []
    
    for i, pdf_file in enumerate(pdf_files, 1):
        log_message("info", f"\n\n{'#'*70}")
        log_message("info", f"# Processing {i}/{len(pdf_files)}: {pdf_file}")
        log_message("info", f"{'#'*70}")
        
        result = process_single_pdf(pdf_file, pdf_folder)
        
        if result:
            extracted_data, total_time, variable_times = result
            all_results.append(extracted_data)
            
            timing_data = {
                "filename": pdf_file,
                "total_time_seconds": f"{total_time:.2f}",
                "timestamp": datetime.datetime.now().isoformat()
            }
            # Add individual variable times
            for var, var_time in variable_times.items():
                timing_data[f"{var}_time"] = f"{var_time:.2f}"
            
            all_timing.append(timing_data)
            
            # Save incrementally
            save_results(all_results)
            save_timing(all_timing)
    
    # Final summary
    log_message("info", "\n" + "="*70)
    log_message("info", "🎯 PIPELINE 3 COMPLETED!")
    log_message("info", "="*70)
    log_message("info", f"📊 Total PDFs processed: {len(all_results)}")
    log_message("info", f"📄 Results file: {RESULTS_FILE}")
    log_message("info", f"⏱️  Timing file: {TIMING_FILE}")
    log_message("info", "="*70)

if __name__ == "__main__":
    main()
