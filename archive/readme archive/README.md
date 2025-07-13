---

## 🧠 July 1, 2025 — Version 5 Release

- ✨ Introduced `mudroom_sorter_v5.py`:
  - Parses all `.txt` files in `batch_txts/`
  - Extracts **latest date mentioned in the text** (not file metadata)
  - Saves to `mudroom_logs/YYYY-MM-DD-filename-LX.md`
  - Includes emoji-tagging (e.g. ✅ = L2, 🎯 = L3, 🐛 = L1, 🧠 = L3)
- 🔁 Added `run_mudroom_sort_v5.bat` for Windows users
- 📦 Added `requirements.txt` for clean setup

Use case: drop your raw `.txt` logs in `batch_txts/`, double-click the `.bat`, and commit the outputs.