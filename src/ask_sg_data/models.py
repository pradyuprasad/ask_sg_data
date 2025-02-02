from enum import Enum
from pydantic import BaseModel
from typing import Any, Dict, Optional, List

# First, let's define our search types
class SearchMethod(Enum):
    SEMANTIC = "semantic"
    KEYWORD = "keyword"
    HYBRID = "hybrid"

# Then extend our minimal models to include search method info
class SearchScore(BaseModel):
    semantic_score: Optional[float] = None
    keyword_score: Optional[float] = None
    combined_score: Optional[float] = None

class SearchResult(BaseModel):
    collection_id: str
    name: str
    description: str
    scores: SearchScore

class SearchResponse(BaseModel):
    results: List[SearchResult]
    method: SearchMethod

class Question(BaseModel):
   question: str

class APIResponse(BaseModel):
   text_response: str
   visualization_data: Optional[Dict[str, Any]] = None
   sources: list[str]
