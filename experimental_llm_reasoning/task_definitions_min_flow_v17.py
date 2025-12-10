"""
V17 STRUCTURED EXTRACTION - Returns full metadata for RLS decision-making
"""

def get_prompts_v17():
    """
    V17: Returns structured JSON with metadata fields required for deterministic selection + RLS
    """
    return {
        "Project_Name": """
You are an assistant that extracts the official hydropower project name from regulatory and technical documents.

Instructions:
- Extract the official project name (e.g., "Fort Peck Hydroelectric Project")
- If not found, return "Not mentioned"

Respond ONLY with this JSON format:
{
    "value": "[Project name or 'Not mentioned']",
    "inferred_context": "[Source sentence]",
    "exact_sentences": "[Exact text]"
}

Question: {{question}}
""",

        "Project_Location": """
You are an assistant that extracts the official location of a hydropower project.

Instructions:
- Extract location with river, city, county, state
- If not found, return "Not mentioned"

Respond ONLY with this JSON format:
{
    "value": "[Location or 'Not mentioned']",
    "inferred_context": "[Source sentence]",
    "exact_sentences": "[Exact text]"
}

Question: {{question}}
""",

        "Minimum_Flow": """
**V17 STRUCTURED MINIMUM FLOW EXTRACTION**

You are extracting minimum flow requirements from hydroelectric dam regulatory documents.

**CRITICAL**: You MUST return structured JSON with metadata fields for EVERY candidate you find.

**YOUR TASK**:
1. Find ALL potential minimum flow values in the text
2. For EACH value, determine its metadata (is it mandated? temporal? at-dam? etc.)
3. Return a JSON array with ALL candidates

**OUTPUT FORMAT** (CRITICAL - FOLLOW EXACTLY):
```json
{
  "candidates": [
    {
      "candidate_id": "c1",
      "value": "3,000 cfs",
      "numeric_value": 3000,
      "units": "cfs",
      "is_mandated": true,
      "is_temporal": false,
      "is_operational": false,
      "location": "at_dam",
      "source_type": "paragraph",
      "raw_evidence": "A minimum release of 3,000 cfs was established in 1992 under Section 7-10.2.1..."
    },
    {
      "candidate_id": "c2",
      "value": "1 hour generation daily",
      "numeric_value": null,
      "units": "temporal",
      "is_mandated": true,
      "is_temporal": true,
      "is_operational": false,
      "location": "at_dam",
      "source_type": "paragraph",
      "raw_evidence": "Article 401 requires discharge equivalent to one hour of generation per day..."
    }
  ]
}
```

**FIELD DEFINITIONS**:

1. **candidate_id**: Unique ID (c1, c2, c3, ...)

2. **value**: The flow value as stated in document
   - Examples: "3,000 cfs", "70,000-100,000 cfs", "1 hour generation daily", "5-7 cfs"

3. **numeric_value**: 
   - Single number if one value (e.g., 3000)
   - Lowest value if range (e.g., 70000 for "70,000-100,000 cfs")
   - null if temporal (e.g., "1 hour generation")

4. **units**: "cfs", "cms", "temporal", "gpm", etc.

5. **is_mandated**: true/false
   - TRUE if: "shall release", "must maintain", "required", "mandated", "Article XXX requires", "license condition"
   - FALSE if: "typical", "average", "observed", "approximately", "leakage", "operational target"

6. **is_temporal**: true/false
   - TRUE if: "1 hour generation", "0.5 hour every other day", "X hours generation daily"
   - FALSE if: numeric flow in cfs/cms

7. **is_operational**: true/false
   - TRUE if: "typical operation", "normal operating range", "target flow", "operational schedule" (NOT mandated)
   - FALSE if: mandated requirement or temporal minimum

8. **location**: 
   - "at_dam" - flow at the dam/powerhouse
   - "downstream_X_miles" - flow at downstream gage (specify distance)
   - "bypass_reach" - flow in bypass reach
   - "tailrace" - flow in tailrace
   - "unknown" - location not specified

9. **source_type**:
   - "paragraph" - from text paragraph
   - "table" - from data table
   - "cost_table" - from cost/budget table (⚠️ likely hallucination)
   - "license_article" - from FERC license article
   - "figure" - from figure/diagram

10. **raw_evidence**: The EXACT sentence(s) from document that mention this value
    - Include surrounding context (50-200 characters)
    - Include Article numbers, section references
    - This is what RLS will use to judge mandate language

**EXTRACTION RULES**:

✅ **INCLUDE**:
- Mandated minimums with "shall", "must", "required", "Article XXX"
- Temporal requirements ("1 hour generation daily")
- Seasonal minimums (extract each season separately)
- Conditional minimums ("when inflow > X, release Y")
- Bypass reach flows
- Downstream gage requirements
- Run-of-river requirements
- Any value labeled "minimum flow" or "minimum release"

❌ **EXCLUDE**:
- Historical data ("low flow: 18 cfs based on 1978 measurements")
- Years, dates, percentages (unless it's "release X% of inflow")
- Equipment capacity ("turbine capacity: 5000 kW")
- Non-flow units ("acres", "MW", "feet") unless explicitly a flow requirement
- Flood control or maximum release limits
- Rate-of-change constraints ("limited to X cfs/hour increase")

**SPECIAL CASES**:

1. **No Separate Requirement**:
   If document says "project operates using Corps/USACE/BOR flows" or "no separate minimum":
   ```json
   {
     "candidates": [{
       "candidate_id": "c1",
       "value": "No separate minimum flow required",
       "numeric_value": null,
       "units": "none",
       "is_mandated": false,
       "is_temporal": false,
       "is_operational": true,
       "location": "at_dam",
       "source_type": "paragraph",
       "raw_evidence": "The licensee shall operate the project as directed by the Corps using flows provided by the Corps..."
     }]
   }
   ```

2. **Multiple Seasonal Minimums**:
   Extract EACH season as separate candidate:
   ```json
   {
     "candidates": [
       {
         "candidate_id": "c1",
         "value": "50 cfs (Jan-Mar)",
         "numeric_value": 50,
         "units": "cfs",
         "is_mandated": true,
         "is_temporal": false,
         "is_operational": false,
         "location": "at_dam",
         "source_type": "license_article",
         "raw_evidence": "Article 401: Release 50 cfs January through March for downstream fish habitat..."
       },
       {
         "candidate_id": "c2",
         "value": "100 cfs (Apr-Dec)",
         "numeric_value": 100,
         "units": "cfs",
         "is_mandated": true,
         "is_temporal": false,
         "is_operational": false,
         "location": "at_dam",
         "source_type": "license_article",
         "raw_evidence": "Article 401: Release 100 cfs April through December..."
       }
     ]
   }
   ```

3. **Cost Table Hallucinations**:
   If you see a table with $ symbols, item numbers, contractors:
   ```json
   {
     "candidate_id": "c5",
     "value": "2,900",
     "numeric_value": 2900,
     "units": "unknown",
     "is_mandated": false,
     "is_temporal": false,
     "is_operational": false,
     "location": "unknown",
     "source_type": "cost_table",
     "raw_evidence": "Item No. 2,900 - Levees - $450,000..."
   }
   ```

**RETURN FORMAT**:
You MUST return ONLY a valid JSON object with a "candidates" array.
Each candidate MUST have ALL 10 fields defined above.

Question: {{question}}
"""
    }
