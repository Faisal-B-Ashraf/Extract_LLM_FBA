# Data Directory

## Overview
This directory contains input PDFs, validation data, and supporting files for the minimum flow extraction pipeline.

## Files and Folders

### `input_pdfs/`
**PDF documents to be processed**
- **FERC Licenses**: 43 hydropower license documents (1978-2018)
- **Water Control Manuals**: 7 operational manuals (2014-2021)
- **Total**: 50 regulatory documents

**Naming conventions:**
- FERC: `P[number]_License_[YYYYMMDD].pdf`
- WCMs: `[ProjectName]_WCM_[YEAR].pdf`

### `Observed.csv`
**Ground truth validation dataset**

Human-verified minimum flow values used to validate pipeline accuracy.

**Purpose:**
- Benchmark for pipeline accuracy
- Contains target values that should be extracted
- Used by validation scripts to measure performance

**Structure:**
- **58 entries** across 54 documents (some have multiple values)
- **Columns**:
  - `filename`: PDF document name
  - `Project name`: Hydropower project identifier
  - `Value`: Minimum flow requirement (cubic feet per second)
  - Additional metadata fields

**Creation Process:**
1. Manual extraction by domain experts
2. Review of regulatory language and context
3. Standardization to consistent units (cfs)
4. Cross-validation of complex cases

### Validation Scope

Of the 58 ground truth entries:
- **54 have matching documents** in input_pdfs/
- **4 are supplementary** (multiple flows for same project)
- Pipeline tested against all 54 document-matched entries
- Current accuracy: **88.9%** (48 correct extractions)

## Data Sources

**FERC License Documents:**
- Publicly available from FERC eLibrary
- Official hydropower project licenses
- Contain minimum flow requirements as license conditions

**Water Control Manuals:**
- U.S. Army Corps of Engineers operational manuals
- Define operational rules including minimum flows
- Cover major dam projects (Fort Peck, Grand Coulee, etc.)

## Usage

### Pipeline Processing
```bash
# Pipeline reads PDFs from input_pdfs/
cd src
python llama_70b_complex_pipeline.py
```

### Validation
```bash
# Compare pipeline output against Observed.csv
cd src
python compare_v14_results.py
```

## Data Privacy

All documents are publicly available regulatory filings. No proprietary or confidential information is included.
