from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import json
from models.schemas import AIConfig, AnalysisResult
from services.parser_service import parse_document
from services.llm_service import extract_bidding_info
from services.generator_service import create_styled_document
from services.db_service import init_db, save_project, get_projects

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(title="Bidding Assistant API", lifespan=lifespan)

# 配置 CORS 允许前端跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "message": "Backend is running"}

@app.post("/api/analyze")
async def analyze_document(
    file: UploadFile = File(...),
    config: str = Form(...)
):
    try:
        # 1. 解析前端传来的大模型配置
        ai_config_dict = json.loads(config)
        ai_config = AIConfig(**ai_config_dict)
        
        # 2. 读取上传的文件内容
        file_bytes = await file.read()
        
        # 3. 解析文档文本 (PDF/DOCX)
        print(f"Parsing document: {file.filename}...")
        text = parse_document(file.filename, file_bytes)
        
        if not text or len(text.strip()) == 0:
            raise HTTPException(status_code=400, detail="未能从文档中提取到有效文本")
            
        # 4. 调用大模型提取招投标信息
        print("Extracting bidding info via LLM...")
        analysis_result = await extract_bidding_info(text, ai_config)
        
        return {
            "status": "success",
            "data": analysis_result
        }
    except Exception as e:
        print(f"Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate")
async def generate_document(
    data: str = Form(...),
    attachment: UploadFile = File(None)
):
    try:
        analysis_dict = json.loads(data)
        att_bytes = await attachment.read() if attachment else None
        doc_io = create_styled_document(analysis_dict, att_bytes)
        
        return StreamingResponse(
            doc_io,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={
                "Content-Disposition": "attachment; filename=Bidding_Document.docx"
            }
        )
    except Exception as e:
        print(f"Generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/projects")
async def create_project(data: dict):
    try:
        project_name = data.get('projectInfo', {}).get('name', '未命名项目')
        project_number = data.get('projectInfo', {}).get('number', '')
        pid = save_project(project_name, project_number, data)
        return {"status": "success", "id": pid}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/projects")
async def list_projects():
    try:
        return {"status": "success", "data": get_projects()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/projects/{project_id}")
async def get_project(project_id: str):
    from services.db_service import get_project_by_id
    proj = get_project_by_id(project_id)
    if proj:
        return {"status": "success", "data": proj}
    raise HTTPException(status_code=404, detail="Project not found")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

