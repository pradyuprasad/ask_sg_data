from dotenv import load_dotenv
import os

load_dotenv()

class Config:
    _instance: 'Config' | None = None
    mini_model: str = "gpt-4o-mini"
    regular_model: str = "gpt-4"
    openai_api_key: str

    def __new__(cls):
        if cls._instance is None:
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key is None:
                raise ValueError("OPENAI_API_KEY not found in environment")

            cls._instance = super(Config, cls).__new__(cls)
            cls._instance.openai_api_key = api_key
        return cls._instance

    @classmethod
    def load(cls):
        return cls()

config = Config.load()
