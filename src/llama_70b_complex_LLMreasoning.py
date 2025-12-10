"""
🧠 V16.5 RLS PIPELINE: Minimum Flow Extraction with LLM Reasoning
==================================================================

This pipeline uses LLM reasoning for candidate selection instead of
rule-based scoring. It's an alternative to llama_70b_complex_pipeline.py.

DIFFERENCE FROM V16.4:
- V16.4: Uses keyword scoring to select best candidate
- V16.5 RLS: Uses LLM reasoning with justification

Usage:
    python3 llama_70b_complex_LLMreasoning.py
"""

import os
import sys
import time
import csv
import datetime
import json
import re
import logging
import requests

sys.path.insert(0, '/home/fbg/Extract_LLM_FBA/src')

from pdf_processor_min_flow import extract_text_from_pdf, split_text_by_tokens
from api_handler import check_ollama_server, enhanced_flow_extraction, OLLAMA_URL
from api_handler_rls import select_best_flow_with_reasoning
from task_definitions_min_flow import get_prompts
from config import get_pdf_folder, ensure_directories, validate_setup

# ✅ Configure logging
logging.basicConfig(
    filename="debug_rls.log",
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# ✅ Files for storing results (separate from V16.4)
RESULTS_FILE = "min_flow_results_RLS.csv"
TIMING_RESULTS_FILE = "min_flow_timing_results_RLS.csv"


def log_message(level, message):
    """🔥 Logs messages and prints them in real-time."""
    print(message)
    getattr(logging, level)(message)


# Create a simple LLM wrapper that uses Ollama's API
class SimpleLLM:
    def __init__(self, model="llama3.3:70b", base_url="http://127.0.0.1:11434"):
        self.model = model
        self.base_url = base_url
        self.api_url = f"{base_url}/api/generate"
    
    def invoke(self, prompt):
        """Send prompt to Ollama and return response."""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.1, "top_p": 0.9, "num_ctx": 8192}
        }
        
        response = requests.post(self.api_url, json=payload, timeout=180)
        response.raise_for_status()
        result = response.json()
        llm_text = result.get("response", "")
        
        # Debug: Log response length
        print(f"   🔍 LLM returned {len(llm_text)} characters")
        if not llm_text:
            print(f"   ⚠️ EMPTY RESPONSE! Full result: {result}")
        
        return llm_text


def is_cost_or_unrelated_table(chunk):
    """
    Detect cost/financial/construction tables that should be skipped entirely.
    Check the RAW chunk text, not LLM output.
    V16.5.1 FIX: Relaxed - only skip EXPLICIT financial tables, not generic terms
    """
    chunk_lower = chunk.lower()
    
    # Only EXPLICIT cost/financial table indicators (removed broad terms)
    cost_keywords = [
        'item no', 'unit price', 'contract awarded', 'bid amount',
        'payment made', 'construction cost', 'total cost',
        'lands and damages', 'permanent operating equipment',
        'schedule of prices', 'cost estimate'
    ]
    
    # Must have $ AND cost-related term together (not just one)
    has_dollar = '$' in chunk_lower
    has_cost_term = any(keyword in chunk_lower for keyword in cost_keywords)
    
    return has_dollar and has_cost_term


def has_flow_indicators(chunk):
    """
    Check if chunk contains flow-related keywords OR regulatory language.
    V16.5.1 FIX: Relaxed - also accept chunks with Articles/mandates even without explicit flow terms
    """
    chunk_lower = chunk.lower()
    
    flow_keywords = [
        'cfs', 'kcfs', 'cubic feet', 'ft³/s', 'cf/s',
        'discharge', 'release', 'flow', 'minimum flow',
        'shall release', 'must release', 'required flow',
        'generation', 'hour'  # V16.5.1: Added for temporal minimums
    ]
    
    # Also accept regulatory language even without explicit flow terms
    regulatory_keywords = [
        'article', 'shall', 'must', 'required', 'mandated',
        'license condition', 'we are requiring'
    ]
    
    has_flow = any(keyword in chunk_lower for keyword in flow_keywords)
    has_regulatory = any(keyword in chunk_lower for keyword in regulatory_keywords)
    
    return has_flow or has_regulatory


def is_from_cost_table(context, value):
    """Check if extracted value comes from a cost/construction table context."""
    if not context:
        return False
    
    context_lower = context.lower()
    
    # Cost/construction table indicators in the CONTEXT
    cost_indicators = [
        'construction cost',
        'payment made', 
        'contract awarded',
        'contractor',
        'lands and damages',
        'relocations',
        'roads, railroads and bridges',
        'levees',
        'buildings, quarters',
        'spillway and non-overflow',
        'fish passage facilities',
        'permanent operating equipment',
        'total cost',
        'total 83,585,600'  # Specific to Bonneville cost table
    ]
    
    # If context contains cost indicators, this value is from a cost table
    return any(indicator in context_lower for indicator in cost_indicators)


