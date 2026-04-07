import os

# ROOT DATA FOLDER
DATA_FOLDER = os.getenv("OPEN_NOTEBOOK_DATA_DIR", ".runtime-cache/state/local/data")

# LANGGRAPH CHECKPOINT FILE
sqlite_folder = f"{DATA_FOLDER}/sqlite-db"
os.makedirs(sqlite_folder, exist_ok=True)
LANGGRAPH_CHECKPOINT_FILE = f"{sqlite_folder}/checkpoints.sqlite"

# UPLOADS FOLDER
UPLOADS_FOLDER = f"{DATA_FOLDER}/uploads"
os.makedirs(UPLOADS_FOLDER, exist_ok=True)

# TIKTOKEN CACHE FOLDER
# Allow runtime environments to relocate the cache while keeping a blank-safe
# fallback to the canonical repo data tree.
TIKTOKEN_CACHE_DIR = (
    os.environ.get("TIKTOKEN_CACHE_DIR", "").strip() or f"{DATA_FOLDER}/tiktoken-cache"
)
os.makedirs(TIKTOKEN_CACHE_DIR, exist_ok=True)
