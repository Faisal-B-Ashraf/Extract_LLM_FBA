# Experimental LLM Reasoning Pipeline

This folder contains experimental work on using LLM reasoning for minimum flow extraction.

## Status: EXPERIMENTAL ⚠️

The main production pipeline uses **scoring-based selection** (in parent `src/` folder).
These LLM reasoning approaches are under development and may not work correctly.

## Files

**V17 - Structured Extraction + Deterministic + RLS:**
- `extraction_v17_structured.py` - Extract candidates with metadata
- `deterministic_selector_v17.py` - Rule-based pre-selection
- `api_handler_rls.py` - LLM reasoning for tie-breaking
- `llama_70b_v17_pipeline.py` - Integration pipeline
- Status: Has bugs, chunk loading issues

**V18 - Simple LLM Reading:**
- `llama_70b_v18_simple.py` - One LLM call per document (first 15 chunks)
- `llama_70b_v18_iterative.py` - Multiple LLM calls, reads all chunks in batches
- Status: V18 simple hits context limits; iterative untested

## Why Experimental?

1. Context window limitations (can't read 50+ chunks at once)
2. Inconsistent LLM responses
3. More complex than scoring approach
4. Accuracy not yet validated

## Production Pipeline

Use `../src/llama_70b_complex_pipeline.py` - the scoring-based approach that works.
