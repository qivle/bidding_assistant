from pydantic import BaseModel
from typing import List, Dict, Optional

class AIConfig(BaseModel):
    baseUrl: str
    apiKey: str
    model: str
    model_flash: Optional[str] = None

class FileItem(BaseModel):
    name: str
    is_required: bool
    template_text: Optional[str] = None

class Volume(BaseModel):
    volume_name: str
    items: List[FileItem]

class FatalFlawItem(BaseModel):
    description: str
    page: str

class FatalFlawCategory(BaseModel):
    category: str
    items: List[FatalFlawItem]

class AnalysisResult(BaseModel):
    projectInfo: Dict[str, str]
    fatalFlaws: List[FatalFlawCategory]
    volumes: List[Volume]

