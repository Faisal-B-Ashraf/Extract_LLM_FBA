"""
V17 Structured Extraction - Returns metadata-rich candidates
"""
import re
import json
from typing import List, Dict
import requests

# Import OLLAMA_URL from api_handler
from api_handler import OLLAMA_URL

def get_structured_extraction_prompt() -> str:
    """Returns the V17 structured extraction prompt with all required metadata fields."""
    
    return """You are extracting MINIMUM FLOW requirements from hydroelectric dam regulatory documents.

**YOUR TASK**: Find ALL mentions of minimum flow requirements in this text and return them as structured JSON.

**WHAT TO EXTRACT**:
- Mandated minimum releases (from license articles, FERC requirements)
- Temporal minimums ("1 hour generation daily", "0.5 hour every other day")
- At-dam flow requirements
- Downstream gage requirements
- Instream flow requirements

**WHAT TO REJECT**:
- Construction costs, budget items ($/unit, contractor bids)
- Historical flood data ("1992 flood was X cfs")
- Operational targets without mandate language
- Maximum flows, design capacities
- Non-flow values (acres, MW, years, percentages)

**OUTPUT FORMAT** (CRITICAL - return JSON array):
```json
{{{{
  "candidates": [
    {{{{
      "candidate_id": "c1",
      "value": "3,000 cfs",
      "numeric_value": 3000,
      "units": "cfs",
      "is_mandated": true,
      "is_temporal": false,
      "is_operational": false,
      "location": "at_dam",
      "source_type": "paragraph",
      "raw_evidence": "Article 401 requires a minimum release of 3,000 cfs year-round established in 1992..."
    }}}},
    {{{{
      "candidate_id": "c2",
      "value": "1 hour generation daily",
      "numeric_value": null,
      "units": "temporal",
      "is_mandated": true,
      "is_temporal": true,
      "is_operational": false,
      "location": "at_dam",
      "source_type": "paragraph",
      "raw_evidence": "License Article 7 requires discharge equivalent to 1 hour of generation per day..."
    }}}}
  ]
}}}}
```

**FIELD DEFINITIONS**:
- `candidate_id`: Unique ID like "c1", "c2", etc.
- `value`: The flow value as stated (number, range, or temporal description)
- `numeric_value`: Numeric value if extractable, null for temporal
- `units`: "cfs", "cubic feet per second", "temporal", etc.
- `is_mandated`: true if mandate language present ("shall", "must", "required", "Article X")
- `is_temporal`: true for temporal minimums (hourly generation requirements)
- `is_operational`: true for operational targets without mandate language
- `location`: "at_dam", "downstream_gage", "instream", "unknown"
- `source_type`: "paragraph", "table", "list", "article"
- `raw_evidence`: The exact text containing the requirement (200 char max)

**EXAMPLES**:

**Example 1 - Mandated minimum**:
Text: "Article 401 requires the Licensee to release a minimum of 3,000 cfs year-round"
```json
{{
  "candidates": [
    {{
      "candidate_id": "c1",
      "value": "3,000 cfs",
      "numeric_value": 3000,
      "units": "cfs",
      "is_mandated": true,
      "is_temporal": false,
      "is_operational": false,
      "location": "at_dam",
      "source_type": "paragraph",
      "raw_evidence": "Article 401 requires the Licensee to release a minimum of 3,000 cfs year-round"
    }}
  ]
}}
```

**Example 2 - Temporal minimum**:
Text: "The project shall release a 24-hour minimum discharge equivalent to one hour of generation daily"
```json
{{
  "candidates": [
    {{
      "candidate_id": "c1",
      "value": "1 hour generation daily",
      "numeric_value": null,
      "units": "temporal",
      "is_mandated": true,
      "is_temporal": true,
      "is_operational": false,
      "location": "at_dam",
      "source_type": "paragraph",
      "raw_evidence": "The project shall release a 24-hour minimum discharge equivalent to one hour of generation daily"
    }}
  ]
}}
```

**Example 3 - No minimum found**:
```json
{{
  "candidates": []
}}
```

Now analyze this text and extract ALL minimum flow candidates with complete metadata:

DOCUMENT TEXT:
{chunk_text}

Return ONLY the JSON object with the candidates array. Do NOT include any other text."""


def extract_structured_candidates_from_chunk(chunk: str, chunk_id: int) -> List[Dict]:
    """Extract structured candidates from a single chunk using V17 prompt."""
    
    prompt = get_structured_extraction_prompt().format(chunk_text=chunk)
    
    payload = {
        "model": "llama3.3:70b",
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.1, "top_p": 0.9, "num_ctx": 8192}
    }
    
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=120)
        response.raise_for_status()
        result_text = response.json()["response"].strip()
        
        # Try to parse JSON
        if result_text.startswith("{"):
            data = json.loads(result_text)
        elif "```json" in result_text:
            json_match = re.search(r'```json\s*\n(.*?)\n```', result_text, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(1))
            else:
                return []
        elif "```" in result_text:
            json_match = re.search(r'```\s*\n(.*?)\n```', result_text, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(1))
            else:
                return []
        else:
            return []
        
        candidates = data.get("candidates", [])
        
        # Add chunk_id to each candidate
        for candidate in candidates:
            candidate['chunk_id'] = chunk_id
        
        return candidates
        
    except Exception as e:
        print(f"      ⚠️ Extraction error on chunk {chunk_id}: {e}")
        return []


def extract_all_structured_candidates(chunks: List[str]) -> List[Dict]:
    """Extract structured candidates from all chunks."""
    
    all_candidates = []
    
    for i, chunk in enumerate(chunks, 1):
        candidates = extract_structured_candidates_from_chunk(chunk, i)
        if candidates:
            print(f"      ✅ Chunk {i}: Extracted {len(candidates)} candidates")
            all_candidates.extend(candidates)
        else:
            print(f"      ⚪ Chunk {i}: No candidates")
    
    return all_candidates
