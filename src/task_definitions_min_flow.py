def get_prompts():
    """
    Returns task-specific prompts and instructions for extracting data from documents.
    """
    return {
        "Project_Name": """
You are an assistant that extracts the official hydropower project name from regulatory and technical documents. The project name may differ from the dam name and is often found in the document title, introduction, or licensing sections.

Instructions:
- Search for the official project name, which may include terms like "Hydroelectric Project," "Hydropower Project," or similar.
- If multiple names are mentioned, select the one most clearly identified as the project name in the context of licensing or regulation.
- If the project name is not explicitly stated, return "Not mentioned."
- Do not confuse the project name with the physical dam name unless they are clearly the same.

Respond ONLY with this JSON format:
{{
    "value": "[Official project name, or 'Not mentioned']",
    "inferred_context": "[The sentence or section where the project name was found, or 'Not mentioned.']",
    "exact_sentences": "[Exact sentence(s) where the project name was found, or 'Not mentioned.']"
}}
Do not include any text outside this JSON object.

Question: {{question}}
""",

        "Project_Location": """
You are an assistant that extracts the official location of a hydropower project from regulatory and technical documents.

Instructions:
- Search for the project's location, which may be described in the introduction, summary, or licensing sections.
- Extract as much detail as possible: river, city/town, county, and state.
- Look for phrases like "located on", "situated on", "on the [River Name]", or geographic descriptions.
- If multiple locations are mentioned, select the one most clearly identified as the project's official location.
- If the location is not explicitly stated, return "Not mentioned."

Respond ONLY with this JSON format:
{{
    "value": "[Project location (e.g., 'Smith River, near Springfield, Clark County, Ohio'), or 'Not mentioned']",
    "inferred_context": "[The sentence or section where the location was found, or 'Not mentioned.']",
    "exact_sentences": "[Exact sentence(s) where the location was found, or 'Not mentioned.']"
}}

Question: {{question}}
""",

        "Minimum_Flow": """
V12 Enhanced Minimum Flow Extraction Prompt (2024-07)

Extract any minimum discharge ("minimum flow") that must be released downstream from a dam, powerhouse, or project, as required by any regulatory document (WCM, FERC license, system manual, etc.).

INCLUDE as "minimum flow":
- Any explicit, operational, legal, or practical minimum flow that is mandated at the dam or any specific downstream point—for any reason, at any time, and for any duration (year-round, seasonal, conditional, for events, or even short periods).
- All values labeled or described as minimum, required, or base flow—including special/exceptional minimums (e.g., for fish passage, navigation, water quality, emergencies, refill, or downstream projects).
- System or downstream requirements: If a project must discharge enough water to maintain a minimum flow at a downstream location (even if not at the dam itself), record this as a "minimum flow" with an explanation of the location and operational context.
- Conditional minimums: Include minimums that apply only in certain circumstances (e.g., during fish spawning, drought, navigation windows, or other management events). Extract all applicable values (not just the highest or lowest).
- Any minimum specified in cfs, cms, inches over crest, hours of generation, or other quantifiable criteria (with unit specified).
- **TEMPORAL MINIMUMS (V16.5.1 - CRITICAL)**: Include requirements stated as time-based generation (e.g., "1 hour generation daily", "0.5 hour generation every other day", "discharge equivalent to one hour of generation"). These are VALID minimum flow requirements - DO NOT convert to cfs, preserve the temporal description exactly as stated.
- Non-volumetric minimums: Include requirements stated as physical measurements (e.g., "1-inch veil over dam," "maintain elevation at X feet") - these are valid minimum flow requirements.
- Percentage-based minimums: Include requirements stated as percentages of inflow (e.g., "release minimum of 10% of inflow" or "pass 80% of weekly average") - state both percentage and approximate cfs if calculable.
- Run-of-river requirements: If license mandates "outflow must equal/approximate inflow" with no numeric minimum, state this as the requirement type.
- Multiple minimums: If more than one applies (by season, event, or management goal), extract all with context.

DO NOT include:
- Historical or obsolete minimums no longer in force (pre-2010).
- Flows that are "typical," "average," or "usual" but not required.
- OBSERVED flows that are not mandated (e.g., "the gage records a minimum flow of X cfs" without stating it's required).
- LEAKAGE or incidental flows (e.g., "from leakage through gates") unless explicitly mandated.
- Equipment capacity or turbine ratings (e.g., "minimum hydraulic capacity") unless they represent actual flow requirements.
- Recommendations or values that are not operationally binding.
- Rate limits or operational constraints that are not actual minimum flow requirements.
- Flood control operations or maximum release constraints (these are operational ceilings, not minimum floors).

CRITICAL - FLOW VALUE TYPE HIERARCHY (V15.8):
When multiple flow values exist in the document, you MUST distinguish between different TYPES of flows and prioritize them correctly:

1. LICENSE ARTICLE MINIMUM FLOW REQUIREMENTS (HIGHEST PRIORITY):
   - Look for: "Article XXX requires/mandates", "licensee shall maintain", "continuous minimum flow", "bypass reach flow"
   - These are LEGAL REQUIREMENTS specific to the hydropower project
   - Example: "Article 105: maintain 55 cubic feet per second" → Extract 55 cfs
   
2. OPERATIONAL SCHEDULES FROM OTHER ENTITIES (MEDIUM PRIORITY):
   - Look for: flows maintained by "Corps", "USACE", "BOR", "dam operator" (NOT the hydropower licensee)
   - These may be mentioned but are NOT the project's minimum if project "follows" or "operates using" these flows
   - Example: "Corps maintains minimum flow of 100 cfs" + "project operates using Corps flows" → NOT the project's minimum
   
3. HISTORICAL STREAMFLOW DATA/STATISTICS (LOWEST PRIORITY - DO NOT EXTRACT):
   - Look for: "low flow", "high flow", "average flow", "flows based on measurements from [dates]", "flow parameter"
   - These are OBSERVATIONAL DATA, not requirements
   - Example: "low flow: 18 cfs, high flow: 160 cfs based on 1978-1981 measurements" → DO NOT extract these
   - These may appear in environmental impact sections describing existing conditions - they are NOT minimum flow requirements

WHEN MULTIPLE TYPES EXIST:
- ALWAYS prioritize License Article requirements (Type 1) over operational schedules (Type 2) over historical data (Type 3)
- Example: Document contains "Article 105: 55 cfs" + "Corps maintains 100 cfs" + "historical low flow: 18 cfs, high flow: 160 cfs"
  → Extract ONLY "55 cfs" from Article 105 (Type 1 - highest priority)
- Example: Document contains "project operates using flows provided by Corps" + "Corps maintains 100 cfs minimum"
  → Extract "No separate minimum flow required" (project follows Corps, has no independent requirement)

CRITICAL - UNIT VALIDATION (V15.7):
- ONLY extract values with FLOW UNITS: 'cfs', 'cubic feet per second', 'cms', 'cubic meters per second', 'gpm', 'gallons per minute', 'dsf', or similar flow rate units.
- REJECT and IGNORE values with NON-FLOW UNITS like 'kW' (kilowatts), 'MW' (megawatts), 'acres', 'acre-feet', 'feet', 'meters', 'hours' (unless explicitly stated as flow requirement like '1 hour generation requirement equals X cfs').

CRITICAL CLASSIFICATION RULES:
0. MANDATED vs OBSERVED: ONLY extract flows that are REQUIRED, MANDATED, or LEGALLY BINDING. Look for words like "shall," "must," "required," "mandated," "license condition," "Article XXX requires." REJECT flows described as "observed," "typical," "recorded," "approximately," or "leakage" unless explicitly mandated.
1. HISTORICAL vs CURRENT: ONLY extract requirements currently in force (2010-present). REJECT any flows described as "historical," "past," "in 1948," "prior to," "previously," "former," or with dates older than 2010. Look for "current," "present," "now," "effective," or recent regulatory language.
2. OPERATIONAL CONSTRAINTS vs MINIMUMS: Do not confuse release rate limits (e.g., "increases limited to X cfs per hour") with minimum flow requirements.
2.5. NO SEPARATE REQUIREMENT DETECTION (V15.8 - EXPANDED): If the document explicitly states that the hydropower project has no independent minimum flow requirement and instead follows another entity's operational schedule, then:
   
   DETECT these patterns indicating no separate requirement:
   - "no separate minimum flow requirement"
   - "must follow USACE/Corps/BOR minimums"
   - "operates according to Corps schedule"
   - "operates as directed by Corps/USACE/BOR"
   - "shall operate...as provided by Corps/USACE"
   - "using flows provided by Corps/USACE/BOR"
   - "utilizing flows...provided by Corps/USACE"
   - "project will only use flows released under dam's operating schedule"
   - "releases are controlled by USACE/Corps/BOR"
   - "follows [entity] operating schedule"
   - "operated in conjunction with [entity] releases"
   
   When detected, respond with:
   - value: "No separate minimum flow required"
   - inferred_context: "The hydropower project has no independent minimum flow requirement. The project operates [as directed by/using flows provided by/according to schedule of] the [Corps/USACE/BOR] and uses whatever flows are released by the [dam operator]. The [entity] maintains [X cfs] operational minimum for the dam, but this is not a requirement of the hydropower project itself."
   - Do NOT extract the Corps/USACE/BOR operational minimum (e.g., "Corps maintains 100 cfs") as the project's minimum
   
   Example: Document states "licensee shall operate the project as directed by the Corps" and "utilizing flows as provided by the Corps" and separately mentions "a minimum flow of 100 cfs is provided at all times [by the Corps]"
   → Extract: value="No separate minimum flow required", context="Project operates as directed by Corps using flows provided by Corps. Corps maintains 100 cfs operational minimum for dam operations, but hydropower project has no independent requirement."
3. MULTIPLE MINIMUMS: When multiple minimums exist (seasonal, operational, exceptional), extract ALL with precise operational context, including ranges (e.g., "70,000-100,000 cfs"). 
   - For SEASONAL flows: Put ABSOLUTE LOWEST in "value", then list all seasonal variations with complete timing in "inferred_context"
   - For TIERED flows (e.g., Tier A/B based on inflow): Put ABSOLUTE LOWEST tier in "value", document all tiers with conditions in "inferred_context"
   - For LIMITED/EXCEPTIONAL flows alongside typical minimums: Put the ABSOLUTE LOWEST in "value" (even if exceptional), document typical and exceptional in "inferred_context"
   - Example: Bonneville has 70k-80k instantaneous, 100k daily, 58k exceptional → value="58,000 cfs", inferred_context explains all three with complete operational context
4. GENERATION-BASED REQUIREMENTS: Include requirements stated as generation hours/schedules if they represent minimum discharge obligations.
5. DOWNSTREAM COORDINATION: Include flows required to maintain downstream minimum flows at other projects/locations.

Respond ONLY with this JSON format:
{{
    "value": "[ABSOLUTE LOWEST minimum flow value with units - even if exceptional/conditional, or 'No minimum flow required', or 'Not mentioned']",
    "inferred_context": "[COMPREHENSIVE explanation listing ALL minimum flow requirements: (1) Base/typical operational minimums with purposes, (2) Seasonal variations with exact timing, (3) Exceptional/conditional minimums with triggers, (4) Clear explanation of why each minimum exists and when it applies. For multiple minimums, list EVERY value with complete context.]",
    "exact_sentences": "[ALL sentences and passages that mention ANY minimum flow value - not just the lowest. Include complete text for base minimums, seasonal minimums, and exceptional minimums so reader has full picture.]"
}}

CRITICAL - For "value" field when MULTIPLE minimums exist:
- Put the ABSOLUTE LOWEST minimum in the "value" field (even if it's exceptional, conditional, or limited duration)
- List ALL minimum flow values with COMPLETE explanations in "inferred_context" (base + seasonal + exceptional + conditional)
- Include ALL supporting sentences for ALL minimums in "exact_sentences" (not just the lowest) so the user has complete context
- Example: Bonneville has 70,000-80,000 cfs instantaneous, 100,000 cfs daily, and 58,000 cfs exceptional:
  - value: "58,000 cfs"
  - inferred_context: "Multiple minimum flows: (1) BASE OPERATIONAL: 70,000-80,000 cfs minimum instantaneous flows depending on weekly inflow, for peaking operations, efficient use of Second Powerhouse, and navigation; (2) DAILY MINIMUM: 100,000 cfs minimum daily flow (or 80% of weekly inflow, minimum 70,000 cfs); (3) EXCEPTIONAL MINIMUM: 58,000 cfs allowed only between November 1 and January 15 when minimum releases cause tailwater to exceed 11.5 feet during chum spawning. The 58,000 cfs represents the absolute lowest flow permitted under any circumstances, based on navigational requirements for commercial vessels."
  - exact_sentences: [Include ALL text passages mentioning 70,000 cfs, 80,000 cfs, 100,000 cfs, AND 58,000 cfs with their complete contexts and explanations]

Always:
- PRIORITIZE: Extract the ABSOLUTE LOWEST minimum flow value (even if exceptional/conditional) in the "value" field
- For seasonal-only minimums (no year-round base): Put the ABSOLUTE LOWEST seasonal value in "value", list all seasonal values with months in "inferred_context"
  - Example: If only seasonal flows exist (e.g., "50 cfs Jan-Mar, 100 cfs Apr-Jun, 75 cfs Jul-Dec"), put "50 cfs (lowest seasonal minimum)" in value
  - If seasonal values include "or inflow if less" clause, include that: "30 cfs (lowest seasonal, or inflow if less)"
- For conditional-only minimums (no base flow): State the primary condition and flow in "value", explain conditions in "inferred_context"
  - Example: "100 cfs when inflow > 500 cfs, otherwise natural flow"
- For multiple location-specific minimums: Prioritize the PRIMARY PROJECT LOCATION or MOST RESTRICTIVE value in "value"
  - Example: Reynolds Creek has bypassed reach (10 cfs) and anadromous reach (12 cfs) - put "10 cfs bypassed reach, 12 cfs anadromous reach" or prioritize the most critical reach
- For complex operational minimums with MULTIPLE types (instantaneous, daily, weekly):
  - Put the ABSOLUTE LOWEST in "value" field (even if exceptional)
  - Document ALL types (instantaneous, daily, exceptional) in "inferred_context" with complete explanations
  - Example: Bonneville value="58,000 cfs", context explains 70k-80k instantaneous, 100k daily, and 58k exceptional with full details
- For run-of-river with no numeric minimum: State "Run-of-river operation (outflow must equal/approximate inflow)" in value
- For non-volumetric minimums: State the requirement as given (e.g., "1-inch veil over dam at all times" or "1 hour generation daily")
- Clearly state the context and operational purpose of each minimum flow
- DISTINGUISH between:
  - OPERATIONAL minimums (for navigation, power generation, dam operations) - typically larger flows
  - ENVIRONMENTAL minimums (for fish, habitat, spawning) - typically base requirements
  - EXCEPTIONAL minimums (drought, special events, temporary conditions) - note as conditional
  - LIMITED exceptions (e.g., "0 cfs Dec-Feb limited" when typical minimum exists) - note as exception, prioritize typical minimum
  - Check for keywords: "limited," "allowed," "exceptional," "emergency," "temporary" to identify exceptions vs requirements
- If the minimum is not required at the dam but at a downstream location, specify this in "inferred_context"
- If no minimum flow is required in the current document, state "No minimum flow required" in value, and explain why (e.g., "Corps-controlled releases," "No separate requirement," "Off-site mitigation in lieu of minimum flow")
- For complex multiple minimums (e.g., Bonneville has instantaneous, daily, and exceptional minimums), put the ABSOLUTE LOWEST value in "value" field (even if exceptional), then document ALL minimums with complete operational context in "inferred_context" and include all relevant text in "exact_sentences"
  - Example: Bonneville has 70,000-80,000 cfs instantaneous, 100,000 cfs daily, 58,000 cfs exceptional
  - value: "58,000 cfs"
  - inferred_context: "Multiple minimum flows with distinct purposes: (1) OPERATIONAL BASE: 70,000-80,000 cfs minimum instantaneous flows (varies with weekly inflow) for peaking operations, Second Powerhouse efficiency, and navigation; (2) DAILY REQUIREMENT: 100,000 cfs minimum daily flow or 80% of weekly inflow (minimum 70,000 cfs); (3) EXCEPTIONAL ALLOWANCE: 58,000 cfs represents absolute lowest flow permitted, allowed only Nov 1-Jan 15 when standard minimum releases cause tailwater elevation to exceed 11.5 feet during chum spawning period. This exceptional minimum was established based on navigational requirements for commercial vessels in the Federal navigation channel."
  - exact_sentences: [Include ALL passages from document that mention 70,000 cfs, 80,000 cfs, 100,000 cfs, AND 58,000 cfs - provide complete sentences with full context for each value so user understands all requirements and their conditions]

Question: {{question}}
"""
    }
