# def get_prompts():
#     """
#     Returns task-specific prompts and instructions for extracting data from documents.
#     """
#     return {
#         "Project_Name": """
# You are an assistant that extracts the official hydropower project name from regulatory and technical documents. The project name may differ from the dam name and is often found in the document title, introduction, or licensing sections.

# Instructions:
# - Search for the official project name, which may include terms like "Hydroelectric Project," "Hydropower Project," or similar.
# - If multiple names are mentioned, select the one most clearly identified as the project name in the context of licensing or regulation.
# - If the project name is not explicitly stated, return "Not mentioned."
# - Do not confuse the project name with the physical dam name unless they are clearly the same.

# Respond ONLY with this JSON format:
# {{
#     "value": "[Official project name, or 'Not mentioned']",
#     "inferred_context": "[The sentence or section where the project name was found, or 'Not mentioned.']"
# }}
# Do not include any text outside this JSON object.

# Question: {{question}}
# """,

#         "Project_Location": """
# You are an assistant that extracts the official location of a hydropower project from regulatory and technical documents. The location may include river, city, county, and state.

# Instructions:
# - Search for the project's location, which may be described in the introduction, summary, or licensing sections.
# - Extract as much detail as possible: river, city/town, county, and state.
# - If multiple locations are mentioned, select the one most clearly identified as the project’s official location.
# - If the location is not explicitly stated, return "Not mentioned."
# - Do not infer location from unrelated context.

# Respond ONLY with this JSON format:
# {{
#     "value": "[Project location (e.g., 'Smith River, near Springfield, Clark County, Ohio'), or 'Not mentioned']",
#     "inferred_context": "[The sentence or section where the location was found, or 'Not mentioned.']"
# }}
# Do not include any text outside this JSON object.

# Question: {{question}}
# """,

#         "Minimum_Flow": """
# You are an expert at extracting minimum flow requirements from regulatory documents.

# Instructions:
# - Search the entire document, including tables, for any minimum flow requirements (including seasonal, monthly, or conditional values).
# - Look for phrases like "minimum flow", "minimum discharge", "not less than", "at least", or similar.
# - If a minimum flow is explicitly required by regulation or license, extract the lowest value, convert it to cfs for the "value" field, and list all original values, units, and time periods in "inferred_context".
# - If the minimum flow value is written as a number word (e.g., "three cubic feet per second"), treat it the same as a numeric value and convert it to digits (e.g., "3 cfs").
# - If the requirement is stated as "minimum flow of X cfs or the natural flow, whichever is less", extract "X cfs or natural flow" as the value.
# - If a range is given, extract the lower bound.
# - If there are multiple requirements, extract the strictest (lowest) one.
# - If the document explicitly states that no minimum flow is required, set "value" to "No minimum flow required" and provide the supporting sentence(s) in "exact_sentences".
# - If only observed or measured minimum flows are mentioned (not required), set "value" to "Observed only, not mandated" and include those values and context.
# - If minimum flow is not mentioned at all, set "value" to "Not mentioned" and "inferred_context" and "exact_sentences" to "Not applicable." or "Not mentioned."
# - Always specify units. If you convert, include the original unit and conversion factor in "inferred_context".
# - Do not infer a requirement from observed values unless the document explicitly states it is required.

# Respond ONLY with this JSON format:
# {{
#     "value": "[lowest required minimum flow in cfs, or 'No minimum flow required', or 'Observed only, not mandated', or 'Not mentioned']",
#     "inferred_context": "[all minimum flow values, units, time periods, and conversion details if any. If none, 'Not applicable.']",
#     "exact_sentences": "[exact sentence(s) or table rows where found, or 'Not mentioned.']"
# }}
# Do not include any text outside this JSON object.

# Question: {{question}}
# """
#     }



def get_prompts():
    """
    Returns task-specific prompts and instructions for extracting data from documents.
    """
    return {
        "Minimum_Flow": """
V12 Enhanced Minimum Flow Extraction Prompt (2024-07)

Extract any minimum discharge ("minimum flow") that must be released downstream from a dam, powerhouse, or project, as required by any regulatory document (WCM, FERC license, system manual, etc.).

INCLUDE as "minimum flow":
- Any explicit, operational, legal, or practical minimum flow that is mandated at the dam or any specific downstream point—for any reason, at any time, and for any duration (year-round, seasonal, conditional, for events, or even short periods).
- All values labeled or described as minimum, required, or base flow—including special/exceptional minimums (e.g., for fish passage, navigation, water quality, emergencies, refill, or downstream projects).
- System or downstream requirements: If a project must discharge enough water to maintain a minimum flow at a downstream location (even if not at the dam itself), record this as a "minimum flow" with an explanation of the location and operational context.
- Conditional minimums: Include minimums that apply only in certain circumstances (e.g., during fish spawning, drought, navigation windows, or other management events). Extract all applicable values (not just the highest or lowest).
- Any minimum specified in cfs, cms, inches over crest, hours of generation, or other quantifiable criteria (with unit specified).
- Multiple minimums: If more than one applies (by season, event, or management goal), extract all with context.

DO NOT include:
- Historical or obsolete minimums no longer in force (pre-2010).
- Flows that are "typical," "average," or "usual" but not required.
- Recommendations or values that are not operationally binding.
- Rate limits or operational constraints that are not actual minimum flow requirements.
- Flood control operations or maximum release constraints (these are operational ceilings, not minimum floors).

CRITICAL CLASSIFICATION RULES:
1. HISTORICAL vs CURRENT: ONLY extract requirements currently in force (2010-present). REJECT any flows described as "historical," "past," "in 1948," "prior to," "previously," "former," or with dates older than 2010. Look for "current," "present," "now," "effective," or recent regulatory language.
2. OPERATIONAL CONSTRAINTS vs MINIMUMS: Do not confuse release rate limits (e.g., "increases limited to X cfs per hour") with minimum flow requirements.
3. MULTIPLE MINIMUMS: When multiple minimums exist (seasonal, operational, exceptional), extract ALL with precise operational context, including ranges (e.g., "70,000-100,000 cfs").
4. GENERATION-BASED REQUIREMENTS: Include requirements stated as generation hours/schedules if they represent minimum discharge obligations.
5. DOWNSTREAM COORDINATION: Include flows required to maintain downstream minimum flows at other projects/locations.

Respond ONLY with this JSON format:
{{
    "value": "[minimum flow value with units, or 'No minimum flow required', or 'Not mentioned']",
    "inferred_context": "[Complete explanation: nature, duration, location, reason for minimum flow, seasonal variations, all applicable minimums]",
    "exact_sentences": "[Direct excerpts from source document supporting the minimum flow requirement]"
}}

Always:
- Clearly state the context and operational purpose of each minimum flow.
- If the minimum is not required at the dam but at a downstream location, specify this in "inferred_context."
- If no minimum flow is required in the current document, state "No minimum flow required" in value, and explain.
- For multiple minimums (e.g., Bonneville: 70,000–100,000 cfs operational, 58,000 cfs navigation), record ALL scenarios with precise context: "70,000-100,000 cfs typical navigation; 58,000 cfs exceptional conditions for chum spawning."

Question: {{question}}
"""
    }