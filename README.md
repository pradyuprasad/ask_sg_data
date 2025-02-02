# Ask SG Data

Natural language interface to Singapore government datasets from data.gov.sg.

## Setup

1. Install [uv](https://github.com/astral-sh/uv) for dependency management
2. Clone this repository:
```
git clone [your-repo-url]
cd ask-sg-data
```

3. Create a virtual environment and install dependencies:
```
uv venv
source .venv/bin/activate  # On Windows use: .venv\Scripts\activate
uv pip install -r requirements.txt
```

4. Create a `.env` file with your API keys:
```
OPENAI_API_KEY=your_key_here
HUGGINGFACE_API_KEY=your_key_here  # Optional, for HF embeddings
```

## Usage

1. Initialize the data and embeddings:
```
uv run -m src.ask_sg_data.startup
```
This will:
- Fetch collections from data.gov.sg
- Download metadata for each collection
- Create embeddings for search
- Save everything to the `data/` directory

2. (Coming soon) Run the API server:
```
uv run -m src.ask_sg_data.api
```

## Project Structure
```
src/ask_sg_data/
├── __init__.py
├── api.py          # FastAPI endpoints
├── config.py       # Configuration and environment handling
├── startup.py      # Data initialization scripts
└── utils.py        # Helper functions
```

## Development

To recreate embeddings:
```
uv run -m src.ask_sg_data.startup --ignore-existing
```

## Data Sources

All data is sourced from [data.gov.sg](https://data.gov.sg/) via their public API.
