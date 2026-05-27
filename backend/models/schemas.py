from pydantic import BaseModel
from typing import List, Dict, Optional

class AIConfig(BaseModel):
    baseUrl: str
    apiKey: str
    model: str

class FileItem(BaseModel):
    name: str
    is_required: bool
    template_text: Optional[str] = None

class Volume(BaseModel):
    volume_name: str
    items: List[FileItem]

class AnalysisResult(BaseModel):
    projectInfo: Dict[str, str]
    fatalFlaws: List[str]
    volumes: List[Volume]
