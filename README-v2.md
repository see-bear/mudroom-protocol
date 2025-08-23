# Mudroom Protocol — V2 Semantic Upgrade

This branch (`v2-semantic-upgrade`) introduces a fully restructured classifier designed for intelligent context engineering. It replaces the basic keyword system from V1 with semantic embeddings, topic flow analysis, and metadata-rich outputs.

---

## 🔍 What’s New in V2

- ✅ Semantic search using sentence-transformers
- ✅ Topic shift detection via cosine similarity
- ✅ Conversation chunking with session ID tagging
- ✅ Context-aware scoring (speaker transitions, topic pivots)
- ✅ Numpy serialization fixes for stable JSON output
- ✅ Fully locked Python 3.11.8 environment (see `requirements-locked-py311.txt`)

---

## 🧠 Key Components

| File | Purpose |
|------|---------|
| `mudroom_classifier_v2.py` | Main classifier logic |
| `semantic_scorer.py` | Embedding and similarity scoring |
| `context_analyzer.py` | Topic shifts, session segmentation |
| `test_context_analyzer.py` | Verifies flow analysis works |
| `metadata_enricher.py` | (Planned) Adds structured metadata to outputs |

---

## 🛠 How to Run

1. Activate the environment:
   ```bash
   venv\Scripts\activate
   ```

2. Run the main classifier:
   ```bash
   python run_mudroom_v2.py
   ```

3. Test the analyzer:
   ```bash
   python test_context_analyzer.py
   ```

---

## 🚧 Roadmap

See `UPGRADE_PLAN.md` for active development phases.