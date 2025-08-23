# Mudroom Protocol V2 — Upgrade Plan

This document outlines the planned phases, milestones, and deliverables for building a context-aware, semantically intelligent classifier pipeline for AI conversation analysis.

---

## ✅ Phase 1: Enhanced Core Classifier (COMPLETE)

**Goal:** Replace basic keyword matching with semantic understanding and foundational chunk processing.

**Key Components:**
- `semantic_scorer.py` – Embedding-based semantic similarity
- `mudroom_classifier_v2.py` – New classifier pipeline
- `test_context_analyzer.py` – Testing harness

---

## ✅ Phase 2: Intelligent Context Understanding (IN PROGRESS)

**Goal:** Analyze conversation flow, topic shifts, and speaker roles.

**Next Components:**
- `context_analyzer.py` – Session detection, flow tracking ✅
- `speaker_detector.py` – Score by user/AI turns (planned)
- `temporal_parser.py` – Identify time gaps, topic gaps (planned)

---

## 🔜 Phase 3: Enhanced Output & Metadata

**Goal:** Export structured insights with timestamps, confidence scores, and cross-session links.

**Planned Components:**
- `metadata_enricher.py` – JSON+YAML metadata output
- `output_formatter.py` – Markdown summaries, HTML export
- `session_linker.py` – Cross-reference similar sessions

---

## 🔜 Phase 4: CLI Tool & Batch System

**Goal:** Provide a professional-grade CLI interface.

**Planned Components:**
- `mudroom_cli.py` – Command-line interface
- `config_manager.py` – Configs per user/project
- `plugin_system.py` – Allow scoring/formatting extensions

---

## 🧪 Phase 5: Web Interface & Platform Integration

**Goal:** Build dashboard and live tools for UX.

**Planned Components:**
- `web_dashboard/` – FastAPI or Flask web app
- `browser_extension/` – Chrome/Firefox plugin
- `api_server.py` – Serve predictions via REST
- `export_plugins/` – Obsidian / Notion / Logseq integrations

---

## 🗂 Supporting Files

- `requirements-locked-py311.txt` – Stable environment
- `.gitignore` – Prevents venv/ and artifacts
- `README-v2.md` – Human-readable overview

---

## 👥 Contributors

- Chris Fitzgerald
- ChatGPT (contextual planner)
- Cursor (IDE agent)