def extract_all_candidates_rls(document_text, task, filename=""):
    """
    🧠 V16.5 RLS: Extract ALL candidate flows without final selection.
    
    This function replicates the extraction logic from api_handler.py's
    process_document_with_smart_chunking but returns the list of candidates
    BEFORE the ask_ollama_to_select_best selection happens.
    
    Returns:
        list: All extracted candidate flows with their contexts
    """
    from api_handler import smart_chunking_strategy, analyze_chunk
    from flow_scoring import calculate_chunk_score
    
    # Apply smart chunking
    chunks = smart_chunking_strategy(document_text, filename=filename)
    
    # Determine document type
    document_type = ""
    if ('WCM' in filename or 'Water Control Manual' in filename or 
        'Bonneville' in filename or 'Grand Coulee' in filename or
        'Corps' in filename or 'Reservoir Regulation Manual' in filename):
        document_type = "Corps Water Control Manual"
    elif any(indicator in filename for indicator in ['License', 'P1', 'P2', 'P3']):
        document_type = "FERC License"
    
    # Score chunks and take top 15
    chunk_scores = []
    for i, chunk in enumerate(chunks):
        score = calculate_chunk_score(chunk, filename)
        chunk_scores.append((i, chunk, score))
    
    chunk_scores.sort(key=lambda x: x[2], reverse=True)
    top_chunks = chunk_scores[:15]
    
    # Filter out proposal-only chunks if Article/mandatory chunks exist
    has_article_chunks = any('article' in chunk.lower() or 'licensee shall release' in chunk.lower() or 'shall release' in chunk.lower() 
                             or 'we are requiring' in chunk.lower() or 'our requirement' in chunk.lower() 
                             for _, chunk, _ in top_chunks)
    
    if has_article_chunks:
        filtered_chunks = []
        for i, chunk, score in top_chunks:
            chunk_lower = chunk.lower()
            has_proposal = any(term in chunk_lower for term in ['applicant proposes', 'proposes to', 'licensee proposes', 'as proposed by'])
            has_mandatory = any(term in chunk_lower for term in ['article', 'licensee shall release', 'shall release', 'we are requiring', 'our requirement', 'must release'])
            
            if not (has_proposal and not has_mandatory):
                filtered_chunks.append((i, chunk, score))
        
        top_chunks = filtered_chunks if filtered_chunks else top_chunks
    
    # Process top-scoring chunks and collect ALL results
    all_results = []
    for i, chunk, score in top_chunks:
        # ✅ PRE-FILTER 1: Skip cost/construction table chunks entirely
        if is_cost_or_unrelated_table(chunk):
            print(f"   ⏭️  SKIPPED chunk {i} (cost/construction table)")
            continue
        
        # ✅ PRE-FILTER 2: Skip chunks without flow indicators
        if not has_flow_indicators(chunk):
            print(f"   ⏭️  SKIPPED chunk {i} (no flow keywords)")
            continue
        
        # Now extract from valid chunks only
        result = analyze_chunk(chunk, task, all_chunks=chunks, filename=filename, document_type=document_type)
        
        value = str(result.get("value", "")).lower()
        if value not in ["not mentioned", "error", ""]:
            # ✅ POST-EXTRACTION VALIDATION: Reject hallucinated "Min. Daily" on cost table numbers
            # Check if value has suspicious patterns indicating LLM fabrication
            if "min. daily" in value or "min daily" in value:
                # Extract just the number
                import re
                nums = re.findall(r'\d+', value)  # Find digits only (no commas)
                if nums and len(nums) > 0:
                    try:
                        num_val = int(nums[0])
                        # If "Min. Daily" + small number for large dam, likely hallucination
                        if num_val < 10000 and ('wcm' in filename.lower() or 'bonneville' in filename.lower() or 'water control' in filename.lower()):
                            print(f"   ⚠️  REJECTED: Suspicious 'Min. Daily {num_val}' likely hallucinated from cost table")
                            continue
                    except (ValueError, IndexError):
                        pass  # If parsing fails, just include the result
            
            all_results.append(result)
    
    print(f"   ✅ Extracted {len(all_results)} candidates from {len(top_chunks)} chunks")
    
    # Return all candidates (not just the best one)
    return all_results


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
    """📂 Load previously extracted chunks from file if available."""
    base_name = os.path.splitext(pdf_file)[0]
    chunk_file = f"extracted_chunks_{base_name}.txt"
    
    if not os.path.exists(chunk_file):
        return None
    
    try:
        with open(chunk_file, "r", encoding="utf-8") as f:
            content = f.read()
        
        chunks = []
        parts = content.split("--- Chunk ")
        for part in parts[1:]:
            chunk_content = part.split("---\n", 1)[1].strip()
            if chunk_content:
                chunks.append(chunk_content)
        
        print(f"   📂 Loaded {len(chunks)} existing chunks from {chunk_file}")
        return chunks
    except Exception as e:
        print(f"   ⚠️ Error loading chunks from {chunk_file}: {e}")
        return None


