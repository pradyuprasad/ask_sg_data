import numpy as np
import requests
from typing import List, Dict, Any
import json

from sentence_transformers import SentenceTransformer
from src.ask_sg_data.config import Config
import os
from src.ask_sg_data.utils import make_safe_filename
import time
import faiss

def fetch_all_collections() -> List[Dict[str, Any]]:
    """Fetch all collections from the API by paginating until no more data is available."""
    base_url: str = "https://api-production.data.gov.sg/v2/public/api/collections"
    page: int = 1
    all_collections: List[Dict[str, Any]] = []

    while True:
        params: Dict[str, int] = {"page": page}
        print("sending with page", page)
        response = requests.get(base_url, params=params)

        if response.status_code != 200:
            print(f"Error: Received status code {response.status_code}")
            break

        data: Dict[str, Any] = response.json()

        if "data" not in data or "collections" not in data["data"]:
            print("No more collections or invalid response format.")
            break

        collections: List[Dict[str, Any]] = data["data"]["collections"]
        if not collections:
            print("No more collections to fetch.")
            break

        all_collections.extend(collections)
        page += 1

    return all_collections



def print_collections(collections: List[Dict[str, Any]]) -> None:
    """Print a summary of collections."""
    print(f"Total collections fetched: {len(collections)}")

def get_collections_wrapper(config: Config, ignore_existing:bool = False) -> None:
    if not ignore_existing and os.path.isfile(config.all_collections_list_path):
        print("collections already exists")
        return
    print("starting to load all collections")
    all_collections: List[Dict[str, Any]] = fetch_all_collections()
    all_collections = sorted(all_collections, key=lambda x: int(x["collectionId"]))
    with open(config.all_collections_list_path, 'w') as f:
        json.dump(all_collections, f)
    print("saved to", config.all_collections_list_path)
    print_collections(all_collections)


def get_metatata_collection(collection: Dict[str, Any]) -> Dict[str, Any]:
   """Fetch metadata for a single collection including its datasets.

   Args:
       collection: Dictionary containing collection info with at least collectionId

   Returns:
       Dict containing collection and dataset metadata

   Raises:
       requests.exceptions.RequestException: If API call fails
   """
   collection_id = collection["collectionId"]
   url = f"https://api-production.data.gov.sg/v2/public/api/collections/{collection_id}/metadata"
   params = {"withDatasetMetadata": "true"}

   response = requests.get(url, params=params)
   if response.status_code != 200:
       print(f"Error fetching metadata for collection {collection_id}: {response.status_code}")
       return {}

   data: Dict[str, Any] = response.json()

   if "data" not in data:
       print(f"Invalid response format for collection {collection_id}")
       return {}

   return data


def get_metadata_wrapper(config: Config, ignore_existing:bool=False) -> None:
    if not os.path.isfile(config.all_collections_list_path):
        raise ValueError("all collections don't exist! run the function to get the collections wrapper instead!")

    collections_list: List[Dict[str, Any]]
    with open(config.all_collections_list_path, 'r') as f:
        collections_list = json.load(f)

    dir_exists:bool = os.path.isdir(config.collections_metadata_dir)
    count_dir_correct: bool = len([p for p in config.collections_metadata_dir.glob('*') if p.is_file()]) == len(collections_list)



    if not ignore_existing and count_dir_correct:
        print("metadata exists with correct length")
        return

    if not ignore_existing and dir_exists and not count_dir_correct:
        print("directory exists but file length is wrong")


    os.makedirs(config.collections_metadata_dir, exist_ok=True)


    for collection in collections_list:
        collection_name = collection['name']
        safe_filename = make_safe_filename(collection_name)

        file_path = os.path.join(config.collections_metadata_dir, f"{safe_filename}.json")

        print(f"Getting metadata for: {collection['name']}")
        metadata = get_metatata_collection(collection)

        with open(file_path, 'w') as f:
            json.dump(metadata, f)
        print(f"Saved metadata for: {collection['name']}")


def get_embedding_single_string(config: Config, text: str, use_hf: bool = True) -> List[float]:
    print(f"getting embedding for {text} with use api as {use_hf}")
    if use_hf:
       # HF API version
       while True:
           headers = {"Authorization": f"Bearer {config.hf_token}"}
           payload = {"inputs": [text]}
           response = requests.post(config.huggingface_embedding_endpoint, headers=headers, json=payload)
           output = response.json()

           if isinstance(output, list):
               return output[0]

           print(f"Error response: {output}")
           time.sleep(1)
    else:
       # Local embeddings using sentence-transformers
       model = SentenceTransformer('all-MiniLM-L6-v2')  # Fast and lightweight model
       embedding = model.encode(text, convert_to_tensor=False)  # Returns numpy array
       return embedding.tolist()  # Convert to list to match HF API output format


def get_text_from_collection(collection: Dict[str, Any]) -> str:
    if 'name' not in collection:
        raise KeyError("Missing 'name' in collection.")
    name = collection['name']
    description = collection.get('description', 'No description available')
    if 'description' not in collection:
        print(f"Description not found for collection: {name}")
    return f"Name: {name} \nDescription: {description}"

def create_embeddings(config: Config, ignore_existing: bool = False) -> None:
   # Check for collections list
   if not os.path.isfile(config.all_collections_list_path):
       raise ValueError("all collections don't exist! run the function to get the collections wrapper instead!")

   # Load collections
   with open(config.all_collections_list_path, 'r') as f:
       collections_list = json.load(f)

   # Verify metadata files exist
   count_dir_correct = len([p for p in config.collections_metadata_dir.glob('*') if p.is_file()]) == len(collections_list)
   if not count_dir_correct:
       raise ValueError(f"Expected {len(collections_list)} json files but got only {len([p for p in config.collections_metadata_dir.glob('*') if p.is_file()])} json files")

   # Get embeddings
   embeddings = []
   for collection in collections_list:
       text = get_text_from_collection(collection)
       name = collection['name']
       print(f"Getting embedding for: {name}")

       embedding = get_embedding_single_string(config=config, text=text, use_hf=False)
       embeddings.append(embedding)

       time.sleep(2)

   # Create and save Faiss index
   embeddings_array = np.array(embeddings, dtype=np.float32)
   dimension = len(embeddings[0])
   index = faiss.IndexFlatL2(dimension)
   index.add(embeddings_array)

   faiss.write_index(index, str(config.collections_embeddings_index))




def main() -> None:
    config = Config.load()
    get_collections_wrapper(config)
    get_metadata_wrapper(config)
    create_embeddings(config)

main()
