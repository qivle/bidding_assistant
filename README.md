# 政企标书助手 (Bidding Assistant)

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Python](https://img.shields.io/badge/Python-3.8%2B-green.svg)
![Next.js](https://img.shields.io/badge/Next.js-14.0%2B-black.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

> 一个由大模型驱动的智能化政企招投标文件解析与生成平台。
> A Large Language Model-driven intelligent platform for parsing and generating government & enterprise bidding documents.

---

## 🌟 中文介绍 (Chinese)

政企标书助手是一款旨在解决企业在编写政企招投标文件时“格式繁琐、易漏项、模板提取难”等痛点的智能化系统。系统基于前端 React (Next.js) + 后端 FastAPI (Python) 架构，深度集成大语言模型，不仅能够智能解析长篇幅招标书，还能自动组装和排版标准的投标分册。

### ✨ 核心功能与最新优化
1. **智能解析与废标雷达扫描**
   - 自动解析数百页的长篇招标文件 (支持 `.docx`, `.pdf` 等格式)。
   - **废标雷达**：精准捕捉文档中的实质性响应项（如带有“★”、“▲”标记的废标项），自动提取物理页码并按“商务资质”、“技术参数”等类别分组展示，防范漏项风险。
2. **多 Agent 协同与质检核验机制 (Triple-Agent 架构)**
   - **Agent 1 (结构分析)**：梳理项目整体架构、提取关键项目信息。
   - **Agent 2 (模板匹配)**：逐一寻找并提取招标文件末尾的响应文件模板特征词。
   - **Agent 3 (质检与对齐)**：专门对提取的目录和卷册结构进行核验，自动纠偏，**智能找回丢失的原始序号**，并根据招标文件要求**合并同名分册**，防止信息漏缺。
3. **XML 级别原生 Word 模板深度克隆**
   - 采用底层 XML 节点级深度分析算法，**精准定位、切割并拷贝**源文件（Word）中的官方表格和承诺函排版，拒绝生硬的纯文本拼凑。
   - **格式清理**：在克隆过程中自动清理原文档中残留的页眉页脚，以及多余的强制换页符/节属性（`w:br` / `w:pageBreakBefore` / `w:sectPr`），保障生成文档结构健康。
4. **自适应排版与智能分页**
   - 在生成的 PDF/Word 分册中，为每个独立材料与小标题之间自动插入跨页分页符，确保排版美观大方，内容分布井然有序，杜绝页面挤压。
   - **边界安全保障**：引入了模板评分机制与智能正则匹配，能准确识别正文列表项（避免误识别为新模板标题），并在识别到下一个模板时自动精准截断，防止内容越界拷贝。
5. **便捷的一键启动机制**
   - 提供 `start_all.bat` 脚本，双击即可在一键在单个窗口静默启动前后端服务，并自动打开浏览器。

### 🚀 快速启动
1. 确保已安装 Node.js 和 Python (3.8+)。
2. 在 `backend` 目录下创建 `.env` 文件，并配置您的大模型 API 密钥（例如 `DEEPSEEK_API_KEY=your_key`）。
3. 安装依赖：
   - 后端：`cd backend && pip install -r requirements.txt`
   - 前端：`cd frontend && npm install`
4. 在项目根目录，双击运行 `start_all.bat`。

---

## 🌟 English Introduction

**Bidding Assistant** is an intelligent system designed to solve the pain points of writing government and enterprise bidding documents, such as tedious formatting, easily missed requirements, and difficult template extraction. Based on a React (Next.js) frontend and FastAPI (Python) backend architecture, the system deeply integrates Large Language Models to parse lengthy bidding documents and automatically assemble standard bidding volumes.

### ✨ Key Features
1. **Intelligent Parsing & Risk Radar**
   - Automatically parses lengthy bidding documents (supports `.docx`, `.pdf`, etc.).
   - **Risk Radar (废标雷达)**: Accurately captures substantive response items (marked with "★" or "▲"), extracts physical page numbers, and groups them by categories to prevent missing critical items.
2. **Triple-Agent Collaboration & QA Verification**
   - **Agent 1 (Structure Extraction)**: Extracts overall project info and requirements.
   - **Agent 2 (Template Association)**: Identifies template feature markers from the annex sections.
   - **Agent 3 (Quality Inspection)**: Runs a dedicated verification pass to align names, **restore missing index/hierarchy numbers**, and **merge duplicate volumes** to ensure strict adherence to the bidding document layout.
3. **XML-Level Native Word Template Cloning**
   - Uses deep XML node copying to **precisely slice and clone** original tables, styling, and forms.
   - **Cleanup Utilities**: Automatically strips residual headers, footers, page breaks, and section properties (`w:br`, `w:pageBreakBefore`, `w:sectPr`) during cloning to ensure document structural integrity.
4. **Adaptive Pagination & Formatting**
   - Automatically inserts standard page breaks between items and headings, preventing text crowding and ensuring professional publication-ready documents.
   - **Boundary Safety**: Implements heuristic scoring and pattern analysis to prevent misidentifying standard paragraphs as new template headers, ensuring clean boundaries during extraction.
5. **One-Click Local Launcher**
   - Run `start_all.bat` to launch both backend and frontend servers instantly and open the browser.

### 🚀 Quick Start
1. Ensure Node.js and Python (3.8+) are installed.
2. Create a `.env` file in the `backend` directory and configure your LLM API key (e.g., `DEEPSEEK_API_KEY=your_key`).
3. Install dependencies:
   - Backend: `cd backend && pip install -r requirements.txt`
   - Frontend: `cd frontend && npm install`
4. In the project root, run `start_all.bat` to start the application.

---

## 📄 开源协议 (License)

本项目采用 [MIT License](LICENSE) 开源协议。你可以自由使用、修改和分发本项目代码，但请保留原作者的版权声明和免责声明。
Built with ❤️ for efficient and precise bidding preparation.
