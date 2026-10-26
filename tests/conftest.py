import os
import sys

# the app runs as `python src/main.py`, so its modules import each other from src/
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
