"""
🚀 V17 Pipeline - Full Implementation with:
1. Structured Extraction (metadata-rich candidates)
2. Deterministic Selection (rule-based fast path)
3. RLS Reasoning (tie-breaking only)
"""
import os
import sys
import csv
import logging
from typing import List, Dict

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from extraction_v17_structured import extract_all_structured_candidates
from deterministic_selector_v17 import select_deterministic
from api_handler_rls import select_best_flow_with_reasoning_v17
from pdf_processor_min_flow import extract_text_from_pdf
from api_handler import smart_chunking_strategy, OLLAMA_URL, PDF_DIR
import requests
import json
import re

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('v17_pipeline.log'),
        logging.StreamHandler()
    ]
)

RESULTS_FILE = "min_flow_results_V17.csv"

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
            # Split by " ---\n" to get content after chunk number and delimiter
            if " ---\n" in part:
                chunk_content = part.split(" ---\n", 1)[1].strip()
                if chunk_content:
                    chunks.append(chunk_content)
        
        return chunks if chunks else None
    except Exception as e:
        logging.warning(f"Error loading chunks: {e}")
        return None

def extract_project_metadata(pdf_file: str, text: str) -> Dict:
    """Extract project name from filename."""
    # Simple extraction from filename (e.g., "P10198_License_19880427.pdf" -> "P10198")
    project_name = pdf_file.split('_')[0] if '_' in pdf_file else pdf_file.replace('.pdf', '')
    
    return {
        'name': project_name,
        'location': 'Not mentioned'  # Not needed for V17
    }

        location_result = {"value": "Not mentioned"}
    
    return {
        'project_name': name_result.get('value', 'Not mentioned'),
        'project_location': location_result.get('value', 'Not mentioned')
    }


def process_document_v17(pdf_file: str, pdf_dir: str, llm) -> Dict:
    """
    Process a single document with V17 pipeline:
    1. Extract structured candidates
    2. Apply deterministic selection
    3. Use RLS only for tie-breaking
    """
    
    logging.info(f"📂 Processing {pdf_file}...")
    
    pdf_path = os.path.join(pdf_dir, pdf_file)
    
    # Load or extract chunks
    chunks = load_existing_chunks(pdf_file)
    
    if chunks:
        logging.info(f"   ✅ Using {len(chunks)} existing chunks")
    else:
        logging.info(f"   📖 Extracting text from PDF...")
        text = extract_text_from_pdf(pdf_path)
        if not text:
            logging.warning(f"   ⚠️ No text extracted from {pdf_file}")
            return {
                'value': 'Not mentioned',
                'context': '',
                'reasoning': 'No text extracted from PDF',
                'method': 'error'
            }
        
        chunks = smart_chunking_strategy(text, filename=pdf_file)
        logging.info(f"   ✅ Created {len(chunks)} chunks")
    
    # Get full text for metadata extraction
    if not chunks:
        return {
            'value': 'Not mentioned',
            'context': '',
            'reasoning': 'No chunks available',
            'method': 'error'
        }
    
    full_text = "\n\n".join(chunks[:3])  # Use first few chunks for metadata
    
    # Extract metadata
    metadata = extract_project_metadata(pdf_file, full_text)
    
    # STEP 1: Extract structured candidates from all chunks
    logging.info(f"   🔍 Extracting structured candidates...")
    candidates = extract_all_structured_candidates(chunks)
    
    logging.info(f"   ✅ Extracted {len(candidates)} candidates total")
    
    if not candidates:
        return {
            'project_name': metadata['project_name'],
            'project_location': metadata['project_location'],
            'value': 'Not mentioned',
            'context': '',
            'reasoning': 'No candidates extracted',
            'method': 'no_candidates'
        }
    
    # STEP 2: Try deterministic selection first
    logging.info(f"   🎯 Applying deterministic selection...")
    selected, method = select_deterministic(candidates)
    
    if selected is not None:
        # Deterministic selection succeeded!
        logging.info(f"   ✅ Deterministic selection: {selected['value']} (method: {method})")
        return {
            'project_name': metadata['project_name'],
            'project_location': metadata['project_location'],
            'value': selected['value'],
            'context': selected.get('raw_evidence', ''),
            'reasoning': f"Selected deterministically: {method}",
            'method': method
        }
    
    # STEP 3: Need RLS for tie-breaking
    logging.info(f"   🧠 Deterministic selection failed ({method}) - using V17 RLS...")
    result = select_best_flow_with_reasoning_v17(candidates, llm, verbose=False)
    
    result['project_name'] = metadata['project_name']
    result['project_location'] = metadata['project_location']
    
    return result


def save_results_v17(pdf_file: str, result: Dict):
    """Save V17 results to CSV."""
    
    project_name = result.get('project_name', 'Not mentioned')
    project_location = result.get('project_location', 'Not mentioned')
    value = result.get('value', 'Not mentioned')
    context = result.get('context', '')
    reasoning = result.get('reasoning', '')
    method = result.get('method', 'unknown')
    
    # Read existing results
    rows = []
    headers = ["Row_Number", "Project_Name", "filename", "Project_Location",
               "Minimum_Flow_Value", "Minimum_Flow_Context", "Selection_Reasoning", 
               "Selection_Method"]
    
    if os.path.exists(RESULTS_FILE):
        with open(RESULTS_FILE, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            rows = list(reader)
    
    # Check if exists
    found = False
    for i, row in enumerate(rows):
        if row["filename"] == pdf_file:
            rows[i]["Project_Name"] = project_name
            rows[i]["Project_Location"] = project_location
            rows[i]["Minimum_Flow_Value"] = value
            rows[i]["Minimum_Flow_Context"] = context
            rows[i]["Selection_Reasoning"] = reasoning
            rows[i]["Selection_Method"] = method
            found = True
            break
    
    if not found:
        new_row = {
            "Row_Number": len(rows) + 1,
            "Project_Name": project_name,
            "filename": pdf_file,
            "Project_Location": project_location,
            "Minimum_Flow_Value": value,
            "Minimum_Flow_Context": context,
            "Selection_Reasoning": reasoning,
            "Selection_Method": method
        }
        rows.append(new_row)
    
    # Save
    with open(RESULTS_FILE, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(rows)
    
    logging.info(f"✅ Results saved to {RESULTS_FILE}")


def main():
    """Run V17 pipeline on all PDFs."""
    
    logging.info("🚀 Starting V17 Pipeline")
    logging.info("=" * 70)
    
    # Get PDF files
    pdf_files = sorted([f for f in os.listdir(PDF_DIR) if f.endswith('.pdf')])
    
    if not pdf_files:
        logging.error(f"❌ No PDF files found in {PDF_DIR}")
        return
    
    logging.info(f"✅ Found {len(pdf_files)} PDF files")
    
    # Initialize LLM
    llm = OllamaLLM(model="llama3.3:70b", base_url=OLLAMA_URL)
    logging.info("✅ LLM initialized")
    
    # Process each file
    for i, pdf_file in enumerate(pdf_files, 1):
        try:
            logging.info(f"\n{'='*70}")
            logging.info(f"Processing {i}/{len(pdf_files)}: {pdf_file}")
            logging.info(f"{'='*70}")
            
            result = process_document_v17(pdf_file, PDF_DIR, llm)
            save_results_v17(pdf_file, result)
            
        except Exception as e:
            logging.error(f"❌ Error processing {pdf_file}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    logging.info("\n" + "="*70)
    logging.info("✅ V17 Pipeline Complete!")
    logging.info(f"📊 Results saved to: {RESULTS_FILE}")
    logging.info("="*70)


if __name__ == "__main__":
    main()
