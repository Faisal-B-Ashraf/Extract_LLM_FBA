# LLM-Based Extraction Pipeline for Hydropower Regulatory Documents

**Automated information extraction from FERC licenses and Water Control Manuals using large language models.**

## Overview

This repository contains the code and data accompanying the research paper on automated extraction of regulatory information from hydropower documents. The pipeline implements both simple zero-shot extraction and sophisticated targeted extraction approaches using large language models.

## Repository Structure

```
├── src/                                    # Main extraction pipelines
│   ├── llama_70b_complex_pipeline.py      # Targeted extraction pipeline (minimum flow)
│   ├── llama_70b_v18_simple.py            # Simple zero-shot extraction pipeline
│   ├── api_handler.py                     # LLM interface and document processing
│   ├── deterministic_selector.py          # Candidate scoring and selection
│   ├── task_definitions_min_flow.py       # Extraction task definitions
│   └── config.py                          # Configuration settings
├── data/                                   # Input documents and validation data
│   ├── input_pdfs/                        # Regulatory documents (50 PDFs)
│   └── Observed_LLM_comparison.csv        # Manual validation ground truth
├── experimental_llm_reasoning/            # Experimental pipeline variants
├── figures/                               # Generated figures
├── results/                               # Extraction results and analysis
└── requirements.txt                       # Python dependencies
```

## Dataset

**Document Collection:**
- 43 FERC hydropower licenses (1978-2018)
- 7 Water Control Manuals (2014-2021)
- Total: 50 regulatory documents

**Extracted Variables:**
- Project/Dam Name
- Owner/Operator
- Location (City, County, River)
- Generation Capacity
- Plant Type
- Licensing Dates
- Key Stakeholders
- Project Costs
- Migratory Fish Species
- Minimum Flow Requirements

## Installation

### Prerequisites

- Python 3.8 or higher
- Ollama server for LLM inference
- 16GB+ RAM (recommended for 70B model)

### Setup

```bash
# Clone repository
git clone https://github.com/Faisal-B-Ashraf/Extract_LLM_FBA.git
cd Extract_LLM_FBA

# Install dependencies
pip install -r requirements.txt

# Install and start Ollama server
curl -fsSL https://ollama.ai/install.sh | sh
ollama serve &

# Download required model
ollama pull llama3.3:70b
```

## Usage

### Simple Zero-Shot Extraction

Extract all ten variables from documents using direct prompting:

```bash
cd src
python llama_70b_v18_simple.py
```

**Output:** `multi_variable_simple_results.csv`

### Targeted Extraction (Minimum Flow)

Extract minimum flow requirements using sophisticated multi-step pipeline:

```bash
cd src
python llama_70b_complex_pipeline.py
```

**Output:** 
- `min_flow_results.csv` - Extracted values with context
- `min_flow_timing_results.csv` - Processing times

## Pipeline Architecture

### Simple Zero-Shot Extraction
1. Extract full text from PDF
2. Submit entire document text to LLM with variable-specific prompts
3. Parse structured JSON output

### Targeted Extraction
1. **Document Chunking:** Split document into overlapping text segments
2. **Relevance Filtering:** Identify chunks containing target information
3. **Candidate Extraction:** Extract multiple candidates with supporting context
4. **Deterministic Selection:** Score and select most authoritative candidate based on:
   - Regulatory language strength
   - Location specificity
   - Temporal constraints
   - Numeric precision

## Validation Data

Manual validation results are provided in `data/Observed_LLM_comparison.csv` containing:
- Ground truth minimum flow values
- Extraction correctness classifications
- 50 documents manually reviewed

## Analysis and Figures

Generate analysis figures from `src/`:
```bash
python create_pipeline3_figure.py         # Main performance analysis
python create_model_comparison_figure.py  # Multi-model comparison
```

## Results

Key findings from 50-document test set:
- Simple extraction: High accuracy (>90%) for structured data, lower (<50%) for complex variables
- Targeted extraction: 76% accuracy for minimum flow (vs 43% simple)
- Processing time trade-off: 8.2s (simple) vs 249.7s (targeted) per document

See paper for complete analysis.

## Configuration

Edit `src/config.py` to customize:
- PDF input folder location
- LLM model selection
- API endpoints
- Output file paths

## Troubleshooting

**Ollama server not responding:**
- Ensure Ollama is running: `ollama serve &`
- Check server status: `curl http://localhost:11434/api/tags`

**Model not found:**
- Download model: `ollama pull llama3.3:70b`
- Verify available models: `ollama list`

**Processing performance:**
- Llama 70B requires significant compute resources
- Consider GPU acceleration if available
- Processing times: ~8s (simple) to ~250s (targeted) per document

## Citation

If you use this code or data in your research, please cite:

```bibtex
@article{your_paper_2026,
  title={Automated Extraction of Regulatory Information from Hydropower Documents Using Large Language Models},
  author={Your Name et al.},
  journal={Journal Name},
  year={2026}
}
```

## License

MIT License - See LICENSE file for details.

## Contact

For questions or issues, please open a GitHub issue or contact the authors.
