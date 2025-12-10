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
from config import get_pdf_folder, ensure_directories, validate_setup, MODELS
from flow_scoring import apply_flow_scoring

# ✅ Configure logging
logging.basicConfig(
    filename="multi_model_debug.log",
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# 🤖 Model configurations to test (excluding 70B which is tested separately)
MODELS_TO_TEST = [
    {
        "name": MODELS["llama_8b"]["name"],
        "display_name": MODELS["llama_8b"]["display_name"],
        "results_file": "min_flow_results_llama3_8b.csv",
        "timing_file": "min_flow_timing_llama3_8b.csv"
    },
    {
        "name": MODELS["llama_3b"]["name"], 
        "display_name": MODELS["llama_3b"]["display_name"],
        "results_file": "min_flow_results_llama32_3b.csv",
        "timing_file": "min_flow_timing_llama32_3b.csv"
    },
    {
        "name": MODELS["gpt_oss_20b"]["name"],
        "display_name": MODELS["gpt_oss_20b"]["display_name"],
        "results_file": "min_flow_results_gpt_oss_20b.csv",
        "timing_file": "min_flow_timing_gpt_oss_20b.csv"
    }
]

def log_message(level, message):
    """🔥 Logs messages and prints them in real-time."""
    print(message)
    getattr(logging, level)(message)

def calculate_task_hash(pdf_text, task_prompt):
    """🔑 Generate a unique hash based on the PDF text and the task prompt."""
    combined_string = pdf_text + task_prompt  # Combine text + prompt
    return hashlib.sha256(combined_string.encode()).hexdigest()

def load_existing_results(results_file):
    """📂 Load existing results to avoid redundant processing."""
    existing_files = set()
    if os.path.exists(results_file):
        with open(results_file, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                existing_files.add(row['filename'])
    return existing_files

def ensure_all_texts_extracted(pdf_folder, pdf_files):
    """Ensure all PDFs have extracted text files. Extract any missing ones."""
    print("🔍 Checking for missing extracted text files...")
    
    missing_pdfs = []
    existing_count = 0
    
    for pdf_file in pdf_files:
        base_name = os.path.splitext(pdf_file)[0]
        
        # Check if extracted text exists
        extracted_file_path = f"extracted_chunks/extracted_chunks_{base_name}.txt"
        current_dir_path = f"extracted_chunks_{base_name}.txt"
        
        if os.path.exists(extracted_file_path) or os.path.exists(current_dir_path):
            existing_count += 1
        else:
            missing_pdfs.append(pdf_file)
    
    print(f"   ✅ Found {existing_count}/{len(pdf_files)} extracted text files")
    
    if missing_pdfs:
        print(f"   📄 Need to extract {len(missing_pdfs)} missing PDFs:")
        for pdf in missing_pdfs:
            print(f"      - {pdf}")
        print()
        
        # Extract missing PDFs
        for i, pdf_file in enumerate(missing_pdfs, 1):
            print(f"   🔄 Extracting {i}/{len(missing_pdfs)}: {pdf_file}")
            pdf_path = os.path.join(pdf_folder, pdf_file)
            
            try:
                text = extract_text_from_pdf(pdf_path)
                if text:
                    # Save extracted text
                    base_name = os.path.splitext(pdf_file)[0]
                    
                    # Create extracted_chunks directory if it doesn't exist
                    os.makedirs("extracted_chunks", exist_ok=True)
                    
                    # Save as full document text (simpler format)
                    out_path = f"extracted_chunks/extracted_chunks_{base_name}.txt"
                    with open(out_path, "w", encoding="utf-8") as f:
                        f.write(f"--- Full Document Text ---\n{text}\n\n")
                    
                    print(f"      ✅ Extracted and saved ({len(text):,} chars)")
                else:
                    print(f"      ⚠️ No text extracted from {pdf_file}")
            except Exception as e:
                print(f"      ❌ Error extracting {pdf_file}: {e}")
        
        print(f"   🎯 Text extraction completed for {len(missing_pdfs)} PDFs")
    else:
        print(f"   🎉 All PDFs already have extracted text files!")
    
    print()

def load_extracted_text(pdf_file):
    """Load previously extracted text from file if it exists, otherwise extract from PDF."""
    base_name = os.path.splitext(pdf_file)[0]
    
    # Check in extracted_chunks folder first
    extracted_file_path = f"extracted_chunks/extracted_chunks_{base_name}.txt"
    if os.path.exists(extracted_file_path):
        print(f"   📄 Loading cached extracted text...")
        with open(extracted_file_path, "r", encoding="utf-8") as f:
            content = f.read()
            # Extract the actual document text (skip the header)
            if "--- Full Document Text ---" in content:
                text = content.split("--- Full Document Text ---\n", 1)[1]
            elif "--- Chunk 1 ---" in content:
                # If it's chunked, combine all chunks
                chunks = []
                chunk_parts = content.split("--- Chunk ")[1:]  # Skip first empty part
                for chunk_part in chunk_parts:
                    chunk_text = chunk_part.split(" ---\n", 1)[1] if " ---\n" in chunk_part else chunk_part
                    chunks.append(chunk_text)
                text = "\n".join(chunks)
            else:
                text = content
            return text.strip()
    
    # Check in current directory
    extracted_file_path = f"extracted_chunks_{base_name}.txt"
    if os.path.exists(extracted_file_path):
        print(f"   📄 Loading cached extracted text from current directory...")
        with open(extracted_file_path, "r", encoding="utf-8") as f:
            content = f.read()
            if "--- Full Document Text ---" in content:
                text = content.split("--- Full Document Text ---\n", 1)[1]
            else:
                text = content
            return text.strip()
    
    # If no cached text exists, extract from PDF
    print(f"   📖 No cached text found, extracting from PDF...")
    return None

def save_extracted_chunks(pdf_file, chunks, model_name):
    """Save extracted text chunks to a file for debugging."""
    base_name = os.path.splitext(pdf_file)[0]
    safe_model_name = model_name.replace(":", "_").replace(".", "_")
    out_path = f"extracted_chunks_{base_name}_{safe_model_name}.txt"
    with open(out_path, "w", encoding="utf-8") as f:
        for i, chunk in enumerate(chunks, 1):
            f.write(f"--- Chunk {i} ---\n{chunk}\n\n")

def enhanced_flow_extraction_with_model(document_text, task, filename, model_name):
    """Modified version of enhanced_flow_extraction that accepts a model parameter."""
    from api_handler import smart_chunking_strategy
    import requests
    import json
    
    # Get chunks using the same strategy
    chunks = smart_chunking_strategy(document_text, filename=filename)
    
    # Process each chunk with the specified model
    all_results = []
    
    for i, chunk in enumerate(chunks):
        # Create the payload with the specified model
        payload = {
            "model": model_name,
            "prompt": f"{task}\n\nDocument text:\n{chunk}",
            "stream": False,
            "options": {
                "temperature": 0.1,
                "top_p": 0.9,
                "num_predict": 1000
            }
        }
        
        try:
            response = requests.post("http://localhost:11434/api/generate", 
                                   json=payload, 
                                   timeout=120)
            
            if response.status_code == 200:
                result = response.json()
                response_text = result.get("response", "").strip()
                all_results.append(response_text)
            else:
                print(f"   ⚠️ API Error for chunk {i+1}: {response.status_code}")
                all_results.append("Error")
                
        except Exception as e:
            print(f"   ⚠️ Exception for chunk {i+1}: {str(e)}")
            all_results.append("Error")
    
    # Combine and parse results (using same logic as original)
    combined_response = "\n".join([r for r in all_results if r != "Error"])
    
    # Parse the response to extract structured data
    result = {
        "value": "Not mentioned",
        "inferred_context": "No context provided",
        "exact_sentences": "No exact sentences found"
    }
    
    if combined_response and "Not mentioned" not in combined_response:
        lines = combined_response.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith("Value:"):
                result["value"] = line.replace("Value:", "").strip()
            elif line.startswith("Context:"):
                result["inferred_context"] = line.replace("Context:", "").strip()
            elif line.startswith("Exact Sentences:"):
                result["exact_sentences"] = line.replace("Exact Sentences:", "").strip()
    
    return result

def save_results_for_model(pdf_file, final_values, task_hashes=None, results_file=""):
    """📂 Save extracted results in clean CSV format for specific model."""
    
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
               "Minimum_Flow Value", "Minimum_Flow Inferred Context", 
               "Minimum_Flow Exact Sentences"]
    
    if os.path.exists(results_file):
        with open(results_file, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            rows = list(reader)
    
    # Check if this project already exists
    found_existing = False
    for i, row in enumerate(rows):
        if row["filename"] == pdf_file:
            # Update existing row
            rows[i]["Project_Location"] = final_values["Project_Location"]["value"]
            rows[i]["Minimum_Flow Value"] = final_values["Minimum_Flow"]["value"]
            rows[i]["Minimum_Flow Inferred Context"] = final_values["Minimum_Flow"]["inferred_context"]
            rows[i]["Minimum_Flow Exact Sentences"] = final_values["Minimum_Flow"]["exact_sentences"]
            found_existing = True
            break
    
    if not found_existing:
        # Add new row
        new_row = {
            "Row_Number": len(rows) + 1,
            "Project_Name": project_name,
            "filename": pdf_file,
            "Project_Location": final_values["Project_Location"]["value"],
            "Minimum_Flow Value": final_values["Minimum_Flow"]["value"],
            "Minimum_Flow Inferred Context": final_values["Minimum_Flow"]["inferred_context"],
            "Minimum_Flow Exact Sentences": final_values["Minimum_Flow"]["exact_sentences"]
        }
        rows.append(new_row)

    # Save clean CSV
    with open(results_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)

def save_timing_results_for_model(pdf_file, processing_time, result, timing_file, model_name):
    """📊 Save timing and result information for specific model."""
    if not os.path.exists(timing_file):
        with open(timing_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['filename', 'model', 'processing_time_seconds', 'result_value', 'has_result', 'timestamp'])
    
    # Append timing data
    with open(timing_file, 'a', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([
            pdf_file,
            model_name,
            f"{processing_time:.2f}",
            result.get('value', 'Not mentioned'),
            'Yes' if result.get('value', 'Not mentioned') not in ['Not mentioned', 'Error'] else 'No',
            datetime.datetime.now().isoformat()
        ])

def process_file_with_model(pdf_file, pdf_folder, model_config, existing_results):
    """📄 Process a single PDF file using specified model."""
    pdf_path = os.path.join(pdf_folder, pdf_file)
    model_name = model_config["name"]
    display_name = model_config["display_name"]
    
    # ✅ Check if the file was already processed
    if pdf_file in existing_results:
        print(f"   ⏩ Already processed with {display_name}. Skipping...")
        return None

    log_message("info", f"📂 Processing {pdf_file} with {display_name}...")
    start_file_time = time.time()

    # ✅ Try to load cached extracted text first
    text = load_extracted_text(pdf_file)
    
    if not text:
        # Extract from PDF if no cached text exists
        print(f"   📖 Extracting text from PDF...")
        text = extract_text_from_pdf(pdf_path)
        if not text:
            print(f"   ⚠️ No text extracted from {pdf_file}. Skipping...")
            return None
        
        # Save extracted text for future use
        from api_handler import smart_chunking_strategy
        chunks = smart_chunking_strategy(text, filename=pdf_file)
        save_extracted_chunks(pdf_file, chunks, model_name)
    else:
        print(f"   ✅ Using cached extracted text (saves time!)")

    print(f"   🔍 Analyzing for minimum flow requirements with {display_name}...")
    
    # 🎯 Use optimized baseline prompts
    prompts = get_prompts()
    
    # Extract Project Name (use first 15000 chars where name is typically mentioned)
    name_text = text[:15000]
    name_task = prompts["Project_Name"]
    name_result = enhanced_flow_extraction_with_model(
        document_text=name_text,
        task=name_task,
        filename=pdf_file,
        model_name=model_name
    )
    
    # Extract Project Location (use first 15000 chars where location is typically mentioned)
    location_text = text[:15000]
    location_task = prompts["Project_Location"]
    location_result = enhanced_flow_extraction_with_model(
        document_text=location_text,
        task=location_task,
        filename=pdf_file,
        model_name=model_name
    )
    
    # 🔧 Validate location result - remove flow values if present
    import re
    location_value = location_result.get('value', '')
    if re.match(r'^[\d,\.]+\s*(cfs|cms|cusecs|cubic feet)?\s*$', location_value, re.IGNORECASE):
        location_result['value'] = 'Not mentioned'
        location_result['inferred_context'] = 'Location extraction returned flow value instead of geographic location.'
        location_result['exact_sentences'] = 'Not mentioned'
    
    # Extract Minimum Flow
    enhanced_task = prompts["Minimum_Flow"]
    result = enhanced_flow_extraction_with_model(
        document_text=text,
        task=enhanced_task,
        filename=pdf_file,
        model_name=model_name
    )
    
    # 🎯 Apply scoring mechanism to select best minimum flow
    result = apply_flow_scoring(result, document_name=pdf_file)

    file_time = time.time() - start_file_time

    print(f"   ⏱️  Completed in {file_time:.2f} seconds")
    print(f"   🏷️  Project: {name_result.get('value', 'Not mentioned')}")
    print(f"   📍 Location: {location_result.get('value', 'Not mentioned')}")
    print(f"   💧 Found: {result.get('value', 'Not mentioned')}")

    # ✅ Save results in the expected format
    final_values = {
        'Project_Name': name_result,
        'Project_Location': location_result,
        'Minimum_Flow': result
    }
    
    save_results_for_model(pdf_file, final_values, {}, model_config["results_file"])
    
    # ✅ Save timing results
    save_timing_results_for_model(pdf_file, file_time, result, model_config["timing_file"], model_name)
    
    return {
        'filename': pdf_file,
        'model': display_name,
        'result': result,
        'processing_time': file_time
    }

def test_model_availability(model_name):
    """🔍 Test if a model is available in Ollama."""
    import requests
    try:
        payload = {
            "model": model_name,
            "prompt": "Test",
            "stream": False,
            "options": {"num_predict": 1}
        }
        response = requests.post("http://localhost:11434/api/generate", 
                               json=payload, 
                               timeout=30)
        return response.status_code == 200
    except:
        return False

def main():
    """🚀 Main function to process PDFs with multiple models for comparison."""
    print("🔍 Starting MULTI-MODEL comparison pipeline...")
    print("🎯 Testing models for accuracy and timing comparison")
    print("=" * 80)

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

    # Test which models are available
    print("🤖 Checking model availability...")
    available_models = []
    for model_config in MODELS_TO_TEST:
        model_name = model_config["name"]
        display_name = model_config["display_name"]
        print(f"   Testing {display_name} ({model_name})...", end=" ")
        
        if test_model_availability(model_name):
            print("✅ Available")
            available_models.append(model_config)
        else:
            print("❌ Not available")
    
    if not available_models:
        print("❌ No models are available! Please install models first.")
        print("   Example: ollama pull llama3:8b")
        return
    
    print(f"\n📊 Will test {len(available_models)} available models")
    print("=" * 80)

    # Validate setup before starting
    ensure_directories()
    if not validate_setup():
        return

    pdf_folder = get_pdf_folder()
    pdf_files = sorted([file for file in os.listdir(pdf_folder) if file.endswith('.pdf')])
    
    print(f"📚 Found {len(pdf_files)} PDF documents in: {pdf_folder}")
    
    # ✅ Ensure all PDFs have extracted text before starting multi-model testing
    ensure_all_texts_extracted(pdf_folder, pdf_files)
    
    print(f"📊 Will test {len(available_models)} available models")
    print("=" * 80)
    
    # Process each model separately
    for model_idx, model_config in enumerate(available_models, 1):
        model_name = model_config["name"]
        display_name = model_config["display_name"]
        
        print(f"\n🤖 TESTING MODEL {model_idx}/{len(available_models)}: {display_name}")
        print(f"📄 Results will be saved to: {model_config['results_file']}")
        print(f"⏱️  Timing will be saved to: {model_config['timing_file']}")
        print("-" * 60)
        
        existing_results = load_existing_results(model_config["results_file"])
        
        model_start_time = time.time()
        successful_extractions = 0
        
        for i, pdf_file in enumerate(pdf_files, 1):
            print(f"\n🚀 Processing {i}/{len(pdf_files)}: {pdf_file}")
            result = process_file_with_model(pdf_file, pdf_folder, model_config, existing_results)
            
            if result and result['result'].get('value', 'Not mentioned') not in ['Not mentioned', 'Error']:
                successful_extractions += 1
            
            print(f"✅ Completed {i}/{len(pdf_files)} for {display_name}")
        
        model_total_time = time.time() - model_start_time
        success_rate = (successful_extractions / len(pdf_files)) * 100
        
        print(f"\n📊 {display_name} SUMMARY:")
        print(f"   ⏱️  Total time: {model_total_time:.2f} seconds")
        print(f"   ⚡ Avg time per file: {model_total_time/len(pdf_files):.2f} seconds")
        print(f"   ✅ Successful extractions: {successful_extractions}/{len(pdf_files)} ({success_rate:.1f}%)")
        print(f"   📄 Results: {model_config['results_file']}")
        print(f"   ⏱️  Timing: {model_config['timing_file']}")

    print("\n" + "=" * 80)
    print("🎯 MULTI-MODEL COMPARISON COMPLETED!")
    print("📊 Results Summary:")
    for model_config in available_models:
        print(f"   🤖 {model_config['display_name']}: {model_config['results_file']}")
    print("\n💡 Use the comparison scripts to analyze results across models:")
    print("   - compare_model_results.py (to be created)")
    print("   - analyze_timing_comparison.py (to be created)")
    print("=" * 80)

if __name__ == "__main__":
    main()
