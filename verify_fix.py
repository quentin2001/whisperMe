"""Full verification after PyAnnote numpy fix + torchaudio downgrade"""
import sys
import os

# Use venv's packages
print("=== Environment ===")
print(f"Python: {sys.executable}")

# 1. Check numpy
import numpy as np
print(f"numpy: {np.__version__}")
print(f"np.nan exists: {hasattr(np, 'nan')}")

# 2. Check torch
import torch
print(f"torch: {torch.__version__}")
print(f"CUDA: {torch.cuda.is_available()}")

# 3. Check torchaudio
try:
    import torchaudio
    print(f"torchaudio: {torchaudio.__version__} ✅")
except Exception as e:
    print(f"torchaudio: FAILED - {e} ❌")

# 4. Check pyannote import chain
try:
    from pyannote.audio import Pipeline
    print(f"pyannote.audio Pipeline import: OK ✅")
except Exception as e:
    print(f"pyannote.audio Pipeline import: FAILED - {e} ❌")

try:
    from pyannote.audio import Model, Inference
    print(f"pyannote.audio Model/Inference import: OK ✅")
except Exception as e:
    print(f"pyannote.audio Model/Inference import: FAILED - {e} ❌")

# 5. Check speaker diarization pipeline specifically
try:
    from pyannote.audio.pipelines import SpeakerDiarization
    print(f"SpeakerDiarization pipeline import: OK ✅")
except Exception as e:
    print(f"SpeakerDiarization pipeline import: FAILED - {e} ❌")

print("\n=== Summary ===")
print("If all checks show ✅, the fix is successful!")
print("Restart the backend server and reprocess a podcast to verify end-to-end.")
