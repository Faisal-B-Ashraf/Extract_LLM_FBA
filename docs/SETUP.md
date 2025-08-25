# Setup Instructions

## Prerequisites

1. **Python 3.8+**
2. **Ollama** (for local model execution)

## Installation Steps

### 1. Clone Repository
```bash
git clone <your-repository-url>
cd Extract_LLM_FBA
```

### 2. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 3. Install and Setup Ollama
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# 🚨 CRITICAL: Start Ollama service (REQUIRED BEFORE RUNNING EXPERIMENTS)
ollama serve &

# Download required models (this may take time)
ollama pull llama3.3:70b      # ~40GB
ollama pull llama3:8b         # ~4.7GB  
ollama pull llama3.2:3b       # ~2GB
ollama pull gpt-oss:20b       # ~12GB
```

### 4. Verify Setup
```bash
# Test if Ollama is working
ollama run llama3.2:3b "What is 2+2?"
```

> **⚠️ Important:** Always run `ollama serve &` in a terminal before starting experiments. You can check if it's running with `ps aux | grep ollama`.

## Running Experiments

### Quick Test (3B Model)
```bash
cd src/simple_pipeline
python multi_model_simple_pipeline.py --models llama3.2:3b --sample 5
```

### Full Experiment (All Models)
```bash
# Complex pipeline (70B only)
cd src/complex_pipeline
python llama_70b_complex_pipeline.py

# Complex pipeline (3 smaller models)
cd src/complex_pipeline
python multi_model_complex_pipeline.py

# Simple pipeline (all models)
cd src/simple_pipeline  
python multi_model_simple_pipeline.py

# Generate analysis
cd src/evaluation
python create_final_comparison.py
```

## Expected Runtime
- **Llama 3.2 3B**: ~2 minutes per document
- **Llama 3 8B**: ~1.5 minutes per document  
- **GPT-OSS 20B**: ~9 minutes per document
- **Llama 3.3 70B**: ~10 minutes per document

## Troubleshooting

### Ollama Not Responding
```bash
pkill ollama
ollama serve &
sleep 5
ollama run llama3.2:3b "test"
```

### Memory Issues
- Ensure 16GB+ RAM for 70B model
- Use 8GB+ RAM for smaller models
- Close other applications if needed

### GPU Acceleration (Optional)
Ollama automatically uses GPU if available (NVIDIA/AMD).
