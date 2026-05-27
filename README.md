# 政企标书助手 (Bidding Assistant)

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Python](https://img.shields.io/badge/Python-3.8%2B-green.svg)
![Next.js](https://img.shields.io/badge/Next.js-14.0%2B-black.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

> 一个由大模型驱动的智能化政企招投标文件解析与生成平台。
> A Large Language Model-driven intelligent platform for parsing and generating government & enterprise bidding documents.

---

## 🌟 中文介绍 (Chinese)

政企标书助手是一款旨在解决企业在编写政企招投标文件时“格式繁琐、易漏项、模板提取难”等痛点的智能化系统。系统基于前端 React (Next.js) + 后端 FastAPI (Python) 架构，深度集成大语言模型（如 DeepSeek V4 Pro），不仅能够智能解析长篇幅招标书，还能自动组装和排版标准的投标分册。

### ✨ 核心功能
1. **智能解析与废标雷达扫描**
   - 自动解析数百页的长篇招标文件 (支持 `.docx`, `.pdf` 等格式)。
   - **废标雷达**：精准捕捉文档中的实质性响应项（如带有“★”、“▲”标记的废标项），自动提取物理页码并按“商务资质”、“技术参数”等类别分组展示，防范漏项风险。
2. **大模型深度特征提取 (双 Agent 架构)**
   - Agent 1 负责梳理项目整体架构、提取关键资质要求。
   - Agent 2 负责逐一提取并匹配招标文件中的附件及模板特征词。
3. **原生 Word 模板级精准切割与克隆**
   - 不再依赖生硬的文本拼凑。后端采用底层 XML 节点深度分析算法，能够**精准寻找、切割并拷贝**源文件（Word）中的官方表格和承诺函排版，自动过滤多余的大纲指引。
4. **一键分册生成与下载**
   - 按照常见投标标准，将材料自动化分为“资格文件”、“商务技术文件”、“报价文件”等多卷分册。
   - 自动插入跨页分页符、保留原有复杂样式格式，一键下载即可使用。
5. **便捷的一键启动机制**
   - 提供 `start_all.bat` 脚本，双击即可在单个窗口静默启动前后端服务，并自动打开浏览器。

### 🚀 快速启动
1. 确保已安装 Node.js 和 Python (3.8+)。
2. 在 `backend` 目录下创建 `.env` 文件，并配置您的大模型 API 密钥（例如 `DEEPSEEK_API_KEY=your_key`）。
3. 安装依赖：
   - 后端：`cd backend && pip install -r requirements.txt`
   - 前端：`cd frontend && npm install`
4. 在项目根目录，双击运行 `start_all.bat`。

---

## 🌟 English Introduction

**Bidding Assistant** is an intelligent system designed to solve the pain points of writing government and enterprise bidding documents, such as tedious formatting, easily missed requirements, and difficult template extraction. Based on a React (Next.js) frontend and FastAPI (Python) backend architecture, the system deeply integrates Large Language Models (like DeepSeek V4 Pro) to parse lengthy bidding documents and automatically assemble standard bidding volumes.

### ✨ Key Features
1. **Intelligent Parsing & Risk Radar**
   - Automatically parses hundreds of pages of lengthy bidding documents (supports `.docx`, `.pdf`, etc.).
   - **Risk Radar (废标雷达)**: Accurately captures substantive response items (such as rejection clauses marked with "★" or "▲"), automatically extracts physical page numbers, and groups them by categories like "Business Qualifications" and "Technical Parameters" to prevent missing critical items.
2. **Deep LLM Feature Extraction (Dual-Agent Architecture)**
   - Agent 1 structures the overall project requirements and extracts key qualifications.
   - Agent 2 extracts and matches attachment and template marker words from the bidding document.
3. **Native Word Template Precision Slicing & Cloning**
   - No more rigid text generation. The backend uses a deep XML node analysis algorithm to **precisely locate, slice, and clone** official tables and letter of commitment layouts from the original Word file, automatically filtering out redundant outline instructions.
4. **One-Click Volume Generation & Download**
   - Automatically divides materials into multiple volumes such as "Qualification Documents", "Business & Technical Documents", and "Quotation Documents" according to common bidding standards.
   - Automatically inserts page breaks, preserves complex original styles and formats, ready to download and use with one click.
5. **Convenient One-Click Startup**
   - Provides a `start_all.bat` script. Simply double-click to silently start both frontend and backend services in a single window and automatically open your browser.

### 🚀 Quick Start
1. Ensure Node.js and Python (3.8+) are installed.
2. Create a `.env` file in the `backend` directory and configure your LLM API key (e.g., `DEEPSEEK_API_KEY=your_key`).
3. Install dependencies:
   - Backend: `cd backend && pip install -r requirements.txt`
   - Frontend: `cd frontend && npm install`
4. In the project root, double-click `start_all.bat` to run.

---
*Built with ❤️ for efficient and precise bidding preparation.*
