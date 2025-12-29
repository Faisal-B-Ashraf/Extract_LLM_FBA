# Minimum Flow Extraction Pipeline

**Automated extraction of minimum flow requirements from hydropower regulatory documents using LLM-assisted analysis.**

## Overview

This pipeline automatically extracts minimum flow requirements from FERC hydropower licenses and Water Control Manuals (WCMs). It processes PDF documents, identifies relevant flow requirements, and uses intelligent scoring to select the most authoritative values.

## Purpose

**What it does:**
- Extracts minimum flow requirements from regulatory PDFs
- Processes FERC licenses (1978-2018) and Water Control Manuals (2014-2021)
- Identifies flow values with context and supporting evidence
- Validates against human-verified ground truth data

**Why it exists:**
Manually reviewing hundreds of regulatory documents to extract minimum flow requirements is time-consuming and error-prone. This pipeline automates the extraction process while maintaining high accuracy through intelligent candidate scoring.

## Performance

- **Accuracy:** 88.9% on validated test set (48 of 54 documents)
- **Speed:** ~10 minutes per document
- **Coverage:** Processes 50 regulatory documents (43 FERC licenses + 7 WCMs)

## Repository Structure

```
├── src/                                    # Production pipeline
│   ├── llama_70b_complex_pipeline.py     # Main extraction pipeline
│   ├── api_handler.py                     # LLM interface and chunking
│   ├── flow_scoring.py                    # Candidate scoring logic
│   ├── task_definitions_min_flow.py       # Extraction prompts
│   ├── pdf_processor_min_flow.py          # PDF text extraction
│   └── config.py                          # Configuration
├── data/                                   # Input data and validation
│   ├── input_pdfs/                        # PDF documents to process
│   └── Observed.csv                       # Ground truth validation data
├── experimental_llm_reasoning/            # Experimental approaches
├── results/                               # Output files
└── requirements.txt                       # Python dependencies
```

## Quick Start

### 1. Prerequisites

**System Requirements:**
- Python 3.8 or higher
- 16GB+ RAM recommended (for Llama 70B)
- ~40GB disk space for model

**Install Ollama:**
```bash
# Linux
curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama server
ollama serve &

# Download Llama 3.3 70B model (~40GB download)
ollama pull llama3.3:70b

# Verify installation
ollama run llama3.3:70b "Test message"
```

### 2. Setup Pipeline

```bash
# Clone repository
git clone https://github.com/Faisal-B-Ashraf/Extract_LLM_FBA.git
cd Extract_LLM_FBA

# Install Python dependencies
pip install -r requirements.txt

# Verify setup
./setup.sh
```

### 3. Add PDF Documents

```bash
# Copy PDFs to input folder
cp /path/to/your/pdfs/*.pdf data/input_pdfs/

# Or use symbolic links
ln -s /path/to/pdf/folder/* data/input_pdfs/
```

### 4. Run Extraction Pipeline

```bash
cd src
python llama_70b_complex_pipeline.py
```

**Output:**
- `min_flow_results.csv` - Extracted minimum flow values with context
- `min_flow_timing_results.csv` - Processing time per document
- `extracted_chunks_*.txt` - Intermediate text chunks (for debugging)

## How It Works

### 1. Document Processing
- Extracts text from PDF documents using PyPDF2
- Splits text into manageable chunks (~500 tokens each)
- Preserves document structure and context

### 2. Candidate Extraction
- Uses Llama 3.3 70B to identify potential minimum flow values in each chunk
- Extracts supporting context and exact source sentences
- Captures multiple candidates per document

### 3. Intelligent Scoring
- Scores candidates based on:
  - **Regulatory language** (mandatory vs advisory)
  - **Location specificity** (at dam, downstream, at gage)
  - **Temporal constraints** (continuous, seasonal, conditional)
  - **Numeric precision** (range bounds, exact values)
- Selects highest-scored candidate as final answer

### 4. Validation
- Compares results against human-verified ground truth
- Provides detailed extraction context for manual review

## Document Types

**FERC Hydropower Licenses** (43 documents)
- Date range: 1978-2018
- Format: P[number]_License_[YYYYMMDD].pdf
- Example: P1051_License_20070817.pdf

**Water Control Manuals** (7 documents)
- Date range: 2014-2021
- Format: [ProjectName]_WCM_[YEAR].pdf
- Example: FortPeck_WCM_2018.pdf

## Configuration

Edit `src/config.py` to customize:
- PDF input folder location
- LLM model selection
- API endpoints
- Output file paths

## Validation

Ground truth data in `data/Observed.csv` contains human-verified minimum flow values for 54 documents. The pipeline achieves 88.9% accuracy against this validation set.

## Troubleshooting

**"Ollama server not responding"**
- Ensure Ollama is running: `ollama serve &`
- Check server status: `curl http://localhost:11434/api/tags`

**"Model not found"**
- Download model: `ollama pull llama3.3:70b`
- Verify available models: `ollama list`

**Slow processing**
- Llama 70B requires significant compute resources
- Expected: ~10 minutes per document
- Consider using GPU acceleration if available

**Low accuracy on custom documents**
- Pipeline is optimized for FERC licenses and WCMs
- May require prompt tuning for other document types
- See `task_definitions_min_flow.py` for prompt engineering

## License

MIT License - See LICENSE file for details.
