# LLM Pipeline Performance Study

**Production-Grade Document Extraction: A Comparative Analysis of LLM Capabilities**

## Abstract

This repository contains the complete implementation and evaluation code for our research testing 4 Large Language Models (LLMs) with production-grade document extraction pipelines. Our key finding: **only large-scale models can handle complex production prompts** for reliable deployment.

## Key Results

| Model | Production Pipeline | Speed (docs/hr) | Status |
|-------|-------------------|-----------------|---------|
| **Llama 3.3 70B** | **88.9%** | 5.7 | ✅ Production Ready |
| **GPT-OSS 20B** | **0%** | 6.6 | ❌ Complete Failure |
| **Llama 3 8B** | **0%** | 34.0 | ❌ Complete Failure |
| **Llama 3.2 3B** | **0%** | 28.8 | ❌ Complete Failure |

### Main Discovery
- **Only 70B model succeeds** with production-grade prompts (88.9% accuracy)
- **Smaller models completely fail** (0% success rate)
- **89 percentage point performance gap** between largest and smaller models
- **Model scale is critical** for complex prompt engineering

## Repository Structure

```
├── src/                     # Source code
│   ├── llama_70b_complex_pipeline.py       # 70B model implementation
│   ├── multi_model_complex_pipeline.py     # Multi-model testing
│   ├── api_handler.py                      # LLM API interface
│   ├── task_definitions_min_flow.py        # Production-grade prompts
│   ├── pdf_processor_min_flow.py          # Document processing
│   └── config.py                           # Configuration system
├── data/                    # Ground truth and test datasets
├── results/                 # Model performance results
├── figures/                 # Publication-ready visualizations
├── docs/                    # Additional documentation
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## Quick Start

### 1. Clone and Setup
```bash
git clone <repository-url>
cd Extract_LLM_FBA
./setup.sh
```

### 2. Add Your PDF Documents
```bash
# Copy your PDF files to the input folder
cp /path/to/your/documents/*.pdf data/input_pdfs/

# Or create symbolic links
ln -s /path/to/your/pdf/folder/* data/input_pdfs/
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Setup and Start Ollama (REQUIRED)
```bash
# Install Ollama if not already installed
curl -fsSL https://ollama.ai/install.sh | sh

# 🚨 IMPORTANT: Start Ollama server (MUST RUN FIRST)
ollama serve &

# Download models (this may take time - models are large)
ollama pull llama3.3:70b      # ~40GB
ollama pull llama3:8b         # ~4.7GB  
ollama pull llama3.2:3b       # ~2GB
ollama pull gpt-oss:20b       # ~12GB

# Verify Ollama is running
ollama run llama3.2:3b "Hello, are you working?"
```

> **⚠️ Critical Step:** You MUST run `ollama serve &` before running any experiments. The scripts will fail with clear error messages if Ollama is not running.

### 5. Run Experiments

**Test 70B Model:**
```bash
cd src
python llama_70b_complex_pipeline.py
```

**Test All Models:**
```bash
cd src
python multi_model_complex_pipeline.py
```

## Results
```bash
cd src/simple_pipeline
python multi_model_simple_pipeline.py
```

**Generate Comparison Analysis:**
```bash
cd src/evaluation
python create_comparison_analysis.py
```

## Models Tested

1. **Llama 3.3 70B** - State-of-the-art large model
2. **GPT-OSS 20B** - Mid-size open source model
3. **Llama 3 8B** - Efficient small-large model
4. **Llama 3.2 3B** - Resource-constrained model

## Methodology

### Ground Truth Validation
- **58 human-verified entries** from regulatory documents
- **54 matched test cases** with document text chunks
- **String matching with contextual validation**

### Pipeline Approaches
1. **Complex Pipeline**: Multi-stage processing with advanced prompting
2. **Simple Pipeline**: Direct extraction with minimal prompting

### Evaluation Metrics
- **Accuracy**: Exact match against human ground truth
- **Speed**: Documents processed per hour
- **Resource Efficiency**: Performance per parameter count

## Citation

If you use this code or data in your research, please cite:

```bibtex
@article{yourname2025llm,
  title={Engineering Approach vs Model Size: A Comparative Analysis of LLM Document Extraction Pipelines},
  author={Your Name},
  journal={Your Journal},
  year={2025}
}
```

## License

MIT License - see LICENSE file for details.

## Contact

- **Author**: [Your Name]
- **Email**: [your.email@domain.com]
- **Paper**: [Link to paper when published]

---

**Generated**: August 2025  
**Study Focus**: Engineering approach impact on LLM accessibility across model scales