def save_results(pdf_file, final_values, task_hashes=None):
    """📂 Save extracted results in clean CSV format with RLS reasoning."""
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
               "Minimum_Flow_Exact_Sentences", "RLS_Reasoning", "RLS_Method"]
    
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
            rows[i]["RLS_Reasoning"] = final_values["Minimum_Flow"].get("reasoning", "")
            rows[i]["RLS_Method"] = final_values["Minimum_Flow"].get("method", "")
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
            "Minimum_Flow_Exact_Sentences": final_values["Minimum_Flow"]["exact_sentences"],
            "RLS_Reasoning": final_values["Minimum_Flow"].get("reasoning", ""),
            "RLS_Method": final_values["Minimum_Flow"].get("method", "")
        }
        rows.append(new_row)

    # Save clean CSV with proper quoting
    with open(RESULTS_FILE, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"✅ Results saved to {RESULTS_FILE}")
    print(f"📊 Total projects: {len(rows)}")


def process_file_with_rls(pdf_file, pdf_folder, existing_results, llm):
    """📄 V16.5 RLS: Process a single PDF file using LLM reasoning for selection."""
    pdf_path = os.path.join(pdf_folder, pdf_file)
    
    # Check if already processed
    if pdf_file in existing_results:
        print(f"   ⏩ Already processed. Skipping...")
        return None

    log_message("info", f"📂 Processing {pdf_file}...")
    start_file_time = time.time()

    # Load or extract chunks
    chunks = load_existing_chunks(pdf_file)
    
    if chunks:
        text = "\n\n".join(chunks)
        print(f"   ✅ Using {len(chunks)} existing chunks")
    else:
        print(f"   📖 Extracting text from PDF...")
        text = extract_text_from_pdf(pdf_path)
        if not text:
            print(f"   ⚠️ No text extracted from {pdf_file}. Skipping...")
            return None
        
        from api_handler import smart_chunking_strategy
        chunks = smart_chunking_strategy(text, filename=pdf_file)
        save_extracted_chunks(pdf_file, chunks)
        print(f"   💾 Created and saved {len(chunks)} chunks")

    print(f"   🔍 Analyzing for minimum flow requirements...")
    
    prompts = get_prompts()
    
    # Extract Project Name
    name_text = text[:5000]
    name_task = prompts["Project_Name"]
    
    payload = {
        "model": "llama3.3:70b",
        "prompt": f"{name_task}\n\nDocument:\n{name_text}",
        "stream": False,
        "options": {"temperature": 0.1, "top_p": 0.9, "num_ctx": 8192}
    }
    
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=60)
        response.raise_for_status()
        result_text = response.json()["response"].strip()
        
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
    
    print(f"   🏷️  Project Name: {name_result.get('value', 'Not mentioned')}")
    
    # Extract Project Location
    location_text = text[:5000]
    location_task = prompts["Project_Location"]
    
    payload["prompt"] = f"{location_task}\n\nDocument:\n{location_text}"
    
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
    
    print(f"   📍 Location: {location_result.get('value', 'Not mentioned')}")
    
    # Validate location/name results
    location_value = location_result.get('value', '')
    if re.match(r'^[\d,\.]+\s*(cfs|cms|cusecs|cubic feet)?\s*$', location_value, re.IGNORECASE):
        location_result['value'] = 'Not mentioned'
    
    name_value = name_result.get('value', '')
    if re.match(r'^[\d,\.]+\s*(cfs|cms|cusecs|cubic feet|dsf|generation|hour)\s*$', name_value, re.IGNORECASE):
        name_result['value'] = 'Not mentioned'
    
    # 🧠 V16.5 RLS: Extract candidates and use LLM reasoning for selection
    print(f"   🧠 V16.5 RLS: Using LLM reasoning for candidate selection...")
    enhanced_task = prompts["Minimum_Flow"]
    
    # Get all candidates before final selection
    from api_handler import process_document_with_smart_chunking
    candidates = extract_all_candidates_rls(text, enhanced_task, pdf_file)
    
    # Apply RLS reasoning if multiple candidates exist
    if len(candidates) > 1:
        print(f"   🤖 Found {len(candidates)} candidates - applying RLS reasoning...")
        
        # Apply RLS reasoning
        rls_result = select_best_flow_with_reasoning(
            candidates=candidates,
            llm=llm,
            fallback_to_scoring=True,
            verbose=True
        )
        
        # Build result dict
        result = {
            'value': rls_result['value'],
            'inferred_context': rls_result.get('context', ''),
            'exact_sentences': rls_result.get('exact_sentences', ''),
            'reasoning': rls_result.get('reasoning', ''),
            'method': rls_result.get('method', '')
        }
        
        print(f"   ✅ RLS selected: {result['value']}")
        print(f"   💡 Method: {result['method']}")
    else:
        # Single or no candidates - use no-interference extraction with scoring
        # V16.5.1 FIX: Use the new no-selection extraction to avoid double-scoring
        print(f"   ℹ️  Single/no candidates - using fallback with post-scoring...")
        
        from api_handler import process_document_with_smart_chunking_no_selection
        from flow_scoring import apply_flow_scoring
        
        # Get all candidates without pre-selection
        all_candidates = process_document_with_smart_chunking_no_selection(
            document_text=text,
            prompt=enhanced_task,
            filename=pdf_file
        )
        
        # Apply scoring mechanism to select best
        result = apply_flow_scoring(all_candidates, document_name=pdf_file)
        
        # Add RLS metadata
        result['reasoning'] = 'Single candidate or no candidates available - used scoring fallback'
        result['method'] = 'single_candidate'
        print(f"   ℹ️  Fallback extraction: {result.get('value', 'Not mentioned')}")

    file_time = time.time() - start_file_time

    print(f"   ⏱️  Completed in {file_time:.2f} seconds")
    print(f"   💧 Found: {result.get('value', 'Not mentioned')}")

    # Save results
    final_values = {
        'Project_Name': name_result,
        'Project_Location': location_result,
        'Minimum_Flow': result
    }
    
    save_results(pdf_file, final_values, {})
    
    return {
        'filename': pdf_file,
        'result': result,
        'processing_time': file_time
    }


