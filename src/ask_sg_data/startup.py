import requests
from typing import List, Dict, Any
import json
from src.ask_sg_data.config import Config
import os

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


def get_metadata_wrapper(config: Config, ignore_existing:bool) -> None:
    if not ignore_existing and os.path.isdir(config.collections_metadata_dir):
        print("metadata exists")
        return

    if not os.path.isfile(config.all_collections_list_path):
        raise ValueError("all collections don't exist! run the function to get the collections wrapper instead!")

    os.makedirs(config.collections_metadata_dir, exist_ok=True)

    collections_list: List[Dict[str, Any]]
    with open(config.all_collections_list_path, 'r') as f:
        collections_list = json.load(f)

    for collection in collections_list:
        # Clean filename - replace problematic characters
        collection_name = collection['name']
        safe_filename = collection_name.replace(' ', '_')\
                                     .replace('/', '_')\
                                     .replace('\\', '_')\
                                     .replace(':', '_')\
                                     .replace('*', '_')\
                                     .replace('?', '_')\
                                     .replace('"', '_')\
                                     .replace('<', '_')\
                                     .replace('>', '_')\
                                     .replace('|', '_')

        file_path = os.path.join(config.collections_metadata_dir, f"{safe_filename}.json")

        print(f"Getting metadata for: {collection['name']}")
        metadata = get_metatata_collection(collection)

        with open(file_path, 'w') as f:
            json.dump(metadata, f)
        print(f"Saved metadata for: {collection['name']}")


def main() -> None:
    config = Config.load()
    get_collections_wrapper(config)
    get_metadata_wrapper(config, ignore_existing=True)

main()
