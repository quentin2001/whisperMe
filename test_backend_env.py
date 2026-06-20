import sys
import os
import traceback

sys.path.insert(0, 'e:/Projects/whisperMe/backend')
import app.config

from pyannote.audio import Pipeline
from app.config import HF_TOKEN

try:
    print("Loading pipeline...")
    Pipeline.from_pretrained('pyannote/speaker-diarization-3.1', use_auth_token=HF_TOKEN)
    print("SUCCESS")
except Exception as e:
    print(f"FAILED with {type(e).__name__}: {e}")
    traceback.print_exc()
