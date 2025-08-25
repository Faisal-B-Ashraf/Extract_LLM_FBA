# Production-Grade LLM Pipeline Study

## ✅ Repository Ready for Publication

This repository demonstrates the **critical importance of model scale** for production-grade document extraction pipelines.

### � Research Focus
**Testing production-grade prompts across 4 LLM scales** to determine deployment viability

### 📊 Key Finding
**Only large-scale models (70B+) can handle complex production prompts**
- **Llama 3.3 70B**: 88.9% success ✅ Production Ready
- **GPT-OSS 20B**: 0% success ❌ Complete Failure  
- **Llama 3 8B**: 0% success ❌ Complete Failure
- **Llama 3.2 3B**: 0% success ❌ Complete Failure

### 🏗️ Repository Structure
**Clean, focused implementation** for production pipeline testing:

```
src/
├── llama_70b_complex_pipeline.py       # 70B model testing
├── multi_model_complex_pipeline.py     # Multi-model comparison  
├── task_definitions_min_flow.py        # Production-grade prompts
├── api_handler.py                      # LLM interface
├── pdf_processor_min_flow.py          # Document processing
└── config.py                           # Configuration system
```

### 🚀 User Experience
Paper readers can easily reproduce results:
1. **Clone repository**
2. **Run `./setup.sh`** (one-command setup)
3. **Add PDFs** to `data/input_pdfs/`
4. **Start Ollama** with `ollama serve &`
5. **Run experiments** with descriptive script names

### 🛡️ Production-Ready Features
- **Automatic PDF detection** and processing
- **Model availability checking** before testing
- **Clear error messages** with fix instructions
- **Ollama auto-start** attempts with fallback guidance
- **Professional output** with progress indicators

## 🎯 Research Impact

This repository demonstrates that:
- **Model scale is critical** for production deployment
- **Complex prompts require large models** (70B minimum)
- **Smaller models fail completely** with real-world complexity
- **Investment in large models is justified** for reliable production systems
