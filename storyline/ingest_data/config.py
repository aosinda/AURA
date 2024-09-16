import os
from dotenv import load_dotenv, find_dotenv

# Load environment variables
env_file = find_dotenv(".env")
load_dotenv(env_file)

DATA_PATH = "data"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
QUADRANT_API_KEY = os.getenv("QUADRANT_API_KEY")
QDRANT_URL = os.getenv("QDRANT_URL")
