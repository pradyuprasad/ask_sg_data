from ask_sg_data.config import Config
from ask_sg_data.models import SearchResponse, SearchResult, SearchScore
from ask_sg_data.startup import get_embedding_single_string
from rank_bm25 import BM25Okapi
import numpy as np
import faiss
from typing import List, Optional
from enum import Enum

class SearchMethod(Enum):
   SEMANTIC = "semantic"
   KEYWORD = "keyword"
   HYBRID = "hybrid"

class HybridSearch:
   def __init__(
       self,
       collections: List[dict],
       faiss_index: faiss.Index,
       semantic_weight: float = 0.5,
       keyword_weight: float = 0.5,
       k: int = 5,
       config: Optional[Config] = None
   ):
       if abs((semantic_weight + keyword_weight) - 1.0) > 0.001:
           raise ValueError("Weights must sum to 1.0")

       self.collections = collections
       self.faiss_index = faiss_index
       self.semantic_weight = semantic_weight
       self.keyword_weight = keyword_weight
       self.k = k
       self.config = config or Config.load()

       # Create BM25 index
       collection_texts = [f"{c['name']} {c['description']}" for c in collections]
       tokenized_texts = [text.lower().split() for text in collection_texts]
       self.bm25 = BM25Okapi(tokenized_texts)

   def semantic_search(self, query: str, use_hf: bool = False, k: Optional[int] = None) -> List[SearchResult]:
       k = self.k if k is None else k
       query_embedding = get_embedding_single_string(
           config=self.config,
           text=query,
           use_hf=use_hf
       )
       query_embedding = np.array([query_embedding], dtype=np.float32)
       if len(query_embedding.shape) == 1:
           query_embedding = query_embedding.reshape(1, -1)

       scores, indices = self.faiss_index.search(query_embedding, k)
       scores = 1 - (scores[0] / scores[0].max())  # Normalize distances to scores

       results = []
       for idx, score in zip(indices[0], scores):
           collection = self.collections[idx]
           results.append(SearchResult(
               collection_id=collection["collectionId"],
               name=collection["name"],
               description=collection["description"],
               scores=SearchScore(
                   semantic_score=float(score),
                   combined_score=float(score)
               )
           ))
       return results

   def keyword_search(self, query: str) -> List[SearchResult]:
       tokenized_query = query.lower().split()
       scores = self.bm25.get_scores(tokenized_query)
       scores = scores / scores.max()  # Normalize

       top_k_idx = np.argsort(scores)[-self.k:][::-1]
       results = []

       for idx in top_k_idx:
           collection = self.collections[idx]
           results.append(SearchResult(
               collection_id=collection["collectionId"],
               name=collection["name"],
               description=collection["description"],
               scores=SearchScore(
                   keyword_score=float(scores[idx]),
                   combined_score=float(scores[idx])
               )
           ))
       return results

   def hybrid_search(self, query: str, use_hf: bool = False) -> List[SearchResult]:
       semantic_results = self.semantic_search(query, use_hf)
       keyword_results = self.keyword_search(query)

       combined_results = {}

       for result in semantic_results:
           combined_results[result.collection_id] = {
               "name": result.name,
               "description": result.description,
               "semantic_score": result.scores.semantic_score,
               "keyword_score": 0.0
           }

       for result in keyword_results:
           if result.collection_id in combined_results:
               combined_results[result.collection_id]["keyword_score"] = result.scores.keyword_score
           else:
               combined_results[result.collection_id] = {
                   "name": result.name,
                   "description": result.description,
                   "semantic_score": 0.0,
                   "keyword_score": result.scores.keyword_score
               }

       # Calculate combined scores
       results = []
       for cid, data in combined_results.items():
           combined_score = (
               data["semantic_score"] * self.semantic_weight +
               data["keyword_score"] * self.keyword_weight
           )

           results.append(SearchResult(
               collection_id=cid,
               name=data["name"],
               description=data["description"],
               scores=SearchScore(
                   semantic_score=data["semantic_score"],
                   keyword_score=data["keyword_score"],
                   combined_score=combined_score
               )
           ))

       # Sort by combined score and return top k
       results.sort(key=lambda x: x.scores.combined_score, reverse=True)
       return results[:self.k]

   def search(
       self,
       query: str,
       method: SearchMethod = SearchMethod.HYBRID,
       use_hf: bool = False
   ) -> SearchResponse:
       if method == SearchMethod.SEMANTIC:
           results = self.semantic_search(query, use_hf)
       elif method == SearchMethod.KEYWORD:
           results = self.keyword_search(query)
       else:
           results = self.hybrid_search(query, use_hf)

       return SearchResponse(
           results=results,
           method=method
       )
