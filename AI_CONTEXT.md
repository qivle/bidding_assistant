# AI_CONTEXT - Project Architecture & Handoff Guide

> **[TO THE AI AGENT READING THIS FILE]**
> You are picking up the development of the "Bidding Assistant" (政企标书智能辅助系统). Please read this context carefully before making any code changes.

## 1. Project Overview (项目概述)
This system is designed to automate the parsing of complex Chinese Bidding Documents (招标文件). It prevents fatal bidding flaws (废标) and dynamically generates native Microsoft Word (`.docx`) bid frameworks. 

**Key Features:**
- **Zero-Tolerance Checklist**: Forces users to review all "★" and "▲" clauses.
- **Multi-Agent Parsing**: Uses a chained LLM workflow to handle massive context windows.
- **Native Docx Generation**: Generates multi-volume (三分册) Word files and converts PDF attachments into high-res images appended to the document.
- **Project Library**: Saves parsed projects locally for later retrieval.

## 2. Tech Stack (技术栈)
- **Frontend**: Next.js 14 (App Router), React, TailwindCSS, shadcn/ui.
- **Backend**: Python 3.13, FastAPI, Uvicorn, SQLite.
- **AI Integration**: OpenAI Compatible Async API (`openai` Python package), dynamically configured by the frontend.
- **Parsers & Generators**: `pdfplumber` / `python-docx` (for reading), `PyMuPDF (fitz)` (for PDF-to-image conversion), `python-docx` (for writing).

## 3. Core Architecture (核心架构)

### Backend (`/backend`)
- **`main.py`**: The FastAPI entry point. Defines `/api/analyze`, `/api/generate`, and `/api/projects`.
- **`services/llm_service.py`**: Contains the critical **Multi-Agent Pipeline**.
  - *Agent 1*: Extracts Project Info, Fatal Flaws, and the Multi-Volume Structure (分册结构).
  - *Agent 2*: Traverses the extracted structure to find and extract exact text templates (e.g., 《承诺函》) from the original document.
- **`services/generator_service.py`**: Dynamically writes `.docx` files based on the LLM's volume array. Injects the cloned templates and appends `PyMuPDF`-rendered images.
- **`services/db_service.py`**: SQLite CRUD logic for the local Project Library.
- **`services/parser_service.py`**: Raw text extraction from PDF/Word.

### Frontend (`/frontend`)
- **`src/app/analyze/page.tsx`**: The core dashboard. Handles file uploads, the fatal flaw checklist logic, and the UI for the Multi-Agent parsed volumes. Posts to `/api/projects` and `/api/generate`.
- **`src/app/history/page.tsx`**: Displays saved projects from SQLite and allows regenerating the Word document.
- **`src/hooks/use-ai-config.ts`**: Manages the API Base URL, Key, and Model in browser `localStorage`.

## 4. Development Rules (未来的 AI 开发守则)
1. **Maintain the Multi-Agent Flow**: Chinese bidding documents are 50-150 pages long. Do not revert to single-shot LLM prompts, as they will cause context collapse and hallucination. Keep the `llm_service.py` pipeline robust.
2. **Strict Word Styling**: The generated Word document in `generator_service.py` must maintain strict Chinese official document standards (e.g., '宋体', correct PT sizes). Do not export raw text or markdown to the user for bidding purposes.
3. **Database Simplicity**: Stick to the local SQLite approach unless the user explicitly requests cloud deployment. This is meant to be a privacy-first, locally-run desktop web app.
4. **Execution**: To run locally, use the `start_all.bat` script at the root directory.
