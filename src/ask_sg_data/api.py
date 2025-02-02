from fastapi import FastAPI, HTTPException, Depends
from src.ask_sg_data.models import SearchResponse, SearchMethod, Question
from src.ask_sg_data.search import HybridSearch
import faiss #type: ignore
import json
from src.ask_sg_data.config import Config

app = FastAPI(
    title="AskSGData",
    description="Natural language queries for Singapore public data",
    version="0.1.0"
)

class SearchSingleton:
    _instance = None

    @classmethod
    def get_instance(cls) -> HybridSearch:
        if cls._instance is None:
            config = Config.load()

            with open(config.all_collections_list_path, 'r') as f:
                collections = json.load(f)

            index = faiss.read_index(str(config.collections_embeddings_index))

            cls._instance = HybridSearch(
                collections=collections,
                faiss_index=index
            )
        return cls._instance


def get_search() -> HybridSearch:
    """Dependency to initialize search once and reuse"""
    return SearchSingleton.get_instance()


@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.post("/search", response_model=SearchResponse)
async def search(
    query: Question,
    search_method: SearchMethod = SearchMethod.HYBRID,
    use_hf: bool = False,
    searcher: HybridSearch = Depends(get_search)
):
    try:
        response = searcher.search(
            query=query.question,
            method=search_method,
            use_hf=use_hf
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
