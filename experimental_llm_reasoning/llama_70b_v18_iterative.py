"""
🚀 V18 Iterative - LLM reads ALL chunks in batches
Processes chunks in groups, maintains running findings, makes final decision
"""
import os
import sys
import csv
import logging
from typing import List, Dict
import requests
import json
import re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from api_handler import OLLAMA_URL

PDF_DIR = "../data/input_pdfs"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(message)s',
    handlers=[
        logging.FileHandler('v18_iterative.log'),
        logging.StreamHandler()
    ]
)

RESULTS_FILE = "min_flow_results_V18_iterative.csv"

def load_existing_chunks(pdf_file):
    """Load pre-extracted chunks."""
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
            if " ---\n" in part:
                chunk_content = part.split(" ---\n", 1)[1].strip()
                if chunk_content:
                    chunks.append(chunk_content)
        
        return chunks if chunks else None
    except Exception as e:
        logging.warning(f"Error loading chunks: {e}")
        return None


def analyze_chunk_batch(chunks: List[str], batch_num: int, previous_findings: str) -> str:
    """Analyze a batch of chunks, considering previous findings."""
    
    chunks_text = "\n\n".join([
        f"=== CHUNK {i+1} ===\n{chunk[:1500]}" 
        for i, chunk in enumerate(chunks)
    ])
    
    prompt = f"""You are reading a hydroelectric project document to find MINIMUM FLOW REQUIREMENTS.

**PREVIOUS FINDINGS** (from earlier chunks):
{previous_findings if previous_findings else "No findings yet - this is the first batch."}

**NEW CHUNKS TO ANALYZE** (Batch {batch_num}):
{chunks_text}

**YOUR TASK**:
1. Read these new chunks carefully
2. Look for minimum flow requirements with mandate language ("shall", "must", "required")
3. Update your findings based on what you see

**RESPOND WITH**:
- If you find a minimum flow value: Report it with evidence
- If you see nothing relevant: Say "No minimum flow in this batch"
- If you found something earlier and see nothing new: Confirm previous finding

Keep your response concise (2-3 sentences).
"""
    
    payload = {
        "model": "llama3.3:70b",
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.1, "num_ctx": 8192}
    }
    
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=120)
        response.raise_for_status()
        return response.json()["response"].strip()
    except Exception as e:
        logging.warning(f"   Batch {batch_num} failed: {e}")
        return "Error analyzing batch"


def get_minimum_flow_iterative(chunks: List[str], pdf_file: str) -> Dict:
    """
    Read ALL chunks in batches, building up findings progressively.
    """
    
    batch_size = 10
    findings = ""
    
    # Process chunks in batches
    num_batches = (len(chunks) + batch_size - 1) // batch_size
    logging.info(f"   📖 Processing {len(chunks)} chunks in {num_batches} batches...")
    
    for i in range(0, len(chunks), batch_size):
        batch_chunks = chunks[i:i+batch_size]
        batch_num = (i // batch_size) + 1
        
        logging.info(f"   🔍 Batch {batch_num}/{num_batches} ({len(batch_chunks)} chunks)...")
        
        batch_findings = analyze_chunk_batch(batch_chunks, batch_num, findings)
        
        # Update running findings
        if "No minimum flow" not in batch_findings and "Error" not in batch_findings:
            findings = batch_findings
            logging.info(f"   ✓ Updated findings")
    
    # Final decision
    if not findings or "No minimum flow" in findings:
        return {
            'value': 'Not mentioned',
            'context': '',
            'reasoning': f'Analyzed all {len(chunks)} chunks, no minimum flow found',
            'method': 'v18_iterative'
        }
    
    # Extract value from findings
    value = findings.split('\n')[0] if findings else 'Not mentioned'
    
    return {
        'value': value,
        'context': findings,
        'reasoning': f'Found after analyzing {len(chunks)} chunks in {num_batches} batches',
        'method': 'v18_iterative'
    }


def process_document_v18(pdf_file: str) -> Dict:
    """Process one PDF."""
    
    logging.info(f"\n📄 {pdf_file}")
    
    chunks = load_existing_chunks(pdf_file)
    
    if not chunks:
        return {
            'value': 'Not mentioned',
            'context': '',
            'reasoning': 'No chunks',
            'method': 'no_chunks'
        }
    
    result = get_minimum_flow_iterative(chunks, pdf_file)
    return result


def save_results_v18(pdf_file: str, result: Dict):
    """Save results."""
    
    file_exists = os.path.exists(RESULTS_FILE)
    
    with open(RESULTS_FILE, 'a', newline='', encoding='utf-8') as f:
        fieldnames = ['filename', 'Minimum_Flow_Value', 'Context', 'Reasoning', 'Selection_Method']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        if not file_exists:
            writer.writeheader()
        
        writer.writerow({
            'filename': pdf_file,
            'Minimum_Flow_Value': result.get('value', 'Not mentioned'),
            'Context': result.get('context', '')[:500],
            'Reasoning': result.get('reasoning', ''),
            'Selection_Method': result.get('method', 'unknown')
        })


def main():
    """Run V18 Iterative pipeline."""
    
    logging.info("=" * 70)
    logging.info("🚀 V18 Iterative Pipeline - Reads ALL chunks in batches")
    logging.info("=" * 70)
    
    pdf_files = sorted([f for f in os.listdir(PDF_DIR) if f.endswith('.pdf')])
    logging.info(f"📂 Found {len(pdf_files)} PDFs\n")
    
    for i, pdf_file in enumerate(pdf_files, 1):
        try:
            result = process_document_v18(pdf_file)
            save_results_v18(pdf_file, result)
            logging.info(f"✅ {i}/{len(pdf_files)}: {result.get('value', 'Unknown')}\n")
        except Exception as e:
            logging.error(f"❌ Error: {e}\n")
    
    logging.info("=" * 70)
    logging.info("✅ Complete")
    logging.info("=" * 70)


if __name__ == "__main__":
    main()
