# Data Description

## Overview
This directory contains the ground truth data and test cases used in our LLM pipeline comparison study.

## Files

### `Observed.csv`
**Human-verified ground truth dataset**
- **Source**: Expert manual extraction from regulatory documents
- **Size**: 58 verified entries
- **Columns**:
  - `filename`: PDF document identifier
  - `Project name`: Official project name
  - `Value`: Human-extracted minimum flow value
  - Additional contextual information

### `min_flow_results4.csv`
**70B model baseline results**
- **Source**: Llama 3.3 70B complex pipeline extraction
- **Size**: 54 matched test cases
- **Columns**:
  - `filename`: Document identifier
  - `Project_Name`: Extracted project name
  - `Minimum_Flow Value`: Extracted minimum flow
  - `Minimum_Flow Inferred Context`: Source text context
  - `Minimum_Flow Exact Sentences`: Exact extraction source

## Ground Truth Validation Process

1. **Expert Review**: Human experts manually extracted minimum flow requirements from 58 regulatory documents
2. **Cross-Validation**: Multiple reviewers validated complex cases
3. **Standardization**: Values normalized to consistent units (cfs - cubic feet per second)
4. **Quality Control**: Entries with ambiguous or conflicting information were flagged

## Test Case Matching

Of the 58 ground truth entries, 54 were successfully matched with document text chunks for model testing, providing a robust validation dataset for our comparative analysis.

## Usage in Experiments

Both complex and simple pipeline approaches use this ground truth data for:
- **Accuracy measurement**: Direct comparison against human extractions
- **Consistency validation**: Ensuring fair comparison across all 4 models
- **Error analysis**: Understanding model failure patterns

## Data Privacy

All documents used are publicly available regulatory filings. No sensitive or proprietary information is included in this dataset.
