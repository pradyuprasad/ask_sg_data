import json
from src.ask_sg_data.config import Config

config = Config.load()
with open(config.all_collections_list_path, 'r') as f:
    data = json.load(f)

print(len(data))
for item in (data[:5]):
    print(str(item))
    print("="*50)
    print("\n \n")