def main():
    """🚀 Main function for V16.5 RLS pipeline."""
    print("🧠 Starting V16.5 RLS Pipeline - LLM Reasoning for Candidate Selection")
    print("=" * 70)

    # Validate setup
    ensure_directories()
    if not validate_setup():
        return

    # Check Ollama server
    print("🔧 Checking Ollama server...")
    if not check_ollama_server():
        print("❌ ERROR: Ollama is not responding!")
        print("💡 QUICK FIX: Run 'ollama serve &' in another terminal")
        return

    # Initialize LLM for RLS
    print("🤖 Initializing LLM for reasoning...")
    llm = SimpleLLM(model="llama3.3:70b", base_url="http://127.0.0.1:11434")
    
    # Test LLM
    try:
        test_response = llm.invoke("What is 2+2? Answer with just the number.")
        if "4" in test_response:
            print("✅ LLM is responding correctly")
        else:
            print(f"⚠️ Warning: LLM response seems odd: {test_response}")
    except Exception as e:
        print(f"❌ LLM test failed: {e}")
        return

    pdf_folder = get_pdf_folder()
    pdf_files = sorted([file for file in os.listdir(pdf_folder) if file.endswith('.pdf')])
    
    # Process first 5 files for testing
    pdf_files = pdf_files[:50]
    print(f"📚 V16.5 RLS: Processing {len(pdf_files)} documents")
    for i, pdf_file in enumerate(pdf_files, 1):
        print(f"  {i}. {pdf_file}")
    print("=" * 70)
    
    existing_results = load_existing_results()

    for i, pdf_file in enumerate(pdf_files, 1):
        print(f"\n🚀 Processing {i}/{len(pdf_files)}: {pdf_file}")
        process_file_with_rls(pdf_file, pdf_folder, existing_results, llm)
        print(f"✅ Completed {i}/{len(pdf_files)}")

    print("\n" + "=" * 70)
    print("🎯 V16.5 RLS PIPELINE COMPLETED!")
    print(f"📄 Results saved to: {RESULTS_FILE}")
    print("💡 Open the CSV to see LLM reasoning for each selection")
    print("=" * 70)


if __name__ == "__main__":
    main()
