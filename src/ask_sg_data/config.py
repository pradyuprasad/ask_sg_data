from typing import Optional
from dotenv import load_dotenv
import os
from pathlib import Path

load_dotenv()

class Config:
    _instance: Optional['Config'] = None
    base_dir = Path(__file__).resolve().parents[2]
    mini_model: str = "gpt-4o-mini"
    regular_model: str = "gpt-4o"
    openai_api_key: str
    hf_token: str
    data_dir = base_dir / 'data'
    data_input_dir = data_dir / 'input'
    all_collections_list_path = data_input_dir / 'all_collections.json'
    collections_metadata_dir = data_input_dir / 'collections_metadata'
    embeddings_dir = data_dir / 'embeddings'
    collections_embeddings_index = embeddings_dir / 'collections_embeddings.index'
    huggingface_embedding_model = 'sentence-transformers/all-MiniLM-L6-v2'
    huggingface_base_url = 'https://api-inference.huggingface.co/pipeline/feature-extraction'
    huggingface_embedding_endpoint = huggingface_base_url + '/' + huggingface_embedding_model

    def __new__(cls):
        if cls._instance is None:
            openai_api_key = os.getenv("OPENAI_API_KEY")
            hf_token = os.getenv("HUGGINGFACE_API_KEY")
            if openai_api_key is None:
                raise ValueError("OPENAI_API_KEY not found in environment")
            cls._instance = super().__new__(cls)
            cls._instance.openai_api_key = openai_api_key
            cls.hf_token = hf_token
            cls.data_dir.mkdir(parents=True, exist_ok=True)
            cls.data_input_dir.mkdir(parents=True, exist_ok=True)
        return cls._instance

    @classmethod
    def load(cls):
        return cls()

config = Config.load()
