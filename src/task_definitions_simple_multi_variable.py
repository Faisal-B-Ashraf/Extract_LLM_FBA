"""
Simple Prompt Definitions for Multi-Variable Extraction (Pipeline 3)

Purpose: Simple, direct prompts for extracting multiple variables without 
complex scoring or filtering mechanisms. Designed for comparison against
sophisticated targeted extraction (Pipeline 1).

Approach:
- Direct, straightforward prompts
- No contextual scoring hints
- No multi-step reasoning requirements
- Single-question format per variable

Variables:
1. Project/Dam name
2. Owner/Operator
3. Location (County, City, River)
4. Generation capacity
5. Plant type (run-of-river vs. peaking)
6. Licensing dates
7. Key stakeholders
8. Project costs
9. Migratory fish species
10. Minimum flow requirements
"""

def get_simple_prompt(variable_name):
    """
    Get improved direct prompt for each variable.
    
    More sophisticated than bare-bones extraction, but still single-step without
    post-processing or scoring mechanisms.
    
    Args:
        variable_name: Name of variable to extract
        
    Returns:
        Extraction prompt string
    """
    
    prompts = {
        "project_name": """Extract the official project name or dam name from this document.

Look for:
- Title or header identifying the project/dam
- FERC project numbers (P-XXXX) with associated names
- Dam names in Water Control Manuals
- Official facility designations

Return the most complete project name found. If multiple names exist (e.g., "Project No. 1234, Smith Dam"), return the full designation.

If not found, return "Not mentioned".""",
        
        "owner_operator": """Extract the owner and/or operator of this hydroelectric project or dam.

Look for:
- Licensee names in FERC documents
- Operating entities mentioned in the document
- Organizations responsible for dam operations
- Utility companies or agencies

Return all relevant owner/operator names. Include both if different (e.g., "Owned by ABC Corp, Operated by XYZ Utility").

If not found, return "Not mentioned".""",
        
        "location_county": """Extract the county or counties where this project/dam is located.

Look for:
- Explicit mentions of county names
- Geographic descriptions including county
- Address information mentioning county
- Jurisdictional descriptions

Return the county name(s). If multiple counties, list all (e.g., "Snohomish and King Counties").

If not found, return "Not mentioned".""",
        
        "location_city": """Extract the nearest city, town, or community to this project/dam.

Look for:
- City or town names in location descriptions
- "Near [city]" or "Located in [city]"
- Municipal jurisdictions mentioned
- Geographic reference points

Return the city/town name. If multiple locations mentioned, prioritize the nearest one.

If not found, return "Not mentioned".""",
        
        "location_river": """Extract the river, stream, or water body where this project/dam is located.

Look for:
- River names in project descriptions
- Water body names (rivers, creeks, lakes, reservoirs)
- Tributaries or confluences mentioned
- Geographic water features

Return the primary water body name (e.g., "Columbia River" or "Snake River tributary").

If not found, return "Not mentioned".""",
        
        "generation_capacity": """Extract the hydroelectric generation capacity or total installed capacity of this project.

Look for:
- Nameplate capacity (MW or kW)
- Total installed capacity
- Powerhouse capacity
- Generation unit specifications

Return the capacity with units (e.g., "50 MW" or "12,500 kW"). If multiple units, provide total capacity.

If not found, return "Not mentioned".""",
        
        "plant_type": """Determine the operational type of this hydroelectric facility.

Classification:
- Run-of-river: Minimal or no storage, flows through continuously
- Peaking: Storage reservoir, releases vary based on power demand
- Pumped storage: Can pump water back up

Look for:
- Explicit plant type designations
- Operational descriptions (daily peaking, base load, etc.)
- Storage capacity and operational patterns
- Reservoir descriptions

Return ONLY: "run-of-river", "peaking", "pumped storage", or "Not mentioned".""",
        
        "licensing_dates": """Extract key licensing dates for this FERC-licensed project.

Look for:
- Original license date
- License issuance date
- Amendment dates
- License expiration date
- Relicensing dates

Return all significant dates found with context (e.g., "Original license: April 27, 1988; Amendment: June 15, 2005").

If not found, return "Not mentioned".""",
        
        "key_stakeholders": """Extract key stakeholders involved with or consulted regarding this project.

Look for:
- Federal agencies (FERC, USFWS, NMFS, EPA, Corps of Engineers)
- State agencies (water resources, fish and wildlife, environmental)
- Tribal nations or indigenous communities
- Environmental organizations
- Local governments
- Utility companies

Return a brief list of major stakeholders (e.g., "FERC, U.S. Fish and Wildlife Service, Yakama Nation, Washington Department of Ecology").

If not found, return "Not mentioned".""",
        
        "project_costs": """Extract any project-related costs, expenditures, or financial information mentioned.

Look for:
- Construction costs
- Annual operational costs
- Mitigation measure costs
- Environmental compliance costs
- Capital improvements
- Specific dollar amounts with context

Return costs with context (e.g., "Construction: $45 million; Annual O&M: $2.3 million; Fish passage: $8 million").

If not found, return "Not mentioned".""",
        
        "migratory_fish_species": """Extract migratory or anadromous fish species mentioned in relation to this project.

Look for:
- Salmon species (Chinook, Coho, Sockeye, etc.)
- Steelhead trout
- Other migratory fish
- Species requiring fish passage or protection measures
- ESA-listed species

Return species names (e.g., "Chinook salmon, Steelhead, Bull trout").

If not found, return "Not mentioned".""",
        
        "minimum_flow": """Extract the minimum flow requirement or minimum release requirement for this project.

Look for:
- Minimum instantaneous flow (cfs, cubic feet per second)
- Minimum daily average flow
- Base flow requirements
- Environmental flow requirements
- Required continuous releases
- License article requirements specifying flows

Return the flow value with units and any important conditions (e.g., "500 cfs continuous" or "50 cfs April-October, 30 cfs November-March").

If multiple flow requirements exist, return the most specific or restrictive.

If not found, return "Not mentioned"."""
    }
    
    return prompts.get(variable_name, f"Extract information about {variable_name}")

def get_all_variables():
    """
    Get list of all variables to extract.
    
    Returns:
        List of variable names
    """
    return [
        "project_name",
        "owner_operator",
        "location_county",
        "location_city", 
        "location_river",
        "generation_capacity",
        "plant_type",
        "licensing_dates",
        "key_stakeholders",
        "project_costs",
        "migratory_fish_species",
        "minimum_flow"
    ]

def get_variable_description(variable_name):
    """
    Get human-readable description of variable.
    
    Args:
        variable_name: Name of variable
        
    Returns:
        Description string
    """
    descriptions = {
        "project_name": "Project or dam name",
        "owner_operator": "Owner/operator organization(s)",
        "location_county": "County location",
        "location_city": "City/town location",
        "location_river": "River or water body",
        "generation_capacity": "Power generation capacity (MW or kW)",
        "plant_type": "Plant type (run-of-river or peaking)",
        "licensing_dates": "FERC license dates",
        "key_stakeholders": "Key stakeholders (agencies, tribes, etc.)",
        "project_costs": "Project-related costs",
        "migratory_fish_species": "Migratory fish species present",
        "minimum_flow": "Minimum flow requirement (cfs)"
    }
    
    return descriptions.get(variable_name, variable_name)
