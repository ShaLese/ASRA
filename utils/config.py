import os
from dotenv import load_dotenv
import logging
from pathlib import Path

# Load environment variables
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RESEARCH_PAPERS_DIR = DATA_DIR / "research_papers"
EXPERIMENTAL_DATA_DIR = DATA_DIR / "experimental_data"
OUTPUTS_DIR = DATA_DIR / "outputs"

# Create directories if they don't exist
for dir_path in [RESEARCH_PAPERS_DIR, EXPERIMENTAL_DATA_DIR, OUTPUTS_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# API Keys and Model configurations
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

# Model configurations
MODEL_CONFIGS = {
    "literature_review": {
        "bert_model": "bert-base-uncased",
        "specter_model": "allenai/specter",
    },
    "hypothesis_generator": {
        "model": "deepseek-ai/deepseek-coder-6.7b-instruct",
    },
    "data_analysis": {
        "tabnet_params": {
            "n_d": 8,
            "n_a": 8,
            "n_steps": 3,
        }
    },
    "visualization": {
        "stable_diffusion_model": "stabilityai/sd-v1-5",
    }
}

# Setup logging
def setup_logging(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Create handlers
    c_handler = logging.StreamHandler()
    f_handler = logging.FileHandler(OUTPUTS_DIR / f"{name}.log")
    
    # Create formatters
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    c_handler.setFormatter(formatter)
    f_handler.setFormatter(formatter)
    
    # Add handlers to the logger
    logger.addHandler(c_handler)
    logger.addHandler(f_handler)
    
    return logger
