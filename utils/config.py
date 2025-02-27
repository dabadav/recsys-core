# utils/config.py
from pathlib import Path

class Settings:
    DATA_PATH = Path(__file__).parent.parent / "data"
    SCORE_WEIGHTS = {"motor": 0.6, "cognitive": 0.3, "affective": 0.1}