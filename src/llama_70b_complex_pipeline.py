
import os
import sys
import time
import csv
import datetime
import hashlib
import logging
from concurrent.futures import ThreadPoolExecutor
from pdf_processor_min_flow import extract_text_from_pdf, split_text_by_tokens
from api_handler import enhanced_flow_extraction, check_ollama_server
from task_definitions_min_flow import get_prompts
from config import get_pdf_folder, ensure_directories, validate_setup
from flow_scoring import apply_flow_scoring

# ✅ Configure logging
logging.basicConfig(
    filename="debug.log",
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# ✅ Files for storing results
RESULTS_FILE = "min_flow_results.csv"
TIMING_RESULTS_FILE = "min_flow_timing_results.csv"

def log_message(level, message):
    """🔥 Logs messages and prints them in real-time."""
    print(message)
    getattr(logging, level)(message)

def calculate_task_hash(pdf_text, task_prompt):
    """🔑 Generate a unique hash based on the PDF text and the task prompt."""
    combined_string = pdf_text + task_prompt  # Combine text + prompt
    return hashlib.sha256(combined_string.encode()).hexdigest()

def load_existing_results():
    """📂 Load existing results to avoid redundant processing."""
    existing_files = set()
    if os.path.exists(RESULTS_FILE):
        with open(RESULTS_FILE, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                existing_files.add(row['filename'])
    return existing_files

def save_extracted_chunks(pdf_file, chunks):
    """Save extracted text chunks to a file for debugging."""
    base_name = os.path.splitext(pdf_file)[0]
    out_path = f"extracted_chunks_{base_name}.txt"
    with open(out_path, "w", encoding="utf-8") as f:
        for i, chunk in enumerate(chunks, 1):
            f.write(f"--- Chunk {i} ---\n{chunk}\n\n")

def load_existing_chunks(pdf_file):
    """📂 Load previously extracted chunks from file if available.
    
    Returns:
        list of str: Chunks if file exists, None otherwise
    """
    base_name = os.path.splitext(pdf_file)[0]
    chunk_file = f"extracted_chunks_{base_name}.txt"
    
    if not os.path.exists(chunk_file):
        return None
    
    try:
        with open(chunk_file, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Parse chunks separated by "--- Chunk N ---"
        chunks = []
        parts = content.split("--- Chunk ")
        for part in parts[1:]:  # Skip first empty part before first chunk
            # Extract chunk content (skip the "N ---\n" header)
            chunk_content = part.split("---\n", 1)[1].strip()
            if chunk_content:
                chunks.append(chunk_content)
        
        print(f"   📂 Loaded {len(chunks)} existing chunks from {chunk_file}")
        return chunks
    except Exception as e:
        print(f"   ⚠️ Error loading chunks from {chunk_file}: {e}")
        return None

def load_cached_text(pdf_file):
    """📄 Load cached extracted text if available - DISABLED to avoid chunk corruption
    
    The cached chunks files contain chunk markers that interfere with re-chunking.
    Always extract fresh from PDF to ensure proper chunking.
    """
    # Caching disabled - always extract fresh from PDF
    return None

def process_file_v11(pdf_file, pdf_folder, existing_results):
    """📄 V11 Enhanced: Process a single PDF file using enhanced flow extraction.
    
    Uses optimized baseline prompts for extraction.
    Uses smart chunking and enhanced text analysis.
    """
    pdf_path = os.path.join(pdf_folder, pdf_file)
    
    # ✅ Check if the file was already processed FIRST (before expensive PDF extraction)
    if pdf_file in existing_results:
        # Skip if we already have a good result
        print(f"   ⏩ Already processed. Skipping...")
        return None

    log_message("info", f"📂 Processing {pdf_file}...")
    start_file_time = time.time()

    # ✅ V15.3: Try to load existing chunks first (efficiency optimization)
    chunks = load_existing_chunks(pdf_file)
    
    if chunks:
        # Chunks already exist - reconstruct full text and skip extraction
        text = "\n\n".join(chunks)  # Reconstruct full document text
        print(f"   ✅ Using {len(chunks)} existing chunks (skipped PDF extraction)")
    else:
        # No existing chunks - extract from PDF
        print(f"   📖 Extracting text from PDF...")
        text = extract_text_from_pdf(pdf_path)
        if not text:
            print(f"   ⚠️ No text extracted from {pdf_file}. Skipping...")
            return None
        
        # ✅ Create chunks and save for future reuse
        from api_handler import smart_chunking_strategy
        chunks = smart_chunking_strategy(text, filename=pdf_file)
        save_extracted_chunks(pdf_file, chunks)
        print(f"   💾 Created and saved {len(chunks)} chunks")

    print(f"   🔍 Analyzing for minimum flow requirements...")
    
    # 🎯 Use optimized baseline prompts
    prompts = get_prompts()
    
    # V16.2 FIX: Simple direct extraction for Project_Name (no chunking/scoring needed!)
    # Project names appear early in documents, just send first 5000 chars to LLM directly
    name_text = text[:5000]
    name_task = prompts["Project_Name"]
    
    # Direct LLM call without chunking
    from api_handler import OLLAMA_URL
    import requests
    import json
    
    payload = {
        "model": "llama3.3:70b",
        "prompt": f"{name_task}\n\nDocument:\n{name_text}",
        "stream": False,
        "options": {
            "temperature": 0.1,
            "top_p": 0.9,
            "num_ctx": 8192
        }
    }
    
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=60)
        response.raise_for_status()
        result_text = response.json()["response"].strip()
        
        # Parse JSON response
        if result_text.startswith("{"):
            name_result = json.loads(result_text)
        elif "```json" in result_text:
            json_match = re.search(r'```json\s*\n(.*?)\n```', result_text, re.DOTALL)
            if json_match:
                name_result = json.loads(json_match.group(1))
            else:
                name_result = {"value": "Not mentioned", "inferred_context": "Parse error", "exact_sentences": "Not mentioned"}
        else:
            name_result = {"value": "Not mentioned", "inferred_context": "Invalid response", "exact_sentences": "Not mentioned"}
    except Exception as e:
        print(f"⚠️ Project name extraction error: {e}")
        name_result = {"value": "Not mentioned", "inferred_context": "Extraction failed", "exact_sentences": "Not mentioned"}
    
    print(f"   🏷️  Project Name extracted: {name_result.get('value', 'Not mentioned')}")
    
    # V16.2 FIX: Simple direct extraction for Project_Location (no chunking/scoring needed!)
    location_text = text[:5000]
    location_task = prompts["Project_Location"]
    
    payload = {
        "model": "llama3.3:70b",
        "prompt": f"{location_task}\n\nDocument:\n{location_text}",
        "stream": False,
        "options": {
            "temperature": 0.1,
            "top_p": 0.9,
            "num_ctx": 8192
        }
    }
    
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=60)
        response.raise_for_status()
        result_text = response.json()["response"].strip()
        
        if result_text.startswith("{"):
            location_result = json.loads(result_text)
        elif "```json" in result_text:
            json_match = re.search(r'```json\s*\n(.*?)\n```', result_text, re.DOTALL)
            if json_match:
                location_result = json.loads(json_match.group(1))
            else:
                location_result = {"value": "Not mentioned", "inferred_context": "Parse error", "exact_sentences": "Not mentioned"}
        else:
            location_result = {"value": "Not mentioned", "inferred_context": "Invalid response", "exact_sentences": "Not mentioned"}
    except Exception as e:
        print(f"⚠️ Location extraction error: {e}")
        location_result = {"value": "Not mentioned", "inferred_context": "Extraction failed", "exact_sentences": "Not mentioned"}
    
    print(f"   📍 Location extracted: {location_result.get('value', 'Not mentioned')}")
    
    # 🔧 Validate location result - remove flow values if present
    import re
    location_value = location_result.get('value', '')
    # If location contains only flow values (numbers + cfs/cms), mark as not found
    if re.match(r'^[\d,\.]+\s*(cfs|cms|cusecs|cubic feet)?\s*$', location_value, re.IGNORECASE):
        location_result['value'] = 'Not mentioned'
        location_result['inferred_context'] = 'Location extraction returned flow value instead of geographic location.'
        location_result['exact_sentences'] = 'Not mentioned'
    
    # 🔧 Validate name result - remove flow values if present
    name_value = name_result.get('value', '')
    if re.match(r'^[\d,\.]+\s*(cfs|cms|cusecs|cubic feet|dsf|generation|hour)\s*$', name_value, re.IGNORECASE):
        name_result['value'] = 'Not mentioned'
        name_result['inferred_context'] = 'Project name extraction returned flow value.'
        name_result['exact_sentences'] = 'Not mentioned'
    
    # Extract Minimum Flow
    enhanced_task = prompts["Minimum_Flow"]
    
    # ⚠️ V16.4 FIX: Get ALL candidates without pre-selection to avoid double-scoring interference
    # Use internal function to bypass ask_ollama_to_select_best()
    from api_handler import process_document_with_smart_chunking_no_selection
    all_candidates = process_document_with_smart_chunking_no_selection(
        document_text=text,
        prompt=enhanced_task,
        filename=pdf_file
    )
    
    # 🎯 Apply scoring mechanism ONCE to select best minimum flow (no interference)
    result = apply_flow_scoring(all_candidates, document_name=pdf_file)

    file_time = time.time() - start_file_time

    print(f"   ⏱️  Completed in {file_time:.2f} seconds")
    print(f"   💧 Found: {result.get('value', 'Not mentioned')}")

    # ✅ Save results in the expected format
    final_values = {
        'Project_Name': name_result,
        'Project_Location': location_result,
        'Minimum_Flow': result
    }
    
    save_results(pdf_file, final_values, {})
    
    # ✅ Save timing results
    save_timing_results_v11(pdf_file, file_time, result)
    
    return {
        'filename': pdf_file,
        'result': result,
        'processing_time': file_time
    }

def save_full_document(pdf_file, text):
    """Save full document text for debugging (replaces chunk saving)."""
    base_name = os.path.splitext(pdf_file)[0]
    out_path = f"extracted_chunks_{base_name}.txt"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(f"--- Full Document Text ---\n{text}\n\n")

def save_timing_results_v11(pdf_file, processing_time, result):
    """📊 Save V11 timing and result information."""
    if not os.path.exists(TIMING_RESULTS_FILE):
        with open(TIMING_RESULTS_FILE, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['filename', 'processing_time_seconds', 'result_value', 'has_result', 'timestamp'])
    
    # Append timing data
    with open(TIMING_RESULTS_FILE, 'a', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([
            pdf_file,
            f"{processing_time:.2f}",
            result.get('value', 'Not mentioned'),
            'Yes' if result.get('value', 'Not mentioned') not in ['Not mentioned', 'Error'] else 'No',
            datetime.datetime.now().isoformat()
        ])








def save_results(pdf_file, final_values, task_hashes=None):
    """📂 Save extracted results in clean CSV format (One row per project)."""
    
    import re
    
    # Get project name from LLM extraction (or fallback to cleaned filename)
    extracted_name = final_values.get('Project_Name', {}).get('value', 'Not mentioned')
    if extracted_name and extracted_name != 'Not mentioned':
        project_name = extracted_name
    else:
        # Fallback: Clean project name from filename
        project_name = pdf_file.replace('.pdf', '')
        project_name = re.sub(r'_\d{8}', '', project_name)
        project_name = re.sub(r'_\d{6}', '', project_name)
        project_name = re.sub(r'\d{8}', '', project_name)
        project_name = re.sub(r'_License.*', '', project_name)
        project_name = re.sub(r'_WCM.*', '', project_name)
        project_name = re.sub(r'_Manual.*', '', project_name)
        project_name = re.sub(r'_Redacted', '', project_name, flags=re.IGNORECASE)
        project_name = re.sub(r'_OCT\d{4}', '', project_name)
        project_name = project_name.replace('_', ' ').strip()
    
    # Read existing results
    rows = []
    headers = ["Row_Number", "Project_Name", "filename", "Project_Location", 
               "Minimum_Flow_Value", "Minimum_Flow_Inferred_Context", 
               "Minimum_Flow_Exact_Sentences"]
    
    if os.path.exists(RESULTS_FILE):
        with open(RESULTS_FILE, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            rows = list(reader)
    
    # Check if this project already exists
    found_existing = False
    for i, row in enumerate(rows):
        if row["filename"] == pdf_file:
            # Update existing row
            rows[i]["Project_Location"] = final_values["Project_Location"]["value"]
            rows[i]["Minimum_Flow_Value"] = final_values["Minimum_Flow"]["value"]
            rows[i]["Minimum_Flow_Inferred_Context"] = final_values["Minimum_Flow"]["inferred_context"]
            rows[i]["Minimum_Flow_Exact_Sentences"] = final_values["Minimum_Flow"]["exact_sentences"]
            found_existing = True
            break
    
    if not found_existing:
        # Add new row
        new_row = {
            "Row_Number": len(rows) + 1,
            "Project_Name": project_name,
            "filename": pdf_file,
            "Project_Location": final_values["Project_Location"]["value"],
            "Minimum_Flow_Value": final_values["Minimum_Flow"]["value"],
            "Minimum_Flow_Inferred_Context": final_values["Minimum_Flow"]["inferred_context"],
            "Minimum_Flow_Exact_Sentences": final_values["Minimum_Flow"]["exact_sentences"]
        }
        rows.append(new_row)

    # Save clean CSV with proper quoting
    with open(RESULTS_FILE, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"✅ Results saved to {RESULTS_FILE}")
    print(f"📊 Total projects: {len(rows)}")


def save_timing_results(pdf_file, total_chunks, avg_chunk_time, file_time, task_times):
    """📂 Saves processing time results to a CSV file with per-task execution times."""
    headers = ["Timestamp", "Filename", "Executed Tasks", "Total Chunks", "Avg Chunk Time (s)", "Total File Time (s)", "Task Times"]
    
    # ✅ Get the current timestamp
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

    # ✅ Extract which tasks were executed from results.csv
    if os.path.exists(RESULTS_FILE):
        with open(RESULTS_FILE, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if row['filename'] == pdf_file:
                    executed_tasks_str = "Minimum_Flow"
                    break
            else:
                executed_tasks_str = "Unknown"
    else:
        executed_tasks_str = "Unknown"

    # ✅ Convert per-task execution times into a string
    task_time_str = "; ".join([f"{task}: {sum(times) / len(times):.2f}s" for task, times in task_times.items() if times])

    data = [timestamp, pdf_file, executed_tasks_str, total_chunks, round(avg_chunk_time, 2), round(file_time, 2), task_time_str]

    file_exists = os.path.exists(TIMING_RESULTS_FILE)

    with open(TIMING_RESULTS_FILE, mode='a', newline='') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(headers)  # Write headers if file doesn't exist
        writer.writerow(data)


def main():
    """🚀 Main function to process PDFs and extract minimum flow data.
    
    Optimized pipeline for minimum flow extraction.
    Uses baseline prompts with enhanced text processing.
    """
    print("🔍 Starting minimum flow extraction pipeline...")
    print("=" * 60)

    # Validate setup before starting
    ensure_directories()
    if not validate_setup():
        return

    # Check Ollama server with auto-start option
    print("🔧 Checking Ollama server...")
    try:
        from ollama_helper import check_and_start_ollama
        if not check_and_start_ollama(auto_start=True):
            print("❌ ERROR: Ollama could not be started!")
            print("💡 MANUAL FIX:")
            print("   1. Open a new terminal")
            print("   2. Run: ollama serve &")
            print("   3. Run this script again")
            return
    except ImportError:
        # Fallback to original check
        if not check_ollama_server():
            print("❌ ERROR: Ollama is not responding!")
            print("💡 QUICK FIX: Run 'ollama serve &' in another terminal")
            return

    pdf_folder = get_pdf_folder()
    pdf_files = sorted([file for file in os.listdir(pdf_folder) if file.endswith('.pdf')])
    
    # V16.3: Process first 5 files for testing
    pdf_files = pdf_files[:50]  
    print(f"📚 V16.3: Processing {len(pdf_files)} documents from: {pdf_folder}")
    for i, pdf_file in enumerate(pdf_files, 1):
        print(f"  {i}. {pdf_file}")
    print("=" * 60)
    
    existing_results = load_existing_results()

    for i, pdf_file in enumerate(pdf_files, 1):
        print(f"\n🚀 Processing {i}/{len(pdf_files)}: {pdf_file}")
        process_file_v11(pdf_file, pdf_folder, existing_results)
        print(f"✅ Completed {i}/{len(pdf_files)}")

    print("\n" + "=" * 60)
    print("🎯 PIPELINE COMPLETED!")
    print(f"📄 Results saved to: {RESULTS_FILE}")
    print("💡 Open the CSV file to view all results")
    print("=" * 60)

if __name__ == "__main__":
    main()
