"""
🚀 V18 Pipeline - ULTRA SIMPLE
One LLM call reads ALL chunks and decides the minimum flow.
No extraction, no deterministic rules, no fallback - just pure LLM reasoning.
"""
import os
import sys
import csv
import logging
from typing import List, Dict
import requests
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from api_handler import OLLAMA_URL

PDF_DIR = "../data/input_pdfs"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(message)s',
    handlers=[
        logging.FileHandler('v18_pipeline.log'),
        logging.StreamHandler()
    ]
)

RESULTS_FILE = "min_flow_results_V18.csv"

def load_existing_chunks(pdf_file):
    """Load pre-extracted chunks from file."""
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


def get_minimum_flow_simple(chunks: List[str], pdf_file: str) -> Dict:
    """
    Single LLM call: read chunks and decide minimum flow.
    Limits to first 15 chunks to avoid context overflow.
    """
    
    # Limit chunks to avoid 500 error (context window overflow)
    max_chunks = 15
    chunks_to_analyze = chunks[:max_chunks]
    
    # Build prompt with limited chunks
    chunks_text = "\n\n".join([
        f"=== CHUNK {i+1} ===\n{chunk[:2000]}"  # Also truncate each chunk
        for i, chunk in enumerate(chunks_to_analyze)
    ])
    
    prompt = f"""You are analyzing a hydroelectric project document to find the MINIMUM FLOW REQUIREMENT.

Read through the {len(chunks_to_analyze)} chunks below (from a {len(chunks)}-chunk document).
Your job: Identify the legally required minimum flow release value.

**WHAT TO LOOK FOR**:
- "shall release", "must release", "required to release"
- "minimum flow", "minimum release", "continuous release"
- Values from regulatory Articles or License conditions
- Year-round requirements (not seasonal or temporary)

**WHAT TO AVOID**:
- Cost estimates or budget tables
- Historical data or examples
- Operational targets without mandate language
- Maximum flows or flood releases

**DOCUMENT CHUNKS**:
{chunks_text}

**YOUR ANSWER** (respond in JSON):
{{
  "value": "3,000 cfs" or "1 hour daily generation" or "Not mentioned",
  "evidence": "Quote the specific sentence/paragraph that contains the requirement",
  "location": "Chunk number and section where you found it"
}}

If no minimum flow is mentioned in these chunks, return "Not mentioned".
If you see multiple values, pick the one with the strongest mandate language.
"""
    
    payload = {
        "model": "llama3.3:70b",
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.1,
            "top_p": 0.9,
            "num_ctx": 16384  # Reduced from 32K to be safe
        }
    }
    
    try:
        logging.info(f"   🧠 LLM analyzing {len(chunks_to_analyze)}/{len(chunks)} chunks...")
        response = requests.post(OLLAMA_URL, json=payload, timeout=300)
        response.raise_for_status()
        result_text = response.json()["response"].strip()
        
        # Parse JSON response
        if result_text.startswith("{"):
            result = json.loads(result_text)
        elif "```json" in result_text:
            import re
            json_match = re.search(r'```json\s*\n(.*?)\n```', result_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(1))
            else:
                result = {"value": "Not mentioned", "evidence": "", "location": ""}
        else:
            # LLM didn't return JSON - try to extract value
            result = {
                "value": result_text.split('\n')[0] if result_text else "Not mentioned",
                "evidence": result_text,
                "location": ""
            }
        
        logging.info(f"   ✅ LLM decision: {result.get('value', 'Unknown')}")
        
        return {
            'value': result.get('value', 'Not mentioned'),
            'context': result.get('evidence', ''),
            'reasoning': result.get('location', 'LLM analysis of all chunks'),
            'method': 'v18_simple_llm'
        }
        
    except Exception as e:
        logging.error(f"   ❌ LLM call failed: {e}")
        return {
            'value': 'Error',
            'context': '',
            'reasoning': f'LLM call failed: {str(e)}',
            'method': 'error'
        }


def process_document_v18(pdf_file: str) -> Dict:
    """Process one PDF - load chunks and ask LLM."""
    
    pdf_path = os.path.join(PDF_DIR, pdf_file)
    logging.info(f"\n📄 Processing: {pdf_file}")
    
    # Load chunks
    chunks = load_existing_chunks(pdf_file)
    
    if not chunks:
        logging.warning(f"   ⚠️ No chunks found for {pdf_file}")
        return {
            'value': 'Not mentioned',
            'context': '',
            'reasoning': 'No chunks available',
            'method': 'no_chunks'
        }
    
    logging.info(f"   📚 Loaded {len(chunks)} chunks")
    
    # Get answer from LLM
    result = get_minimum_flow_simple(chunks, pdf_file)
    
    return result


def save_results_v18(pdf_file: str, result: Dict):
    """Save V18 results to CSV."""
    
    file_exists = os.path.exists(RESULTS_FILE)
    
    with open(RESULTS_FILE, 'a', newline='', encoding='utf-8') as f:
        fieldnames = [
            'filename',
            'Minimum_Flow_Value',
            'Context',
            'Reasoning',
            'Selection_Method'
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        if not file_exists:
            writer.writeheader()
        
        writer.writerow({
            'filename': pdf_file,
            'Minimum_Flow_Value': result.get('value', 'Not mentioned'),
            'Context': result.get('context', '')[:500],  # Truncate long context
            'Reasoning': result.get('reasoning', ''),
            'Selection_Method': result.get('method', 'unknown')
        })


def main():
    """Run V18 pipeline on all PDFs."""
    
    logging.info("=" * 70)
    logging.info("🚀 Starting V18 Simple Pipeline")
    logging.info("=" * 70)
    
    # Get all PDFs
    pdf_files = sorted([f for f in os.listdir(PDF_DIR) if f.endswith('.pdf')])
    
    logging.info(f"📂 Found {len(pdf_files)} PDF files")
    
    processed = 0
    for pdf_file in pdf_files:
        try:
            result = process_document_v18(pdf_file)
            save_results_v18(pdf_file, result)
            processed += 1
            logging.info(f"✅ Saved result ({processed}/{len(pdf_files)})")
        except Exception as e:
            logging.error(f"❌ Error processing {pdf_file}: {e}")
            continue
    
    logging.info("=" * 70)
    logging.info(f"✅ V18 Pipeline Complete: {processed}/{len(pdf_files)} files")
    logging.info("=" * 70)


if __name__ == "__main__":
    main()
